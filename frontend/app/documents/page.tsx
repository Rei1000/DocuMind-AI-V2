"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getUploadsList,
  deleteUpload,
  UploadedDocument,
} from '@/lib/api/documentUpload';
import {
  getAllWorkflowDocuments,
  changeDocumentStatus,
  WorkflowStatus,
  WorkflowDocument,
  ChangeStatusRequest,
  WorkflowUtils
} from '@/lib/api/documentWorkflow';
import { WorkflowToast } from '@/lib/toast';
import { KanbanSkeleton, TableSkeleton } from '@/components/DocumentSkeleton';
import { EmptyKanbanColumn, EmptyDocumentsList } from '@/components/EmptyState';
import StatusChangeModal from './StatusChangeModal';

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
  
  // State
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedDocument, setDraggedDocument] = useState<WorkflowDocument | null>(null);
  const [draggedFromColumn, setDraggedFromColumn] = useState<WorkflowStatus | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<WorkflowStatus | null>(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDocument, setModalDocument] = useState<WorkflowDocument | null>(null);
  const [modalNewStatus, setModalNewStatus] = useState<WorkflowStatus | null>(null);
  
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
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/document-types/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Document types response:', data); // Debug log
      
      // Ensure data is an array
      if (Array.isArray(data)) {
        setDocumentTypes(data);
      } else {
        console.error('Document types is not an array:', data);
        setDocumentTypes([]);
      }
    } catch (error) {
      console.error('Failed to load document types:', error);
      setDocumentTypes([]); // Set empty array on error
    }
  };

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load all workflow documents
      const workflowData = await getAllWorkflowDocuments();
      
      // Initialize columns with workflow data
      const initialColumns: KanbanColumn[] = [
        {
          id: 'draft',
          title: 'Entwurf',
          icon: '📝',
          color: 'gray',
          documents: workflowData.draft || []
        },
        {
          id: 'reviewed',
          title: 'Geprüft',
          icon: '✓',
          color: 'blue',
          documents: workflowData.reviewed || []
        },
        {
          id: 'approved',
          title: 'Freigegeben',
          icon: '✅',
          color: 'green',
          documents: workflowData.approved || []
        },
        {
          id: 'rejected',
          title: 'Zurückgewiesen',
          icon: '❌',
          color: 'red',
          documents: workflowData.rejected || []
        }
      ];

      setColumns(initialColumns);
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError(error.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (documentId: number, newStatus: WorkflowStatus, reason: string, comment?: string) => {
    const loadingToast = WorkflowToast.loading('Status wird geändert...');
    
    try {
      const request: ChangeStatusRequest = {
        document_id: documentId,
        new_status: newStatus,
        user_id: 1, // TODO: Get from auth context
        reason: reason,
        comment: comment
      };

      const response = await changeDocumentStatus(request);
      
      if (response.success) {
        // Find document for toast notification
        const document = columns.flatMap(col => col.documents).find(doc => doc.id === documentId);
        if (document) {
          WorkflowToast.statusChanged(
            document.filename,
            WorkflowUtils.getStatusLabel(document.workflow_status),
            WorkflowUtils.getStatusLabel(newStatus)
          );
        }
        
        // Reload documents to reflect changes
        await loadDocuments();
      } else {
        WorkflowToast.statusChangeError(response.message);
      }
    } catch (error: any) {
      console.error('Status change error:', error);
      WorkflowToast.statusChangeError(error.message || 'Unbekannter Fehler');
    } finally {
      WorkflowToast.dismiss(loadingToast);
    }
  };

  const handleModalConfirm = async (comment: string) => {
    if (!modalDocument || !modalNewStatus) return;
    
    const reason = `Status changed from ${WorkflowUtils.getStatusLabel(modalDocument.workflow_status)} to ${WorkflowUtils.getStatusLabel(modalNewStatus)}`;
    await handleStatusChange(modalDocument.id, modalNewStatus, reason, comment);
  };

  const handleDelete = async (documentId: number, filename: string) => {
    if (!confirm(`Möchten Sie "${filename}" wirklich löschen?`)) {
      return;
    }

    const loadingToast = WorkflowToast.loading('Dokument wird gelöscht...');

    try {
      const response = await deleteUpload(documentId);
      
      if (response.success) {
        WorkflowToast.documentDeleted(filename);
        loadDocuments();
      } else {
        WorkflowToast.error('Fehler beim Löschen des Dokuments');
      }
    } catch (error: any) {
      console.error('Delete error:', error);
      WorkflowToast.error(`Löschen fehlgeschlagen: ${error.message || 'Unbekannter Fehler'}`);
    } finally {
      WorkflowToast.dismiss(loadingToast);
    }
  };

  // ============================================================================
  // DRAG & DROP HANDLERS
  // ============================================================================

  const handleDragStart = (e: React.DragEvent, document: WorkflowDocument, fromColumn: WorkflowStatus) => {
    setDraggedDocument(document);
    setDraggedFromColumn(fromColumn);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, columnId: WorkflowStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverColumn(columnId);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = async (e: React.DragEvent, toColumn: WorkflowStatus) => {
    e.preventDefault();
    
    if (!draggedDocument || !draggedFromColumn || draggedFromColumn === toColumn) {
      setDraggedDocument(null);
      setDraggedFromColumn(null);
      return;
    }

    // Open modal for status change confirmation
    setModalDocument(draggedDocument);
    setModalNewStatus(toColumn);
    setIsModalOpen(true);

    setDraggedDocument(null);
    setDraggedFromColumn(null);
    setDragOverColumn(null);
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
          (doc.document_type?.toLowerCase() || '').includes(query) ||
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

  const getDocumentTypeName = (typeName?: string) => {
    return typeName || 'Unbekannt';
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
                {Array.isArray(documentTypes) && documentTypes.map(dt => (
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
          <div>
            {viewMode === 'kanban' ? <KanbanSkeleton /> : <TableSkeleton />}
          </div>
        )}

        {/* Kanban View */}
        {!loading && viewMode === 'kanban' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {filteredColumns.map((column) => (
              <div
                key={column.id}
                className={`bg-gray-50 rounded-lg p-4 transition-all duration-200 ${
                  dragOverColumn === column.id 
                    ? 'ring-2 ring-blue-500 ring-opacity-50 bg-blue-50' 
                    : ''
                }`}
                onDragOver={(e) => handleDragOver(e, column.id)}
                onDragLeave={handleDragLeave}
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
                    <EmptyKanbanColumn status={column.id} />
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
                            {doc.filename}
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
                              onClick={() => handleDelete(doc.id, doc.filename)}
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
                            <span className="font-medium">{getDocumentTypeName(doc.document_type)}</span>
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
                            <span>Status:</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${WorkflowUtils.getStatusColor(doc.workflow_status)}`}>
                              {WorkflowUtils.getStatusLabel(doc.workflow_status)}
                            </span>
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
              <EmptyDocumentsList onUpload={() => router.push('/document-upload')} />
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
                        return (
                          <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4">
                              <div>
                                <p className="font-medium text-gray-900">{doc.filename}</p>
                                <p className="text-sm text-gray-500">
                                  ID: {doc.id} • {doc.interest_group_ids.length} Interest Groups
                                </p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-sm text-gray-900">
                                {getDocumentTypeName(doc.document_type)}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {doc.qm_chapter || '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {doc.version}
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${WorkflowUtils.getStatusColor(doc.workflow_status)} flex items-center gap-1 w-fit`}>
                                <span>{WorkflowUtils.getStatusIcon(doc.workflow_status)}</span> {WorkflowUtils.getStatusLabel(doc.workflow_status)}
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
                                  onClick={() => handleDelete(doc.id, doc.filename)}
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

        {/* Status Change Modal */}
        {isModalOpen && modalDocument && modalNewStatus && (
          <StatusChangeModal
            isOpen={isModalOpen}
            onClose={() => {
              setIsModalOpen(false);
              setModalDocument(null);
              setModalNewStatus(null);
            }}
            onConfirm={handleModalConfirm}
            document={{
              id: modalDocument.id,
              filename: modalDocument.filename,
              version: modalDocument.version,
              currentStatus: modalDocument.workflow_status,
              newStatus: modalNewStatus
            }}
            user={{
              name: 'Test User', // TODO: Get from auth context
              email: 'test@company.com'
            }}
          />
        )}
      </div>
    </div>
  );
}