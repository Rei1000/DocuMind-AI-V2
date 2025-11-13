"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getArchivedDocuments,
  hardDeleteDocument,
  WorkflowDocument,
  HardDeleteDocumentResponse
} from '@/lib/api/documentWorkflow';
import { useUser } from '@/lib/contexts/UserContext';
import Spinner from '@/components/ui/Spinner';
import { Eye, Trash2 } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface HardDeleteModalProps {
  isOpen: boolean;
  document: WorkflowDocument | null;
  onClose: () => void;
  onConfirm: (documentId: number, confirmation: string) => Promise<void>;
}

// ============================================================================
// MODAL COMPONENTS
// ============================================================================

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
          <li>Alle Metadaten werden entfernt</li>
          <li>Archiv-Eintrag wird gelöscht</li>
        </ul>
        <p className="text-sm font-bold text-red-600 mb-4">
          ⚠️ Diese Aktion kann nicht rückgängig gemacht werden!
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<WorkflowDocument | null>(null);
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
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Fehler beim Laden der archivierten Dokumente';
      setError(errorMessage);
      setArchivedDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  // Lade archivierte Dokumente
  useEffect(() => {
    const hasAccess = userLevel >= 4 || isQmsAdmin;
    
    if (hasAccess && userLevel > 0 && archivedDocuments.length === 0 && !loading) {
      loadArchivedDocuments();
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

  const handleHardDelete = async (documentId: number, confirmation: string) => {
    try {
      const result: HardDeleteDocumentResponse = await hardDeleteDocument(documentId, confirmation);
      await loadArchivedDocuments(); // Reload
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

  const hasAccess = userLevel >= 4 || isQmsAdmin;
  
  if (!hasAccess && !userContextLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📦 Archiv</h1>
        <p className="text-gray-600">
          Gelöschte Dokumente - Read-Only Historie ({archivedDocuments.length} {archivedDocuments.length === 1 ? 'Dokument' : 'Dokumente'})
        </p>
        <p className="text-sm text-gray-500 mt-2">
          ℹ️ Archivierte Dokumente können nur angezeigt werden. Endgültige Löschung nur für Admins (Level 5).
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

      {/* Table View - Read-Only Historie */}
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
                      Version
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status (beim Löschen)
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
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {doc.version || 'v1.0'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                          doc.workflow_status === 'approved' ? 'bg-green-100 text-green-800' :
                          doc.workflow_status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                          doc.workflow_status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.workflow_status === 'approved' && '✅'}
                          {doc.workflow_status === 'reviewed' && '✓'}
                          {doc.workflow_status === 'rejected' && '❌'}
                          {doc.workflow_status === 'draft' && '📝'}
                          {' '}
                          {doc.workflow_status === 'approved' ? 'Freigegeben' :
                           doc.workflow_status === 'reviewed' ? 'Geprüft' :
                           doc.workflow_status === 'rejected' ? 'Zurückgewiesen' :
                           'Entwurf'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(doc.uploaded_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => router.push(`/documents/${doc.id}`)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                            title="Dokument ansehen (Read-Only)"
                          >
                            <Eye size={16} />
                            Ansehen
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

      {/* Hard Delete Modal */}
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
