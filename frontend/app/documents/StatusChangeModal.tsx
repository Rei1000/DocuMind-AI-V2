"use client";

import React, { useState, useEffect } from 'react';
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
      await changeDocumentStatus(documentId, {
        new_status: targetStatus as WorkflowStatus,
        reason: comment.trim() // Verwende Kommentar als Grund
      });
      
      toast.success('Status erfolgreich geändert');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Status change error:', error);
      toast.error('Fehler beim Ändern des Status');
    } finally {
      setLoading(false);
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
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !comment.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Wird verarbeitet...
                </div>
              ) : (
                'Bestätigen'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
