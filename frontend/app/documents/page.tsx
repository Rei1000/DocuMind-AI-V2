"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getUploadsList,
  deleteUpload,
  UploadedDocument,
} from '@/lib/api/documentUpload';
import {
  getDocumentsByStatus,
  changeDocumentStatus,
  WorkflowStatus,
  getWorkflowStatusBadge,
  getWorkflowStatusName,
  StatusChangeRequest
} from '@/lib/api/documentWorkflow';

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
  documents: UploadedDocument[];
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentListPage() {
  const router = useRouter();
  
  // State
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedDocument, setDraggedDocument] = useState<UploadedDocument | null>(null);
  const [draggedFromColumn, setDraggedFromColumn] = useState<WorkflowStatus | null>(null);
  
  // Filter state
  const [selectedDocumentTypeId, setSelectedDocumentTypeId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban');

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadDocumentTypes();
    loadDocuments();
  }, [selectedDocumentTypeId]);

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
      for (const column of initialColumns) {
        const response = await getDocumentsByStatus(column.id);
        if (response.success && response.data) {
          let docs = response.data.documents;
          
          // Filter by document type if selected
          if (selectedDocumentTypeId) {
            docs = docs.filter(doc => doc.document_type_id === selectedDocumentTypeId);
          }
          
          column.documents = docs;
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
  // DRAG & DROP HANDLERS
  // ============================================================================

  const handleDragStart = (e: React.DragEvent, document: UploadedDocument, fromColumn: WorkflowStatus) => {
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

    // Confirm status change
    const fromName = getWorkflowStatusName(draggedFromColumn);
    const toName = getWorkflowStatusName(toColumn);
    
    if (confirm(`Dokument "${draggedDocument.original_filename}" von "${fromName}" zu "${toName}" verschieben?`)) {
      await handleStatusChange(draggedDocument.id, toColumn, `Moved from ${fromName} to ${toName}`);
    }

    setDraggedDocument(null);
    setDraggedFromColumn(null);
  };

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
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📚 Dokumentenverwaltung</h1>
          <p className="text-gray-600">Workflow-basierte Dokumentenverwaltung mit Drag & Drop</p>
        </div>

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

            {/* View Mode Toggle */}
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
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {getTotalDocuments()} Dokument(e) gefunden
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

        {/* Kanban View */}
        {!loading && viewMode === 'kanban' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {filteredColumns.map((column) => (
              <div
                key={column.id}
                className="bg-gray-50 rounded-lg p-4"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, column.id)}
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
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-2xl mb-2">📭</div>
                      <p className="text-sm">Keine Dokumente</p>
                    </div>
                  ) : (
                    column.documents.map((doc) => (
                      <div
                        key={doc.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, doc, column.id)}
                        className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-move"
                      >
                        {/* Document Header */}
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 text-sm line-clamp-2">
                            {doc.original_filename}
                          </h4>
                          <div className="flex gap-1 ml-2">
                            <button
                              onClick={() => router.push(`/documents/${doc.id}`)}
                              className="text-blue-600 hover:text-blue-700 text-xs"
                              title="Ansehen"
                            >
                              👁️
                            </button>
                            <button
                              onClick={() => handleDelete(doc.id, doc.original_filename)}
                              className="text-red-600 hover:text-red-700 text-xs"
                              title="Löschen"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>

                        {/* Document Info */}
                        <div className="space-y-1 text-xs text-gray-600">
                          <div className="flex justify-between">
                            <span>Typ:</span>
                            <span className="font-medium">{getDocumentTypeName(doc.document_type_id)}</span>
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

                        {/* Upload Date */}
                        <div className="mt-3 pt-2 border-t border-gray-100">
                          <p className="text-xs text-gray-500">
                            {formatDate(doc.uploaded_at)}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Table View (existing implementation) */}
        {!loading && viewMode === 'table' && (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {getTotalDocuments() === 0 ? (
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
                        Status
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
                        const badge = getWorkflowStatusBadge(column.id);
                        return (
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
                            <td className="px-6 py-4">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text} flex items-center gap-1 w-fit`}>
                                <span>{badge.icon}</span> {badge.label}
                              </span>
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
                        );
                      })
                    )}
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