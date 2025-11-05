"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Spinner from '@/components/ui/Spinner';
import {
  uploadDocument,
  generatePreview,
  assignInterestGroups,
  UploadDocumentRequest,
} from '@/lib/api/documentUpload';
import { Button } from '@/components/ui';
import { useUser } from '@/lib/contexts/UserContext';
import DuplicateWarningModal from '@/components/DuplicateWarningModal';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
  description: string;
  file_types_allowed: string[];
  processing_method: 'ocr' | 'vision';
  is_active: boolean;
}

interface InterestGroup {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
  is_external: boolean;
  description?: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentUploadPage() {
  const router = useRouter();
  const { userLevel, isLoading: userContextLoading, canAccess } = useUser();
  
  // State - ALLE HOOKS MÜSSEN VOR FRÜHEM RETURN SEIN (React Rules of Hooks)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [interestGroups, setInterestGroups] = useState<InterestGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Duplikat-Warnung State
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<{
    documentId: number;
    duplicateOfId: number;
    originalFilename?: string;
  } | null>(null);
  
  // Form state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [qmChapter, setQmChapter] = useState('');
  const [version, setVersion] = useState('');
  const [assignedGroupIds, setAssignedGroupIds] = useState<number[]>([]);
  
  // Filter state for Interest Groups (EXACT COPY from UserManagementView)
  const [groupSearchQuery, setGroupSearchQuery] = useState('');
  const [groupFilterActive, setGroupFilterActive] = useState<'all' | 'active' | 'inactive'>('all');
  
  // Drag & Drop state
  const [draggedGroup, setDraggedGroup] = useState<InterestGroup | null>(null);
  const [dropZoneActive, setDropZoneActive] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // RBAC Phase 6: Permission Check - Nur Level 4+ darf uploaden
  useEffect(() => {
    if (!userContextLoading && userLevel > 0) {
      if (!canAccess('upload')) {
        // Level < 4: Redirect zu Home
        console.log(`RBAC: User Level ${userLevel} hat keinen Zugriff auf Upload, redirect zu Home`)
        router.push('/')
      }
    }
  }, [userLevel, userContextLoading, canAccess, router])
  
  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    if (!userContextLoading && (userLevel === 0 || canAccess('upload'))) {
      loadData();
    }
  }, [userContextLoading, userLevel, canAccess]);
  
  // Während Loading oder wenn kein Zugriff: Loading-Spinner anzeigen
  // FRÜHER RETURN NACH ALLEN HOOKS!
  if (userContextLoading || (userLevel > 0 && !canAccess('upload'))) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner />
      </div>
    )
  }

  // ============================================================================
  // API CALLS
  // ============================================================================

  const loadData = async () => {
    setLoading(true);
    try {
      // Try both possible token storage keys
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token');
      console.log('Token:', token ? 'EXISTS' : 'MISSING');
      console.log('Token value (first 20 chars):', token ? token.substring(0, 20) + '...' : 'NONE');
      
      if (!token) {
        setError('Kein Token gefunden. Bitte neu anmelden.');
        setLoading(false);
        return;
      }

      const headers = { 'Authorization': `Bearer ${token}` };

      console.log('Fetching document types...');
      const docTypesResp = await fetch('http://localhost:8000/api/document-types/', { headers });
      console.log('Document Types Response Status:', docTypesResp.status);
      
      console.log('Fetching interest groups...');
      const groupsResp = await fetch('http://localhost:8000/api/interest-groups/', { headers });
      console.log('Interest Groups Response Status:', groupsResp.status);

      const docTypesData = await docTypesResp.json();
      const groupsData = await groupsResp.json();

      console.log('Document Types Response:', docTypesData);
      console.log('Interest Groups Response:', groupsData);

      // Check if response is array directly OR has document_types property
      let docTypesArray = null;
      if (Array.isArray(docTypesData)) {
        // Response is array directly
        docTypesArray = docTypesData;
      } else if (docTypesData && docTypesData.document_types && Array.isArray(docTypesData.document_types)) {
        // Response has document_types property
        docTypesArray = docTypesData.document_types;
      }

      if (docTypesArray) {
        const activeTypes = docTypesArray.filter((dt: DocumentType) => dt.is_active);
        console.log('✅ Active Document Types:', activeTypes);
        console.log('🔍 First DocumentType:', activeTypes[0]);
        console.log('🔍 Processing Methods:', activeTypes.map((dt: DocumentType) => ({ id: dt.id, name: dt.name, method: dt.processing_method })));
        setDocumentTypes(activeTypes);
      } else {
        console.error('Invalid document types response format:', docTypesData);
        setError('Dokumenttypen konnten nicht geladen werden (ungültiges Format)');
      }

      // Check if groups is an array
      if (Array.isArray(groupsData)) {
        console.log('Interest Groups Count:', groupsData.length);
        setInterestGroups(groupsData);
        
        // RBAC Fix: QM Interest Group automatisch zuweisen (immer erforderlich)
        const qmGroup = groupsData.find((g: InterestGroup) => g.code === 'QM' || g.code === 'qm' || g.name.toLowerCase().includes('qualitätsmanagement'));
        if (qmGroup) {
          console.log('QM Group found, auto-assigning:', qmGroup);
          setAssignedGroupIds([qmGroup.id]);
        } else {
          console.warn('⚠️ QM Interest Group not found! Documents require QM group.');
        }
      } else {
        console.error('Invalid interest groups response format:', groupsData);
        setError('Interest Groups konnten nicht geladen werden (ungültiges Format)');
      }

      setError(null);
    } catch (error) {
      console.error('Failed to load data:', error);
      setError(`Fehler beim Laden der Daten: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // FILTER GROUPS (EXACT COPY from UserManagementView)
  // ============================================================================

  const filteredGroups = interestGroups.filter(group => {
    // Search
    if (groupSearchQuery) {
      const query = groupSearchQuery.toLowerCase();
      if (!group.name.toLowerCase().includes(query) && 
          !group.code.toLowerCase().includes(query)) {
        return false;
      }
    }
    
    // Active Filter
    if (groupFilterActive === 'active' && !group.is_active) return false;
    if (groupFilterActive === 'inactive' && group.is_active) return false;
    
    return true;
  });

  // ============================================================================
  // FILE HANDLING
  // ============================================================================

  const handleFileSelect = (file: File) => {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
      setError('Ungültiger Dateityp. Erlaubt: PDF, DOCX, PNG, JPG');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError('Dateigröße überschreitet 50MB Limit');
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ============================================================================
  // DRAG & DROP INTEREST GROUPS (EXACT COPY from UserManagementView)
  // ============================================================================

  const handleDragStart = (e: React.DragEvent, group: InterestGroup) => {
    setDraggedGroup(group);
    e.dataTransfer.effectAllowed = 'move';
    // Browser kontrolliert den Cursor automatisch - wir lassen das so
  };

  const handleDragEnd = () => {
    setDraggedGroup(null);
    setDropZoneActive(false);
  };

  const handleUploadCardDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDropZoneActive(true);
  };

  const handleUploadCardDragLeave = () => {
    setDropZoneActive(false);
  };

  const handleUploadCardDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDropZoneActive(false);

    // Check if a file was dropped
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      handleFileSelect(file);
      setDraggedGroup(null);
      return;
    }

    // Otherwise, handle Interest Group drag & drop
    if (draggedGroup && !assignedGroupIds.includes(draggedGroup.id)) {
      setAssignedGroupIds([...assignedGroupIds, draggedGroup.id]);
    }
    setDraggedGroup(null);
  };

  const removeAssignedGroup = (groupId: number) => {
    // RBAC Fix: QM darf nicht entfernt werden (immer erforderlich)
    const groupToRemove = getGroupById(groupId);
    if (groupToRemove && (groupToRemove.code === 'QM' || groupToRemove.code === 'qm' || groupToRemove.name.toLowerCase().includes('qualitätsmanagement'))) {
      setError('QM Interest Group kann nicht entfernt werden. Jedes Dokument muss QM zugewiesen haben.');
      return;
    }
    setAssignedGroupIds(assignedGroupIds.filter(id => id !== groupId));
  };

  const getGroupById = (groupId: number) => {
    return interestGroups.find(g => g.id === groupId);
  };

  // ============================================================================
  // UPLOAD HANDLING
  // ============================================================================

  const handleUpload = async () => {
    if (!selectedFile || !selectedDocumentTypeId) {
      setError('Bitte wähle eine Datei und einen Dokumenttyp aus');
      return;
    }

    if (!qmChapter || !version) {
      setError('Bitte fülle QM-Kapitel und Version aus');
      return;
    }

    // RBAC Fix: Validierung - QM muss vorhanden sein
    const qmGroup = interestGroups.find(g => (g.code === 'QM' || g.code === 'qm' || g.name.toLowerCase().includes('qualitätsmanagement')) && assignedGroupIds.includes(g.id));
    if (!qmGroup) {
      setError('QM Interest Group ist erforderlich. Jedes Dokument muss QM zugewiesen haben.');
      return;
    }
    
    if (assignedGroupIds.length === 0) {
      setError('Bitte weise mindestens eine Interest Group zu');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(10);

    try {
      const documentType = documentTypes.find(dt => dt.id === selectedDocumentTypeId);
      if (!documentType) {
        throw new Error('Dokumenttyp nicht gefunden');
      }

      console.log('🔍 Selected DocumentType:', documentType);
      console.log('🔍 Processing Method:', documentType.processing_method);

      // Fallback: Wenn processing_method fehlt, verwende 'vision' als Standard
      const processingMethod = documentType.processing_method || 'vision';
      console.log('🔍 Using Processing Method:', processingMethod);

      // Version normalisieren: Füge "v" hinzu falls nicht vorhanden
      const normalizedVersion = version.startsWith('v') ? version : `v${version}`;
      console.log('🔍 Normalized Version:', normalizedVersion);

      const filename = selectedFile.name.replace(/\s+/g, '_').toLowerCase();
      const request: UploadDocumentRequest = {
        filename,
        original_filename: selectedFile.name,
        document_type_id: selectedDocumentTypeId,
        qm_chapter: qmChapter,
        version: normalizedVersion,
        processing_method: processingMethod,
      };
      
      console.log('🔍 Upload Request:', request);

      setUploadProgress(30);

      console.log('📤 Calling uploadDocument API...');
      const uploadResponse = await uploadDocument(selectedFile, request);
      console.log('✅ Upload Response:', uploadResponse);
      
      if (!uploadResponse.success) {
        throw new Error(uploadResponse.message || 'Upload fehlgeschlagen');
      }

      setUploadProgress(50);

      const previewResponse = await generatePreview(uploadResponse.document.id);
      
      if (!previewResponse.success) {
        throw new Error(previewResponse.message || 'Preview-Generierung fehlgeschlagen');
      }

      setUploadProgress(70);

      const assignResponse = await assignInterestGroups(uploadResponse.document.id, {
        interest_group_ids: assignedGroupIds,
      });

      if (!assignResponse.success) {
        throw new Error(assignResponse.message || 'Interest Group Zuweisung fehlgeschlagen');
      }

      setUploadProgress(100);
      
      // NEU: Prüfe auf Duplikat und zeige entsprechendes Feedback
      const isDuplicate = uploadResponse.document.is_duplicate === true;
      const duplicateOfId = uploadResponse.document.duplicate_of_document_id;
      
      if (isDuplicate && duplicateOfId) {
        // Zeige Duplikat-Modal statt normalem Success
        setDuplicateInfo({
          documentId: uploadResponse.document.id,
          duplicateOfId: duplicateOfId,
          originalFilename: uploadResponse.message?.includes('Dokument ID') 
            ? undefined 
            : undefined // Original-Filename wird später aus API geladen
        });
        setShowDuplicateModal(true);
        setSuccess(null); // Keine normale Success-Message bei Duplikat
      } else {
        // Normales Success bei keinem Duplikat
        setSuccess(`Dokument "${selectedFile.name}" erfolgreich hochgeladen! (${previewResponse.pages_generated} Seiten generiert)`);
        setTimeout(() => {
          router.push(`/documents/${uploadResponse.document.id}`);
        }, 2000);
      }

    } catch (error: any) {
      console.error('❌ Upload error:', error);
      console.error('❌ Error details:', {
        message: error.message,
        stack: error.stack,
        type: typeof error,
        error: error
      });
      setError(`Upload fehlgeschlagen: ${error.message || 'Unbekannter Fehler'}`);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const selectedDocumentType = documentTypes.find(dt => dt.id === selectedDocumentTypeId);

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="text-4xl mb-2">⏳</div>
          <div>Lade Daten...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dokument Upload</h1>
        <p className="text-gray-600">
          Ziehe Interest Groups auf den Upload-Bereich um sie zuzuweisen
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <strong className="font-bold">Fehler: </strong>
          <span>{error}</span>
        </div>
      )}

      {/* Success Alert */}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          <strong className="font-bold">Erfolg: </strong>
          <span>{success}</span>
        </div>
      )}

      {/* NEU: Duplikat-Warning Banner (Option 2) - Zeigt nur wenn Success vorhanden UND Duplikat */}
      {success && duplicateInfo && (
        <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
          <div className="flex items-start">
            <span className="text-yellow-400 text-xl mr-3">⚠️</span>
            <div className="flex-1">
              <h3 className="text-yellow-800 font-semibold mb-1">Duplikat erkannt</h3>
              <p className="text-yellow-700 text-sm mb-2">
                Dieses Dokument existiert bereits im System (Dokument #{duplicateInfo.duplicateOfId}).
              </p>
              <a
                href={`/documents/${duplicateInfo.duplicateOfId}`}
                className="text-yellow-800 underline text-sm hover:text-yellow-900 transition-colors inline-block"
              >
                Zum Original springen →
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Duplikat-Modal (Option 1) */}
      {duplicateInfo && (
        <DuplicateWarningModal
          isOpen={showDuplicateModal}
          onClose={() => {
            setShowDuplicateModal(false);
            // Navigiere zur Dokument-Detail-Seite nach Modal-Schließung
            setTimeout(() => {
              router.push(`/documents/${duplicateInfo.documentId}`);
            }, 500);
          }}
          onKeepDuplicate={() => {
            // Modal bleibt offen, User navigiert manuell
            setShowDuplicateModal(false);
            setTimeout(() => {
              router.push(`/documents/${duplicateInfo.documentId}`);
            }, 500);
          }}
          duplicateOfDocumentId={duplicateInfo.duplicateOfId}
          originalFilename={duplicateInfo.originalFilename}
          currentDocumentId={duplicateInfo.documentId}
        />
      )}

      {/* AI Playground Style Layout (grid 3 columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT: Interest Groups Sidebar - AI Playground Style */}
        <div className="lg:col-span-1 space-y-4 order-2 lg:order-1">
          {/* Search & Filter */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="🔍 Search groups..."
                value={groupSearchQuery}
                onChange={(e) => setGroupSearchQuery(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div className="flex gap-4 flex-wrap">
              {/* Active Filter */}
              <div className="flex gap-2">
                <button
                  onClick={() => setGroupFilterActive('all')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors cursor-pointer ${
                    groupFilterActive === 'all' 
                      ? 'bg-primary text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  All Groups
                </button>
                <button
                  onClick={() => setGroupFilterActive('active')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors cursor-pointer ${
                    groupFilterActive === 'active' 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  🟢 Active
                </button>
                <button
                  onClick={() => setGroupFilterActive('inactive')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors cursor-pointer ${
                    groupFilterActive === 'inactive' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  🔴 Inactive
                </button>
              </div>

              <div className="flex-1 text-right text-sm text-muted-foreground">
                {filteredGroups.length} group{filteredGroups.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          {/* Groups List */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 sticky top-4">
            <div className="text-xs text-muted-foreground mb-3">
              💡 Drag groups onto upload area to assign
            </div>

            <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
              {filteredGroups.map(group => {
                const isAssigned = assignedGroupIds.includes(group.id);
                return (
                  <div
                    key={group.id}
                    draggable={group.is_active && !isAssigned}
                    onDragStart={(e) => group.is_active && !isAssigned && handleDragStart(e, group)}
                    onDragEnd={handleDragEnd}
                    style={{
                      cursor: group.is_active && !isAssigned ? undefined : 'not-allowed'
                    }}
                    className={`group p-3 rounded-md border border-gray-200 transition-all ${
                      isAssigned
                        ? 'bg-gray-100 opacity-60'
                        : group.is_active 
                        ? 'bg-gray-50 hover:bg-primary hover:text-white hover:border-primary' 
                        : 'bg-gray-100 opacity-60'
                    }`}
                  >
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{group.code}</div>
                      <div className="text-xs opacity-70">{group.name}</div>
                      {!group.is_active && (
                        <div className="text-xs text-red-600 font-medium">⚠️ Inaktiv</div>
                      )}
                      {isAssigned && (
                        <div className="text-xs text-green-600 font-medium">✓ Zugewiesen</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        
        {/* RIGHT: Upload Card - AI Playground Style */}
        <div className="lg:col-span-2 order-1 lg:order-2">
          <div 
            className={`bg-white border-2 rounded-lg p-6 transition-all ${
              dropZoneActive ? 'border-primary bg-blue-50' : 'border-gray-200'
            }`}
            onDragOver={handleUploadCardDragOver}
            onDragLeave={handleUploadCardDragLeave}
            onDrop={handleUploadCardDrop}
          >
            
            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Datei auswählen
              </label>
              <label
                htmlFor="file-upload-input"
                className="relative block border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-all cursor-pointer"
              >
                <input
                  id="file-upload-input"
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.png,.jpg,.jpeg"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  className="hidden"
                />

                {!selectedFile ? (
                  <>
                    <div className="text-5xl mb-3">📁</div>
                    <p className="text-gray-600 mb-2">
                      Datei hierher ziehen oder klicken zum Auswählen
                    </p>
                    <span
                      className="mt-3 inline-block bg-primary text-white px-5 py-2 rounded-md hover:bg-primary/90 transition-colors"
                      onClick={(e) => {
                        // Prevent event bubbling, but allow label click to work
                        e.stopPropagation();
                      }}
                    >
                      Datei auswählen
                    </span>
                    <p className="text-gray-400 text-xs mt-3">
                      Unterstützt: PDF, DOCX, PNG, JPG (max 50MB)
                    </p>
                  </>
                ) : (
                  <div 
                    className="flex items-center justify-between bg-gray-50 p-4 rounded-lg pointer-events-none"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-3xl">📄</span>
                      <div className="text-left">
                        <p className="font-medium text-gray-800">{selectedFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        removeFile();
                      }}
                      className="text-red-600 hover:text-red-700 font-bold text-xl pointer-events-auto cursor-pointer"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </label>
            </div>

            {/* Document Type */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Dokumenttyp * {documentTypes.length > 0 && <span className="text-xs text-gray-500">({documentTypes.length} verfügbar)</span>}
              </label>
              <select
                value={selectedDocumentTypeId || ''}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  console.log('Selected Document Type ID:', value);
                  setSelectedDocumentTypeId(value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Dokumenttyp auswählen...</option>
                {documentTypes.map(dt => {
                  console.log('Rendering option:', dt.id, dt.name, dt.processing_method);
                  return (
                    <option key={dt.id} value={dt.id}>
                      {dt.name} {dt.processing_method ? `(${dt.processing_method.toUpperCase()})` : ''}
                    </option>
                  );
                })}
              </select>
              {documentTypes.length === 0 && (
                <p className="text-xs text-red-500 mt-1">
                  ⚠️ Keine Dokumenttypen gefunden. Bitte in Prompt-Verwaltung erstellen.
                </p>
              )}
              {selectedDocumentType && selectedDocumentType.processing_method && (
                <p className="text-xs text-gray-500 mt-1">
                  Verarbeitung: <span className="font-medium">{selectedDocumentType.processing_method.toUpperCase()}</span>
                </p>
              )}
            </div>

            {/* QM Chapter & Version */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  QM-Kapitel *
                </label>
                <input
                  type="text"
                  value={qmChapter}
                  onChange={(e) => setQmChapter(e.target.value)}
                  placeholder="z.B. 1.2.3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Version * <span className="text-xs text-gray-500">(automatisch mit "v" versehen)</span>
                </label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="z.B. 1.0 oder v1.0.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {/* Assigned Interest Groups */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Zugewiesene Interest Groups * (von links hierher ziehen)
              </label>
              <div className={`min-h-[120px] border-2 border-dashed rounded-lg p-4 ${
                dropZoneActive ? 'border-primary bg-blue-50' : 'border-gray-300'
              }`}>
                {assignedGroupIds.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">
                    {draggedGroup 
                      ? '👆 Drop group here to assign' 
                      : 'Ziehe Interest Groups von links hierher'}
                  </p>
                ) : (
                  <div className="space-y-2">
                    {assignedGroupIds.map(groupId => {
                      const group = getGroupById(groupId);
                      if (!group) return null;
                      
                      // RBAC Fix: QM darf nicht entfernt werden
                      const isQM = group.code === 'QM' || group.code === 'qm' || group.name.toLowerCase().includes('qualitätsmanagement');
                      
                      return (
                        <div
                          key={groupId}
                          className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-md p-3"
                        >
                          <div>
                            <div className="font-semibold text-sm">
                              {group.code}
                              {isQM && <span className="ml-2 text-xs text-gray-500">(erforderlich)</span>}
                            </div>
                            <div className="text-xs text-gray-600">{group.name}</div>
                          </div>
                          {!isQM && (
                            <button
                              onClick={() => removeAssignedGroup(groupId)}
                              className="text-red-600 hover:text-red-700 font-bold cursor-pointer"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!selectedFile || !selectedDocumentTypeId || uploading || assignedGroupIds.length === 0}
              className={`w-full py-3 rounded-md font-semibold transition-colors flex items-center justify-center gap-2 ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : selectedFile && selectedDocumentTypeId && assignedGroupIds.length > 0
                  ? 'bg-primary text-white hover:bg-primary/90'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {uploading ? (
                <>
                  <Spinner size="sm" className="border-white border-t-white" />
                  <span>Uploading... {uploadProgress}%</span>
                </>
              ) : (
                'Dokument hochladen'
              )}
            </button>

            {/* Progress Bar */}
            {uploading && (
              <div className="mt-4 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
