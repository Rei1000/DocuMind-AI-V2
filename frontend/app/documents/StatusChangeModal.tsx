"use client";

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui';
import { changeDocumentStatus, WorkflowStatus, getDocumentAuditTrail, WorkflowStatusChange } from '@/lib/api/documentWorkflow';
import { toast } from 'react-hot-toast';

interface StatusChangeModalProps {
  documentId: number;
  currentStatus: string;
  targetStatus: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function StatusChangeModal({
  documentId,
  currentStatus,
  targetStatus,
  onClose,
  onSuccess
}: StatusChangeModalProps) {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [auditTrail, setAuditTrail] = useState<WorkflowStatusChange[]>([]);
  const [auditLoading, setAuditLoading] = useState(true);

  // Lade Audit Trail beim Öffnen des Modals
  useEffect(() => {
    const loadAuditTrail = async () => {
      try {
        setAuditLoading(true);
        const trail = await getDocumentAuditTrail(documentId);
        setAuditTrail(trail);
      } catch (error) {
        console.error('Failed to load audit trail:', error);
        // Fehler nicht anzeigen, da Audit Trail optional ist
      } finally {
        setAuditLoading(false);
      }
    };

    loadAuditTrail();
  }, [documentId]);

  const handleSubmit = async () => {
    if (!comment.trim()) {
      toast.error('Bitte geben Sie einen Kommentar an');
      return;
    }

    setLoading(true);
    try {
      console.log('[StatusChangeModal] Starting status change...', { documentId, targetStatus, comment: comment.trim() });
      
      const response = await changeDocumentStatus(documentId, {
        new_status: targetStatus as WorkflowStatus,
        reason: comment.trim() // Verwende Kommentar als Grund
      });
      
      console.log('[StatusChangeModal] API Response received:', response);
      
      // Prüfe ob API-Call erfolgreich war
      if (!response || !response.success) {
        console.error('[StatusChangeModal] API returned unsuccessful response:', response);
        throw new Error(response?.error || response?.message || 'Status-Änderung fehlgeschlagen');
      }
      
      console.log('[StatusChangeModal] Status change successful, closing modal...');
      
      // WICHTIG: Loading auf false setzen BEVOR wir onSuccess/onClose aufrufen
      setLoading(false);
      
      // Toast anzeigen
      toast.success('Status erfolgreich geändert');
      
      // Erst onSuccess (setzt States zurück), dann Modal schließen
      // Aber mit kurzem Delay, damit React State-Updates verarbeiten kann
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 50);
      
    } catch (error) {
      console.error('[StatusChangeModal] Status change error:', error);
      setLoading(false); // WICHTIG: Loading immer zurücksetzen bei Fehler
      toast.error(`Fehler beim Ändern des Status: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`);
    }
  };

  const getStatusDisplayName = (status: string) => {
    switch (status) {
      case 'draft': return 'Entwurf';
      case 'reviewed': return 'Geprüft';
      case 'approved': return 'Freigegeben';
      case 'rejected': return 'Abgelehnt';
      default: return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'reviewed': return 'bg-blue-100 text-blue-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Status ändern
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Status Transition Display */}
          <div className="mb-6">
            <div className="flex items-center justify-center space-x-2 flex-wrap">
              {/* Zeige alle Status-Schritte aus der Historie */}
              {auditTrail.length > 0 ? (
                <>
                  {auditTrail.map((entry, index) => (
                    <React.Fragment key={index}>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(entry.from_status || 'draft')}`}>
                        {getStatusDisplayName(entry.from_status || 'draft')}
                      </div>
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </React.Fragment>
                  ))}
                  {/* Letzter Status */}
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(targetStatus)}`}>
                    {getStatusDisplayName(targetStatus)}
                  </div>
                </>
              ) : (
                <>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentStatus)}`}>
                    {getStatusDisplayName(currentStatus)}
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(targetStatus)}`}>
                    {getStatusDisplayName(targetStatus)}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Comment Input */}
          <div className="mb-6">
            <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
              Kommentar für die Status-Änderung *
            </label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Bitte geben Sie einen Kommentar für die Status-Änderung an..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Dieser Kommentar wird für Audit-Zwecke gespeichert.
            </p>
          </div>

          {/* Audit Trail */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              📋 Status-Historie
            </h3>
            {auditLoading ? (
              <div className="text-sm text-gray-500 italic">
                Lade Historie...
              </div>
            ) : auditTrail.length > 0 ? (
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {auditTrail.map((entry, index) => (
                  <div key={entry.id || index} className="bg-gray-50 rounded-md p-3 text-xs">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-gray-900">
                        {entry.from_status ? getStatusDisplayName(entry.from_status) : 'Unbekannt'} → {getStatusDisplayName(entry.to_status)}
                      </span>
                      <span className="text-gray-500">
                        {new Date(entry.created_at).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                    <div className="text-gray-600">
                      <strong>User:</strong> {entry.changed_by_user_name || `User ${entry.changed_by_user_id}`}
                    </div>
                    <div className="text-gray-600">
                      <strong>Grund:</strong> {entry.reason || 'Kein Kommentar'}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">
                Keine Status-Änderungen vorhanden.
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <Button
              onClick={onClose}
              disabled={loading}
              variant="secondary"
            >
              Abbrechen
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={loading || !comment.trim()}
              loading={loading}
              variant="primary"
            >
              {loading ? 'Wird verarbeitet...' : 'Bestätigen'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
