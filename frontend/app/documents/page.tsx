"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getUploadsList,
  UploadedDocument,
} from '@/lib/api/documentUpload';
// deleteUpload wird nicht mehr verwendet - alle Löschungen verwenden Soft Delete
import {
  getDocumentsByStatus,
  changeDocumentStatus,
  WorkflowStatus,
  WorkflowDocument,
  getWorkflowStatusBadge,
  getWorkflowStatusName,
  StatusChangeRequest,
  getAllowedTransitions
} from '@/lib/api/documentWorkflow';
import { getInterestGroups, InterestGroup, createInterestGroupLookup, getInterestGroupName } from '@/lib/api/interestGroups';
import { apiClient } from '@/lib/api/rag';
import StatusChangeModal from './StatusChangeModal';
import DocumentSkeleton, { DocumentSkeletonList } from '@/components/DocumentSkeleton';
import { EmptyDocumentsState, EmptySearchState } from '@/components/EmptyState';
import Spinner from '@/components/ui/Spinner';
import { Eye, Trash2 } from 'lucide-react';
import { useUser } from '@/lib/contexts/UserContext';
import FailedDocumentsPanel from '@/components/FailedDocumentsPanel';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
}

interface KanbanColumn {
  id: WorkflowStatus;
  title: string;
  icon: string;
  color: string;
  documents: WorkflowDocument[];
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentListPage() {
  const router = useRouter();
  const { userLevel, isLoading: userContextLoading, canPerformActionOnDocument } = useUser();
  
  // ALLE HOOKS MÜSSEN VOR DEM FRÜHEN RETURN SEIN!
  // State - Alle useState Hooks zuerst
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [interestGroups, setInterestGroups] = useState<InterestGroup[]>([]);
  const [interestGroupLookup, setInterestGroupLookup] = useState<Map<number, InterestGroup>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedDocument, setDraggedDocument] = useState<WorkflowDocument | null>(null);
  const [draggedFromColumn, setDraggedFromColumn] = useState<WorkflowStatus | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [targetStatus, setTargetStatus] = useState<WorkflowStatus | null>(null);
  const [selectedInterestGroups, setSelectedInterestGroups] = useState<number[]>([]);
  
  // Filter state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // NEU: State für gecachte Original-Namen (um API-Calls zu vermeiden)
  const [originalDocumentNames, setOriginalDocumentNames] = useState<Map<number, string>>(new Map());
  
  // State für fehlgeschlagene Dokumente
  const [failedDocuments, setFailedDocuments] = useState<UploadedDocument[]>([]);
  
  // RBAC Phase 7: View-Mode initialisieren basierend auf User-Level
  // Level 2: Immer 'table', Level 3+: Default 'kanban'
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>(() => {
    // Initialisierung erfolgt beim Component-Mount
    // Wir müssen auf userLevel warten, daher setzen wir einen Default
    // NEU: Default 'kanban' für bessere excludeRagIndexed Logik beim ersten Laden
    return 'kanban'; // Default (wird später basierend auf userLevel angepasst)
  });
  
  // RBAC Phase 7: Kanban vs. Table View basierend auf User-Level
  // Level 2: Nur Tabelle, Level 3+: Kanban erlaubt (global)
  const canViewKanban = userLevel >= 3;
  
  // RBAC Phase 8: Workflow-Buttons basierend auf User-Level
  // Level 1-2: Keine Workflow-Transitions
  // Level 3: Nur Draft → Reviewed (nur eigene IG mit Level >= 3)
  // Level 4-5: Alle Transitions
  const canChangeStatus = userLevel >= 3; // Global permission (context-specific wird pro Dokument geprüft)
  const canApproveOrReject = userLevel >= 4; // Nur Level 4+ können approved/rejected setzen
  
  /**
   * RBAC Multi-Level: Helper für required_level für Status-Transitions
   */
  const getRequiredLevelForTransition = (fromStatus: WorkflowStatus, toStatus: WorkflowStatus): number => {
    // Workflow Rules:
    // draft → reviewed: Level 3+
    // draft → approved: Level 4+
    // reviewed → approved: Level 4+
    // reviewed → rejected: Level 4+
    // rejected → draft: Level 3+
    
    if (fromStatus === 'draft' && toStatus === 'reviewed') return 3
    if (fromStatus === 'draft' && toStatus === 'approved') return 4
    if (fromStatus === 'reviewed' && toStatus === 'approved') return 4
    if (fromStatus === 'reviewed' && toStatus === 'rejected') return 4
    if (fromStatus === 'rejected' && toStatus === 'draft') return 3
    
    return 5 // Ungültige Transition = sehr hoch, wird blockiert
  }
  
  // ============================================================================
  // API CALLS - MÜSSEN VOR useEffects SEIN
  // ============================================================================

  const loadDocumentTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/document-types/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      
      // Backend liefert direkt ein Array, nicht data.document_types
      let allTypes: DocumentType[] = [];
      if (Array.isArray(data)) {
        allTypes = data;
      } else if (data.document_types && Array.isArray(data.document_types)) {
        allTypes = data.document_types;
      } else {
        console.error('Invalid document types response format:', data);
        setDocumentTypes([]);
        return;
      }
      
      // RBAC Multi-Level: Für Level 2-3 nur DocumentTypes mit Dokumenten in User-IGs anzeigen
      // Level 4-5: Alle DocumentTypes anzeigen
      if (userLevel >= 4) {
        // Level 4-5: Alle Typen anzeigen
        setDocumentTypes(allTypes);
      } else {
        // Level 2-3: Hole Counts (bereits RBAC-gefiltert durch Backend)
        try {
          const typeIds = allTypes.map(type => type.id);
          const countsResponse = await apiClient.getDocumentTypeCounts(typeIds);
          const counts = countsResponse.data || {};
          
          // Filtere: Nur DocumentTypes mit count > 0 (haben Dokumente in User-IGs)
          const filteredTypes = allTypes.filter(type => {
            const count = counts[type.id] || 0;
            return count > 0;
          });
          
          setDocumentTypes(filteredTypes);
        } catch (countError) {
          console.warn('Fehler beim Laden der Document Type Counts:', countError);
          // Bei Fehler: Leere Liste für Level 2-3 (sicherer)
          setDocumentTypes([]);
        }
      }
    } catch (error) {
      console.error('Failed to load document types:', error);
      setDocumentTypes([]);
    }
  };

  const loadInterestGroups = async () => {
    try {
      const groups = await getInterestGroups();
      setInterestGroups(groups);
      setInterestGroupLookup(createInterestGroupLookup(groups));
    } catch (error) {
      console.error('Failed to load interest groups:', error);
    }
  };

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Initialize columns
      const initialColumns: KanbanColumn[] = [
        {
          id: 'draft',
          title: 'Entwurf',
          icon: '📝',
          color: 'gray',
          documents: []
        },
        {
          id: 'reviewed',
          title: 'Geprüft',
          icon: '✓',
          color: 'blue',
          documents: []
        },
        {
          id: 'approved',
          title: 'Freigegeben',
          icon: '✅',
          color: 'green',
          documents: []
        },
        {
          id: 'rejected',
          title: 'Zurückgewiesen',
          icon: '❌',
          color: 'red',
          documents: []
        }
      ];

      // Load documents for each status
      // NEU: excludeRagIndexed=true für Kanban (indexierte Dokumente ausschließen)
      // Für Tabelle: excludeRagIndexed=false (alle Dokumente anzeigen)
      const excludeRagIndexed = viewMode === 'kanban';  // Nur für Kanban indexierte Dokumente ausschließen
      
      for (const column of initialColumns) {
        const response = await getDocumentsByStatus(
          column.id, 
          selectedInterestGroups.length > 0 ? selectedInterestGroups : undefined,
          selectedDocumentTypeId || undefined,
          excludeRagIndexed  // NEU: Für Kanban=true (filtert indexierte), für Tabelle=false (zeigt alle)
        );
        if (response.success && response.data) {
          // RBAC Multi-Level: Filtere Dokumente für Kanban basierend auf IG-Level
          // Level 4-5: Alle Dokumente (bereits gefiltert durch Backend)
          // Level 1-3: Nur Dokumente, für die User das entsprechende Level hat
          if (userLevel < 4 && canViewKanban) {
            // Level 3: Nur Dokumente mit IG-Level >= 3 für Kanban
            column.documents = response.data.documents.filter(doc => 
              canPerformActionOnDocument(doc.interest_group_ids || [], 3)
            )
          } else {
            // Level 2 oder Level 4+: Alle Dokumente (Level 2 sieht nur Tabelle, Level 4+ sieht alles)
            column.documents = response.data.documents
          }
          
          // NEU: Index-Status wird bereits vom Backend geliefert, kein separater API-Call mehr nötig!
          // (Optimierung: Index-Status ist jetzt Teil des WorkflowDocumentSchema)
          
          // NEU: Für Entwurf-Spalte: Nur Dokumente mit AI-Verarbeitung SUCCESS anzeigen
          // Gilt für BEIDE Ansichten (Kanban UND Tabelle), damit Konsistenz gewährleistet ist
          // OPTIMIERT: Pages sind bereits via joinedload geladen, aber nicht im Frontend verfügbar
          // Daher müssen wir noch getUploadDetails aufrufen, aber nur für Draft-Dokumente
          if (column.id === 'draft') {
            const { getUploadDetails } = await import('@/lib/api/documentUpload');
            
            // Prüfe für jedes Dokument im Entwurf, ob mindestens eine Seite SUCCESS hat
            const documentsWithSuccess = await Promise.all(
              column.documents.map(async (doc) => {
                try {
                  const detailsResponse = await getUploadDetails(doc.id);
                  if (detailsResponse.success && detailsResponse.document.pages) {
                    // Prüfe ob mindestens eine Seite AI-Verarbeitung SUCCESS hat
                    const hasSuccessPage = detailsResponse.document.pages.some(
                      page => page.ai_processing_result?.status === 'success'
                    );
                    if (hasSuccessPage) {
                      // WICHTIG: Übernehme Duplikat-Felder aus detailsResponse (sonst gehen sie verloren!)
                      return {
                        ...doc,
                        is_duplicate: detailsResponse.document.is_duplicate || false,
                        duplicate_of_document_id: detailsResponse.document.duplicate_of_document_id || null
                      };
                    }
                    return null;
                  }
                  return null; // Dokument ohne Details oder ohne SUCCESS → ausblenden
                } catch (error) {
                  console.warn(`Failed to check AI processing status for document ${doc.id}:`, error);
                  return null; // Bei Fehler ausblenden (sicherer)
                }
              })
            );
            
            // Filtere null-Werte heraus (Dokumente ohne SUCCESS)
            column.documents = documentsWithSuccess.filter((doc) => doc !== null) as WorkflowDocument[];
          }
        }
      }

      setColumns(initialColumns);
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError(error.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (documentId: number, newStatus: WorkflowStatus, reason?: string) => {
    try {
      const request: StatusChangeRequest = {
        new_status: newStatus,
        reason: reason || `Status changed to ${getWorkflowStatusName(newStatus)}`
      };

      const response = await changeDocumentStatus(documentId, request);
      
      if (response.success) {
        // Reload documents to reflect changes
        await loadDocuments();
      } else {
        alert(`Status-Änderung fehlgeschlagen: ${response.error}`);
      }
    } catch (error: any) {
      console.error('Status change error:', error);
      alert(`Fehler: ${error.message || 'Unbekannter Fehler'}`);
    }
  };

  const handleDelete = async (documentId: number, filename: string, isIndexed?: boolean) => {
    // WICHTIG: IMMER Soft Delete verwenden (damit Dokumente im Archiv erscheinen)
    // Hard Delete nur aus dem Archiv möglich (Level 5)
    const confirmMessage = isIndexed === true
      ? `"${filename}" ist bereits in RAG indexiert.\n\nEs wird eine Soft Delete durchgeführt (Archivierung + RAG Cleanup).\n\nMöchten Sie fortfahren?`
      : `Möchten Sie "${filename}" wirklich löschen?\n\nDas Dokument wird ins Archiv verschoben (Soft Delete).\n\nFür endgültige Löschung: Gehen Sie ins Archiv.`;
    
    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      // IMMER Soft Delete verwenden (auch für nicht-indexierte Dokumente)
      const reason = prompt('Bitte geben Sie einen Grund für die Löschung an:');
      if (!reason || reason.trim() === '') {
        alert('Löschung abgebrochen: Kein Grund angegeben');
        return;
      }
      
      const { softDeleteDocument } = await import('@/lib/api/documentWorkflow');
      const response = await softDeleteDocument(documentId, reason.trim());
      
      if (response.success) {
        const message = isIndexed === true
          ? '✅ Dokument erfolgreich gelöscht (Soft Delete + RAG Cleanup durchgeführt)'
          : '✅ Dokument erfolgreich gelöscht (Soft Delete - Dokument erscheint im Archiv)';
        alert(message);
        // NEU: Kurzes Delay für Server-Update, dann Reload
        setTimeout(() => {
          loadDocuments().catch(error => {
            console.error('Error reloading after delete:', error);
          });
        }, 200);
      } else {
        alert(`Fehler beim Soft Delete: ${response.error || 'Unbekannter Fehler'}`);
      }
    } catch (error: any) {
      console.error('Delete error:', error);
      alert(`Löschen fehlgeschlagen: ${error.message || 'Unbekannter Fehler'}`);
    }
  };

  // ============================================================================
  // DRAG & DROP HANDLERS
  // ============================================================================

  const handleDragStart = (e: React.DragEvent, document: WorkflowDocument, fromColumn: WorkflowStatus) => {
    // RBAC Phase 8: Drag nur erlauben wenn User Status ändern darf (global)
    if (!canChangeStatus) {
      e.preventDefault();
      return;
    }
    
    // RBAC Multi-Level: Prüfe ob User für dieses Dokument Status ändern darf
    // Mindestens Draft → Reviewed (Level 3) muss möglich sein
    const canDrag = canPerformActionOnDocument(document.interest_group_ids || [], 3)
    if (!canDrag) {
      e.preventDefault();
      return;
    }
    
    setDraggedDocument(document);
    setDraggedFromColumn(fromColumn);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e: React.DragEvent, toColumn: WorkflowStatus) => {
    e.preventDefault();
    
    if (!draggedDocument || !draggedFromColumn || draggedFromColumn === toColumn) {
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // RBAC Phase 8: Frontend-Prüfung basierend auf User-Level (global)
    if (!canChangeStatus) {
      alert('Sie haben keine Berechtigung, den Status zu ändern');
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // RBAC Multi-Level: Context-specific Permission Check
    const requiredLevel = getRequiredLevelForTransition(draggedFromColumn, toColumn)
    const canPerform = canPerformActionOnDocument(draggedDocument.interest_group_ids || [], requiredLevel)
    
    if (!canPerform) {
      alert(`Sie haben keine Berechtigung, dieses Dokument von ${draggedFromColumn} nach ${toColumn} zu verschieben. Benötigt Level ${requiredLevel} für die Interest Group(s) dieses Dokuments.`)
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // RBAC Phase 8: Zusätzliche Validierung für Level 3 (nur Draft → Reviewed)
    if (userLevel === 3) {
      if (!(draggedFromColumn === 'draft' && toColumn === 'reviewed')) {
        alert('Als Abteilungsleiter können Sie Dokumente nur von Entwurf nach Geprüft verschieben');
        setDraggedDocument(null);
        setDraggedFromColumn(null);
        return;
      }
    }

    // RBAC Phase 8: Level 4+ kann approved/rejected, Level 3 nicht
    if (!canApproveOrReject && (toColumn === 'approved' || toColumn === 'rejected')) {
      alert('Nur QM-Mitarbeiter können Dokumente freizugeben oder zurückweisen');
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // Prüfe ob Status-Änderung erlaubt ist (Backend-Validierung)
    try {
      const allowedTransitions = await getAllowedTransitions(draggedDocument.id);
      if (!allowedTransitions.includes(toColumn)) {
        alert('Diese Status-Änderung ist nicht erlaubt');
        setDraggedDocument(null);
        setDraggedFromColumn(null);
        return;
      }
    } catch (error) {
      console.error('Error checking allowed transitions:', error);
      alert('Fehler beim Prüfen der Berechtigung');
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // Zeige Modal für Status-Änderung
    setTargetStatus(toColumn);
    setShowStatusModal(true);
  };

  // ENTFERNT: shouldReloadAfterStatusChange Flag - wird nicht mehr benötigt
  // (Reload erfolgt jetzt direkt in handleStatusChangeSuccess)

  const handleStatusChangeSuccess = () => {
    const changedDocumentId = draggedDocument?.id;
    const fromStatus = draggedFromColumn;
    const toStatus = targetStatus;
    
    console.log('[DocumentListPage] handleStatusChangeSuccess called', { changedDocumentId, fromStatus, toStatus });
    
    // NEU: Optimistisches UI-Update - verschiebe Dokument sofort in neue Spalte
    if (changedDocumentId && fromStatus && toStatus) {
      setColumns(prevColumns => {
        const newColumns = prevColumns.map(col => {
          // Entferne Dokument aus alter Spalte
          if (col.id === fromStatus) {
            return {
              ...col,
              documents: col.documents.filter(doc => doc.id !== changedDocumentId)
            };
          }
          // Füge Dokument zur neuen Spalte hinzu (mit aktualisiertem Status)
          if (col.id === toStatus) {
            const updatedDoc = draggedDocument ? {
              ...draggedDocument,
              workflow_status: toStatus
            } : null;
            
            // Prüfe ob Dokument bereits in Zielspalte vorhanden ist (vermeidet Duplikate)
            const exists = col.documents.some(doc => doc.id === changedDocumentId);
            if (updatedDoc && !exists) {
              return {
                ...col,
                documents: [...col.documents, updatedDoc]
              };
            }
          }
          return col;
        });
        return newColumns;
      });
    }
    
    // Reset State
    setDraggedDocument(null);
    setDraggedFromColumn(null);
    setTargetStatus(null);
    setShowStatusModal(false);
    
    // NEU: Direktes Reload (ohne Flag-Delay) für konsistente Daten
    // Reload mit kurzem Delay, damit React State-Updates verarbeitet hat
    setTimeout(() => {
      console.log('[DocumentListPage] Reloading documents after status change...');
      loadDocuments().catch(error => {
        console.error('[DocumentListPage] Error reloading documents:', error);
      });
    }, 300);
    
    // RBAC Fix: Dispatch Event für Detail-Seite Auto-Refresh
    if (changedDocumentId) {
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('documentStatusChanged', {
          detail: { documentId: changedDocumentId }
        }));
        
        // SessionStorage Flag für direkten Navigations-Fall
        sessionStorage.setItem(`document_${changedDocumentId}_status_changed`, 'true');
      }, 100);
    }
  };

  const handleStatusModalClose = () => {
    setShowStatusModal(false);
    setTargetStatus(null);
    setDraggedDocument(null);
    setDraggedFromColumn(null);
  };

  // ============================================================================
  // EFFECTS - ALLE useEffects NACH DEN FUNKTIONEN
  // ============================================================================

  // ENTFERNT: Reload nach Status-Change wird jetzt direkt in handleStatusChangeSuccess aufgerufen
  // (Optimistisches UI-Update + direktes Reload ist zuverlässiger als Flag-basiertes System)

  // RBAC: Permission Check - Nur Level 2+ darf Dokumenten-Liste sehen
  useEffect(() => {
    if (!userContextLoading && userLevel > 0) {
      if (userLevel < 2) {
        // Level 1: Redirect zu Home (nur RAG Chat)
        console.log(`RBAC: User Level ${userLevel} hat keinen Zugriff auf Dokumenten-Liste, redirect zu Home`)
        router.push('/')
      }
    }
  }, [userLevel, userContextLoading, router])
  
  // RBAC Phase 7: View-Mode basierend auf User-Level setzen
  useEffect(() => {
    if (!userContextLoading && userLevel > 0) {
      if (canViewKanban) {
        // Level 3+: Kann Kanban sehen, default zu 'kanban'
        setViewMode('kanban');
      } else {
        // Level 2: Nur Tabelle
        setViewMode('table');
      }
    }
  }, [userLevel, userContextLoading, canViewKanban]);

  // Lade fehlgeschlagene Dokumente
  const loadFailedDocuments = async () => {
    try {
      const response = await getUploadsList();
      if (response.success && response.documents) {
        // Filtere nur Dokumente mit processing_status='failed'
        const failed = response.documents.filter((doc: UploadedDocument) => doc.processing_status === 'failed');
        setFailedDocuments(failed);
      }
    } catch (error) {
      console.error('Failed to load failed documents:', error);
    }
  };

  useEffect(() => {
    if (!userContextLoading && userLevel > 0) {
      loadDocumentTypes();
      loadInterestGroups();
      loadDocuments();
      loadFailedDocuments(); // NEU: Lade fehlgeschlagene Dokumente
    }
  }, [selectedDocumentTypeId, userLevel, userContextLoading, viewMode]); // NEU: viewMode als Dependency hinzugefügt

  // NEU: Helper um Original-Dokumentnamen zu finden (synchron)
  const getOriginalDocumentName = (duplicateOfId: number): string => {
    if (!duplicateOfId) return '';
    
    // Prüfe Cache zuerst
    if (originalDocumentNames.has(duplicateOfId)) {
      return originalDocumentNames.get(duplicateOfId)!;
    }
    
    // Durchsuche alle Spalten nach dem Original-Dokument
    for (const column of columns) {
      const originalDoc = column.documents.find(doc => doc.id === duplicateOfId);
      if (originalDoc) {
        // Cache den Namen
        setOriginalDocumentNames(prev => new Map(prev).set(duplicateOfId, originalDoc.original_filename));
        return originalDoc.original_filename;
      }
    }
    
    // Wenn nicht gefunden, zeige ID (wird später per useEffect geladen)
    return `Dokument #${duplicateOfId}`;
  };

  // NEU: Lade Original-Namen für alle Duplikate per useEffect
  useEffect(() => {
    if (columns.length === 0 || loading) {
      return; // Früh abbrechen wenn keine Daten
    }
    
    const loadOriginalNames = async () => {
      const duplicateIds = new Set<number>();
      
      // Sammle alle duplicate_of_document_id Werte
      for (const column of columns) {
        for (const doc of column.documents) {
          if (doc.is_duplicate && doc.duplicate_of_document_id) {
            duplicateIds.add(doc.duplicate_of_document_id);
          }
        }
      }
      
      // Filtere bereits geladene IDs heraus
      const missingIds = Array.from(duplicateIds).filter(id => !originalDocumentNames.has(id));
      
      // Lade fehlende Original-Namen über API
      if (missingIds.length > 0) {
        const { getUploadDetails } = await import('@/lib/api/documentUpload');
        const newNames = new Map(originalDocumentNames);
        
        await Promise.all(
          missingIds.map(async (docId) => {
            try {
              const response = await getUploadDetails(docId);
              if (response.success && response.document) {
                newNames.set(docId, response.document.original_filename);
                console.log(`[DuplicateTooltip] Loaded: ID ${docId} = ${response.document.original_filename}`);
              }
            } catch (error) {
              console.warn(`[DuplicateTooltip] Failed for ID ${docId}:`, error);
            }
          })
        );
        
        // Update nur wenn neue Namen hinzugefügt wurden
        if (newNames.size > originalDocumentNames.size) {
          setOriginalDocumentNames(newNames);
        }
      }
    };
    
    loadOriginalNames();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, loading]); // originalDocumentNames absichtlich NICHT in Dependencies (wird nur intern verwendet)

  // Während Loading oder wenn Level < 2: Loading-Spinner anzeigen
  // FRÜHER RETURN NACH ALLEN HOOKS UND FUNKTIONEN!
  if (userContextLoading || (userLevel > 0 && userLevel < 2)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  // ============================================================================
  // FILTERING
  // ============================================================================

  const filteredColumns = columns.map(column => ({
    ...column,
    documents: column.documents.filter(doc => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          doc.filename.toLowerCase().includes(query) ||
          doc.original_filename.toLowerCase().includes(query) ||
          (doc.qm_chapter?.toLowerCase() || '').includes(query) ||
          doc.version.toLowerCase().includes(query)
        );
      }
      return true;
    })
  }));

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDocumentTypeName = (typeId: number) => {
    const type = documentTypes.find(dt => dt.id === typeId);
    return type ? type.name : 'Unbekannt';
  };

  const getTotalDocuments = () => {
    return filteredColumns.reduce((total, column) => total + column.documents.length, 0);
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📚 Dokumentenverwaltung</h1>
          <p className="text-gray-600">Workflow-basierte Dokumentenverwaltung mit Drag & Drop</p>
        </div>

        {/* Failed Documents Panel */}
        <FailedDocumentsPanel
          documents={failedDocuments}
          onDocumentRetried={() => {
            loadFailedDocuments();
            loadDocuments(); // Reload auch normale Dokumente
          }}
          onDocumentDeleted={() => {
            loadFailedDocuments();
            loadDocuments(); // Reload auch normale Dokumente
          }}
        />

        {/* Controls */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Suche
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Dateiname, QM-Kapitel, Version..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Document Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dokumenttyp
              </label>
              <select
                value={selectedDocumentTypeId || ''}
                onChange={(e) => setSelectedDocumentTypeId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Alle Typen</option>
                {documentTypes?.map(dt => (
                  <option key={dt.id} value={dt.id}>
                    {dt.name}
                  </option>
                ))}
              </select>
            </div>

            {/* RBAC Phase 7: View Mode Toggle - Nur für Level 3+ (Kanban erlaubt) */}
            {canViewKanban && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ansicht
                </label>
                <div className="flex rounded-lg border border-gray-300 overflow-hidden">
                  <button
                    onClick={() => setViewMode('kanban')}
                    className={`flex-1 px-3 py-2 text-sm font-medium ${
                      viewMode === 'kanban'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    📋 Kanban
                  </button>
                  <button
                    onClick={() => setViewMode('table')}
                    className={`flex-1 px-3 py-2 text-sm font-medium ${
                      viewMode === 'table'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    📊 Tabelle
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {getTotalDocuments()} Dokument(e) gefunden
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <strong className="font-bold">Fehler: </strong>
            <span>{error}</span>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-6">
            <DocumentSkeletonList count={4} />
          </div>
        )}

        {/* RBAC Phase 7: Kanban View - Nur für Level 3+ */}
        {!loading && viewMode === 'kanban' && canViewKanban && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {filteredColumns.map((column) => {
              // RBAC Phase 8: Prüfe ob diese Spalte droppable ist für aktuellen User
              const isDroppable = canChangeStatus && (
                // Level 3: Nur Draft → Reviewed erlaubt
                (userLevel === 3 && column.id === 'reviewed') ||
                // Level 4+: Alle Spalten (approved, rejected) erlaubt
                (canApproveOrReject && (column.id === 'approved' || column.id === 'rejected')) ||
                // Reviewed ist immer erlaubt für Level 3+
                column.id === 'reviewed'
              );
              
              return (
              <div
                key={column.id}
                className={`rounded-lg p-4 transition-colors ${
                  isDroppable 
                    ? 'bg-gray-50 hover:bg-gray-100' 
                    : 'bg-gray-100 opacity-60'
                }`}
                onDragOver={isDroppable ? handleDragOver : undefined}
                onDrop={isDroppable ? (e) => handleDrop(e, column.id) : undefined}
              >
                {/* Column Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{column.icon}</span>
                    <h3 className="font-semibold text-gray-900">{column.title}</h3>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    column.color === 'gray' ? 'bg-gray-100 text-gray-800' :
                    column.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                    column.color === 'green' ? 'bg-green-100 text-green-800' :
                    column.color === 'red' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {column.documents.length}
                  </span>
                </div>

                {/* Documents */}
                <div className="space-y-3">
                  {column.documents.length === 0 ? (
                    <EmptyDocumentsState />
                  ) : (
                    column.documents.map((doc) => {
                      // RBAC Multi-Level: Prüfe ob User für dieses Dokument drag darf
                      const canDragDoc = canChangeStatus && canPerformActionOnDocument(doc.interest_group_ids || [], 3)
                      
                      return (
                      <div
                        key={doc.id}
                        draggable={canDragDoc}
                        onDragStart={canDragDoc ? (e) => handleDragStart(e, doc, column.id) : undefined}
                        className={`bg-white rounded-lg p-4 shadow-sm border border-gray-200 transition-shadow group ${
                          canDragDoc
                            ? 'hover:shadow-md cursor-move'
                            : 'cursor-default opacity-75'
                        }`}
                      >
                        {/* Document Header */}
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 text-sm line-clamp-2">
                            {doc.original_filename}
                          </h4>
                          <div className="flex gap-2 ml-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/documents/${doc.id}`);
                              }}
                              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-100 rounded transition-all hover:scale-110 cursor-pointer"
                              title="Details ansehen & Indexieren"
                            >
                              <Eye className="w-5 h-5" />
                            </button>
                            <button
                              onClick={async (e) => {
                                e.stopPropagation();
                                // NEU: Lade Indexierungs-Status für Kanban-Dokumente
                                let isIndexed = false;
                                try {
                                  const { apiClient } = await import('@/lib/api/rag');
                                  const indexStatusResponse = await apiClient.getDocumentIndexStatus(doc.id);
                                  if (indexStatusResponse.data) {
                                    isIndexed = indexStatusResponse.data.is_indexed;
                                  }
                                } catch (error) {
                                  console.warn(`Failed to load index status for document ${doc.id}:`, error);
                                }
                                handleDelete(doc.id, doc.original_filename, isIndexed);
                              }}
                              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-100 rounded transition-all hover:scale-110 cursor-pointer"
                              title="Löschen"
                            >
                              <Trash2 className="w-5 h-5" />
                            </button>
                          </div>
                        </div>

                        {/* NEU: Duplikat-Icon (Option 4) - Nur wenn wirklich Duplikat */}
                        {doc.is_duplicate === true && doc.duplicate_of_document_id && (
                          <div className="mb-2 flex items-center gap-1 bg-orange-50 border border-orange-200 rounded px-2 py-1">
                            <span 
                              className="text-orange-500 text-sm cursor-help" 
                              title={`Duplikat von: ${getOriginalDocumentName(doc.duplicate_of_document_id)}`}
                            >
                              ⚠️
                            </span>
                            <span className="text-orange-700 text-xs font-medium">Duplikat</span>
                          </div>
                        )}

                        {/* Document Info */}
                        <div className="space-y-1 text-xs text-gray-600">
                          <div className="flex justify-between">
                            <span>Typ:</span>
                            <span className="font-medium">{doc.document_type_name || (doc.document_type ? getDocumentTypeName(doc.document_type) : 'Unbekannt')}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Kapitel:</span>
                            <span className="font-medium">{doc.qm_chapter || '-'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Version:</span>
                            <span className="font-medium">{doc.version}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Seiten:</span>
                            <span className="font-medium">{doc.page_count || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Größe:</span>
                            <span className="font-medium">{formatFileSize(doc.file_size_bytes)}</span>
                          </div>
                        </div>

                        {/* Interest Groups */}
                        {doc.interest_group_ids && doc.interest_group_ids.length > 0 && (
                          <div className="mt-2">
                            <div className="flex flex-wrap gap-1">
                              {doc.interest_group_ids.map((groupId) => (
                                <span
                                  key={groupId}
                                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                >
                                  {getInterestGroupName(interestGroupLookup, groupId)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Verantwortlicher User */}
                        {doc.responsible_user_name && (
                          <div className="mt-2">
                            <div className="flex items-center gap-1">
                              <span className="text-xs text-gray-500">Verantwortlich:</span>
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                👤 {doc.responsible_user_name}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Betroffene Abteilungen */}
                        {doc.affected_departments && doc.affected_departments.length > 0 && (
                          <div className="mt-2">
                            <div className="flex flex-wrap gap-1">
                              {doc.affected_departments.map((dept, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800"
                                >
                                  🏢 {dept}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Upload Date & History Button */}
                        <div className="mt-3 pt-2 border-t border-gray-100">
                          <div className="flex items-center justify-between">
                            <p className="text-xs text-gray-500">
                              {formatDate(doc.uploaded_at)}
                            </p>
                            <button
                              onClick={() => {
                                setTargetStatus(column.id);
                                setShowStatusModal(true);
                                setDraggedDocument(doc);
                              }}
                              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                              title="Status-Historie anzeigen"
                            >
                              📋 Historie
                            </button>
                          </div>
                        </div>
                      </div>
                      )
                    })
                  )}
                </div>
              </div>
              );
            })}
          </div>
        )}

        {/* Table View (existing implementation) */}
        {!loading && viewMode === 'table' && (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {getTotalDocuments() === 0 ? (
              <div className="p-12 text-center">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-gray-600 text-lg">Keine Dokumente gefunden</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Dokument
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Typ
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        QM-Kapitel
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Version
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        RAG Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Hochgeladen
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Aktionen
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredColumns.flatMap(column => 
                      column.documents.map((doc) => {
                        // Status-Icons basierend auf WorkflowStatus (nicht auf Name)
                        const getStatusIcon = (status: WorkflowStatus): string => {
                          switch (status) {
                            case 'draft': return '📝';
                            case 'reviewed': return '👀';
                            case 'approved': return '✅';
                            case 'rejected': return '❌';
                            default: return '📄';
                          }
                        };
                        
                        const badge = {
                          bg: getWorkflowStatusBadge(column.id).split(' ')[0],
                          text: getWorkflowStatusBadge(column.id).split(' ')[1],
                          icon: getStatusIcon(column.id),
                          label: getWorkflowStatusName(column.id)
                        };
                        return (
                          <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4">
                              <div>
                                <div className="flex items-center gap-2">
                                  <p className="font-medium text-gray-900">
                                    {doc.original_filename}
                                  </p>
                                  {/* NEU: Duplikat-Icon in Tabelle (Option 4) - Nur wenn wirklich Duplikat */}
                                  {doc.is_duplicate === true && doc.duplicate_of_document_id && (
                                    <span 
                                      className="text-orange-500 text-lg cursor-help" 
                                      title={`Duplikat von: ${getOriginalDocumentName(doc.duplicate_of_document_id)}`}
                                    >
                                      ⚠️
                                    </span>
                                  )}
                                  {doc.interest_group_ids && doc.interest_group_ids.length > 0 && (
                                    <div className="group relative inline-block">
                                      <span className="text-gray-400 cursor-help text-xs">ℹ️</span>
                                      <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs text-white bg-gray-900 rounded-lg shadow-lg -top-2 left-6 pointer-events-none">
                                        <div className="font-medium mb-1">Interest Groups:</div>
                                        <div className="text-gray-200">
                                          {doc.interest_group_ids
                                            .map(id => getInterestGroupName(interestGroupLookup, id))
                                            .filter(name => name !== 'Unbekannt')
                                            .join(', ') || 'Unbekannt'}
                                        </div>
                                        <div className="absolute top-2 -left-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                                <p className="text-sm text-gray-500">
                                  {formatFileSize(doc.file_size_bytes)} • {doc.file_type?.toUpperCase() || 'N/A'}
                                </p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-sm text-gray-900">
                                {doc.document_type_name || (doc.document_type ? getDocumentTypeName(doc.document_type) : 'Unbekannt')}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {doc.qm_chapter || '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {doc.version}
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text} flex items-center gap-1 w-fit`}>
                                <span>{badge.icon}</span> {badge.label}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              {doc.is_indexed ? (
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                                  ✅ Indexiert
                                  {doc.indexed_at && (
                                    <span className="text-xs opacity-75">
                                      ({new Date(doc.indexed_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })})
                                    </span>
                                  )}
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                  ⏳ Nicht indexiert
                                </span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {formatDate(doc.uploaded_at)}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => router.push(`/documents/${doc.id}`)}
                                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-100 rounded transition-all hover:scale-110 cursor-pointer"
                                  title="Details ansehen & Indexieren"
                                >
                                  <Eye className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() => {
                                    setTargetStatus(doc.workflow_status);
                                    setShowStatusModal(true);
                                    setDraggedDocument(doc);
                                  }}
                                  className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-100 rounded transition-all hover:scale-110 cursor-pointer"
                                  title="Status-Historie anzeigen"
                                >
                                  📋
                                </button>
                                <button
                                  onClick={() => handleDelete(doc.id, doc.original_filename, doc.is_indexed)}
                                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-100 rounded transition-all hover:scale-110 cursor-pointer"
                                  title={doc.is_indexed ? "Soft Delete (Archivierung + RAG Cleanup)" : "Löschen"}
                                >
                                  <Trash2 className="w-5 h-5" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

      {/* Status Change Modal */}
      {showStatusModal && draggedDocument && targetStatus && (
        <StatusChangeModal
          documentId={draggedDocument.id}
          currentStatus={draggedFromColumn || 'draft'}
          targetStatus={targetStatus}
          onClose={handleStatusModalClose}
          onSuccess={handleStatusChangeSuccess}
        />
      )}
    </div>
  );
}