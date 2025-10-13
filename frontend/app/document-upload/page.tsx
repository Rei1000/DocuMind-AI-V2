"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  uploadDocument,
  generatePreview,
  assignInterestGroups,
  UploadDocumentRequest,
  UploadedDocument,
  DocumentPage,
} from '@/lib/api/documentUpload';

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
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentUploadPage() {
  const router = useRouter();
  
  // State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [interestGroups, setInterestGroups] = useState<InterestGroup[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [qmChapter, setQmChapter] = useState('');
  const [version, setVersion] = useState('');
  const [assignedGroupIds, setAssignedGroupIds] = useState<number[]>([]);
  
  // Drag & Drop state
  const [draggedGroupId, setDraggedGroupId] = useState<number | null>(null);
  const [dropZoneActive, setDropZoneActive] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadDocumentTypes();
    loadInterestGroups();
  }, []);

  // ============================================================================
  // API CALLS
  // ============================================================================

  const loadDocumentTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/document-types/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setDocumentTypes(data.document_types.filter((dt: DocumentType) => dt.is_active));
    } catch (error) {
      console.error('Failed to load document types:', error);
    }
  };

  const loadInterestGroups = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/interest-groups/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setInterestGroups(data.filter((ig: InterestGroup) => ig.is_active));
    } catch (error) {
      console.error('Failed to load interest groups:', error);
    }
  };

  // ============================================================================
  // FILE HANDLING
  // ============================================================================

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
      setError('Ungültiger Dateityp. Erlaubt: PDF, DOCX, PNG, JPG');
      return;
    }

    // Validate file size (max 50MB)
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
  // DRAG & DROP INTEREST GROUPS
  // ============================================================================

  const handleGroupDragStart = (e: React.DragEvent, groupId: number) => {
    setDraggedGroupId(groupId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleGroupDragEnd = () => {
    setDraggedGroupId(null);
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

    if (draggedGroupId !== null && !assignedGroupIds.includes(draggedGroupId)) {
      setAssignedGroupIds([...assignedGroupIds, draggedGroupId]);
    }
    setDraggedGroupId(null);
  };

  const removeAssignedGroup = (groupId: number) => {
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

    if (assignedGroupIds.length === 0) {
      setError('Bitte weise mindestens eine Interest Group zu');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(10);

    try {
      // Get selected document type
      const documentType = documentTypes.find(dt => dt.id === selectedDocumentTypeId);
      if (!documentType) {
        throw new Error('Dokumenttyp nicht gefunden');
      }

      // Prepare upload request
      const filename = selectedFile.name.replace(/\s+/g, '_').toLowerCase();
      const request: UploadDocumentRequest = {
        filename,
        original_filename: selectedFile.name,
        document_type_id: selectedDocumentTypeId,
        qm_chapter: qmChapter,
        version,
        processing_method: documentType.processing_method,
      };

      setUploadProgress(30);

      // Upload document
      const uploadResponse = await uploadDocument(selectedFile, request);
      
      if (!uploadResponse.success) {
        throw new Error(uploadResponse.message || 'Upload fehlgeschlagen');
      }

      setUploadProgress(50);

      // Generate preview
      const previewResponse = await generatePreview(uploadResponse.document.id);
      
      if (!previewResponse.success) {
        throw new Error(previewResponse.message || 'Preview-Generierung fehlgeschlagen');
      }

      setUploadProgress(70);

      // Assign interest groups
      const assignResponse = await assignInterestGroups(uploadResponse.document.id, {
        interest_group_ids: assignedGroupIds,
      });

      if (!assignResponse.success) {
        throw new Error(assignResponse.message || 'Interest Group Zuweisung fehlgeschlagen');
      }

      setUploadProgress(100);
      setSuccess(`Dokument "${selectedFile.name}" erfolgreich hochgeladen! (${previewResponse.pages_generated} Seiten generiert)`);
      
      // Reset form after 2 seconds
      setTimeout(() => {
        resetForm();
        router.push('/documents');
      }, 2000);

    } catch (error: any) {
      console.error('Upload error:', error);
      setError(`Upload fehlgeschlagen: ${error.message || 'Unbekannter Fehler'}`);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setSelectedDocumentTypeId(null);
    setQmChapter('');
    setVersion('');
    setAssignedGroupIds([]);
    setSuccess(null);
    setError(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const selectedDocumentType = documentTypes.find(dt => dt.id === selectedDocumentTypeId);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-6 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📤 Dokument Upload</h1>
          <p className="text-gray-600">Lade Dokumente hoch und weise sie Interest Groups zu</p>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT: Upload Card (2 columns) */}
          <div 
            className={`lg:col-span-2 bg-white border-2 rounded-xl p-6 transition-all ${
              dropZoneActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            }`}
            onDragOver={handleUploadCardDragOver}
            onDragLeave={handleUploadCardDragLeave}
            onDrop={handleUploadCardDrop}
          >
            <h2 className="text-xl font-bold text-gray-800 mb-6">Upload-Bereich</h2>
            
            {/* File Upload Dropzone */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Datei auswählen
              </label>
              <div
                className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.png,.jpg,.jpeg"
                  onChange={handleFileInputChange}
                  className="hidden"
                />

                {!selectedFile ? (
                  <>
                    <div className="text-5xl mb-3">📁</div>
                    <p className="text-gray-600 mb-2">
                      Datei hierher ziehen oder klicken zum Auswählen
                    </p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-3 bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition"
                    >
                      Datei auswählen
                    </button>
                    <p className="text-gray-400 text-xs mt-3">
                      Unterstützt: PDF, DOCX, PNG, JPG (max 50MB)
                    </p>
                  </>
                ) : (
                  <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg">
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
                      onClick={removeFile}
                      className="text-red-600 hover:text-red-700 font-bold text-xl"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Document Type */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dokumenttyp *
              </label>
              <select
                value={selectedDocumentTypeId || ''}
                onChange={(e) => setSelectedDocumentTypeId(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Dokumenttyp auswählen...</option>
                {documentTypes.map(dt => (
                  <option key={dt.id} value={dt.id}>
                    {dt.name} ({dt.processing_method.toUpperCase()})
                  </option>
                ))}
              </select>
              {selectedDocumentType && (
                <p className="text-xs text-gray-500 mt-1">
                  Verarbeitung: <span className="font-medium">{selectedDocumentType.processing_method.toUpperCase()}</span>
                </p>
              )}
            </div>

            {/* QM Chapter & Version */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  QM-Kapitel *
                </label>
                <input
                  type="text"
                  value={qmChapter}
                  onChange={(e) => setQmChapter(e.target.value)}
                  placeholder="z.B. 1.2.3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Version *
                </label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="z.B. v1.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Assigned Interest Groups */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zugewiesene Interest Groups * (von rechts hierher ziehen)
              </label>
              <div className={`min-h-[120px] border-2 border-dashed rounded-lg p-4 ${
                dropZoneActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              }`}>
                {assignedGroupIds.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">
                    Ziehe Interest Groups von rechts hierher
                  </p>
                ) : (
                  <div className="space-y-2">
                    {assignedGroupIds.map(groupId => {
                      const group = getGroupById(groupId);
                      return group ? (
                        <div
                          key={groupId}
                          className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3"
                        >
                          <div>
                            <p className="font-medium text-gray-900">{group.name}</p>
                            <p className="text-sm text-gray-500">{group.code}</p>
                          </div>
                          <button
                            onClick={() => removeAssignedGroup(groupId)}
                            className="text-red-600 hover:text-red-700 font-bold"
                          >
                            ✕
                          </button>
                        </div>
                      ) : null;
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!selectedFile || !selectedDocumentTypeId || uploading || assignedGroupIds.length === 0}
              className={`w-full py-3 rounded-lg font-bold text-lg transition ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : selectedFile && selectedDocumentTypeId && assignedGroupIds.length > 0
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {uploading ? `Uploading... ${uploadProgress}%` : '🚀 Dokument hochladen'}
            </button>

            {/* Progress Bar */}
            {uploading && (
              <div className="mt-4 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>

          {/* RIGHT: Interest Groups (1 column) */}
          <div className="lg:col-span-1">
            <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Interest Groups</h2>
              <p className="text-sm text-gray-600 mb-4">
                Ziehe Gruppen nach links zum Upload-Bereich
              </p>
              
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {interestGroups.map(group => {
                  const isAssigned = assignedGroupIds.includes(group.id);
                  return (
                    <div
                      key={group.id}
                      draggable={!isAssigned}
                      onDragStart={(e) => handleGroupDragStart(e, group.id)}
                      onDragEnd={handleGroupDragEnd}
                      className={`p-3 rounded-lg border-2 transition cursor-move ${
                        isAssigned
                          ? 'bg-gray-100 border-gray-200 opacity-50 cursor-not-allowed'
                          : draggedGroupId === group.id
                          ? 'bg-blue-100 border-blue-500'
                          : 'bg-white border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                      }`}
                    >
                      <p className="font-medium text-gray-900">{group.name}</p>
                      <p className="text-sm text-gray-500">{group.code}</p>
                      {isAssigned && (
                        <p className="text-xs text-green-600 mt-1">✓ Zugewiesen</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
