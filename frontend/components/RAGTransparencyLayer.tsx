/**
 * RAG Transparency Layer
 * 
 * Zeigt alle Metadaten und Details für eine RAG Chat-Antwort.
 * PHASE 3.2: Vollständige Transparenz für Auditierbarkeit.
 */

"use client";

import { useState } from 'react';
import { ChevronDown, ChevronUp, Info, Zap, Database, Search, Clock, Hash, Sparkles } from 'lucide-react';
import { SourceReference } from '@/lib/api/rag';

interface RAGTransparencyLayerProps {
  messageId: number;
  sourceReferences: SourceReference[];
  modelUsed?: string;
  processingTimeMs?: number;
  tokensUsed?: number;
  queryParams?: {
    top_k?: number;
    score_threshold?: number;
    use_hybrid_search?: boolean;
    use_multi_query?: boolean;
  };
  embeddingProvider?: string;  // openai/gemini/local
  embeddingDimensions?: number;
}

export default function RAGTransparencyLayer({
  messageId,
  sourceReferences,
  modelUsed,
  processingTimeMs,
  tokensUsed,
  queryParams,
  embeddingProvider,
  embeddingDimensions
}: RAGTransparencyLayerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getProviderIcon = (provider?: string) => {
    switch (provider) {
      case 'openai':
        return <Sparkles className="w-4 h-4 text-purple-600" />;
      case 'gemini':
        return <Zap className="w-4 h-4 text-blue-600" />;
      case 'local':
        return <Database className="w-4 h-4 text-green-600" />;
      default:
        return <Info className="w-4 h-4 text-gray-600" />;
    }
  };

  const getProviderName = (provider?: string) => {
    switch (provider) {
      case 'openai':
        return 'OpenAI (1536 dim)';
      case 'gemini':
        return 'Gemini (768 dim)';
      case 'local':
        return 'Local (384 dim)';
      default:
        return 'Unbekannt';
    }
  };

  return (
    <div className="mt-3 border border-gray-200 rounded-lg bg-gray-50">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">
            Transparenz & Metadaten
          </span>
          <span className="text-xs text-gray-500">
            ({sourceReferences.length} Quellen)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-600" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 space-y-4 border-t border-gray-200">
          {/* Performance Metrics */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              Performance
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {processingTimeMs !== undefined && (
                <div className="bg-white rounded p-2 border border-gray-200">
                  <span className="text-gray-600">Verarbeitungszeit:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {processingTimeMs} ms
                  </span>
                </div>
              )}
              {tokensUsed !== undefined && (
                <div className="bg-white rounded p-2 border border-gray-200">
                  <span className="text-gray-600">Tokens:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {tokensUsed.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Query Parameters */}
          {queryParams && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Search className="w-4 h-4 text-green-600" />
                Query-Parameter
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {queryParams.top_k !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <span className="text-gray-600">Top K:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {queryParams.top_k}
                    </span>
                  </div>
                )}
                {queryParams.score_threshold !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <span className="text-gray-600">Score Threshold:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {(queryParams.score_threshold * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {queryParams.use_hybrid_search !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <span className="text-gray-600">Hybrid Search:</span>
                    <span className={`ml-2 font-medium ${
                      queryParams.use_hybrid_search ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {queryParams.use_hybrid_search ? 'Aktiviert' : 'Deaktiviert'}
                    </span>
                  </div>
                )}
                {queryParams.use_multi_query !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <span className="text-gray-600">Multi-Query:</span>
                    <span className={`ml-2 font-medium ${
                      queryParams.use_multi_query ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {queryParams.use_multi_query ? 'Aktiviert' : 'Deaktiviert'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Embedding Info */}
          {(embeddingProvider || embeddingDimensions) && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                {getProviderIcon(embeddingProvider)}
                Embedding-Provider
              </h4>
              <div className="bg-white rounded p-2 border border-gray-200 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Provider:</span>
                  <span className="font-medium text-gray-900">
                    {getProviderName(embeddingProvider)}
                  </span>
                </div>
                {embeddingDimensions && (
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-gray-600">Dimensionen:</span>
                    <span className="font-medium text-gray-900">
                      {embeddingDimensions}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Model */}
          {modelUsed && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-purple-600" />
                AI-Modell
              </h4>
              <div className="bg-white rounded p-2 border border-gray-200 text-xs">
                <span className="font-medium text-gray-900">{modelUsed}</span>
              </div>
            </div>
          )}

          {/* Source References Summary */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              Verwendete Quellen ({sourceReferences.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {sourceReferences.map((ref, index) => (
                <div
                  key={index}
                  className="bg-white rounded p-2 border border-gray-200 text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 truncate">
                      {ref.document_title}
                    </span>
                    <span className="text-gray-600 ml-2">
                      {Math.round(ref.relevance_score * 100)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <span>Seite {ref.page_number}</span>
                    <span>•</span>
                    <span>Chunk {ref.chunk_id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

