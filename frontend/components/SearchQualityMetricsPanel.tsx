/**
 * Search Quality Metrics Panel Component
 * 
 * Zeigt Search Quality Metrics für RAG-Suchergebnisse:
 * - Precision@k, Recall@k, NDCG@k, MRR
 * - Hybrid vs ML Ranking Vergleich
 * - Visualisierung der Metriken
 * 
 * Version: 2.9.0
 */

'use client'

import { TrendingUp, TrendingDown, Target, BarChart3, Award, Zap, Info, MessageSquare, Settings, Thermometer, Hash, Sliders } from 'lucide-react'
import Tooltip from './ui/Tooltip'
import Collapsible from './ui/Collapsible'

interface SearchQualityMetrics {
  precision_at_1: number
  precision_at_3: number
  precision_at_5: number
  precision_at_10: number
  recall_at_1: number
  recall_at_3: number
  recall_at_5: number
  recall_at_10: number
  ndcg_at_1: number
  ndcg_at_3: number
  ndcg_at_5: number
  ndcg_at_10: number
  mrr: number
  average_relevance_score: number
  num_relevant_results: number
  num_total_results: number
  has_feedback?: boolean
  num_feedback_items?: number
  hybrid_ndcg_at_10?: number | null
  ml_ndcg_at_10?: number | null
  // NEU v2.10.3: AI-Modell-Einstellungen
  temperature?: number | null
  max_tokens?: number | null
  top_p?: number | null
  // Filter-Informationen
  filters_applied?: { [key: string]: any } | null
  score_threshold?: number | null
  top_k_limit?: number | null
}

interface SearchQualityMetricsPanelProps {
  metrics: SearchQualityMetrics
  query?: string
}

export default function SearchQualityMetricsPanel({ 
  metrics, 
  query 
}: SearchQualityMetricsPanelProps) {
  
  const formatPercent = (value: number) => {
    return (value * 100).toFixed(1) + '%'
  }

  const getScoreColor = (value: number) => {
    if (value >= 0.8) return 'text-green-600'
    if (value >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (value: number) => {
    if (value >= 0.8) return 'bg-green-100'
    if (value >= 0.6) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <div className="space-y-6">
      {/* Header mit Query */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Target className="w-7 h-7 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Search Quality Metrics</h2>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">Was sind Search Quality Metrics?</p>
                  <p className="text-xs">
                    Diese Zahlen zeigen dir, wie gut die Suche funktioniert. Sie messen die Qualität der Suchergebnisse.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li><strong>Precision@k:</strong> Wie viele der Top-Ergebnisse sind wirklich hilfreich?</li>
                    <li><strong>Recall@k:</strong> Wie viele hilfreiche Dokumente wurden überhaupt gefunden?</li>
                    <li><strong>NDCG@k:</strong> Wie gut sind die Ergebnisse sortiert? (Beste zuerst?)</li>
                    <li><strong>MRR:</strong> Wie schnell findest du das erste hilfreiche Ergebnis?</li>
                  </ul>
                  <p className="text-xs text-gray-300 mt-2">
                    <strong>Wie werden sie berechnet?</strong><br />
                    Basierend auf deinem Feedback (👍/👎) oder automatisch aus den Scores der Suchergebnisse.
                  </p>
                </div>
              }
            />
          </div>
        </div>
        
        {/* Feedback-Status Badge */}
        {metrics.has_feedback !== undefined && (
          <div className={`rounded-lg p-4 border-l-4 ${
            metrics.has_feedback 
              ? 'bg-green-50 border-green-500' 
              : 'bg-yellow-50 border-yellow-500'
          }`}>
            <div className="flex items-start gap-3">
              {metrics.has_feedback ? (
                <>
                  <MessageSquare className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-green-900 mb-1">✅ Metriken basieren auf Feedback</h3>
                    <p className="text-sm text-green-800">
                      Die Metriken wurden basierend auf deinem Feedback berechnet ({metrics.num_feedback_items || 0} Feedback-Einträge).
                      Das gibt präzisere Ergebnisse als automatische Score-Berechnung.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <Info className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-900 mb-1">⚠️ Metriken basieren auf Scores</h3>
                    <p className="text-sm text-yellow-800">
                      Die Metriken wurden automatisch aus den Scores der Suchergebnisse berechnet.
                      <strong> Gib Feedback im Chat (👍/👎), um präzisere Metriken zu erhalten!</strong>
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
        
        {/* WICHTIG: Frage prominent anzeigen */}
        {query && (
          <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
            <div className="flex items-start gap-3">
              <MessageSquare className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-1">
                  Bewertete Query
                </div>
                <div className="text-lg font-medium text-blue-900">
                  &quot;{query}&quot;
                </div>
                <div className="text-xs text-blue-700 mt-2">
                  Diese Metriken beziehen sich auf die oben genannte Frage. Die Qualität der Suchergebnisse 
                  wurde für diese spezifische Query gemessen.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* NEU v2.10.3: AI-Modell-Einstellungen */}
        {(metrics.temperature !== null && metrics.temperature !== undefined) ||
         (metrics.max_tokens !== null && metrics.max_tokens !== undefined) ||
         (metrics.top_p !== null && metrics.top_p !== undefined) ? (
          <div className="bg-purple-50 border-l-4 border-purple-500 rounded-r-lg p-4">
            <div className="flex items-start gap-3">
              <Settings className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-xs font-semibold text-purple-900 uppercase tracking-wide mb-2">
                  AI-Modell Einstellungen
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {metrics.temperature !== null && metrics.temperature !== undefined && (
                    <div className="flex items-center gap-2">
                      <Thermometer className="w-4 h-4 text-purple-600" />
                      <div>
                        <div className="text-xs text-purple-700 font-medium">Temperature</div>
                        <div className="text-sm font-semibold text-purple-900">{metrics.temperature.toFixed(1)}</div>
                      </div>
                    </div>
                  )}
                  {metrics.max_tokens !== null && metrics.max_tokens !== undefined && (
                    <div className="flex items-center gap-2">
                      <Hash className="w-4 h-4 text-purple-600" />
                      <div>
                        <div className="text-xs text-purple-700 font-medium">Max Tokens</div>
                        <div className="text-sm font-semibold text-purple-900">{metrics.max_tokens}</div>
                      </div>
                    </div>
                  )}
                  {metrics.top_p !== null && metrics.top_p !== undefined && (
                    <div className="flex items-center gap-2">
                      <Sliders className="w-4 h-4 text-purple-600" />
                      <div>
                        <div className="text-xs text-purple-700 font-medium">Top P</div>
                        <div className="text-sm font-semibold text-purple-900">{metrics.top_p.toFixed(2)}</div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="text-xs text-purple-700 mt-2">
                  Diese Einstellungen beeinflussen die Qualität und Konsistenz der AI-Antworten.
                </div>
              </div>
            </div>
          </div>
        ) : null}
        
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Precision@10 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="text-sm text-gray-600">Precision@10</div>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <p className="font-semibold">Precision@10</p>
                    <p className="text-xs">
                      <strong>Was bedeutet das?</strong><br />
                      Anteil der relevanten Ergebnisse in den Top-10 Suchergebnissen.
                    </p>
                    <p className="text-xs">
                      <strong>Berechnung:</strong><br />
                      Precision@10 = (Anzahl relevante Ergebnisse in Top-10) / 10
                    </p>
                    <p className="text-xs">
                      <strong>Beispiel:</strong><br />
                      Wenn 7 von 10 Top-Ergebnissen relevant sind: 7/10 = 0.7 (70%)
                    </p>
                    <p className="text-xs text-gray-300 mt-2">
                      <strong>Interpretation:</strong><br />
                      Höher ist besser. 100% bedeutet, alle Top-10 Ergebnisse sind relevant.
                    </p>
                  </div>
                }
              />
            </div>
            <BarChart3 className="w-4 h-4 text-blue-600" />
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(metrics.precision_at_10)}`}>
            {formatPercent(metrics.precision_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metrics.num_relevant_results} von {metrics.num_total_results} relevant
          </div>
        </div>

        {/* Recall@10 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="text-sm text-gray-600">Recall@10</div>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <p className="font-semibold">Recall@10</p>
                    <p className="text-xs">
                      <strong>Was bedeutet das?</strong><br />
                      Anteil der gefundenen relevanten Dokumente (von allen relevanten Dokumenten).
                    </p>
                    <p className="text-xs">
                      <strong>Berechnung:</strong><br />
                      Recall@10 = (Relevante in Top-10) / (Gesamtanzahl relevante Dokumente)
                    </p>
                    <p className="text-xs">
                      <strong>Beispiel:</strong><br />
                      Wenn 8 von 10 relevanten Dokumenten in Top-10 sind: 8/10 = 0.8 (80%)
                    </p>
                    <p className="text-xs text-gray-300 mt-2">
                      <strong>Interpretation:</strong><br />
                      Höher ist besser. 100% bedeutet, alle relevanten Dokumente wurden gefunden.
                    </p>
                  </div>
                }
              />
            </div>
            <TrendingUp className="w-4 h-4 text-purple-600" />
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(metrics.recall_at_10)}`}>
            {formatPercent(metrics.recall_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Relevante Dokumente gefunden
          </div>
        </div>

        {/* NDCG@10 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="text-sm text-gray-600">NDCG@10</div>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <p className="font-semibold">NDCG@10 (Normalized Discounted Cumulative Gain)</p>
                    <p className="text-xs">
                      <strong>Was bedeutet das?</strong><br />
                      Misst die Qualität des Rankings, berücksichtigt dabei die Position der Ergebnisse.
                    </p>
                    <p className="text-xs">
                      <strong>Berechnung:</strong><br />
                      DCG = Σ (relevance / log₂(Position + 1))<br />
                      NDCG = DCG / IDCG (ideales Ranking)
                    </p>
                    <p className="text-xs">
                      <strong>Beispiel:</strong><br />
                      Wenn relevante Dokumente an Position 1, 2, 3 stehen: NDCG ≈ 0.95
                    </p>
                    <p className="text-xs text-gray-300 mt-2">
                      <strong>Interpretation:</strong><br />
                      Höher ist besser. 1.0 = perfektes Ranking (relevante Dokumente ganz oben).
                    </p>
                  </div>
                }
              />
            </div>
            <Award className="w-4 h-4 text-indigo-600" />
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(metrics.ndcg_at_10)}`}>
            {formatPercent(metrics.ndcg_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Ranking-Qualität
          </div>
        </div>

        {/* MRR */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="text-sm text-gray-600">MRR</div>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <p className="font-semibold">MRR (Mean Reciprocal Rank)</p>
                    <p className="text-xs">
                      <strong>Was bedeutet das?</strong><br />
                      Misst an welcher Position das erste relevante Ergebnis steht.
                    </p>
                    <p className="text-xs">
                      <strong>Berechnung:</strong><br />
                      MRR = 1 / Position_des_ersten_relevanten_Ergebnisses
                    </p>
                    <p className="text-xs">
                      <strong>Beispiel:</strong><br />
                      Erstes relevantes Ergebnis an Position 2: MRR = 1/2 = 0.5 (50%)<br />
                      Erstes relevantes Ergebnis an Position 1: MRR = 1/1 = 1.0 (100%)
                    </p>
                    <p className="text-xs text-gray-300 mt-2">
                      <strong>Interpretation:</strong><br />
                      Höher ist besser. 1.0 = erstes Ergebnis ist relevant (optimal).
                    </p>
                  </div>
                }
              />
            </div>
            <Zap className="w-4 h-4 text-yellow-600" />
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(metrics.mrr)}`}>
            {formatPercent(metrics.mrr)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Mean Reciprocal Rank
          </div>
        </div>
      </div>

      {/* Detailed Metrics Table - Aufklappbar */}
      <Collapsible
        title="Detaillierte Metriken (@1, @3, @5, @10)"
        defaultOpen={false}
        icon={<BarChart3 className="w-4 h-4" />}
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600 mb-4">
            <p className="mb-2">
              <strong>Was bedeuten @1, @3, @5, @10?</strong> Die Zahl nach dem @ gibt an, wie viele Top-Ergebnisse betrachtet werden.
            </p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li><strong>@1:</strong> Nur das beste Ergebnis</li>
              <li><strong>@3:</strong> Die Top-3 Ergebnisse</li>
              <li><strong>@5:</strong> Die Top-5 Ergebnisse</li>
              <li><strong>@10:</strong> Die Top-10 Ergebnisse</li>
            </ul>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metrik
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    @1
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    @3
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    @5
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    @10
                  </th>
                </tr>
              </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {/* Precision Row */}
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-900">Precision</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.precision_at_1)}`}>
                    {formatPercent(metrics.precision_at_1)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.precision_at_3)}`}>
                    {formatPercent(metrics.precision_at_3)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.precision_at_5)}`}>
                    {formatPercent(metrics.precision_at_5)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.precision_at_10)}`}>
                    {formatPercent(metrics.precision_at_10)}
                  </span>
                </td>
              </tr>

              {/* Recall Row */}
              <tr className="bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-gray-900">Recall</span>
                    <Tooltip
                      icon
                      content={
                        <div className="space-y-2">
                          <p className="font-semibold">Recall@k - Was bedeutet das?</p>
                          <p className="text-xs">
                            <strong>Recall@k</strong> misst: Von allen relevanten Dokumenten, wie viele wurden in den Top-k gefunden?
                          </p>
                          <p className="text-xs">
                            <strong>Berechnung:</strong><br />
                            Recall@k = (Relevante in Top-k) / (Gesamtanzahl relevante Dokumente)
                          </p>
                          <p className="text-xs">
                            <strong>Beispiel:</strong><br />
                            Wenn es 5 relevante Dokumente gibt:<br />
                            • Recall@1 = 1/5 = 20% (1 von 5 gefunden)<br />
                            • Recall@3 = 3/5 = 60% (3 von 5 gefunden)<br />
                            • Recall@5 = 5/5 = 100% (alle gefunden)
                          </p>
                          <p className="text-xs text-gray-300 mt-2">
                            <strong>Warum verschiedene Werte?</strong><br />
                            Je mehr Top-Ergebnisse betrachtet werden, desto mehr relevante Dokumente werden gefunden.
                          </p>
                        </div>
                      }
                    />
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex flex-col items-center">
                    <span className={`text-sm font-semibold ${getScoreColor(metrics.recall_at_1)}`}>
                      {formatPercent(metrics.recall_at_1)}
                    </span>
                    <span className="text-xs text-gray-500 mt-0.5">
                      {Math.round(metrics.recall_at_1 * metrics.num_relevant_results)}/{metrics.num_relevant_results}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex flex-col items-center">
                    <span className={`text-sm font-semibold ${getScoreColor(metrics.recall_at_3)}`}>
                      {formatPercent(metrics.recall_at_3)}
                    </span>
                    <span className="text-xs text-gray-500 mt-0.5">
                      {Math.round(metrics.recall_at_3 * metrics.num_relevant_results)}/{metrics.num_relevant_results}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex flex-col items-center">
                    <span className={`text-sm font-semibold ${getScoreColor(metrics.recall_at_5)}`}>
                      {formatPercent(metrics.recall_at_5)}
                    </span>
                    <span className="text-xs text-gray-500 mt-0.5">
                      {Math.round(metrics.recall_at_5 * metrics.num_relevant_results)}/{metrics.num_relevant_results}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex flex-col items-center">
                    <span className={`text-sm font-semibold ${getScoreColor(metrics.recall_at_10)}`}>
                      {formatPercent(metrics.recall_at_10)}
                    </span>
                    <span className="text-xs text-gray-500 mt-0.5">
                      {Math.round(metrics.recall_at_10 * metrics.num_relevant_results)}/{metrics.num_relevant_results}
                    </span>
                  </div>
                </td>
              </tr>

              {/* NDCG Row */}
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <Award className="w-4 h-4 text-indigo-600" />
                    <span className="text-sm font-medium text-gray-900">NDCG</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.ndcg_at_1)}`}>
                    {formatPercent(metrics.ndcg_at_1)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.ndcg_at_3)}`}>
                    {formatPercent(metrics.ndcg_at_3)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.ndcg_at_5)}`}>
                    {formatPercent(metrics.ndcg_at_5)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`text-sm font-semibold ${getScoreColor(metrics.ndcg_at_10)}`}>
                    {formatPercent(metrics.ndcg_at_10)}
                  </span>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Collapsible>

      {/* Hybrid vs ML Comparison */}
      {metrics.hybrid_ndcg_at_10 !== null && metrics.hybrid_ndcg_at_10 !== undefined &&
       metrics.ml_ndcg_at_10 !== null && metrics.ml_ndcg_at_10 !== undefined && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Hybrid vs ML Ranking Vergleich
            </h3>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">Hybrid vs ML Ranking</p>
                  <p className="text-xs">
                    <strong>Hybrid Ranking:</strong><br />
                    Kombiniert Vector-Score (semantische Ähnlichkeit) und Text-Score (Keyword-Matching).
                    Einfache, schnelle Methode.
                  </p>
                  <p className="text-xs">
                    <strong>ML Ranking:</strong><br />
                    Verwendet ein Machine-Learning-Modell, das auf historischen Daten trainiert wurde.
                    Berücksichtigt mehr Features (z.B. Dokumenttyp, User-Level, Chunk-Länge).
                  </p>
                  <p className="text-xs text-gray-300 mt-2">
                    <strong>Vergleich:</strong><br />
                    Höherer NDCG@10 = besseres Ranking. ML sollte normalerweise besser sein, 
                    da es aus Feedback lernt.
                  </p>
                </div>
              }
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Hybrid NDCG */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-2">Hybrid Ranking</div>
              <div className="text-2xl font-bold text-blue-600">
                {formatPercent(metrics.hybrid_ndcg_at_10)}
              </div>
              <div className="text-xs text-gray-500 mt-1">NDCG@10</div>
            </div>

            {/* ML NDCG */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-2">ML Ranking</div>
              <div className={`text-2xl font-bold ${
                metrics.ml_ndcg_at_10 > metrics.hybrid_ndcg_at_10 
                  ? 'text-green-600' 
                  : metrics.ml_ndcg_at_10 < metrics.hybrid_ndcg_at_10
                  ? 'text-red-600'
                  : 'text-gray-600'
              }`}>
                {formatPercent(metrics.ml_ndcg_at_10)}
              </div>
              <div className="text-xs text-gray-500 mt-1">NDCG@10</div>
            </div>
          </div>

          {/* Improvement Indicator */}
          {metrics.ml_ndcg_at_10 > metrics.hybrid_ndcg_at_10 && (
            <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 rounded-lg p-3">
              <TrendingUp className="w-5 h-5" />
              <span className="text-sm font-medium">
                ML Ranking ist {formatPercent(metrics.ml_ndcg_at_10 - metrics.hybrid_ndcg_at_10)} besser als Hybrid Ranking
              </span>
            </div>
          )}
          {metrics.ml_ndcg_at_10 < metrics.hybrid_ndcg_at_10 && (
            <div className="mt-4 flex items-center gap-2 text-red-700 bg-red-50 rounded-lg p-3">
              <TrendingDown className="w-5 h-5" />
              <span className="text-sm font-medium">
                ML Ranking ist {formatPercent(metrics.hybrid_ndcg_at_10 - metrics.ml_ndcg_at_10)} schlechter als Hybrid Ranking
              </span>
            </div>
          )}
        </div>
      )}

      {/* Additional Info - Aufklappbar */}
      <Collapsible
        title="Wie werden Metriken berechnet?"
        defaultOpen={false}
        icon={<Info className="w-4 h-4" />}
      >
        <div className="space-y-3 text-sm text-gray-700">
          <div>
            <p className="font-semibold mb-2">Berechnung mit Feedback:</p>
            <p>Wenn du Feedback (👍/👎) gegeben hast, werden die Metriken basierend darauf berechnet. Das gibt die präzisesten Ergebnisse.</p>
          </div>
          <div>
            <p className="font-semibold mb-2">Berechnung ohne Feedback:</p>
            <p>Wenn kein Feedback vorhanden ist, werden die Scores der Suchergebnisse als Proxy verwendet. Chunks mit hohen Scores werden als "relevant" angenommen.</p>
          </div>
          <div className="bg-blue-50 rounded p-3 mt-4">
            <p className="text-xs text-blue-800">
              <strong>Beispiel:</strong> Wenn 8 von 10 Top-Ergebnissen relevant sind (oder hohe Scores haben), 
              dann ist Precision@10 = 0.8 (80%).
            </p>
          </div>
        </div>
      </Collapsible>
      
      {/* Legacy: Additional Info - Falls noch vorhanden */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 hidden">
        <div className="flex items-start gap-3 mb-3">
          <Info className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900 mb-2">Zusätzliche Informationen</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <div>
                <strong>Durchschnittlicher Relevance Score:</strong> {formatPercent(metrics.average_relevance_score)}
                <Tooltip
                  icon
                  content={
                    <div className="space-y-2">
                      <p className="font-semibold">Durchschnittlicher Relevance Score</p>
                      <p className="text-xs">
                        Der Mittelwert aller Relevance Scores der Suchergebnisse.
                        Zeigt die durchschnittliche Relevanz der gefundenen Dokumente.
                      </p>
                      <p className="text-xs text-gray-300 mt-2">
                        <strong>Interpretation:</strong><br />
                        Näher an 1.0 = durchschnittlich sehr relevante Ergebnisse.
                      </p>
                    </div>
                  }
                />
              </div>
              <div>
                <strong>Relevante Ergebnisse:</strong> {metrics.num_relevant_results} von {metrics.num_total_results}
                <Tooltip
                  icon
                  content={
                    <div className="space-y-2">
                      <p className="font-semibold">Relevante Ergebnisse</p>
                      <p className="text-xs">
                        Anzahl der Suchergebnisse, die als relevant eingestuft wurden 
                        (Relevance Score > 0.5).
                      </p>
                      <p className="text-xs text-gray-300 mt-2">
                        <strong>Berechnung:</strong><br />
                        Ein Ergebnis ist relevant, wenn der Relevance Score > 0.5 ist.
                      </p>
                    </div>
                  }
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

