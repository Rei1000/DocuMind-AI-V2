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
  const [selectedInterestGroups, setSelectedInterestGroups] = useState<number[]>([]);
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null);
  const [previewPages, setPreviewPages] = useState<DocumentPage[]>([]);
  
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
      setError('Invalid file type. Allowed: PDF, DOCX, PNG, JPG');
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size exceeds 50MB limit');
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const removeFile = () => {
    setSelectedFile(null);
    setUploadedDocument(null);
    setPreviewPages([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ============================================================================
  // UPLOAD HANDLING
  // ============================================================================

  const handleUpload = async () => {
    if (!selectedFile || !selectedDocumentTypeId) {
      setError('Please select a file and document type');
      return;
    }

    if (!qmChapter || !version) {
      setError('Please fill in QM Chapter and Version');
      return;
    }

    if (selectedInterestGroups.length === 0) {
      setError('Please select at least one interest group');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(10);

    try {
      // Get selected document type
      const documentType = documentTypes.find(dt => dt.id === selectedDocumentTypeId);
      if (!documentType) {
        throw new Error('Document type not found');
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
        throw new Error(uploadResponse.message || 'Upload failed');
      }

      setUploadedDocument(uploadResponse.document);
      setUploadProgress(50);

      // Generate preview
      const previewResponse = await generatePreview(uploadResponse.document.id);
      
      if (!previewResponse.success) {
        throw new Error(previewResponse.message || 'Preview generation failed');
      }

      setPreviewPages(previewResponse.pages);
      setUploadProgress(70);

      // Assign interest groups
      const assignResponse = await assignInterestGroups(uploadResponse.document.id, {
        interest_group_ids: selectedInterestGroups,
      });

      if (!assignResponse.success) {
        throw new Error(assignResponse.message || 'Interest group assignment failed');
      }

      setUploadProgress(100);
      setSuccess(`Document "${selectedFile.name}" uploaded successfully! (${previewResponse.pages_generated} pages generated)`);
      
      // Reset form after 2 seconds
      setTimeout(() => {
        resetForm();
      }, 2000);

    } catch (error: any) {
      console.error('Upload error:', error);
      setError(`Upload failed: ${error.message || 'Unknown error'}`);
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
    setSelectedInterestGroups([]);
    setUploadedDocument(null);
    setPreviewPages([]);
    setSuccess(null);
    setError(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ============================================================================
  // INTEREST GROUP SELECTION
  // ============================================================================

  const toggleInterestGroup = (groupId: number) => {
    setSelectedInterestGroups(prev => {
      if (prev.includes(groupId)) {
        return prev.filter(id => id !== groupId);
      } else {
        return [...prev, groupId];
      }
    });
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">📤 Document Upload</h1>
          <p className="text-gray-600">Upload and process documents for quality management</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <strong className="font-bold">Error: </strong>
            <span>{error}</span>
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            <strong className="font-bold">Success: </strong>
            <span>{success}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* LEFT: Upload Section */}
          <div className="space-y-6">
            
            {/* File Upload Dropzone */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">1. Select Document</h2>
              
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
                    <div className="text-6xl mb-4">📁</div>
                    <p className="text-gray-600 mb-2">
                      Drag & drop your document here
                    </p>
                    <p className="text-gray-400 text-sm mb-4">
                      or
                    </p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                    >
                      Browse Files
                    </button>
                    <p className="text-gray-400 text-xs mt-4">
                      Supported: PDF, DOCX, PNG, JPG (max 50MB)
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
                      className="text-red-600 hover:text-red-700 font-bold"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Document Metadata */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">2. Document Information</h2>
              
              {/* Document Type */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Type *
                </label>
                <select
                  value={selectedDocumentTypeId || ''}
                  onChange={(e) => setSelectedDocumentTypeId(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select document type...</option>
                  {documentTypes.map(dt => (
                    <option key={dt.id} value={dt.id}>
                      {dt.name} ({dt.processing_method.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              {/* QM Chapter */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  QM Chapter *
                </label>
                <input
                  type="text"
                  value={qmChapter}
                  onChange={(e) => setQmChapter(e.target.value)}
                  placeholder="e.g., 1.2.3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Version */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Version *
                </label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="e.g., v1.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* RIGHT: Interest Groups */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">3. Assign Interest Groups *</h2>
              
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {interestGroups.map(group => (
                  <div
                    key={group.id}
                    onClick={() => toggleInterestGroup(group.id)}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                      selectedInterestGroups.includes(group.id)
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                    }`}
                  >
                    <div>
                      <p className="font-medium text-gray-800">{group.name}</p>
                      <p className="text-sm text-gray-500">{group.code}</p>
                    </div>
                    {selectedInterestGroups.includes(group.id) && (
                      <span className="text-blue-600 text-xl">✓</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  {selectedInterestGroups.length} group(s) selected
                </p>
              </div>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!selectedFile || !selectedDocumentTypeId || uploading}
              className={`w-full py-4 rounded-xl font-bold text-lg transition ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : selectedFile && selectedDocumentTypeId
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {uploading ? `Uploading... ${uploadProgress}%` : '🚀 Upload Document'}
            </button>

            {/* Progress Bar */}
            {uploading && (
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Preview Section */}
        {previewPages.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              📄 Preview ({previewPages.length} pages)
            </h2>
            <div className="grid grid-cols-4 gap-4">
              {previewPages.map(page => (
                <div key={page.id} className="border border-gray-200 rounded-lg p-2">
                  <p className="text-sm text-gray-600 mb-2">Page {page.page_number}</p>
                  <div className="bg-gray-100 rounded aspect-[3/4]"></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

