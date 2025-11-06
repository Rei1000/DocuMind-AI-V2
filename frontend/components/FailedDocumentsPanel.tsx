/**
 * Failed Documents Panel
 * 
 * Zeigt Dokumente mit fehlgeschlagener AI-Verarbeitung an.
 * Ermöglicht Retry und Delete-Aktionen.
 */

"use client";

import { useState, useEffect } from 'react';
import { AlertCircle, RefreshCw, Trash2, XCircle, CheckCircle2 } from 'lucide-react';
import { UploadedDocument, retryDocumentProcessing, RetryProcessingResponse } from '@/lib/api/documentUpload';
import { softDeleteDocument } from '@/lib/api/documentWorkflow';
import Spinner from './ui/Spinner';

interface FailedDocumentsPanelProps {
  documents: UploadedDocument[];
  onDocumentRetried?: () => void;
  onDocumentDeleted?: () => void;
}

export default function FailedDocumentsPanel({
  documents,
  onDocumentRetried,
  onDocumentDeleted
}: FailedDocumentsPanelProps) {
  const [retrying, setRetrying] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [retryResult, setRetryResult] = useState<{ documentId: number; result: RetryProcessingResponse } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const failedDocuments = documents.filter(doc => doc.processing_status === 'failed');

  if (failedDocuments.length === 0) {
    return null; // Kein Panel anzeigen wenn keine fehlgeschlagenen Dokumente
  }

  const handleRetry = async (documentId: number) => {
    setRetrying(documentId);
    setError(null);
    setRetryResult(null);

    try {
      const result = await retryDocumentProcessing(documentId, false); // Nur fehlgeschlagene Seiten
      
      setRetryResult({ documentId, result });
      
      // Warte kurz, dann triggere Refresh
      setTimeout(() => {
        if (onDocumentRetried) {
          onDocumentRetried();
        }
        setRetryResult(null);
      }, 3000);
      
    } catch (err: any) {
      console.error('Retry failed:', err);
      setError(`Fehler beim Wiederholen: ${err.message || 'Unbekannter Fehler'}`);
    } finally {
      setRetrying(null);
    }
  };

  const handleDelete = async (documentId: number, filename: string) => {
    if (!confirm(`Möchtest du das fehlgeschlagene Dokument "${filename}" wirklich löschen?`)) {
      return;
    }

    setDeleting(documentId);
    setError(null);

    try {
      await softDeleteDocument(documentId, 'Fehlgeschlagene AI-Verarbeitung - Dokument gelöscht');
      
      if (onDocumentDeleted) {
        onDocumentDeleted();
      }
      
    } catch (err: any) {
      console.error('Delete failed:', err);
      setError(`Fehler beim Löschen: ${err.message || 'Unbekannter Fehler'}`);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <AlertCircle className="w-5 h-5 text-red-600" />
        <h3 className="text-lg font-semibold text-red-800">
          Fehlgeschlagene Dokumente ({failedDocuments.length})
        </h3>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 bg-red-100 border border-red-300 rounded-lg p-3 flex items-start gap-2">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Retry Result */}
      {retryResult && (
        <div className={`mb-4 border rounded-lg p-3 flex items-start gap-2 ${
          retryResult.result.success 
            ? 'bg-green-100 border-green-300' 
            : 'bg-yellow-100 border-yellow-300'
        }`}>
          {retryResult.result.success ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">{retryResult.result.message}</p>
                <p className="text-xs text-green-700 mt-1">
                  {retryResult.result.statistics.successful_pages} von {retryResult.result.statistics.retried_pages} Seiten erfolgreich
                </p>
              </div>
            </>
          ) : (
            <>
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800">{retryResult.result.message}</p>
                {retryResult.result.errors.length > 0 && (
                  <ul className="text-xs text-yellow-700 mt-1 list-disc list-inside">
                    {retryResult.result.errors.slice(0, 3).map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Document List */}
      <div className="space-y-2">
        {failedDocuments.map((doc) => (
          <div
            key={doc.id}
            className="bg-white rounded-lg border border-red-200 p-3 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            {/* Document Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900 truncate">
                  {doc.original_filename}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                  <XCircle className="w-3 h-3 mr-1" />
                  Fehlgeschlagen
                </span>
              </div>
              <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                <span>{doc.document_type_name || `Typ ${doc.document_type_id}`}</span>
                <span>{doc.page_count} Seite{doc.page_count !== 1 ? 'n' : ''}</span>
                <span>{new Date(doc.uploaded_at).toLocaleDateString('de-DE')}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 ml-4">
              {/* Retry Button */}
              <button
                onClick={() => handleRetry(doc.id)}
                disabled={retrying === doc.id || deleting === doc.id}
                className="inline-flex items-center px-3 py-1.5 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="AI-Verarbeitung wiederholen"
              >
                {retrying === doc.id ? (
                  <>
                    <Spinner size="sm" className="mr-1.5" />
                    Wird wiederholt...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-1.5" />
                    Wiederholen
                  </>
                )}
              </button>

              {/* Delete Button */}
              <button
                onClick={() => handleDelete(doc.id, doc.original_filename)}
                disabled={retrying === doc.id || deleting === doc.id}
                className="inline-flex items-center px-3 py-1.5 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Dokument löschen"
              >
                {deleting === doc.id ? (
                  <>
                    <Spinner size="sm" className="mr-1.5" />
                    Wird gelöscht...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-1.5" />
                    Löschen
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

