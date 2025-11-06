/**
 * Chunking Strategy Wizard
 * 
 * Frontend-Wizard zur Auswahl der Chunking-Strategie vor der Indexierung.
 * PHASE 2.3: Transparente Strategie-Auswahl mit dreistufiger Embedding-Strategie.
 */

"use client";

import { useState, useEffect } from 'react';
import { X, Check, Sparkles, Zap, Cpu, Info, AlertCircle } from 'lucide-react';
import { getChunkingStrategies, ChunkingStrategyOption, ChunkingStrategiesResponse } from '@/lib/api/rag';
import Spinner from './ui/Spinner';

interface ChunkingStrategyWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (strategyId: string) => void;
  documentType?: string;
  documentTypeName?: string;
}

export default function ChunkingStrategyWizard({
  isOpen,
  onClose,
  onSelect,
  documentType,
  documentTypeName
}: ChunkingStrategyWizardProps) {
  const [strategies, setStrategies] = useState<ChunkingStrategyOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [defaultStrategy, setDefaultStrategy] = useState<string | null>(null);
  const [suggestedStrategy, setSuggestedStrategy] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadStrategies();
    }
  }, [isOpen, documentType]);

  const loadStrategies = async () => {
    setLoading(true);
    setError(null);

    try {
      const response: ChunkingStrategiesResponse = await getChunkingStrategies(documentType);
      setStrategies(response.strategies);
      setDefaultStrategy(response.default_strategy);
      setSuggestedStrategy(response.document_type_suggestion);
      
      // Setze initiale Auswahl: Empfehlung > Standard
      const initialSelection = response.document_type_suggestion || response.default_strategy;
      setSelectedStrategy(initialSelection);
    } catch (err: any) {
      console.error('Failed to load chunking strategies:', err);
      setError(err.message || 'Fehler beim Laden der Strategien');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (selectedStrategy) {
      onSelect(selectedStrategy);
      onClose();
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai':
        return <Sparkles className="w-5 h-5 text-purple-600" />;
      case 'gemini':
        return <Zap className="w-5 h-5 text-blue-600" />;
      case 'local':
        return <Cpu className="w-5 h-5 text-green-600" />;
      default:
        return <Info className="w-5 h-5 text-gray-600" />;
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'openai':
        return 'border-purple-300 bg-purple-50 hover:bg-purple-100';
      case 'gemini':
        return 'border-blue-300 bg-blue-50 hover:bg-blue-100';
      case 'local':
        return 'border-green-300 bg-green-50 hover:bg-green-100';
      default:
        return 'border-gray-300 bg-gray-50 hover:bg-gray-100';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Chunking-Strategie auswählen</h2>
            <p className="text-sm text-gray-500 mt-1">
              Wähle die optimale Strategie für die Dokument-Indexierung
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="md" />
              <span className="ml-3 text-gray-600">Lade Strategien...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          ) : (
            <>
              {/* Info Box */}
              {documentTypeName && suggestedStrategy && (
                <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-blue-900">
                        Empfehlung für "{documentTypeName}"
                      </p>
                      <p className="text-sm text-blue-700 mt-1">
                        Basierend auf dem Dokumenttyp wird eine optimale Strategie empfohlen.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Strategy Cards */}
              <div className="space-y-4">
                {strategies.map((strategy) => {
                  const isSelected = selectedStrategy === strategy.id;
                  const isSuggested = suggestedStrategy === strategy.id;
                  const isDefault = defaultStrategy === strategy.id;

                  return (
                    <div
                      key={strategy.id}
                      onClick={() => setSelectedStrategy(strategy.id)}
                      className={`border-2 rounded-lg p-5 cursor-pointer transition-all ${
                        isSelected
                          ? `${getProviderColor(strategy.embedding_provider)} border-opacity-100 ring-2 ring-offset-2 ring-blue-500`
                          : `${getProviderColor(strategy.embedding_provider)} border-opacity-50`
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            {getProviderIcon(strategy.embedding_provider)}
                            <h3 className="text-lg font-semibold text-gray-900">
                              {strategy.name}
                            </h3>
                            {isDefault && (
                              <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-700">
                                Standard
                              </span>
                            )}
                            {isSuggested && (
                              <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-200 text-blue-700">
                                Empfohlen
                              </span>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3">
                            {strategy.description}
                          </p>

                          {/* Details */}
                          <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
                            <div>
                              <span className="font-medium">Provider:</span>{' '}
                              {strategy.embedding_provider.toUpperCase()}
                            </div>
                            <div>
                              <span className="font-medium">Dimensionen:</span>{' '}
                              {strategy.embedding_dimensions}
                            </div>
                            {strategy.recommended_for.length > 0 && (
                              <div className="col-span-2">
                                <span className="font-medium">Empfohlen für:</span>{' '}
                                {strategy.recommended_for.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Radio Button */}
                        <div className="ml-4">
                          <div
                            className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                              isSelected
                                ? 'border-blue-600 bg-blue-600'
                                : 'border-gray-300'
                            }`}
                          >
                            {isSelected && (
                              <Check className="w-4 h-4 text-white" />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Info: Dreistufige Strategie */}
              <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  💡 Dreistufige Embedding-Strategie
                </h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• <strong>OpenAI (1536 dim):</strong> Beste Qualität für komplexe Dokumente</li>
                  <li>• <strong>Gemini (768 dim):</strong> Gute Qualität, kostenlos und schnell</li>
                  <li>• <strong>Local (384 dim):</strong> Lokal, offline verfügbar, keine API-Kosten</li>
                </ul>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            Abbrechen
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedStrategy || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Strategie auswählen
          </button>
        </div>
      </div>
    </div>
  );
}

