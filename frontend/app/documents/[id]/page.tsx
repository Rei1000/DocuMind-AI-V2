"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  getUploadDetails,
  deleteUpload,
  getPreviewImageUrl,
  getThumbnailImageUrl,
  UploadedDocumentDetail,
  DocumentPage,
  InterestGroupAssignment,
} from '@/lib/api/documentUpload';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
}

interface InterestGroup {
  id: number;
  name: string;
  code: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = parseInt(params.id as string);
  
  // State
  const [document, setDocument] = useState<UploadedDocumentDetail | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [interestGroups, setInterestGroups] = useState<InterestGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadDocumentTypes();
    loadInterestGroups();
    loadDocumentDetails();
  }, [documentId]);

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
      setDocumentTypes(data.document_types);
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
      setInterestGroups(data);
    } catch (error) {
      console.error('Failed to load interest groups:', error);
    }
  };

  const loadDocumentDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUploadDetails(documentId);
      
      if (response.success) {
        setDocument(response.document);
      } else {
        setError('Failed to load document details');
      }
    } catch (error: any) {
      console.error('Failed to load document details:', error);
      setError(error.message || 'Failed to load document details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!document) return;
    
    if (!confirm(`Are you sure you want to delete "${document.original_filename}"?`)) {
      return;
    }

    try {
      const response = await deleteUpload(documentId);
      
      if (response.success) {
        router.push('/documents');
      } else {
        alert('Failed to delete document');
      }
    } catch (error: any) {
      console.error('Delete error:', error);
      alert(`Delete failed: ${error.message || 'Unknown error'}`);
    }
  };

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const getDocumentTypeName = (typeId: number) => {
    const type = documentTypes.find(dt => dt.id === typeId);
    return type ? type.name : 'Unknown';
  };

  const getInterestGroupName = (groupId: number) => {
    const group = interestGroups.find(ig => ig.id === groupId);
    return group ? group.name : 'Unknown';
  };

  const getInterestGroupCode = (groupId: number) => {
    const group = interestGroups.find(ig => ig.id === groupId);
    return group ? group.code : '';
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      processing: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Processing' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },
    };

    const badge = badges[status] || badges.pending;

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="text-6xl mb-4">⏳</div>
            <p className="text-gray-600 text-lg">Loading document details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="text-6xl mb-4">❌</div>
            <p className="text-red-600 text-lg mb-4">{error || 'Document not found'}</p>
            <button
              onClick={() => router.push('/documents')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
            >
              Back to Documents
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <button
              onClick={() => router.push('/documents')}
              className="text-blue-600 hover:text-blue-700 font-medium mb-2 flex items-center"
            >
              ← Back to Documents
            </button>
            <h1 className="text-4xl font-bold text-gray-800">{document.original_filename}</h1>
          </div>
          <div className="flex items-center space-x-3">
            {getStatusBadge(document.processing_status)}
            <button
              onClick={handleDelete}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
            >
              🗑️ Delete
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT: Document Info */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Metadata */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">📋 Document Information</h2>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Document Type</p>
                  <p className="font-medium text-gray-900">
                    {getDocumentTypeName(document.document_type_id)}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">QM Chapter</p>
                  <p className="font-medium text-gray-900">{document.qm_chapter}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Version</p>
                  <p className="font-medium text-gray-900">{document.version}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">File Size</p>
                  <p className="font-medium text-gray-900">
                    {formatFileSize(document.file_size_bytes)}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">File Type</p>
                  <p className="font-medium text-gray-900">{document.file_type.toUpperCase()}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Pages</p>
                  <p className="font-medium text-gray-900">{document.page_count}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Processing Method</p>
                  <p className="font-medium text-gray-900">
                    {document.processing_method.toUpperCase()}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Uploaded</p>
                  <p className="font-medium text-gray-900">{formatDate(document.uploaded_at)}</p>
                </div>
              </div>
            </div>

            {/* Interest Groups */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">🏢 Interest Groups</h2>
              
              {document.interest_groups.length === 0 ? (
                <p className="text-gray-500 text-sm">No interest groups assigned</p>
              ) : (
                <div className="space-y-2">
                  {document.interest_groups.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                    >
                      <p className="font-medium text-gray-900">
                        {getInterestGroupName(assignment.interest_group_id)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {getInterestGroupCode(assignment.interest_group_id)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Page Navigation */}
            {document.pages.length > 0 && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">📄 Pages</h2>
                
                <div className="grid grid-cols-4 gap-2">
                  {document.pages.map((page, index) => (
                    <button
                      key={page.id}
                      onClick={() => setSelectedPageIndex(index)}
                      className={`aspect-[3/4] rounded-lg border-2 transition ${
                        selectedPageIndex === index
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-center h-full">
                        <p className="text-xs font-medium text-gray-600">
                          {page.page_number}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">
                🔍 Preview
                {document.pages.length > 0 && (
                  <span className="text-gray-500 font-normal ml-2">
                    (Page {document.pages[selectedPageIndex]?.page_number || 1} of {document.page_count})
                  </span>
                )}
              </h2>
              
              {document.pages.length === 0 ? (
                <div className="bg-gray-50 rounded-lg p-12 text-center">
                  <div className="text-6xl mb-4">📭</div>
                  <p className="text-gray-600">No preview available</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Preview generation may still be in progress
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Main Preview */}
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[600px] flex items-center justify-center">
                    <div className="bg-white shadow-lg rounded">
                      {/* Placeholder for actual image */}
                      <div className="w-full aspect-[3/4] bg-gray-200 rounded flex items-center justify-center">
                        <div className="text-center">
                          <p className="text-gray-600 mb-2">📄</p>
                          <p className="text-sm text-gray-500">
                            Page {document.pages[selectedPageIndex]?.page_number}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {document.pages[selectedPageIndex]?.width} × {document.pages[selectedPageIndex]?.height} px
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Navigation Controls */}
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setSelectedPageIndex(Math.max(0, selectedPageIndex - 1))}
                      disabled={selectedPageIndex === 0}
                      className={`px-4 py-2 rounded-lg font-medium transition ${
                        selectedPageIndex === 0
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      ← Previous
                    </button>
                    
                    <p className="text-sm text-gray-600">
                      Page {selectedPageIndex + 1} of {document.pages.length}
                    </p>
                    
                    <button
                      onClick={() => setSelectedPageIndex(Math.min(document.pages.length - 1, selectedPageIndex + 1))}
                      disabled={selectedPageIndex === document.pages.length - 1}
                      className={`px-4 py-2 rounded-lg font-medium transition ${
                        selectedPageIndex === document.pages.length - 1
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      Next →
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

