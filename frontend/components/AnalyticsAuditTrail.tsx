/**
 * Analytics Audit Trail Component - v2.10.4
 * 
 * Zeigt nachvollziehbar:
 * - Was wurde ausgewertet (Query, Chunks, Scores)
 * - Wie wurde ausgewertet (Metriken, Normalisierung, Feedback)
 * - Wo wurde ausgewertet (Backend, Frontend, Datenbank)
 * - Wie trägt es zur Verbesserung bei (Trends, Insights, Empfehlungen)
 */

'use client'

import { FileText, Calculator, Database, TrendingUp, Lightbulb, CheckCircle, AlertTriangle, Info, Settings } from 'lucide-react'
import Collapsible from './ui/Collapsible'
import Tooltip from './ui/Tooltip'

interface AnalyticsAuditTrailProps {
  analytics: any
  searchQualityMetrics?: any
}

export default function AnalyticsAuditTrail({ analytics, searchQualityMetrics }: AnalyticsAuditTrailProps) {
  if (!analytics) {
    return null
  }

  // Extrahiere Audit-Informationen
  const query = analytics.query || 'N/A'
  const numChunks = analytics.scores?.length || 0
  const hasFeedback = searchQualityMetrics?.has_feedback || false
  const feedbackCoverage = searchQualityMetrics?.feedback_coverage || 0
  const numRelevant = searchQualityMetrics?.num_relevant_results || 0
  const numTotal = searchQualityMetrics?.num_total_results || 0
  
  // Metriken-Informationen
  const precisionAt10 = searchQualityMetrics?.precision_at_10 || 0
  const recallAt10 = searchQualityMetrics?.recall_at_10 || 0
  const ndcgAt10 = searchQualityMetrics?.ndcg_at_10 || 0
  const mrr = searchQualityMetrics?.mrr || 0
  
  // Filter-Informationen
  const filtersApplied = searchQualityMetrics?.filters_applied || {}
  const scoreThreshold = searchQualityMetrics?.score_threshold
  const topKLimit = searchQualityMetrics?.top_k_limit
  
  // AI-Einstellungen
  const temperature = searchQualityMetrics?.temperature
  const maxTokens = searchQualityMetrics?.max_tokens
  const topP = searchQualityMetrics?.top_p
  
  // Normalisierte Scores
  const normalizedScores = searchQualityMetrics?.normalized_relevance_scores || {}
  const hasNormalizedScores = Object.keys(normalizedScores).length > 0

  // Bewertung der Qualität
  const getQualityLevel = () => {
    if (precisionAt10 >= 0.8 && recallAt10 >= 0.8 && ndcgAt10 >= 0.8) {
      return { level: 'excellent', color: 'green', text: 'Exzellent' }
    } else if (precisionAt10 >= 0.6 && recallAt10 >= 0.6 && ndcgAt10 >= 0.6) {
      return { level: 'good', color: 'blue', text: 'Gut' }
    } else if (precisionAt10 >= 0.4 && recallAt10 >= 0.4 && ndcgAt10 >= 0.4) {
      return { level: 'fair', color: 'yellow', text: 'Ausreichend' }
    } else {
      return { level: 'poor', color: 'red', text: 'Verbesserungswürdig' }
    }
  }

  const qualityLevel = getQualityLevel()

  // Verbesserungs-Empfehlungen
  const getImprovementRecommendations = () => {
    const recommendations: string[] = []
    
    if (feedbackCoverage < 0.3) {
      recommendations.push('Mehr Feedback geben: Nur ' + Math.round(feedbackCoverage * 100) + '% der Chunks haben Feedback. Gib mehr 👍/👎 Feedback für präzisere Metriken.')
    }
    
    if (precisionAt10 < 0.6) {
      recommendations.push('Precision verbessern: Nur ' + Math.round(precisionAt10 * 100) + '% der Top-10 Ergebnisse sind relevant. Prüfe die Suchparameter.')
    }
    
    if (recallAt10 < 0.6) {
      recommendations.push('Recall verbessern: Nur ' + Math.round(recallAt10 * 100) + '% der relevanten Dokumente wurden gefunden. Erhöhe top_k oder senke score_threshold.')
    }
    
    if (ndcgAt10 < 0.6) {
      recommendations.push('Ranking verbessern: NDCG@10 von ' + Math.round(ndcgAt10 * 100) + '% zeigt, dass relevante Ergebnisse nicht optimal sortiert sind.')
    }
    
    if (!hasNormalizedScores) {
      recommendations.push('Normalisierte Scores fehlen: Die Relevanz-Bewertung basiert auf rohen Scores. Normalisierte Scores würden die Bewertung verbessern.')
    }
    
    if (recommendations.length === 0) {
      recommendations.push('Exzellente Ergebnisse! Die Metriken zeigen eine hohe Qualität. Weiter so!')
    }
    
    return recommendations
  }

  const recommendations = getImprovementRecommendations()

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-6">
        <FileText className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-bold text-gray-900">Audit Trail</h3>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
          Nachvollziehbar & Transparent
        </span>
      </div>

      <div className="space-y-6">
        {/* 1. Was wurde ausgewertet */}
        <Collapsible
          title="Was wurde ausgewertet?"
          defaultOpen={true}
          icon={<FileText className="w-5 h-5" />}
        >
          <div className="space-y-4 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="font-semibold text-blue-900">Query</span>
                </div>
                <p className="text-blue-800 text-sm">"{query}"</p>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="font-semibold text-green-900">Chunks analysiert</span>
                </div>
                <p className="text-green-800 text-sm font-bold text-lg">{numChunks} Chunks</p>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-purple-600" />
                  <span className="font-semibold text-purple-900">Relevante Ergebnisse</span>
                </div>
                <p className="text-purple-800 text-sm font-bold text-lg">
                  {numRelevant} von {numTotal} relevant
                </p>
              </div>
              
              <div className={`rounded-lg p-4 ${hasFeedback ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <div className="flex items-center gap-2 mb-2">
                  {hasFeedback ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-yellow-600" />
                  )}
                  <span className={`font-semibold ${hasFeedback ? 'text-green-900' : 'text-yellow-900'}`}>
                    Feedback-Abdeckung
                  </span>
                </div>
                <p className={`text-sm font-bold text-lg ${hasFeedback ? 'text-green-800' : 'text-yellow-800'}`}>
                  {Math.round(feedbackCoverage * 100)}%
                </p>
              </div>
            </div>
          </div>
        </Collapsible>

        {/* 2. Wie wurde ausgewertet */}
        <Collapsible
          title="Wie wurde ausgewertet?"
          defaultOpen={true}
          icon={<Calculator className="w-5 h-5" />}
        >
          <div className="space-y-4 pt-4">
            {/* Metriken */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Calculator className="w-4 h-4" />
                Berechnete Metriken
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 mb-1">Precision@10</div>
                  <div className="text-lg font-bold text-gray-900">{Math.round(precisionAt10 * 100)}%</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 mb-1">Recall@10</div>
                  <div className="text-lg font-bold text-gray-900">{Math.round(recallAt10 * 100)}%</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 mb-1">NDCG@10</div>
                  <div className="text-lg font-bold text-gray-900">{Math.round(ndcgAt10 * 100)}%</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 mb-1">MRR</div>
                  <div className="text-lg font-bold text-gray-900">{Math.round(mrr * 100)}%</div>
                </div>
              </div>
            </div>

            {/* Normalisierung */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Score-Normalisierung
              </h4>
              <div className="bg-gray-50 rounded-lg p-4">
                {hasNormalizedScores ? (
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">
                      Percentile-basierte Normalisierung aktiv ({Object.keys(normalizedScores).length} Chunks normalisiert)
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">
                      Keine normalisierten Scores verfügbar (verwendet rohe Hybrid-Scores)
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Filter & Einstellungen */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Angewendete Filter & Einstellungen
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {scoreThreshold !== undefined && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Score Threshold</div>
                    <div className="text-sm font-semibold text-gray-900">{scoreThreshold}</div>
                  </div>
                )}
                {topKLimit !== undefined && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Top-K Limit</div>
                    <div className="text-sm font-semibold text-gray-900">{topKLimit}</div>
                  </div>
                )}
                {temperature !== undefined && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">AI Temperature</div>
                    <div className="text-sm font-semibold text-gray-900">{temperature}</div>
                  </div>
                )}
                {maxTokens !== undefined && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Max Tokens</div>
                    <div className="text-sm font-semibold text-gray-900">{maxTokens}</div>
                  </div>
                )}
                {topP !== undefined && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Top P</div>
                    <div className="text-sm font-semibold text-gray-900">{topP}</div>
                  </div>
                )}
                {Object.keys(filtersApplied).length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 mb-1">Weitere Filter</div>
                    <div className="text-sm font-semibold text-gray-900">
                      {Object.keys(filtersApplied).join(', ')}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Collapsible>

        {/* 3. Wo wurde ausgewertet */}
        <Collapsible
          title="Wo wurde ausgewertet?"
          defaultOpen={false}
          icon={<Database className="w-5 h-5" />}
        >
          <div className="space-y-4 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900">Backend</span>
                </div>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Metriken-Berechnung (search_quality_metrics.py)</li>
                  <li>• Score-Normalisierung (Percentile-basiert)</li>
                  <li>• Feedback-Integration</li>
                  <li>• API: /api/rag/analytics/search-quality</li>
                </ul>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4 border-l-4 border-green-500">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">Datenbank</span>
                </div>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Chat Messages (source_chunks, metadata)</li>
                  <li>• Feedback (rag_feedback, chunk_feedback)</li>
                  <li>• Search Quality Metrics (wenn Feedback vorhanden)</li>
                </ul>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 border-l-4 border-purple-500">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-purple-600" />
                  <span className="font-semibold text-purple-900">Frontend</span>
                </div>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>• Analytics-Daten aus localStorage</li>
                  <li>• Metriken-API-Request (bei Bedarf)</li>
                  <li>• Visualisierung & Darstellung</li>
                </ul>
              </div>
            </div>
          </div>
        </Collapsible>

        {/* 4. Wie trägt es zur Verbesserung bei */}
        <Collapsible
          title="Wie trägt es zur Verbesserung bei?"
          defaultOpen={true}
          icon={<Lightbulb className="w-5 h-5" />}
        >
          <div className="space-y-4 pt-4">
            {/* Qualitäts-Bewertung */}
            <div className={`rounded-lg p-4 border-l-4 ${
              qualityLevel.color === 'green' ? 'bg-green-50 border-green-500' :
              qualityLevel.color === 'blue' ? 'bg-blue-50 border-blue-500' :
              qualityLevel.color === 'yellow' ? 'bg-yellow-50 border-yellow-500' :
              'bg-red-50 border-red-500'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                {qualityLevel.color === 'green' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                )}
                <span className={`font-semibold ${
                  qualityLevel.color === 'green' ? 'text-green-900' :
                  qualityLevel.color === 'blue' ? 'text-blue-900' :
                  qualityLevel.color === 'yellow' ? 'text-yellow-900' :
                  'text-red-900'
                }`}>
                  Qualitäts-Bewertung: {qualityLevel.text}
                </span>
              </div>
              <p className={`text-sm ${
                qualityLevel.color === 'green' ? 'text-green-800' :
                qualityLevel.color === 'blue' ? 'text-blue-800' :
                qualityLevel.color === 'yellow' ? 'text-yellow-800' :
                'text-red-800'
              }`}>
                Basierend auf Precision@10 ({Math.round(precisionAt10 * 100)}%), 
                Recall@10 ({Math.round(recallAt10 * 100)}%), 
                und NDCG@10 ({Math.round(ndcgAt10 * 100)}%)
              </p>
            </div>

            {/* Verbesserungs-Empfehlungen */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Verbesserungs-Empfehlungen
              </h4>
              <div className="space-y-2">
                {recommendations.map((rec, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-3 flex items-start gap-2">
                    <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-gray-800">{rec}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Nächste Schritte */}
            <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">
              <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Nächste Schritte zur Verbesserung
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>1. Gib regelmäßig Feedback (👍/👎) zu den Suchergebnissen</li>
                <li>2. Prüfe die Filter-Einstellungen (score_threshold, top_k)</li>
                <li>3. Vergleiche verschiedene AI-Modell-Einstellungen (Temperature, Max Tokens)</li>
                <li>4. Nutze die Trend-Analyse um langfristige Verbesserungen zu erkennen</li>
              </ul>
            </div>
          </div>
        </Collapsible>
      </div>
    </div>
  )
}

