"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getUploadsList,
  deleteUpload,
  UploadedDocument,
} from '@/lib/api/documentUpload';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
}

interface User {
  id: number;
  email: string;
}

type WorkflowStatus = 'draft' | 'reviewed' | 'approved' | 'rejected';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentListPage() {
  const router = useRouter();
  
  // State
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedWorkflowStatus, setSelectedWorkflowStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadDocumentTypes();
    loadDocuments();
  }, [selectedDocumentTypeId, selectedStatus, selectedWorkflowStatus]);

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
      setDocumentTypes(data.document_types || []);
    } catch (error) {
      console.error('Failed to load document types:', error);
    }
  };

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params: any = {
        limit: 100,
        offset: 0,
      };

      if (selectedDocumentTypeId) {
        params.document_type_id = selectedDocumentTypeId;
      }

      if (selectedStatus !== 'all') {
        params.processing_status = selectedStatus;
      }

      const response = await getUploadsList(params);
      
      if (response.success) {
        // Filter by workflow status if needed
        let docs = response.documents;
        if (selectedWorkflowStatus !== 'all') {
          docs = docs.filter(doc => (doc as any).workflow_status === selectedWorkflowStatus);
        }
        setDocuments(docs);
      } else {
        setError('Failed to load documents');
      }
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError(error.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId: number, filename: string) => {
    if (!confirm(`Möchten Sie "${filename}" wirklich löschen?`)) {
      return;
    }

    try {
      const response = await deleteUpload(documentId);
      
      if (response.success) {
        loadDocuments();
      } else {
        alert('Fehler beim Löschen des Dokuments');
      }
    } catch (error: any) {
      console.error('Delete error:', error);
      alert(`Löschen fehlgeschlagen: ${error.message || 'Unbekannter Fehler'}`);
    }
  };

  // ============================================================================
  // FILTERING
  // ============================================================================

  const filteredDocuments = documents.filter(doc => {
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
  });

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const getProcessingStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Ausstehend' },
      processing: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'In Bearbeitung' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Abgeschlossen' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Fehlgeschlagen' },
    };

    const badge = badges[status] || badges.pending;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const getWorkflowStatusBadge = (status: WorkflowStatus) => {
    const badges: Record<WorkflowStatus, { bg: string; text: string; label: string; icon: string }> = {
      draft: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Entwurf', icon: '📝' },
      reviewed: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Geprüft', icon: '✓' },
      approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'Freigegeben', icon: '✅' },
      rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'Zurückgewiesen', icon: '❌' },
    };

    const badge = badges[status] || badges.draft;

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text} flex items-center gap-1`}>
        <span>{badge.icon}</span> {badge.label}
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

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📚 Dokumentenverwaltung</h1>
          <p className="text-gray-600">Verwalten und überprüfen Sie alle hochgeladenen Dokumente</p>
        </div>

        {/* Filter Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            
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

            {/* Workflow Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Workflow-Status
              </label>
              <select
                value={selectedWorkflowStatus}
                onChange={(e) => setSelectedWorkflowStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Alle Status</option>
                <option value="draft">📝 Entwurf</option>
                <option value="reviewed">✓ Geprüft</option>
                <option value="approved">✅ Freigegeben</option>
                <option value="rejected">❌ Zurückgewiesen</option>
              </select>
            </div>

            {/* Processing Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Verarbeitungsstatus
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Alle Status</option>
                <option value="pending">Ausstehend</option>
                <option value="processing">In Bearbeitung</option>
                <option value="completed">Abgeschlossen</option>
                <option value="failed">Fehlgeschlagen</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {filteredDocuments.length} Dokument(e) gefunden
            </p>
            <button
              onClick={() => router.push('/document-upload')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Neues Dokument hochladen
            </button>
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
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <div className="text-4xl mb-4">⏳</div>
            <p className="text-gray-600">Dokumente werden geladen...</p>
          </div>
        )}

        {/* Documents Table */}
        {!loading && (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {filteredDocuments.length === 0 ? (
              <div className="p-12 text-center">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-gray-600 text-lg mb-4">Keine Dokumente gefunden</p>
                <button
                  onClick={() => router.push('/document-upload')}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Erstes Dokument hochladen
                </button>
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
                        Seiten
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Workflow
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Verarbeitung
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
                    {filteredDocuments.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4">
                          <div>
                            <p className="font-medium text-gray-900">{doc.original_filename}</p>
                            <p className="text-sm text-gray-500">
                              {formatFileSize(doc.file_size_bytes)} • {doc.file_type.toUpperCase()}
                            </p>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-sm text-gray-900">
                            {getDocumentTypeName(doc.document_type_id)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {doc.qm_chapter || '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {doc.version}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {doc.page_count || 0}
                        </td>
                        <td className="px-6 py-4">
                          {getWorkflowStatusBadge((doc as any).workflow_status || 'draft')}
                        </td>
                        <td className="px-6 py-4">
                          {getProcessingStatusBadge(doc.processing_status)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {formatDate(doc.uploaded_at)}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-3">
                            <button
                              onClick={() => router.push(`/documents/${doc.id}`)}
                              className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                            >
                              Ansehen
                            </button>
                            <button
                              onClick={() => handleDelete(doc.id, doc.original_filename)}
                              className="text-red-600 hover:text-red-700 font-medium text-sm"
                            >
                              Löschen
                            </button>
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
      </div>
    </div>
  );
}