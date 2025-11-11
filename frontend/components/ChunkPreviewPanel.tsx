/**
 * Chunk Preview Panel
 * 
 * Zeigt alle Chunks eines Dokuments in einer übersichtlichen Ansicht.
 * PHASE 2.1: Chunk-Vorschau für Transparenz und Auditierbarkeit.
 * PHASE 2.2: Chunk-Editor (Edit/Delete/Split/Merge) für Level 4+.
 * 
 * UX: 3-Stufen-System
 * 1. Zugeklappt: Nur Header sichtbar
 * 2. Vorschau: Erste 500 Zeichen + "Klicken für vollständigen Text"
 * 3. Vollständig: Kompletter Chunk-Text
 */

"use client";

import { useState, useEffect, useMemo } from 'react';
import { FileText, ChevronDown, ChevronUp, Hash, Calendar, Layers, Edit, Trash2, Scissors, Merge, X, Check, ChevronRight, Expand } from 'lucide-react';
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
import SplitChunkModal from './SplitChunkModal';

interface ChunkPreviewPanelProps {
  documentId: number;
  onChunksLoaded?: (count: number) => void;
  onChunksChanged?: () => void;  // Callback wenn Chunks geändert wurden
  initialChunkId?: string;  // NEU: Chunk-ID die automatisch geöffnet werden soll (aus Query-Parameter)
  highlightTerms?: string[];  // NEU: Suchwörter die rot markiert werden sollen
}

// Chunk-Expansion States
type ChunkExpansionState = 'collapsed' | 'preview' | 'full';

export default function ChunkPreviewPanel({
  documentId,
  onChunksLoaded,
  onChunksChanged,
  initialChunkId,
  highlightTerms = []
}: ChunkPreviewPanelProps) {
  const { userLevel } = useUser();
  const canEditChunks = userLevel >= 4;  // Nur Level 4+ können Chunks bearbeiten
  
  const [chunks, setChunks] = useState<ChunkPreview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Panel-Level Collapse: Standardmäßig zugeklappt
  const [isPanelCollapsed, setIsPanelCollapsed] = useState<boolean>(true);
  // Seiten-Level Collapse: Welche Seiten sind eingeklappt
  const [collapsedPages, setCollapsedPages] = useState<Set<number>>(new Set());
  // 3-Stufen-System: collapsed → preview → full
  const [chunkExpansionStates, setChunkExpansionStates] = useState<Map<number, ChunkExpansionState>>(new Map());
  const [indexedDocumentId, setIndexedDocumentId] = useState<number | null>(null);
  
  // Editor State
  const [editingChunkId, setEditingChunkId] = useState<number | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [splitChunkModal, setSplitChunkModal] = useState<{ isOpen: boolean; chunk: ChunkPreview | null }>({
    isOpen: false,
    chunk: null
  });
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
      // Sortiere Chunks nach Seitenzahl (bereits im Backend sortiert, aber sicherstellen)
      const sortedChunks = [...response.chunks].sort((a, b) => {
        const pageA = a.metadata.page_numbers[0] || 999;
        const pageB = b.metadata.page_numbers[0] || 999;
        if (pageA !== pageB) return pageA - pageB;
        // Bei gleicher Seite: nach chunk_id sortieren
        return a.chunk_id.localeCompare(b.chunk_id);
      });
      setChunks(sortedChunks);
      setIndexedDocumentId(response.indexed_document_id);
      
      // Initialisiere alle Chunks als 'collapsed'
      const initialStates = new Map<number, ChunkExpansionState>();
      sortedChunks.forEach(chunk => {
        initialStates.set(chunk.id, 'collapsed');
      });
      setChunkExpansionStates(initialStates);
      
      // Initialisiere alle Seiten als eingeklappt (standardmäßig zugeklappt)
      const allPageNumbers = new Set<number>();
      sortedChunks.forEach(chunk => {
        const pageNumber = chunk.metadata.page_numbers[0] || 0;
        if (pageNumber > 0) {
          allPageNumbers.add(pageNumber);
        }
      });
      setCollapsedPages(allPageNumbers); // Alle Seiten standardmäßig eingeklappt
      
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

  // NEU: Auto-Öffnen des Chunks wenn initialChunkId gesetzt ist
  useEffect(() => {
    if (!initialChunkId || chunks.length === 0 || loading) return;

    // Finde den Chunk mit der passenden chunk_id
    const targetChunk = chunks.find(chunk => chunk.chunk_id === initialChunkId);
    
    if (targetChunk) {
      // 1. Öffne das Panel
      setIsPanelCollapsed(false);
      
      // 2. Öffne die Seite (entferne aus collapsedPages)
      const pageNumber = targetChunk.metadata.page_numbers[0] || 0;
      if (pageNumber > 0) {
        setCollapsedPages(prev => {
          const newSet = new Set(prev);
          newSet.delete(pageNumber);
          return newSet;
        });
      }
      
      // 3. Erweitere den Chunk auf 'full'
      setChunkExpansionStates(prev => {
        const newMap = new Map(prev);
        newMap.set(targetChunk.id, 'full');
        return newMap;
      });
      
      // 4. Scrolle zum Chunk (mit kleiner Verzögerung für DOM-Update)
      setTimeout(() => {
        const chunkElement = document.getElementById(`chunk-${targetChunk.id}`);
        if (chunkElement) {
          chunkElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 300);
    }
  }, [initialChunkId, chunks, loading]);

  /**
   * NEU: Markiert Suchwörter im Text rot.
   */
  const highlightText = (text: string, terms: string[]): string => {
    if (!terms || terms.length === 0) return text;
    
    let highlighted = text;
    
    // Sortiere nach Länge (längere Wörter zuerst) um Überschneidungen zu vermeiden
    const sortedTerms = [...terms].sort((a, b) => b.length - a.length);
    
    sortedTerms.forEach(term => {
      // Case-insensitive Suche mit Regex
      const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark style="background-color: #fee2e2; color: #991b1b; padding: 2px 4px; border-radius: 3px; font-weight: 600;">$1</mark>');
    });
    
    return highlighted;
  };

  // Gruppiere Chunks nach Seiten
  const chunksByPage = useMemo(() => {
    const grouped = new Map<number, ChunkPreview[]>();
    chunks.forEach(chunk => {
      const pageNumber = chunk.metadata.page_numbers[0] || 0;
      if (!grouped.has(pageNumber)) {
        grouped.set(pageNumber, []);
      }
      grouped.get(pageNumber)!.push(chunk);
    });
    return grouped;
  }, [chunks]);

  const toggleChunkExpansion = (chunkId: number) => {
    setChunkExpansionStates(prev => {
      const newMap = new Map(prev);
      const currentState = newMap.get(chunkId) || 'collapsed';
      
      // 3-Stufen-Zyklus: collapsed → preview → full → collapsed
      let nextState: ChunkExpansionState;
      if (currentState === 'collapsed') {
        nextState = 'preview';
      } else if (currentState === 'preview') {
        nextState = 'full';
      } else {
        nextState = 'collapsed';
      }
      
      newMap.set(chunkId, nextState);
      return newMap;
    });
  };

  const expandToFull = (chunkId: number) => {
    setChunkExpansionStates(prev => {
      const newMap = new Map(prev);
      newMap.set(chunkId, 'full');
      return newMap;
    });
  };

  const handleEdit = (chunk: ChunkPreview) => {
    setEditingChunkId(chunk.id);
    setEditText(chunk.chunk_text);
    // Erweitere auf 'full' wenn im Edit-Modus
    expandToFull(chunk.id);
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
      await loadChunks();
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      console.error('Failed to edit chunk:', err);
      setError(err.message || 'Fehler beim Bearbeiten des Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingChunkId(null);
    setEditText('');
  };

  const handleSplit = async (chunk: ChunkPreview) => {
    // Öffne Modal statt prompt()
    setSplitChunkModal({ isOpen: true, chunk });
  };

  const handleSplitConfirm = async (splitPosition: number, overlapSentences: number) => {
    if (!splitChunkModal.chunk) return;

    setActionLoading(splitChunkModal.chunk.id);
    setError(null);

    try {
      await splitChunk(splitChunkModal.chunk.id, splitPosition, overlapSentences);
      await loadChunks();
      if (onChunksChanged) {
        onChunksChanged();
      }
      setSplitChunkModal({ isOpen: false, chunk: null });
    } catch (err: any) {
      console.error('Failed to split chunk:', err);
      setError(err.message || 'Fehler beim Splitten des Chunks');
      throw err; // Re-throw damit Modal offen bleibt
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (chunkId: number) => {
    if (!confirm('Möchten Sie diesen Chunk wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) {
      return;
    }

    setActionLoading(chunkId);
    setError(null);

    try {
      await deleteChunk(chunkId);
      await loadChunks();
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      console.error('Failed to delete chunk:', err);
      setError(err.message || 'Fehler beim Löschen des Chunks');
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
      setError('Bitte wählen Sie mindestens 2 Chunks zum Zusammenführen aus');
      return;
    }

    const chunkIds = Array.from(selectedChunks);
    setActionLoading(chunkIds[0]);
    setError(null);

    try {
      await mergeChunks(chunkIds);
      setSelectedChunks(new Set());
      await loadChunks();
      if (onChunksChanged) {
        onChunksChanged();
      }
    } catch (err: any) {
      console.error('Failed to merge chunks:', err);
      setError(err.message || 'Fehler beim Zusammenführen der Chunks');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center py-8">
          <Spinner size="md" />
          <span className="ml-3 text-gray-600">Lade Chunks...</span>
        </div>
      </div>
    );
  }

  if (error && !chunks.length) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
          className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
        >
          <div className="flex items-center gap-2">
            {isPanelCollapsed ? (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">✂️ Chunk-Vorschau</h3>
              <p className="text-sm text-gray-500 mt-1">
                {chunks.length} Chunk{chunks.length !== 1 ? 's' : ''} • Sortiert nach Seiten
              </p>
            </div>
          </div>
        </button>
        {!isPanelCollapsed && canEditChunks && selectedChunks.size >= 2 && (
          <button
            onClick={handleMerge}
            disabled={actionLoading !== null}
            className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Zusammenführen...
              </>
            ) : (
              <>
                <Merge className="w-4 h-4 mr-2" />
                {selectedChunks.size} Chunks zusammenführen
              </>
            )}
          </button>
        )}
      </div>

      {/* Panel Content - Nur anzeigen wenn nicht eingeklappt */}
      {!isPanelCollapsed && (
        <>
          {/* Error Message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Chunks List - Gruppiert nach Seiten */}
          <div className="space-y-6">
        {Array.from(chunksByPage.entries())
          .sort(([pageA], [pageB]) => pageA - pageB)
          .map(([pageNumber, pageChunks]) => {
            const isPageCollapsed = collapsedPages.has(pageNumber);
            
            return (
            <div key={pageNumber} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Seiten-Header - Klickbar zum Ein-/Ausklappen */}
              <button
                onClick={() => {
                  setCollapsedPages(prev => {
                    const newSet = new Set(prev);
                    if (newSet.has(pageNumber)) {
                      newSet.delete(pageNumber);
                    } else {
                      newSet.add(pageNumber);
                    }
                    return newSet;
                  });
                }}
                className="w-full bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-2 border-b border-gray-200 hover:from-blue-100 hover:to-indigo-100 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  {isPageCollapsed ? (
                    <ChevronRight className="w-4 h-4 text-blue-600" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-blue-600" />
                  )}
                  <Layers className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-900">
                    Seite {pageNumber}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({pageChunks.length} Chunk{pageChunks.length !== 1 ? 's' : ''})
                  </span>
                </div>
              </button>

              {/* Chunks dieser Seite - Nur anzeigen wenn Seite nicht eingeklappt */}
              {!isPageCollapsed && (
              <div className="divide-y divide-gray-100">
                {pageChunks.map((chunk, index) => {
                  const expansionState = chunkExpansionStates.get(chunk.id) || 'collapsed';
                  const isTruncated = chunk.chunk_text.length > 500;

                  return (
                    <div
                      key={chunk.id}
                      id={`chunk-${chunk.id}`}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      {/* Chunk Header */}
                      <div
                        className="p-4 cursor-pointer flex items-start justify-between"
                        onClick={() => toggleChunkExpansion(chunk.id)}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
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
                          <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                            {chunk.metadata.token_count && (
                              <div className="flex items-center gap-1">
                                <Hash className="w-3 h-3" />
                                <span>{chunk.metadata.token_count} Tokens</span>
                              </div>
                            )}
                            {chunk.metadata.sentence_count && (
                              <div className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                <span>{chunk.metadata.sentence_count} Sätze</span>
                              </div>
                            )}
                            {chunk.metadata.has_overlap && chunk.metadata.overlap_sentence_count > 0 && (
                              <div className="flex items-center gap-1">
                                <Scissors className="w-3 h-3 text-green-600" />
                                <span className="text-green-700 font-medium">
                                  Overlap: {chunk.metadata.overlap_sentence_count} Sätze
                                </span>
                              </div>
                            )}
                            {chunk.metadata.heading_hierarchy.length > 0 && (
                              <div className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                <span className="truncate max-w-xs">
                                  {chunk.metadata.heading_hierarchy.join(' > ')}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons (Level 4+) - Am Ende des Headers */}
                        {canEditChunks && (
                          <div className="ml-4 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => handleEdit(chunk)}
                              disabled={editingChunkId === chunk.id || actionLoading === chunk.id}
                              className="p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed group relative"
                              title="Chunk bearbeiten: Text direkt im Editor ändern"
                            >
                              <Edit className="w-4 h-4" />
                              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                Chunk bearbeiten
                              </span>
                            </button>
                            <button
                              onClick={() => handleSplit(chunk)}
                              disabled={actionLoading === chunk.id}
                              className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed group relative"
                              title="Chunk splitten: In zwei Teile aufteilen mit optionalem Overlap (0-10 Sätze)"
                            >
                              <Scissors className="w-4 h-4" />
                              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                Chunk splitten (mit Overlap)
                              </span>
                            </button>
                            <button
                              onClick={() => handleDelete(chunk.id)}
                              disabled={actionLoading === chunk.id}
                              className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed group relative"
                              title="Chunk löschen: Aus Datenbank und Vector Store entfernen"
                            >
                              {actionLoading === chunk.id ? (
                                <Spinner size="sm" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
                              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                Chunk löschen
                              </span>
                            </button>
                          </div>
                        )}

                        {/* Expansion State Indicator */}
                        <button
                          className="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleChunkExpansion(chunk.id);
                          }}
                          title={
                            expansionState === 'collapsed' 
                              ? 'Vorschau anzeigen' 
                              : expansionState === 'preview' 
                              ? 'Vollständigen Text anzeigen' 
                              : 'Zuklappen'
                          }
                        >
                          {expansionState === 'collapsed' && (
                            <ChevronRight className="w-5 h-5" />
                          )}
                          {expansionState === 'preview' && (
                            <ChevronDown className="w-5 h-5" />
                          )}
                          {expansionState === 'full' && (
                            <ChevronUp className="w-5 h-5" />
                          )}
                        </button>
                      </div>

                      {/* Chunk Content - 3-Stufen-System */}
                      {expansionState === 'preview' && (
                        <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50">
                          <div className="mt-4">
                            <div className="bg-white rounded-lg p-4 border border-gray-200">
                              <pre 
                                className="whitespace-pre-wrap text-sm text-gray-700 font-sans"
                                dangerouslySetInnerHTML={{
                                  __html: highlightText(chunk.chunk_text.substring(0, 500), highlightTerms) + '...'
                                }}
                              />
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                expandToFull(chunk.id);
                              }}
                              className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
                            >
                              <Expand className="w-4 h-4" />
                              Vollständigen Text anzeigen ({chunk.chunk_text.length} Zeichen)
                            </button>
                          </div>
                        </div>
                      )}

                      {expansionState === 'full' && (
                        <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50">
                          <div className="mt-4">
                            {/* Edit Mode */}
                            {editingChunkId === chunk.id ? (
                              <div className="space-y-3">
                                <textarea
                                  value={editText}
                                  onChange={(e) => setEditText(e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                                  rows={Math.min(20, Math.max(10, Math.ceil(editText.length / 80)))}
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
                              <div className="bg-white rounded-lg p-4 border border-gray-200">
                                <pre 
                                  className="whitespace-pre-wrap text-sm text-gray-700 font-sans"
                                  dangerouslySetInnerHTML={{
                                    __html: highlightText(chunk.chunk_text, highlightTerms)
                                  }}
                                />
                              </div>
                            )}

                            {/* Additional Metadata */}
                            <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-600 bg-white rounded-lg p-3 border border-gray-200">
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
                              <div>
                                <span className="font-medium">Zeichen:</span>{' '}
                                {chunk.chunk_text.length.toLocaleString('de-DE')}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              )}
            </div>
            );
          })}
          </div>
        </>
      )}

      {/* Split Chunk Modal */}
      <SplitChunkModal
        isOpen={splitChunkModal.isOpen}
        onClose={() => setSplitChunkModal({ isOpen: false, chunk: null })}
        chunk={splitChunkModal.chunk}
        onSplit={handleSplitConfirm}
      />
    </div>
  );
}
