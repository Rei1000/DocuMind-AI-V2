"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getArchivedDocuments,
  restoreDocument,
  hardDeleteDocument,
  WorkflowDocument,
  WorkflowStatus,
  getWorkflowStatusName,
  RestoreDocumentResponse,
  HardDeleteDocumentResponse
} from '@/lib/api/documentWorkflow';
import { useUser } from '@/lib/contexts/UserContext';
import Spinner from '@/components/ui/Spinner';
import { Eye, RotateCcw, Trash2 } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface RestoreModalProps {
  isOpen: boolean;
  document: WorkflowDocument | null;
  onClose: () => void;
  onRestore: (documentId: number, restoreToStatus: WorkflowStatus) => Promise<void>;
}

interface HardDeleteModalProps {
  isOpen: boolean;
  document: WorkflowDocument | null;
  onClose: () => void;
  onConfirm: (documentId: number, confirmation: string) => Promise<void>;
}

// ============================================================================
// MODAL COMPONENTS
// ============================================================================

function RestoreModal({ isOpen, document, onClose, onRestore }: RestoreModalProps) {
  const [restoreToStatus, setRestoreToStatus] = useState<WorkflowStatus>('draft');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !document) return null;

  const handleRestore = async () => {
    setLoading(true);
    setError(null);
    try {
      await onRestore(document.id, restoreToStatus);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Wiederherstellen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">📝 Dokument wiederherstellen</h2>
        <p className="text-gray-600 mb-4">
          Dokument: <strong>{document.original_filename}</strong>
        </p>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Wiederherstellen als:
          </label>
          <select
            value={restoreToStatus}
            onChange={(e) => setRestoreToStatus(e.target.value as WorkflowStatus)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="draft">Entwurf</option>
            <option value="reviewed">Geprüft</option>
            <option value="approved">Freigegeben</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Empfohlen: Als "Entwurf" wiederherstellen für erneute Prüfung
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
          >
            Abbrechen
          </button>
          <button
            onClick={handleRestore}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Spinner size="sm" /> : <RotateCcw size={16} />}
            Wiederherstellen
          </button>
        </div>
      </div>
    </div>
  );
}

function HardDeleteModal({ isOpen, document, onClose, onConfirm }: HardDeleteModalProps) {
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !document) return null;

  const handleConfirm = async () => {
    if (confirmation.trim().toUpperCase() !== 'LÖSCHEN') {
      setError('Bitte geben Sie "LÖSCHEN" zur Bestätigung ein');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onConfirm(document.id, confirmation);
      onClose();
      setConfirmation('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Löschen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4 text-red-600">⚠️ Endgültige Löschung</h2>
        <p className="text-gray-600 mb-4">
          Dieses Dokument wird <strong>permanent</strong> aus dem System entfernt:
        </p>
        <ul className="list-disc list-inside text-sm text-gray-600 mb-4 space-y-1">
          <li>Datei wird gelöscht</li>
          <li>Preview-Bilder werden gelöscht</li>
          <li>RAG-Index wird entfernt (falls indexiert)</li>
        </ul>
        <p className="text-sm font-bold text-red-600 mb-4">
          WICHTIG: Diese Aktion kann nicht rückgängig gemacht werden!
        </p>
        <p className="text-gray-600 mb-2">
          Dokument: <strong>{document.original_filename}</strong>
        </p>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Zur Bestätigung geben Sie ein: <strong>"LÖSCHEN"</strong>
          </label>
          <input
            type="text"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            placeholder="LÖSCHEN"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50"
          >
            Abbrechen
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || confirmation.trim().toUpperCase() !== 'LÖSCHEN'}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? <Spinner size="sm" /> : <Trash2 size={16} />}
            Endgültig löschen
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ArchivePage() {
  const router = useRouter();
  const { userLevel: userLevelFromContext, isLoading: userContextLoading, isQmsAdmin: isQmsAdminFromContext } = useUser();
  
  // Fallback: Extrahiere Level direkt aus JWT Token (falls UserContext noch nicht fertig)
  const [effectiveUserLevel, setEffectiveUserLevel] = useState<number>(userLevelFromContext || 0);
  const [effectiveIsQmsAdmin, setEffectiveIsQmsAdmin] = useState<boolean>(isQmsAdminFromContext || false);
  
  useEffect(() => {
    // Extrahiere Level direkt aus JWT Token als Fallback
    try {
      const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
      if (token) {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const payload = JSON.parse(jsonPayload);
        const level = payload.user_level || payload.permission_level || 1;
        const isAdmin = payload.is_qms_admin || level === 5;
        setEffectiveUserLevel(level);
        setEffectiveIsQmsAdmin(isAdmin);
      }
    } catch (e) {
      // Fallback: Nutze UserContext-Werte
      setEffectiveUserLevel(userLevelFromContext || 0);
      setEffectiveIsQmsAdmin(isQmsAdminFromContext || false);
    }
  }, [userLevelFromContext, isQmsAdminFromContext]);
  
  const userLevel = effectiveUserLevel;
  const isQmsAdmin = effectiveIsQmsAdmin;
  
  const [archivedDocuments, setArchivedDocuments] = useState<WorkflowDocument[]>([]);
  const [loading, setLoading] = useState(false); // Starte mit false, wird in useEffect auf true gesetzt
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<WorkflowDocument | null>(null);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [showHardDeleteModal, setShowHardDeleteModal] = useState(false);
  
  // Filter state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // RBAC: Nur Level 4+ dürfen Archiv sehen
  useEffect(() => {
    // Warte max 2 Sekunden auf UserContext, dann nutze Fallback
    const timeout = setTimeout(() => {
      if (userLevel < 4 && !isQmsAdmin) {
        router.push('/documents');
      }
    }, 2000);
    
    if (!userContextLoading && userLevel < 4 && !isQmsAdmin) {
      clearTimeout(timeout);
      router.push('/documents');
    }
    
    return () => clearTimeout(timeout);
  }, [userLevel, userContextLoading, isQmsAdmin, router]);

  const loadArchivedDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      // Timeout nach 10 Sekunden
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      const documentsPromise = getArchivedDocuments({
        limit: 100,
        offset: 0,
        document_type_id: selectedDocumentTypeId || undefined
      });
      
      const documents = await Promise.race([documentsPromise, timeoutPromise]) as WorkflowDocument[];
      setArchivedDocuments(documents || []);
    } catch (err) {
      console.error('[ArchivePage] Error loading archived documents:', err);
      // WICHTIG: Stelle sicher, dass error ein String ist, nicht ein Objekt
      const errorMessage = err instanceof Error 
        ? err.message 
        : (typeof err === 'string' 
          ? err 
          : (err && typeof err === 'object' && 'message' in err 
            ? String(err.message) 
            : 'Fehler beim Laden der archivierten Dokumente'));
      setError(errorMessage);
      setArchivedDocuments([]); // Setze leeres Array bei Fehler
    } finally {
      setLoading(false);
    }
  };

  // Lade archivierte Dokumente - WICHTIG: Nutze auch isQmsAdmin als Fallback
  useEffect(() => {
    // Prüfe ob User Level 4+ hat ODER QMS Admin ist
    const hasAccess = userLevel >= 4 || isQmsAdmin;
    
    console.log('[ArchivePage] useEffect - userLevel:', userLevel, 'isQmsAdmin:', isQmsAdmin, 'hasAccess:', hasAccess, 'archivedDocuments.length:', archivedDocuments.length, 'loading:', loading);
    
    // Wenn Zugriff vorhanden UND userLevel bereits bekannt (nicht 0), lade Dokumente
    // WICHTIG: Nur einmal beim Mount laden (archivedDocuments.length === 0)
    if (hasAccess && userLevel > 0 && archivedDocuments.length === 0 && !loading) {
      console.log('[ArchivePage] Calling loadArchivedDocuments...');
      loadArchivedDocuments();
    } else {
      console.log('[ArchivePage] Skipping load - conditions not met');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userLevel, isQmsAdmin]);
  
  // Separater useEffect für Filter-Änderungen
  useEffect(() => {
    const hasAccess = userLevel >= 4 || isQmsAdmin;
    if (hasAccess && userLevel > 0 && selectedDocumentTypeId !== null && !loading) {
      loadArchivedDocuments();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDocumentTypeId]);

  const handleRestore = async (documentId: number, restoreToStatus: WorkflowStatus) => {
    try {
      await restoreDocument(documentId, restoreToStatus);
      await loadArchivedDocuments(); // Reload
      // Optional: Toast notification
      alert(`✅ Dokument erfolgreich wiederhergestellt (Status: ${getWorkflowStatusName(restoreToStatus)})`);
    } catch (err) {
      throw err;
    }
  };

  const handleHardDelete = async (documentId: number, confirmation: string) => {
    try {
      const result: HardDeleteDocumentResponse = await hardDeleteDocument(documentId, confirmation);
      await loadArchivedDocuments(); // Reload
      // Optional: Toast notification
      alert(`🗑️ Dokument endgültig gelöscht. ${result.files_deleted.length} Dateien entfernt.`);
    } catch (err) {
      throw err;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Filter documents
  const filteredDocuments = archivedDocuments.filter(doc => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        doc.original_filename.toLowerCase().includes(query) ||
        doc.document_type_name?.toLowerCase().includes(query) ||
        doc.qm_chapter?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Zeige Loading nur kurz beim initialen Load
  // Wenn userLevel bekannt ist (< 4), wird redirect ausgeführt
  const hasAccess = userLevel >= 4 || isQmsAdmin;
  
  if (!hasAccess && !userContextLoading) {
    // Redirect wird ausgeführt, zeige kurz Loading
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📦 Archiv</h1>
        <p className="text-gray-600">
          Gelöschte Dokumente ({archivedDocuments.length} {archivedDocuments.length === 1 ? 'Dokument' : 'Dokumente'})
        </p>
      </div>

      {/* Filter & Search */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="🔍 Suche nach Dokumentenname, Typ oder QM-Kapitel..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-400 rounded">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Spinner />
        </div>
      )}

      {/* Table View */}
      {!loading && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {filteredDocuments.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-gray-600 text-lg">
                {archivedDocuments.length === 0 
                  ? 'Keine archivierten Dokumente gefunden'
                  : 'Keine Dokumente entsprechen den Filtern'}
              </p>
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
                      Gelöscht am
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Aktionen
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">
                            {doc.original_filename}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(doc.file_size_bytes)} • {doc.file_type?.toUpperCase() || 'N/A'}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-900">
                          {doc.document_type_name || 'Unbekannt'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {doc.qm_chapter || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(doc.uploaded_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedDocument(doc);
                              setShowRestoreModal(true);
                            }}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
                            title="Dokument wiederherstellen"
                          >
                            <RotateCcw size={16} />
                            Wiederherstellen
                          </button>
                          {userLevel >= 5 && (
                            <button
                              onClick={() => {
                                setSelectedDocument(doc);
                                setShowHardDeleteModal(true);
                              }}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
                              title="Endgültig löschen (nur Admin)"
                            >
                              <Trash2 size={16} />
                              Endgültig löschen
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <RestoreModal
        isOpen={showRestoreModal}
        document={selectedDocument}
        onClose={() => {
          setShowRestoreModal(false);
          setSelectedDocument(null);
        }}
        onRestore={handleRestore}
      />

      <HardDeleteModal
        isOpen={showHardDeleteModal}
        document={selectedDocument}
        onClose={() => {
          setShowHardDeleteModal(false);
          setSelectedDocument(null);
        }}
        onConfirm={handleHardDelete}
      />
    </div>
  );
}

