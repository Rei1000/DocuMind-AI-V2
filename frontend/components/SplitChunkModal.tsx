/**
 * Split Chunk Modal
 * 
 * Modal zum Splitten eines Chunks nach Sätzen mit Overlap-Option.
 */

"use client";

import { useState, useEffect } from 'react';
import { X, Scissors, AlertCircle } from 'lucide-react';
import { ChunkPreview } from '@/lib/api/rag';

interface SplitChunkModalProps {
  isOpen: boolean;
  onClose: () => void;
  chunk: ChunkPreview | null;
  onSplit: (splitAfterSentence: number, overlapSentences: number) => Promise<void>;
}

export default function SplitChunkModal({
  isOpen,
  onClose,
  chunk,
  onSplit
}: SplitChunkModalProps) {
  const [splitAfterSentence, setSplitAfterSentence] = useState<number>(0);
  const [overlapSentences, setOverlapSentences] = useState<number>(0);
  const [sentences, setSentences] = useState<string[]>([]);
  const [isSplitting, setIsSplitting] = useState(false);

  // Teile Text in Sätze auf
  useEffect(() => {
    if (chunk?.chunk_text) {
      // Einfache Satz-Trennung (verbessert: berücksichtigt Abkürzungen)
      const splitSentences = chunk.chunk_text.split(/(?<=[.!?])\s+/).filter(s => s.trim());
      setSentences(splitSentences);
      // Setze Standard-Split-Position auf die Hälfte
      setSplitAfterSentence(Math.floor(splitSentences.length / 2));
    }
  }, [chunk]);

  const handleSplit = async () => {
    if (!chunk || splitAfterSentence < 1 || splitAfterSentence >= sentences.length) {
      return;
    }

    setIsSplitting(true);
    try {
      // Berechne Split-Position in Zeichen
      const textBeforeSplit = sentences.slice(0, splitAfterSentence).join(' ');
      const splitPosition = textBeforeSplit.length;
      
      await onSplit(splitPosition, overlapSentences);
      onClose();
    } catch (error) {
      console.error('Failed to split chunk:', error);
    } finally {
      setIsSplitting(false);
    }
  };

  if (!isOpen || !chunk) return null;

  const maxOverlap = Math.min(splitAfterSentence, sentences.length - splitAfterSentence, 10);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Scissors className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-900">Chunk splitten</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-6">
            <p className="text-sm text-gray-600 mb-4">
              Wählen Sie, nach welchem Satz der Chunk gesplittet werden soll. 
              Der zweite Chunk beginnt dann mit den letzten N Sätzen des ersten Chunks (Overlap).
            </p>
            
            {/* Split-Position */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Split nach Satz: {splitAfterSentence} von {sentences.length}
              </label>
              <input
                type="range"
                min="1"
                max={sentences.length - 1}
                value={splitAfterSentence}
                onChange={(e) => setSplitAfterSentence(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Satz 1</span>
                <span>Satz {sentences.length - 1}</span>
              </div>
            </div>

            {/* Overlap */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Overlap-Sätze: {overlapSentences} (max: {maxOverlap})
              </label>
              <input
                type="range"
                min="0"
                max={maxOverlap}
                value={overlapSentences}
                onChange={(e) => setOverlapSentences(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-xs text-gray-500 mt-1">
                Der zweite Chunk beginnt mit den letzten {overlapSentences} Sätzen des ersten Chunks.
              </p>
            </div>

            {/* Preview */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Vorschau:</h3>
              
              {/* Erster Chunk */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                    Chunk 1 ({sentences.slice(0, splitAfterSentence).length} Sätze)
                  </span>
                  {overlapSentences > 0 && (
                    <span className="text-xs text-gray-500">
                      (endet nach Satz {splitAfterSentence})
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-700 bg-white p-3 rounded border max-h-40 overflow-y-auto">
                  {sentences.slice(0, splitAfterSentence).map((sentence, idx) => (
                    <span key={idx} className={idx >= splitAfterSentence - overlapSentences && overlapSentences > 0 ? 'text-green-600 font-medium' : ''}>
                      {sentence}{' '}
                    </span>
                  ))}
                </div>
              </div>

              {/* Zweiter Chunk */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                    Chunk 2 ({sentences.slice(splitAfterSentence - overlapSentences).length} Sätze)
                  </span>
                  {overlapSentences > 0 && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                      Overlap: {overlapSentences} Sätze
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-700 bg-white p-3 rounded border max-h-40 overflow-y-auto">
                  {overlapSentences > 0 && (
                    <span className="text-green-600 font-medium">
                      {sentences.slice(splitAfterSentence - overlapSentences, splitAfterSentence).join(' ')}{' '}
                    </span>
                  )}
                  {sentences.slice(splitAfterSentence).map((sentence, idx) => (
                    <span key={idx}>{sentence}{' '}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Abbrechen
          </button>
          <button
            onClick={handleSplit}
            disabled={isSplitting || splitAfterSentence < 1 || splitAfterSentence >= sentences.length}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSplitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Splitte...
              </>
            ) : (
              <>
                <Scissors className="w-4 h-4" />
                Chunk splitten
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

