/**
 * Prompt Viewer Modal
 * 
 * Zeigt den verwendeten Prompt für eine RAG Chat-Message (Read-Only).
 * PHASE 3.1: Transparenz und Auditierbarkeit für RAG Chat.
 */

"use client";

import { useState, useEffect } from 'react';
import { X, FileText, Info, Copy, Check } from 'lucide-react';
import { getPromptForMessage, PromptViewerResponse } from '@/lib/api/rag';
import Spinner from './ui/Spinner';
import toast from 'react-hot-toast';

interface PromptViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  messageId: number;
}

export default function PromptViewerModal({
  isOpen,
  onClose,
  messageId
}: PromptViewerModalProps) {
  const [promptData, setPromptData] = useState<PromptViewerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && messageId) {
      loadPrompt();
    }
  }, [isOpen, messageId]);

  const loadPrompt = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getPromptForMessage(messageId);
      setPromptData(data);
    } catch (err: any) {
      console.error('Failed to load prompt:', err);
      setError(err.message || 'Fehler beim Laden des Prompts');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!promptData) return;

    try {
      await navigator.clipboard.writeText(promptData.prompt_text);
      setCopied(true);
      toast.success('Prompt in Zwischenablage kopiert');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Fehler beim Kopieren');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Prompt Viewer</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Prompt kopieren"
            >
              {copied ? (
                <Check className="w-5 h-5 text-green-600" />
              ) : (
                <Copy className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="md" />
              <span className="ml-3 text-gray-600">Lade Prompt...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 text-sm">❌ {error}</p>
            </div>
          ) : promptData ? (
            <div className="space-y-6">
              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">AI-Modell:</span>{' '}
                  <span className="text-gray-900">{promptData.model_used}</span>
                </div>
                {promptData.document_type && (
                  <div>
                    <span className="font-medium text-gray-700">Dokumenttyp:</span>{' '}
                    <span className="text-gray-900">{promptData.document_type}</span>
                  </div>
                )}
                {promptData.tokens_used && (
                  <div>
                    <span className="font-medium text-gray-700">Tokens:</span>{' '}
                    <span className="text-gray-900">{promptData.tokens_used}</span>
                  </div>
                )}
                <div>
                  <span className="font-medium text-gray-700">Chunks verwendet:</span>{' '}
                  <span className="text-gray-900">{promptData.context_chunks.length}</span>
                </div>
              </div>

              {/* User Question */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <Info className="w-5 h-5 text-blue-600" />
                  User-Frage
                </h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-gray-900">{promptData.question}</p>
                </div>
              </div>

              {/* Prompt Text */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-purple-600" />
                  Vollständiger Prompt
                </h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                    {promptData.prompt_text}
                  </pre>
                </div>
              </div>

              {/* Context Chunks (Collapsible) */}
              {promptData.context_chunks.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Verwendete Chunks ({promptData.context_chunks.length})
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {promptData.context_chunks.map((chunk, index) => (
                      <div
                        key={index}
                        className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm"
                      >
                        <div className="font-medium text-gray-700 mb-1">
                          Chunk {index + 1}: {chunk.chunk_id}
                        </div>
                        {chunk.metadata?.page_numbers && (
                          <div className="text-xs text-gray-500 mb-1">
                            Seiten: {chunk.metadata.page_numbers.join(', ')}
                          </div>
                        )}
                        <div className="text-gray-600 mt-1 line-clamp-2">
                          {chunk.chunk_text?.substring(0, 200)}
                          {chunk.chunk_text && chunk.chunk_text.length > 200 && '...'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
}

