/**
 * Chunk Preview Panel
 * 
 * Zeigt alle Chunks eines Dokuments in einer übersichtlichen Ansicht.
 * PHASE 2.1: Chunk-Vorschau für Transparenz und Auditierbarkeit.
 * PHASE 2.2: Chunk-Editor (Edit/Delete/Split/Merge) für Level 4+.
 */

"use client";

import { useState, useEffect } from 'react';
import { FileText, ChevronDown, ChevronUp, Hash, Calendar, Layers, Edit, Trash2, Scissors, Merge, X, Check } from 'lucide-react';
import { 
  getChunksForDocument, 
  ChunksListResponse, 
  ChunkPreview,
  editChunk,
  deleteChunk,
  splitChunk,
  mergeChunks
} from '@/lib/api/rag';
import Spinner from './ui/Spinner';
import { useUser } from '@/lib/contexts/UserContext';

interface ChunkPreviewPanelProps {
  documentId: number;
  onChunksLoaded?: (count: number) => void;
  onChunksChanged?: () => void;  // Callback wenn Chunks geändert wurden
}

export default function ChunkPreviewPanel({
  documentId,
  onChunksLoaded,
  onChunksChanged
}: ChunkPreviewPanelProps) {
  const { userLevel } = useUser();
  const canEditChunks = userLevel >= 4;  // Nur Level 4+ können Chunks bearbeiten
  
  const [chunks, setChunks] = useState<ChunkPreview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());
  const [indexedDocumentId, setIndexedDocumentId] = useState<number | null>(null);
  
  // Editor State
  const [editingChunkId, setEditingChunkId] = useState<number | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [selectedChunks, setSelectedChunks] = useState<Set<number>>(new Set());
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    loadChunks();
  }, [documentId]);

  const loadChunks = async () => {
    setLoading(true);
    setError(null);

    try {
      const response: ChunksListResponse = await getChunksForDocument(documentId);
      setChunks(response.chunks);
      setIndexedDocumentId(response.indexed_document_id);
      
      if (onChunksLoaded) {
        onChunksLoaded(response.total_chunks);
      }
    } catch (err: any) {
      console.error('Failed to load chunks:', err);
      setError(err.message || 'Fehler beim Laden der Chunks');
    } finally {
      setLoading(false);
    }
  };

  const toggleChunk = (chunkId: number) => {
    setExpandedChunks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  };

  const handleEdit = (chunk: ChunkPreview) => {
    setEditingChunkId(chunk.id);
    setEditText(chunk.chunk_text);
  };

  const handleSaveEdit = async (chunkId: number) => {
    if (!editText.trim()) {
      setError('Chunk-Text darf nicht leer sein');
      return;
    }

    setActionLoading(chunkId);
    setError(null);

    try {
      await editChunk(chunkId, editText);
      setEditingChunkId(null);
      setEditText('');
      await loadChunks();  // Reload
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      setError(err.message || 'Fehler beim Bearbeiten des Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingChunkId(null);
    setEditText('');
  };

  const handleDelete = async (chunkId: number) => {
    if (!confirm('Möchtest du diesen Chunk wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) {
      return;
    }

    setActionLoading(chunkId);
    setError(null);

    try {
      await deleteChunk(chunkId);
      await loadChunks();  // Reload
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      setError(err.message || 'Fehler beim Löschen des Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSplit = async (chunk: ChunkPreview) => {
    const position = prompt(`An welcher Position soll der Chunk gesplittet werden? (0-${chunk.chunk_text.length})`);
    if (!position) return;

    const splitPos = parseInt(position);
    if (isNaN(splitPos) || splitPos < 0 || splitPos >= chunk.chunk_text.length) {
      setError('Ungültige Split-Position');
      return;
    }

    setActionLoading(chunk.id);
    setError(null);

    try {
      await splitChunk(chunk.id, splitPos);
      await loadChunks();  // Reload
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      setError(err.message || 'Fehler beim Splitten des Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  const toggleChunkSelection = (chunkId: number) => {
    setSelectedChunks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  };

  const handleMerge = async () => {
    if (selectedChunks.size < 2) {
      setError('Bitte wähle mindestens 2 Chunks zum Zusammenführen aus');
      return;
    }

    if (!confirm(`Möchtest du ${selectedChunks.size} Chunks wirklich zusammenführen?`)) {
      return;
    }

    setActionLoading(-1);  // Special ID für Merge
    setError(null);

    try {
      await mergeChunks(Array.from(selectedChunks));
      setSelectedChunks(new Set());
      await loadChunks();  // Reload
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      setError(err.message || 'Fehler beim Zusammenführen der Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center py-8">
          <Spinner size="md" />
          <span className="ml-3 text-gray-600">Lade Chunks...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">❌ {error}</p>
      </div>
    );
  }

  if (!indexedDocumentId) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-700 text-sm">
          ⚠️ Dokument ist noch nicht indexiert. Chunks werden nach der Indexierung angezeigt.
        </p>
      </div>
    );
  }

  if (chunks.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-600 text-sm">Keine Chunks gefunden.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Dokument-Chunks ({chunks.length})
          </h3>
        </div>
        <div className="flex items-center gap-3">
          {canEditChunks && selectedChunks.size >= 2 && (
            <button
              onClick={handleMerge}
              disabled={actionLoading === -1}
              className="inline-flex items-center px-3 py-1.5 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === -1 ? (
                <>
                  <Spinner size="sm" className="mr-1.5" />
                  Zusammenführen...
                </>
              ) : (
                <>
                  <Merge className="w-4 h-4 mr-1.5" />
                  {selectedChunks.size} Chunks zusammenführen
                </>
              )}
            </button>
          )}
          <span className="text-sm text-gray-500">
            {canEditChunks ? 'Editierbar (Level 4+)' : 'Read-Only Vorschau'}
          </span>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Chunks List */}
      <div className="space-y-3">
        {chunks.map((chunk, index) => {
          const isExpanded = expandedChunks.has(chunk.id);
          const isTruncated = chunk.chunk_text.length > 500;

          return (
            <div
              key={chunk.id}
              className="border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
            >
              {/* Chunk Header */}
              <div
                className="p-4 cursor-pointer flex items-start justify-between"
                onClick={() => toggleChunk(chunk.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    {/* Checkbox für Merge (nur Level 4+) */}
                    {canEditChunks && (
                      <input
                        type="checkbox"
                        checked={selectedChunks.has(chunk.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          toggleChunkSelection(chunk.id);
                        }}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    )}
                    <span className="text-sm font-medium text-gray-500">
                      Chunk #{index + 1}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">
                      {chunk.chunk_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      chunk.metadata.chunk_type === 'metadata' 
                        ? 'bg-purple-100 text-purple-700'
                        : chunk.metadata.chunk_type === 'section'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {chunk.metadata.chunk_type}
                    </span>
                  </div>

                  {/* Metadata Icons */}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {chunk.metadata.page_numbers.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Layers className="w-3 h-3" />
                        <span>Seite {chunk.metadata.page_numbers.join(', ')}</span>
                      </div>
                    )}
                    {chunk.metadata.token_count && (
                      <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        <span>{chunk.metadata.token_count} Tokens</span>
                      </div>
                    )}
                    {chunk.metadata.heading_hierarchy.length > 0 && (
                      <div className="flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        <span>{chunk.metadata.heading_hierarchy.join(' > ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons (Level 4+) */}
                {canEditChunks && (
                  <div className="ml-4 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleEdit(chunk)}
                      disabled={editingChunkId === chunk.id || actionLoading === chunk.id}
                      className="p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Bearbeiten"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleSplit(chunk)}
                      disabled={actionLoading === chunk.id}
                      className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Splitten"
                    >
                      <Scissors className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(chunk.id)}
                      disabled={actionLoading === chunk.id}
                      className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Löschen"
                    >
                      {actionLoading === chunk.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                )}

                {/* Expand/Collapse Button */}
                <button
                  className="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleChunk(chunk.id);
                  }}
                >
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </button>
              </div>

              {/* Chunk Content (Expandable) */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="mt-4">
                    {/* Edit Mode */}
                    {editingChunkId === chunk.id ? (
                      <div className="space-y-3">
                        <textarea
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                          rows={10}
                          disabled={actionLoading === chunk.id}
                        />
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleSaveEdit(chunk.id)}
                            disabled={actionLoading === chunk.id || !editText.trim()}
                            className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === chunk.id ? (
                              <>
                                <Spinner size="sm" className="mr-1.5" />
                                Speichern...
                              </>
                            ) : (
                              <>
                                <Check className="w-4 h-4 mr-1.5" />
                                Speichern
                              </>
                            )}
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            disabled={actionLoading === chunk.id}
                            className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            <X className="w-4 h-4 mr-1.5" />
                            Abbrechen
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                          {chunk.chunk_text}
                        </pre>
                      </div>
                    )}

                    {/* Additional Metadata */}
                    <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">Sätze:</span>{' '}
                        {chunk.metadata.sentence_count || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Overlap:</span>{' '}
                        {chunk.metadata.has_overlap ? 'Ja' : 'Nein'}
                        {chunk.metadata.has_overlap && chunk.metadata.overlap_sentence_count > 0 && (
                          <span> ({chunk.metadata.overlap_sentence_count} Sätze)</span>
                        )}
                      </div>
                      <div>
                        <span className="font-medium">Erstellt:</span>{' '}
                        {new Date(chunk.created_at).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Truncated Preview (when collapsed) */}
              {!isExpanded && isTruncated && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="mt-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                        {chunk.chunk_text}
                      </pre>
                    </div>
                    <p className="mt-2 text-xs text-gray-500 text-center">
                      Klicken zum Erweitern...
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

