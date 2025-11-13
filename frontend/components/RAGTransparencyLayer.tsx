/**
 * RAG Transparency Layer
 * 
 * Zeigt alle Metadaten und Details für eine RAG Chat-Antwort.
 * PHASE 3.2: Vollständige Transparenz für Auditierbarkeit.
 */

"use client";

import { useState } from 'react';
import { ChevronDown, ChevronUp, Info, Zap, Database, Search, Clock, Hash, Sparkles, HelpCircle } from 'lucide-react';
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
              Performance-Metriken
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {processingTimeMs !== undefined && (
                <div className="bg-white rounded p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-gray-600">Verarbeitungszeit:</span>
                    <div className="group relative">
                      <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        <strong>Aktueller Wert:</strong> {processingTimeMs} ms ({(processingTimeMs / 1000).toFixed(2)} Sekunden)
                        <br/><br/>
                        <strong>Was wird gemessen?</strong> Gesamte Zeit für die vollständige Verarbeitung Ihrer Frage:
                        <br/><br/>
                        • <strong>Embedding-Suche:</strong> Vektor-Suche in Qdrant (ca. {Math.round(processingTimeMs * 0.1)}-{Math.round(processingTimeMs * 0.2)} ms)
                        <br/><br/>
                        • <strong>AI-Generierung:</strong> Antwort-Generierung durch {modelUsed || 'AI-Modell'} (ca. {Math.round(processingTimeMs * 0.7)}-{Math.round(processingTimeMs * 0.8)} ms)
                        <br/><br/>
                        • <strong>Datenverarbeitung:</strong> Chunk-Filterung, Kontext-Aufbereitung (ca. {Math.round(processingTimeMs * 0.05)}-{Math.round(processingTimeMs * 0.1)} ms)
                        <br/><br/>
                        <strong>Typische Werte:</strong> {processingTimeMs < 2000 ? 'Schnell' : processingTimeMs < 5000 ? 'Normal' : 'Langsam'} ({processingTimeMs < 2000 ? '< 2s' : processingTimeMs < 5000 ? '2-5s' : '> 5s'})
                      </div>
                    </div>
                  </div>
                  <span className="font-medium text-gray-900">
                    {processingTimeMs} ms
                  </span>
                </div>
              )}
              {tokensUsed !== undefined && (
                <div className="bg-white rounded p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-gray-600">Tokens verwendet:</span>
                    <div className="group relative">
                      <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        <strong>Aktueller Wert:</strong> {tokensUsed.toLocaleString()} Tokens
                        <br/><br/>
                        <strong>Was bedeutet das?</strong> Anzahl der verwendeten AI-Tokens für diese Antwort:
                        <br/><br/>
                        • <strong>Input-Tokens:</strong> Ihre Frage + Kontext aus {queryParams?.top_k || 'X'} Chunks (ca. {Math.round(tokensUsed * 0.7)}-{Math.round(tokensUsed * 0.8)} Tokens)
                        <br/><br/>
                        • <strong>Output-Tokens:</strong> Generierte Antwort (ca. {Math.round(tokensUsed * 0.2)}-{Math.round(tokensUsed * 0.3)} Tokens)
                        <br/><br/>
                        <strong>Kosten-Einfluss:</strong> {tokensUsed < 1000 ? 'Niedrig' : tokensUsed < 5000 ? 'Mittel' : 'Hoch'} ({tokensUsed < 1000 ? '< $0.01' : tokensUsed < 5000 ? '$0.01-0.05' : '> $0.05'} bei GPT-4o Mini)
                        <br/><br/>
                        <strong>Typische Werte:</strong> {tokensUsed < 2000 ? 'Kompakt' : tokensUsed < 5000 ? 'Normal' : 'Umfangreich'} ({tokensUsed < 2000 ? '500-2000' : tokensUsed < 5000 ? '2000-5000' : '> 5000'} Tokens)
                      </div>
                    </div>
                  </div>
                  <span className="font-medium text-gray-900">
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
                Such-Parameter
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {queryParams.top_k !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Top K:</span>
                      <div className="group relative">
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <strong>Anzahl der besten Chunks:</strong> {queryParams.top_k}
                          <br/><br/>
                          <strong>Was bedeutet das?</strong> Die {queryParams.top_k} besten Dokumenten-Abschnitte (basierend auf Relevanz-Score) wurden für die Generierung dieser Antwort verwendet.
                          <br/><br/>
                          <strong>Beispiel:</strong> Bei Top K = {queryParams.top_k} werden die {queryParams.top_k} ähnlichsten Chunks aus allen Dokumenten ausgewählt und als Kontext an das AI-Modell übergeben.
                          <br/><br/>
                          <strong>Einfluss:</strong> Mehr Chunks ({queryParams.top_k < 10 ? 'z.B. 10-20' : 'weniger'}) = mehr Kontext, aber auch mehr "Rauschen". Weniger Chunks ({queryParams.top_k > 3 ? 'z.B. 3-5' : 'mehr'}) = fokussierter, aber möglicherweise wichtige Informationen verpasst.
                        </div>
                      </div>
                    </div>
                    <span className="font-medium text-gray-900">
                      {queryParams.top_k}
                    </span>
                  </div>
                )}
                {queryParams.score_threshold !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Relevanz-Schwelle:</span>
                      <div className="group relative">
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <strong>Aktueller Wert:</strong> {(queryParams.score_threshold * 100).toFixed(1)}% ({queryParams.score_threshold.toFixed(3)})
                          <br/><br/>
                          <strong>Was bedeutet das?</strong> Mindest-Relevanz-Score (Vector-Similarity) für Dokumenten-Abschnitte. Nur Chunks mit einem Score ≥ {(queryParams.score_threshold * 100).toFixed(1)}% werden für die Antwort verwendet.
                          <br/><br/>
                          <strong>Berechnung:</strong> Der Score misst die semantische Ähnlichkeit zwischen Ihrer Frage und jedem Dokumenten-Abschnitt (0% = keine Ähnlichkeit, 100% = identisch).
                          <br/><br/>
                          <strong>Einfluss:</strong> Niedrige Schwelle ({queryParams.score_threshold < 0.01 ? 'wie aktuell' : 'z.B. 0.5%'}) = mehr Chunks, aber möglicherweise weniger relevante. Hohe Schwelle ({queryParams.score_threshold > 0.015 ? 'wie aktuell' : 'z.B. 2-3%'}) = weniger Chunks, aber nur sehr relevante.
                          <br/><br/>
                          <strong>Typische Werte:</strong> OpenAI Embeddings: 0.01-0.02 (1-2%), Gemini: 0.02-0.03 (2-3%)
                        </div>
                      </div>
                    </div>
                    <span className="font-medium text-gray-900">
                      {(queryParams.score_threshold * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {queryParams.use_hybrid_search !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Hybrid-Suche:</span>
                      <div className="group relative">
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <strong>Status:</strong> {queryParams.use_hybrid_search ? 'Aktiviert' : 'Deaktiviert'}
                          <br/><br/>
                          <strong>Was bedeutet das?</strong> {queryParams.use_hybrid_search ? (
                            <>
                              Kombiniert zwei Suchmethoden für optimale Ergebnisse:
                              <br/><br/>
                              • <strong>Vektor-Suche (70%):</strong> Semantische Suche nach Bedeutung - findet ähnliche Inhalte auch bei anderen Formulierungen
                              <br/><br/>
                              • <strong>Text-Suche (30%):</strong> Keyword-Übereinstimmungen - findet exakte Begriffe und Phrasen
                              <br/><br/>
                              <strong>Formel:</strong> Finaler Score = (Vector-Score × 0.7) + (Text-Score × 0.3)
                              <br/><br/>
                              <strong>Vorteil:</strong> Findet sowohl inhaltlich ähnliche als auch exakt passende Chunks. Besser für präzise Fragen mit Fachbegriffen.
                            </>
                          ) : (
                            <>
                              Nur reine Vektor-Suche (semantische Suche nach Bedeutung).
                              <br/><br/>
                              • Findet Chunks basierend auf Ähnlichkeit der Bedeutung
                              <br/><br/>
                              • Ignoriert exakte Wort-Übereinstimmungen
                              <br/><br/>
                              • Filtert direkt nach Vector-Score ≥ Relevanz-Schwelle
                              <br/><br/>
                              <strong>Vorteil:</strong> Schneller, findet ähnliche Inhalte auch bei anderen Formulierungen.
                              <br/><br/>
                              <strong>Nachteil:</strong> Verpasst möglicherweise Chunks mit exakten Wort-Übereinstimmungen.
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className={`font-medium ${
                      queryParams.use_hybrid_search ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {queryParams.use_hybrid_search ? 'Aktiviert' : 'Deaktiviert'}
                    </span>
                  </div>
                )}
                {queryParams.use_multi_query !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Multi-Query:</span>
                      <div className="group relative">
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <strong>Status:</strong> {queryParams.use_multi_query ? 'Aktiviert' : 'Deaktiviert'}
                          <br/><br/>
                          <strong>Was bedeutet das?</strong> {queryParams.use_multi_query ? (
                            <>
                              Ihre Frage wurde automatisch in 3-5 Varianten erweitert, um umfassendere Suchergebnisse zu erhalten.
                              <br/><br/>
                              <strong>Beispiel:</strong> "Loctite 648" → ["Loctite 648 Klebstoff", "Loctite 648 Beständigkeit", "Loctite 648 Anwendung", "Loctite 648 Eigenschaften"]
                              <br/><br/>
                              <strong>Vorteil:</strong> Findet relevante Chunks auch wenn die Formulierung leicht abweicht. Besser für komplexe Fragen.
                              <br/><br/>
                              <strong>Nachteil:</strong> Längere Verarbeitungszeit (mehr Suchvorgänge).
                            </>
                          ) : (
                            <>
                              Nur Ihre Original-Frage wurde für die Suche verwendet.
                              <br/><br/>
                              <strong>Beispiel:</strong> "Loctite 648" → Suche nur nach exakt dieser Formulierung
                              <br/><br/>
                              <strong>Vorteil:</strong> Schneller, fokussierter.
                              <br/><br/>
                              <strong>Nachteil:</strong> Verpasst möglicherweise relevante Chunks mit ähnlicher, aber anderer Formulierung.
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className={`font-medium ${
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
                <div className="group relative">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    Embeddings sind numerische Darstellungen von Text, die semantische Ähnlichkeit messen. Der Provider bestimmt die Qualität und Dimensionen der Embeddings.
                  </div>
                </div>
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
                <div className="group relative">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-56 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    Das verwendete KI-Modell zur Generierung der Antwort. Verschiedene Modelle haben unterschiedliche Stärken und Kosten.
                  </div>
                </div>
              </h4>
              <div className="bg-white rounded p-2 border border-gray-200 text-xs">
                <span className="font-medium text-gray-900">{modelUsed}</span>
              </div>
            </div>
          )}

          {/* Source References Summary */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              Verwendete Quellen ({sourceReferences.length})
              <div className="group relative">
                <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  Diese Dokumenten-Abschnitte wurden für die Generierung der Antwort verwendet. Die Relevanz-Scores zeigen, wie gut jeder Abschnitt zur Frage passt (höher = relevanter).
                </div>
              </div>
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {sourceReferences.map((ref, index) => {
                const hasExtendedMetadata = ref.vector_score !== undefined || ref.text_score !== undefined
                
                return (
                  <div
                    key={index}
                    className="bg-white rounded p-2 border border-gray-200 text-xs hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 truncate">
                        {ref.document_title}
                      </span>
                      <div className="group relative flex items-center gap-1">
                        <span className={`font-semibold ml-2 ${
                          ref.relevance_score >= 0.5 ? 'text-green-600' :
                          ref.relevance_score >= 0.3 ? 'text-yellow-600' :
                          'text-gray-600'
                        }`}>
                          {Math.round(ref.relevance_score * 100)}%
                        </span>
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        <div className="absolute bottom-full right-0 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <strong>Relevanz-Score:</strong> {Math.round(ref.relevance_score * 100)}%<br/>
                          <span className="text-gray-300">
                            {ref.relevance_score >= 0.5 ? 'Sehr relevant' :
                             ref.relevance_score >= 0.3 ? 'Mäßig relevant' :
                             'Wenig relevant'}
                          </span>
                          {/* NEU: Erweiterte Score-Aufschlüsselung im Tooltip */}
                          {hasExtendedMetadata && (
                            <>
                              <br/><br/>
                              <strong>Score-Aufschlüsselung:</strong><br/>
                              {ref.vector_score !== undefined && (
                                <>Vector-Score: {Math.round(ref.vector_score * 100)}%<br/></>
                              )}
                              {ref.text_score !== undefined && (
                                <>Text-Score: {Math.round(ref.text_score * 100)}%<br/></>
                              )}
                              {ref.hybrid_score !== undefined && (
                                <>Hybrid-Score: {Math.round(ref.hybrid_score * 100)}%<br/></>
                              )}
                            </>
                          )}
                          <br/><br/>
                          <strong>Berechnung:</strong> Ähnlichkeit zwischen Ihrer Frage und diesem Dokumenten-Abschnitt (0-100%). Höhere Werte = bessere Übereinstimmung.
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-gray-500 mb-1">
                      <span>Seite {ref.page_number}</span>
                      <span>•</span>
                      <span>Chunk {ref.chunk_id}</span>
                      {/* NEU: Ranking-Informationen */}
                      {ref.rank_position !== undefined && ref.total_candidates !== undefined && (
                        <>
                          <span>•</span>
                          <span className="text-purple-600 font-medium">
                            Rang {ref.rank_position} von {ref.total_candidates}
                          </span>
                        </>
                      )}
                    </div>
                    
                    {/* NEU: Score-Aufschlüsselung */}
                    {hasExtendedMetadata && (
                      <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-4 text-xs">
                        {ref.vector_score !== undefined && (
                          <div className="flex items-center gap-1">
                            <span className="text-gray-600">Vector-Score:</span>
                            <span className="font-semibold text-blue-600">
                              {Math.round(ref.vector_score * 100)}%
                            </span>
                          </div>
                        )}
                        {ref.text_score !== undefined && (
                          <div className="flex items-center gap-1">
                            <span className="text-gray-600">Text-Score:</span>
                            <span className="font-semibold text-green-600">
                              {Math.round(ref.text_score * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* NEU: Chunk-Metadaten */}
                    {ref.chunk_metadata && (
                      <div className="mt-2 pt-2 border-t border-gray-200 text-xs">
                        {ref.chunk_metadata.heading_hierarchy && ref.chunk_metadata.heading_hierarchy.length > 0 && (
                          <div className="mb-1">
                            <span className="text-gray-600 font-medium">Heading-Hierarchy:</span>
                            <div className="text-gray-800 mt-0.5">
                              {ref.chunk_metadata.heading_hierarchy.map((heading, i) => (
                                <span key={i} className="mr-2">{heading}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        {ref.chunk_metadata.confidence_score !== undefined && (
                          <div className="mb-1">
                            <span className="text-gray-600 font-medium">Confidence-Score:</span>
                            <span className="ml-1 font-semibold text-green-600">
                              {Math.round(ref.chunk_metadata.confidence_score * 100)}%
                            </span>
                          </div>
                        )}
                        {ref.chunk_metadata.chunk_type && (
                          <div className="mb-1">
                            <span className="text-gray-600 font-medium">Chunk-Type:</span>
                            <span className="ml-1 text-gray-800">{ref.chunk_metadata.chunk_type}</span>
                          </div>
                        )}
                        {ref.chunk_metadata.token_count !== undefined && (
                          <div>
                            <span className="text-gray-600 font-medium">Token-Count:</span>
                            <span className="ml-1 text-gray-800">{ref.chunk_metadata.token_count}</span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* NEU: Filter-Status */}
                    {(ref.passed_rbac_filter !== undefined || ref.passed_score_threshold !== undefined) && (
                      <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-3 text-xs">
                        {ref.passed_rbac_filter !== undefined && (
                          <div className="flex items-center gap-1">
                            <span className="text-gray-600">RBAC-Filter:</span>
                            <span className={`font-semibold ${ref.passed_rbac_filter ? 'text-green-600' : 'text-red-600'}`}>
                              {ref.passed_rbac_filter ? 'Bestanden' : 'Nicht bestanden'}
                            </span>
                          </div>
                        )}
                        {ref.passed_score_threshold !== undefined && (
                          <div className="flex items-center gap-1">
                            <span className="text-gray-600">Score-Threshold:</span>
                            <span className={`font-semibold ${ref.passed_score_threshold ? 'text-green-600' : 'text-red-600'}`}>
                              {ref.passed_score_threshold ? 'Bestanden' : 'Nicht bestanden'}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

