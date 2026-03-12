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
import { highlightQueryWords } from '@/lib/utils/textHighlighting';  // NEU: Text-Highlighting (Phase 3)

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
    use_ml_reranking?: boolean;  // NEU: ML Re-Ranking (Phase 4, deprecated)
    use_ml_ranking?: boolean;  // NEU: Learning-to-Rank ML-Ranking (v2.7.0)
    adaptive_min_avg_score?: number;  // NEU: Adaptive Filterung - Mindest-Durchschnitts-Score
    adaptive_min_max_score?: number;  // NEU: Adaptive Filterung - Mindest-Maximal-Score
    temperature?: number;  // NEU v2.10.3: AI Temperature
    max_tokens?: number;  // NEU v2.10.3: Max Tokens
    top_p?: number;  // NEU v2.10.3: Top P
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

  const answerModelLower = (modelUsed || '').toLowerCase();
  const embeddingProviderLower = (embeddingProvider || '').toLowerCase();
  const answerUsesGemini = answerModelLower.includes('gemini');
  const answerUsesOpenAI = answerModelLower.includes('gpt') || answerModelLower.includes('openai');
  const isPotentialModelMismatch =
    (answerUsesGemini && embeddingProviderLower === 'openai') ||
    (answerUsesOpenAI && embeddingProviderLower === 'gemini');

  // NEU: Tooltip-Komponente für bessere Darstellung
  const InfoTooltip = ({ content, children }: { content: React.ReactNode; children: React.ReactNode }) => {
    return (
      <div className="group relative inline-flex items-center">
        {children}
        <div className="absolute bottom-full left-0 mb-2 w-80 max-w-[calc(100vw-2rem)] p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
          <div className="space-y-1.5">
            {content}
          </div>
          {/* Tooltip-Pfeil */}
          <div className="absolute top-full left-4 -mt-1">
            <div className="w-2 h-2 bg-gray-900 transform rotate-45"></div>
          </div>
        </div>
      </div>
    );
  };

  // NEU: Verbesserte Tooltip-Komponente für bestehende Tooltips (mit besserer Formatierung)
  const ImprovedTooltip = ({ content }: { content: React.ReactNode }) => {
    return (
      <div className="group relative inline-flex items-center">
        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
        <div className="absolute bottom-full left-0 mb-2 w-80 max-w-[calc(100vw-2rem)] p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
          <div className="space-y-1.5">
            {content}
          </div>
          {/* Tooltip-Pfeil */}
          <div className="absolute top-full left-4 -mt-1">
            <div className="w-2 h-2 bg-gray-900 transform rotate-45"></div>
          </div>
        </div>
      </div>
    );
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
          {/* Modell-Hinweis fuer Auditierbarkeit */}
          {(modelUsed || embeddingProvider || embeddingDimensions !== undefined) && (
            <div
              className={`rounded-lg border p-3 text-xs ${
                isPotentialModelMismatch
                  ? 'border-yellow-200 bg-yellow-50 text-yellow-900'
                  : 'border-blue-200 bg-blue-50 text-blue-900'
              }`}
            >
              <div className="font-semibold">
                {isPotentialModelMismatch
                  ? 'Warnung: Antwort- und Embedding-Modell sind unterschiedlich'
                  : 'Hinweis: Antwort- und Embedding-Modell'}
              </div>
              <div className="mt-1">
                Antwortmodell: <span className="font-medium">{modelUsed || 'Unbekannt'}</span>
                {' '}| Embedding: <span className="font-medium">{getProviderName(embeddingProvider)}</span>
                {embeddingDimensions !== undefined ? ` (${embeddingDimensions} dim)` : ''}
              </div>
              <div className="mt-1">
                Wenn ein Dokumenttyp mit verschiedenen Embedding-Modellen indexiert wurde, kann die Trefferqualitaet schwanken.
                Empfehlung: Dokumenttyp auf ein einheitliches Embedding-Modell re-indexieren.
              </div>
            </div>
          )}

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
                    <ImprovedTooltip
                      content={
                        <>
                          <div className="font-semibold mb-1">Aktueller Wert: {processingTimeMs} ms ({(processingTimeMs / 1000).toFixed(2)} Sekunden)</div>
                          <div className="text-gray-300 space-y-1">
                            <div>Gesamte Zeit für die vollständige Verarbeitung Ihrer Frage:</div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Komponenten:</div>
                              <ul className="list-disc list-inside space-y-0.5 ml-1">
                                <li><strong>Embedding-Suche:</strong> Vektor-Suche in Qdrant (ca. {Math.round(processingTimeMs * 0.1)}-{Math.round(processingTimeMs * 0.2)} ms)</li>
                                <li><strong>AI-Generierung:</strong> Antwort-Generierung durch {modelUsed || 'AI-Modell'} (ca. {Math.round(processingTimeMs * 0.7)}-{Math.round(processingTimeMs * 0.8)} ms)</li>
                                <li><strong>Datenverarbeitung:</strong> Chunk-Filterung, Kontext-Aufbereitung (ca. {Math.round(processingTimeMs * 0.05)}-{Math.round(processingTimeMs * 0.1)} ms)</li>
                              </ul>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Typische Werte:</div>
                              <div>{processingTimeMs < 2000 ? 'Schnell' : processingTimeMs < 5000 ? 'Normal' : 'Langsam'} ({processingTimeMs < 2000 ? '< 2s' : processingTimeMs < 5000 ? '2-5s' : '> 5s'})</div>
                            </div>
                          </div>
                        </>
                      }
                    />
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
                    <ImprovedTooltip
                      content={
                        <>
                          <div className="font-semibold mb-1">Aktueller Wert: {tokensUsed.toLocaleString()} Tokens</div>
                          <div className="text-gray-300 space-y-1">
                            <div>Anzahl der verwendeten AI-Tokens für diese Antwort:</div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Aufschlüsselung:</div>
                              <ul className="list-disc list-inside space-y-0.5 ml-1">
                                <li><strong>Input-Tokens:</strong> Ihre Frage + Kontext aus {queryParams?.top_k || 'X'} Chunks (ca. {Math.round(tokensUsed * 0.7)}-{Math.round(tokensUsed * 0.8)} Tokens)</li>
                                <li><strong>Output-Tokens:</strong> Generierte Antwort (ca. {Math.round(tokensUsed * 0.2)}-{Math.round(tokensUsed * 0.3)} Tokens)</li>
                              </ul>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Kosten-Einfluss:</div>
                              <div>{tokensUsed < 1000 ? 'Niedrig' : tokensUsed < 5000 ? 'Mittel' : 'Hoch'} ({tokensUsed < 1000 ? '< $0.01' : tokensUsed < 5000 ? '$0.01-0.05' : '> $0.05'} bei GPT-4o Mini)</div>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Typische Werte:</div>
                              <div>{tokensUsed < 2000 ? 'Kompakt' : tokensUsed < 5000 ? 'Normal' : 'Umfangreich'} ({tokensUsed < 2000 ? '500-2000' : tokensUsed < 5000 ? '2000-5000' : '> 5000'} Tokens)</div>
                            </div>
                          </div>
                        </>
                      }
                    />
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
                Filter & Suche
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {queryParams.top_k !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Top K:</span>
                      <ImprovedTooltip
                        content={
                          <>
                            <div className="font-semibold mb-1">Anzahl der besten Chunks: {queryParams.top_k}</div>
                            <div className="text-gray-300 space-y-1">
                              <div>Die {queryParams.top_k} besten Dokumenten-Abschnitte (basierend auf Relevanz-Score) wurden für die Generierung dieser Antwort verwendet.</div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Beispiel:</div>
                                <div>Bei Top K = {queryParams.top_k} werden die {queryParams.top_k} ähnlichsten Chunks aus allen Dokumenten ausgewählt und als Kontext an das AI-Modell übergeben.</div>
                              </div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Einfluss:</div>
                                <ul className="list-disc list-inside space-y-0.5 ml-1">
                                  <li>Mehr Chunks ({queryParams.top_k < 10 ? 'z.B. 10-20' : 'weniger'}) = mehr Kontext, aber auch mehr "Rauschen"</li>
                                  <li>Weniger Chunks ({queryParams.top_k > 3 ? 'z.B. 3-5' : 'mehr'}) = fokussierter, aber möglicherweise wichtige Informationen verpasst</li>
                                </ul>
                              </div>
                            </div>
                          </>
                        }
                      />
                    </div>
                    <span className="font-medium text-gray-900">
                      {queryParams.top_k}
                    </span>
                  </div>
                )}
                {queryParams.score_threshold !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">Initialer Score-Filter:</span>
                      <ImprovedTooltip
                        content={
                          <>
                            <div className="font-semibold mb-1">Aktueller Wert: {(queryParams.score_threshold * 100).toFixed(1)}% ({queryParams.score_threshold.toFixed(3)})</div>
                            <div className="text-gray-300 space-y-1">
                              <div>Mindest-Relevanz-Score (Vector-Similarity) für einzelne Chunks während der Suche. Nur Chunks mit einem Score ≥ {(queryParams.score_threshold * 100).toFixed(1)}% werden für die weitere Verarbeitung berücksichtigt.</div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Unterschied zu Adaptive Filterung:</div>
                                <ul className="list-disc list-inside space-y-0.5 ml-1">
                                  <li><strong>Initialer Score-Filter:</strong> Filtert einzelne Chunks während der Suche (pro Chunk)</li>
                                  <li><strong>Adaptive Filterung:</strong> Filtert alle Chunks zusammen nach der Suche (basierend auf Durchschnitts- und Maximal-Scores)</li>
                                </ul>
                              </div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Berechnung:</div>
                                <div>Der Score misst die semantische Ähnlichkeit zwischen Ihrer Frage und jedem Dokumenten-Abschnitt (0% = keine Ähnlichkeit, 100% = identisch).</div>
                              </div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Einfluss:</div>
                                <ul className="list-disc list-inside space-y-0.5 ml-1">
                                  <li>Niedrige Schwelle ({queryParams.score_threshold < 0.01 ? 'wie aktuell' : 'z.B. 0.5%'}) = mehr Chunks, aber möglicherweise weniger relevante</li>
                                  <li>Hohe Schwelle ({queryParams.score_threshold > 0.015 ? 'wie aktuell' : 'z.B. 2-3%'}) = weniger Chunks, aber nur sehr relevante</li>
                                </ul>
                              </div>
                              <div className="mt-2">
                                <div className="font-semibold text-white mb-1">Typische Werte:</div>
                                <ul className="list-disc list-inside space-y-0.5 ml-1">
                                  <li>OpenAI Embeddings: 0.01-0.02 (1-2%)</li>
                                  <li>Gemini: 0.02-0.03 (2-3%)</li>
                                </ul>
                              </div>
                            </div>
                          </>
                        }
                      />
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
                      <ImprovedTooltip
                        content={
                          <>
                            <div className="font-semibold mb-1">Status: {queryParams.use_hybrid_search ? 'Aktiviert' : 'Deaktiviert'}</div>
                            <div className="text-gray-300 space-y-1">
                              {queryParams.use_hybrid_search ? (
                                <>
                                  <div>Kombiniert zwei Suchmethoden für optimale Ergebnisse:</div>
                                  <div className="mt-2">
                                    <ul className="list-disc list-inside space-y-0.5 ml-1">
                                      <li><strong>Vektor-Suche (70%):</strong> Semantische Suche nach Bedeutung - findet ähnliche Inhalte auch bei anderen Formulierungen</li>
                                      <li><strong>Text-Suche (30%):</strong> Keyword-Übereinstimmungen - findet exakte Begriffe und Phrasen</li>
                                    </ul>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Formel:</div>
                                    <div>Finaler Score = (Vector-Score × 0.7) + (Text-Score × 0.3)</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Findet sowohl inhaltlich ähnliche als auch exakt passende Chunks. Besser für präzise Fragen mit Fachbegriffen.</div>
                                  </div>
                                </>
                              ) : (
                                <>
                                  <div>Nur reine Vektor-Suche (semantische Suche nach Bedeutung).</div>
                                  <div className="mt-2">
                                    <ul className="list-disc list-inside space-y-0.5 ml-1">
                                      <li>Findet Chunks basierend auf Ähnlichkeit der Bedeutung</li>
                                      <li>Ignoriert exakte Wort-Übereinstimmungen</li>
                                      <li>Filtert direkt nach Vector-Score ≥ Relevanz-Schwelle</li>
                                    </ul>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Schneller, findet ähnliche Inhalte auch bei anderen Formulierungen.</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Nachteil:</div>
                                    <div>Verpasst möglicherweise Chunks mit exakten Wort-Übereinstimmungen.</div>
                                  </div>
                                </>
                              )}
                            </div>
                          </>
                        }
                      />
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
                      <ImprovedTooltip
                        content={
                          <>
                            <div className="font-semibold mb-1">Status: {queryParams.use_multi_query ? 'Aktiviert' : 'Deaktiviert'}</div>
                            <div className="text-gray-300 space-y-1">
                              {queryParams.use_multi_query ? (
                                <>
                                  <div>Ihre Frage wurde automatisch in 3-5 Varianten erweitert, um umfassendere Suchergebnisse zu erhalten.</div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Beispiel:</div>
                                    <div>"Loctite 648" → ["Loctite 648 Klebstoff", "Loctite 648 Beständigkeit", "Loctite 648 Anwendung", "Loctite 648 Eigenschaften"]</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Findet relevante Chunks auch wenn die Formulierung leicht abweicht. Besser für komplexe Fragen.</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Nachteil:</div>
                                    <div>Längere Verarbeitungszeit (mehr Suchvorgänge).</div>
                                  </div>
                                </>
                              ) : (
                                <>
                                  <div>Nur Ihre Original-Frage wurde für die Suche verwendet.</div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Beispiel:</div>
                                    <div>"Loctite 648" → Suche nur nach exakt dieser Formulierung</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Schneller, fokussierter.</div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Nachteil:</div>
                                    <div>Verpasst möglicherweise relevante Chunks mit ähnlicher, aber anderer Formulierung.</div>
                                  </div>
                                </>
                              )}
                            </div>
                          </>
                        }
                      />
                    </div>
                    <span className={`font-medium ${
                      queryParams.use_multi_query ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {queryParams.use_multi_query ? 'Aktiviert' : 'Deaktiviert'}
                    </span>
                  </div>
                )}
                {queryParams.use_ml_ranking !== undefined && (
                  <div className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-gray-600">ML Ranking:</span>
                      <InfoTooltip
                        content={
                          <>
                            <div className="font-semibold mb-1">Status: {queryParams.use_ml_ranking ? 'Aktiviert' : 'Deaktiviert'}</div>
                            <div className="text-gray-300 space-y-1">
                              {queryParams.use_ml_ranking ? (
                                <>
                                  <div>Learning-to-Rank ML-Modell wird verwendet, um Chunks basierend auf komplexen Features zu bewerten.</div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Features:</div>
                                    <ul className="list-disc list-inside space-y-0.5 ml-1">
                                      <li>Vector-Score (semantische Ähnlichkeit)</li>
                                      <li>Text-Score (Keyword-Übereinstimmungen)</li>
                                      <li>Chunk-Länge und Position</li>
                                      <li>Dokument-Typ und Metadaten</li>
                                    </ul>
                                  </div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Bessere Relevanz-Bewertung durch ML-Modell, das aus historischen Daten gelernt hat.</div>
                                  </div>
                                </>
                              ) : (
                                <>
                                  <div>Standard Hybrid Search Ranking wird verwendet (70% Vector + 30% Text).</div>
                                  <div className="mt-2">
                                    <div className="font-semibold text-white mb-1">Vorteil:</div>
                                    <div>Schneller, keine ML-Berechnung erforderlich.</div>
                                  </div>
                                </>
                              )}
                            </div>
                          </>
                        }
                      >
                        <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                      </InfoTooltip>
                    </div>
                    <span className={`font-medium ${
                      queryParams.use_ml_ranking ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {queryParams.use_ml_ranking ? 'Aktiviert' : 'Deaktiviert'}
                    </span>
                  </div>
                )}
                {/* NEU: Adaptive Filterung - Immer anzeigen wenn queryParams vorhanden */}
                {queryParams && (
                  <>
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="flex items-center gap-1 mb-1">
                        <span className="text-gray-600">Adaptive Filter - Avg:</span>
                        <InfoTooltip
                          content={
                            <>
                              <div className="font-semibold mb-1">Mindest-Durchschnitts-Score: {((queryParams.adaptive_min_avg_score ?? 0.15) * 100).toFixed(0)}%</div>
                              <div className="text-gray-300 space-y-1">
                                <div>Berechnet den durchschnittlichen Hybrid-Score der Top-K Chunks.</div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Logik:</div>
                                  <div>Wenn der durchschnittliche Score &lt; {((queryParams.adaptive_min_avg_score ?? 0.15) * 100).toFixed(0)}% UND der maximale Score &lt; {((queryParams.adaptive_min_max_score ?? 0.25) * 100).toFixed(0)}% → keine Chunks verwendet</div>
                                </div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Zweck:</div>
                                  <div>Verhindert, dass bei irrelevanten Fragen (z.B. "Quantencomputer") unrelevante Chunks verwendet werden.</div>
                                </div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Unterschied zu Initialer Score-Filter:</div>
                                  <div>Der Initiale Score-Filter filtert einzelne Chunks während der Suche. Die Adaptive Filterung prüft alle gefundenen Chunks zusammen nach der Suche.</div>
                                </div>
                              </div>
                            </>
                          }
                        >
                          <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        </InfoTooltip>
                      </div>
                      <span className="font-medium text-gray-900">
                        {((queryParams.adaptive_min_avg_score ?? 0.15) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="flex items-center gap-1 mb-1">
                        <span className="text-gray-600">Adaptive Filter - Max:</span>
                        <InfoTooltip
                          content={
                            <>
                              <div className="font-semibold mb-1">Mindest-Maximal-Score: {((queryParams.adaptive_min_max_score ?? 0.25) * 100).toFixed(0)}%</div>
                              <div className="text-gray-300 space-y-1">
                                <div>Der beste Chunk muss mindestens {((queryParams.adaptive_min_max_score ?? 0.25) * 100).toFixed(0)}% Hybrid-Score haben.</div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Logik:</div>
                                  <div>Wenn der beste Chunk &lt; {((queryParams.adaptive_min_max_score ?? 0.25) * 100).toFixed(0)}% → keine Chunks verwendet</div>
                                </div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Zweck:</div>
                                  <div>Stellt sicher, dass mindestens ein Chunk ausreichend relevant ist, bevor Chunks verwendet werden.</div>
                                </div>
                                <div className="mt-2">
                                  <div className="font-semibold text-white mb-1">Unterschied zu Initialer Score-Filter:</div>
                                  <div>Der Initiale Score-Filter filtert einzelne Chunks während der Suche. Die Adaptive Filterung prüft alle gefundenen Chunks zusammen nach der Suche.</div>
                                </div>
                              </div>
                            </>
                          }
                        >
                          <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                        </InfoTooltip>
                      </div>
                      <span className="font-medium text-gray-900">
                        {((queryParams.adaptive_min_max_score ?? 0.25) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* NEU: AI-Modell-Einstellungen */}
          {queryParams && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-purple-600" />
                AI-Modell-Einstellungen
                <InfoTooltip
                  content={
                    <div className="text-gray-300">
                      Diese Einstellungen beeinflussen die Antwort-Generierung des AI-Modells. Sie können im AI-Modell-Einstellungen Dialog angepasst werden.
                    </div>
                  }
                >
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </InfoTooltip>
              </h4>
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="bg-white rounded p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-gray-600">Temperature:</span>
                    <InfoTooltip
                      content={
                        <>
                          <div className="font-semibold mb-1">Aktueller Wert: {(queryParams.temperature ?? 0.0).toFixed(2)}</div>
                          <div className="text-gray-300 space-y-1">
                            <div>Kontrolliert die Kreativität/Zufälligkeit der Antworten.</div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Werte:</div>
                              <ul className="list-disc list-inside space-y-0.5 ml-1">
                                <li>0.0-0.3: Sehr fokussiert, deterministisch</li>
                                <li>0.4-0.7: Ausgewogen (empfohlen)</li>
                                <li>0.8-1.0: Kreativer, variabler</li>
                                <li>1.0-2.0: Sehr kreativ, weniger vorhersagbar</li>
                              </ul>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Empfehlung:</div>
                              <div>Für präzise, faktische Antworten: 0.3-0.5. Für kreative Antworten: 0.7-0.9.</div>
                            </div>
                          </div>
                        </>
                      }
                    >
                      <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                    </InfoTooltip>
                  </div>
                  <span className="font-medium text-gray-900">
                    {(queryParams.temperature ?? 0.0).toFixed(2)}
                  </span>
                </div>
                <div className="bg-white rounded p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-gray-600">Max Tokens:</span>
                    <InfoTooltip
                      content={
                        <>
                          <div className="font-semibold mb-1">Aktueller Wert: {(queryParams.max_tokens ?? 8000).toLocaleString()}</div>
                          <div className="text-gray-300 space-y-1">
                            <div>Maximale Anzahl der Tokens für die generierte Antwort.</div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Typische Werte:</div>
                              <ul className="list-disc list-inside space-y-0.5 ml-1">
                                <li>500-1000: Kurze, präzise Antworten</li>
                                <li>2000-4000: Ausführliche Antworten (empfohlen)</li>
                                <li>4000-8000: Sehr ausführliche Antworten</li>
                              </ul>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Hinweis:</div>
                              <div>Höhere Werte = längere Antworten, aber auch höhere Kosten.</div>
                            </div>
                          </div>
                        </>
                      }
                    >
                      <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                    </InfoTooltip>
                  </div>
                  <span className="font-medium text-gray-900">
                    {(queryParams.max_tokens ?? 8000).toLocaleString()}
                  </span>
                </div>
                <div className="bg-white rounded p-2 border border-gray-200">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-gray-600">Top P:</span>
                    <InfoTooltip
                      content={
                        <>
                          <div className="font-semibold mb-1">Aktueller Wert: {(queryParams.top_p ?? 0.9).toFixed(2)}</div>
                          <div className="text-gray-300 space-y-1">
                            <div>Nucleus Sampling: Berücksichtigt nur Tokens mit kumulativer Wahrscheinlichkeit bis zu diesem Wert.</div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Werte:</div>
                              <ul className="list-disc list-inside space-y-0.5 ml-1">
                                <li>0.1-0.5: Sehr fokussiert, nur wahrscheinlichste Tokens</li>
                                <li>0.6-0.9: Ausgewogen (empfohlen: 0.9)</li>
                                <li>0.95-1.0: Breiteres Spektrum</li>
                              </ul>
                            </div>
                            <div className="mt-2">
                              <div className="font-semibold text-white mb-1">Empfehlung:</div>
                              <div>0.9 ist ein guter Standardwert für ausgewogene Antworten.</div>
                            </div>
                          </div>
                        </>
                      }
                    >
                      <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                    </InfoTooltip>
                  </div>
                  <span className="font-medium text-gray-900">
                    {(queryParams.top_p ?? 0.9).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Embedding Info */}
          {(embeddingProvider || embeddingDimensions) && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                {getProviderIcon(embeddingProvider)}
                Embedding-Provider
                <ImprovedTooltip
                  content={
                    <div className="text-gray-300">
                      <div className="font-semibold text-white mb-1">Was sind Embeddings?</div>
                      <div>Numerische Darstellungen von Text, die semantische Ähnlichkeit messen. Der Provider bestimmt die Qualität und Dimensionen der Embeddings.</div>
                      <div className="mt-2">
                        <div className="font-semibold text-white mb-1">Provider-Unterschiede:</div>
                        <ul className="list-disc list-inside space-y-0.5 ml-1">
                          <li><strong>OpenAI:</strong> 1536 Dimensionen, hohe Qualität</li>
                          <li><strong>Gemini:</strong> 768 Dimensionen, gute Qualität</li>
                          <li><strong>Local:</strong> 384 Dimensionen, schnell</li>
                        </ul>
                      </div>
                    </div>
                  }
                />
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
                <ImprovedTooltip
                  content={
                    <div className="text-gray-300">
                      <div className="font-semibold text-white mb-1">AI-Modell</div>
                      <div>Das verwendete KI-Modell zur Generierung der Antwort. Verschiedene Modelle haben unterschiedliche Stärken und Kosten.</div>
                      <div className="mt-2">
                        <div className="font-semibold text-white mb-1">Verfügbare Modelle:</div>
                        <ul className="list-disc list-inside space-y-0.5 ml-1">
                          <li><strong>GPT-4o Mini:</strong> Schnell, kostengünstig, gute Qualität</li>
                          <li><strong>GPT-5 Mini:</strong> Verbesserte Version von GPT-4o Mini</li>
                          <li><strong>Gemini 2.5 Flash:</strong> Google's schnelles Modell</li>
                        </ul>
                      </div>
                    </div>
                  }
                />
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
                              {ref.ml_score !== undefined && (
                                <>ML Score: {Math.round(ref.ml_score * 100)}%<br/></>
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
                    
                    {/* NEU: Text-Excerpt mit Highlighting (Phase 3) */}
                    {ref.text_excerpt && (
                      <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-700">
                        <span className="text-gray-600 font-medium">Text-Auszug:</span>
                        <p 
                          className="mt-1 leading-relaxed"
                          dangerouslySetInnerHTML={{
                            __html: ref.query_text 
                              ? highlightQueryWords(ref.text_excerpt, ref.query_text)
                              : ref.text_excerpt
                          }}
                        />
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

