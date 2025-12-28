/**
 * Search Quality Debug Panel
 * 
 * Zeigt detaillierte Analyse der Search Quality Metrics:
 * - Welche Chunks sind relevant/nicht relevant?
 * - Warum ist der Score so niedrig?
 * - Was kann verbessert werden?
 * 
 * Version: 2.10.0
 */

'use client'

import { AlertCircle, CheckCircle, XCircle, TrendingUp, TrendingDown, Target, Info } from 'lucide-react'
import Collapsible from './ui/Collapsible'
import Tooltip from './ui/Tooltip'

interface ChunkDebugInfo {
  chunk_id: string
  rank_position: number
  feedback_rating?: 'positive' | 'negative' | 'neutral' | null
  relevance_score: number
  is_relevant: boolean
  hybrid_score?: number
  ml_score?: number
  vector_score?: number
  text_score?: number
  document_title?: string
  page_number?: number
  text_excerpt?: string
}

interface SearchQualityDebugPanelProps {
  query: string
  metrics: {
    precision_at_10: number
    recall_at_10: number
    ndcg_at_10: number
    mrr: number
    num_relevant_results: number
    num_total_results: number
    has_feedback?: boolean
    num_feedback_items?: number
    feedback_coverage?: number
    filters_applied?: any
    score_threshold?: number
    top_k_limit?: number
  }
  chunks: ChunkDebugInfo[]
}

export default function SearchQualityDebugPanel({
  query,
  metrics,
  chunks
}: SearchQualityDebugPanelProps) {
  
  const formatPercent = (value: number) => {
    return (value * 100).toFixed(1) + '%'
  }

  // Analysiere Probleme
  const problems: string[] = []
  const recommendations: string[] = []

  // Problem 1: Niedrige Precision
  if (metrics.precision_at_10 < 0.5) {
    problems.push(`Niedrige Precision@10: ${formatPercent(metrics.precision_at_10)} - Viele nicht-relevante Chunks in Top-10`)
    recommendations.push('Gib negatives Feedback (👎) für nicht-relevante Chunks, um das System zu trainieren')
  }

  // Problem 2: Niedrige Recall
  if (metrics.recall_at_10 < 0.5) {
    problems.push(`Niedrige Recall@10: ${formatPercent(metrics.recall_at_10)} - Viele relevante Chunks wurden nicht gefunden`)
    recommendations.push('Prüfe, ob wichtige Dokumente indexiert sind. Erweitere die Query mit Synonymen.')
  }

  // Problem 3: Niedrige NDCG
  if (metrics.ndcg_at_10 < 0.5) {
    problems.push(`Niedrige NDCG@10: ${formatPercent(metrics.ndcg_at_10)} - Relevante Chunks stehen nicht oben im Ranking`)
    recommendations.push('Gib positives Feedback (👍) für relevante Chunks, damit sie höher ranken')
  }

  // Problem 4: Zu wenig Feedback
  if (!metrics.has_feedback || metrics.num_relevant_results < 2) {
    problems.push('Zu wenig Feedback: Nur wenige Chunks wurden bewertet')
    recommendations.push('Gib Feedback für alle relevanten/nicht-relevanten Chunks, um präzise Metriken zu erhalten')
  }

  // Sortiere Chunks nach Ranking
  const sortedChunks = [...chunks].sort((a, b) => a.rank_position - b.rank_position)

  // Zähle relevante/nicht-relevante Chunks
  const relevantChunks = sortedChunks.filter(c => c.is_relevant)
  const nonRelevantChunks = sortedChunks.filter(c => !c.is_relevant)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Target className="w-7 h-7 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Search Quality Analyse</h2>
        <Tooltip
          icon
          content={
            <div className="space-y-2">
              <p className="font-semibold">Was zeigt diese Analyse?</p>
              <p className="text-xs">
                Diese Analyse zeigt dir genau, warum deine Suche einen bestimmten Score hat.
                Du siehst, welche Chunks relevant sind und welche nicht, und was verbessert werden kann.
              </p>
            </div>
          }
        />
      </div>

      {/* Query */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-1">
              Analysierte Query
            </div>
            <div className="text-lg font-medium text-blue-900">
              &quot;{query}&quot;
            </div>
          </div>
        </div>
      </div>

      {/* Score-Zusammenfassung */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Precision@10</div>
          <div className={`text-2xl font-bold ${
            metrics.precision_at_10 >= 0.7 ? 'text-green-600' :
            metrics.precision_at_10 >= 0.5 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {formatPercent(metrics.precision_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metrics.num_relevant_results} von {metrics.num_total_results} relevant
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Recall@10</div>
          <div className={`text-2xl font-bold ${
            metrics.recall_at_10 >= 0.7 ? 'text-green-600' :
            metrics.recall_at_10 >= 0.5 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {formatPercent(metrics.recall_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Relevante gefunden
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">NDCG@10</div>
          <div className={`text-2xl font-bold ${
            metrics.ndcg_at_10 >= 0.7 ? 'text-green-600' :
            metrics.ndcg_at_10 >= 0.5 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {formatPercent(metrics.ndcg_at_10)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Ranking-Qualität
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">MRR</div>
          <div className={`text-2xl font-bold ${
            metrics.mrr >= 0.7 ? 'text-green-600' :
            metrics.mrr >= 0.5 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {formatPercent(metrics.mrr)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Erstes relevantes Ergebnis
          </div>
        </div>
      </div>

      {/* Feedback-Abdeckung Warnung */}
      {metrics.feedback_coverage !== undefined && metrics.feedback_coverage < 0.3 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Niedrige Feedback-Abdeckung</h3>
              <p className="text-sm text-yellow-800 mb-2">
                Nur <strong>{(metrics.feedback_coverage * 100).toFixed(0)}%</strong> der Chunks haben Feedback erhalten 
                ({metrics.num_feedback_items || 0} von {metrics.num_total_results} Chunks).
              </p>
              <p className="text-sm text-yellow-800">
                <strong>Warum ist das ein Problem?</strong> Die Metriken sind möglicherweise ungenau, da viele Chunks als "neutral" (0.5) behandelt werden.
                Gib Feedback für <strong>alle</strong> relevanten/nicht-relevanten Chunks, um präzise Metriken zu erhalten.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter-Informationen */}
      {metrics.filters_applied && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-2">🔍 Angewendete Filter</h3>
              <div className="text-sm text-blue-800 space-y-1">
                {metrics.filters_applied.document_type && (
                  <div><strong>Document Type:</strong> {metrics.filters_applied.document_type}</div>
                )}
                {metrics.score_threshold && (
                  <div><strong>Score Threshold:</strong> {metrics.score_threshold}</div>
                )}
                {metrics.top_k_limit && (
                  <div><strong>Top-K Limit:</strong> {metrics.top_k_limit}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Probleme & Empfehlungen */}
      {problems.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 mb-2">Identifizierte Probleme</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-red-800">
                {problems.map((problem, idx) => (
                  <li key={idx}>{problem}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-2">Empfehlungen zur Verbesserung</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                {recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Chunk-Analyse */}
      <Collapsible
        title={`Chunk-Analyse (${relevantChunks.length} relevant, ${nonRelevantChunks.length} nicht relevant)`}
        defaultOpen={true}
        icon={<Target className="w-4 h-4" />}
      >
        <div className="space-y-3">
          {sortedChunks.map((chunk) => (
            <div
              key={chunk.chunk_id}
              className={`border rounded-lg p-4 ${
                chunk.is_relevant
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-lg font-bold text-gray-900">
                      #{chunk.rank_position}
                    </span>
                    {chunk.is_relevant ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                    <span className={`font-semibold ${
                      chunk.is_relevant ? 'text-green-900' : 'text-red-900'
                    }`}>
                      {chunk.is_relevant ? '✅ Relevant' : '❌ Nicht relevant'}
                    </span>
                    {chunk.feedback_rating && (
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-200">
                        Feedback: {chunk.feedback_rating}
                      </span>
                    )}
                  </div>

                  <div className="text-sm text-gray-700 mb-2">
                    <strong>Dokument:</strong> {chunk.document_title || 'Unbekannt'}
                    {chunk.page_number && ` • Seite ${chunk.page_number}`}
                  </div>

                  {chunk.text_excerpt && (
                    <div className="text-xs text-gray-600 bg-white rounded p-2 mt-2 max-h-20 overflow-y-auto">
                      {chunk.text_excerpt.substring(0, 200)}...
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 text-xs">
                    {chunk.hybrid_score !== undefined && (
                      <div>
                        <span className="text-gray-600">Hybrid:</span>{' '}
                        <span className="font-semibold">{(chunk.hybrid_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {chunk.vector_score !== undefined && (
                      <div>
                        <span className="text-gray-600">Vector:</span>{' '}
                        <span className="font-semibold">{(chunk.vector_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {chunk.text_score !== undefined && (
                      <div>
                        <span className="text-gray-600">Text:</span>{' '}
                        <span className="font-semibold">{(chunk.text_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {chunk.ml_score !== undefined && (
                      <div>
                        <span className="text-gray-600">ML:</span>{' '}
                        <span className="font-semibold">{(chunk.ml_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>

                  {/* Warum relevant/nicht relevant? */}
                  <div className="mt-3 text-xs">
                    {chunk.feedback_rating ? (
                      <div className="text-gray-700">
                        <strong>Bewertung basierend auf:</strong> {chunk.feedback_rating === 'positive' ? 'Positivem Feedback (👍)' : chunk.feedback_rating === 'negative' ? 'Negativem Feedback (👎)' : 'Neutralem Feedback'}
                      </div>
                    ) : (
                      <div className="text-gray-700">
                        <strong>Bewertung basierend auf:</strong> Automatischer Score-Bewertung (Relevance Score: {(chunk.relevance_score * 100).toFixed(1)}%)
                        {chunk.relevance_score > 0.5 ? ' → Als relevant eingestuft' : ' → Als nicht relevant eingestuft'}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Collapsible>

      {/* Erklärung: Wie wird der Score berechnet? */}
      <Collapsible
        title="Wie wird der Score berechnet?"
        defaultOpen={false}
        icon={<Info className="w-4 h-4" />}
      >
        <div className="space-y-4 text-sm text-gray-700">
          <div>
            <p className="font-semibold mb-2">Precision@10 = {formatPercent(metrics.precision_at_10)}</p>
            <p className="text-xs text-gray-600">
              Berechnung: {metrics.num_relevant_results} relevante Chunks / {metrics.num_total_results} Gesamt-Chunks = {formatPercent(metrics.precision_at_10)}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              <strong>Was bedeutet das?</strong> Von den Top-10 Ergebnissen sind {metrics.num_relevant_results} wirklich relevant.
            </p>
          </div>

          <div>
            <p className="font-semibold mb-2">Recall@10 = {formatPercent(metrics.recall_at_10)}</p>
            <p className="text-xs text-gray-600">
              Berechnung: {metrics.num_relevant_results} relevante Chunks in Top-10 / {metrics.num_relevant_results} Gesamt relevante Chunks = {formatPercent(metrics.recall_at_10)}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              <strong>Was bedeutet das?</strong> Von allen relevanten Chunks wurden {metrics.num_relevant_results} in den Top-10 gefunden.
            </p>
          </div>

          <div>
            <p className="font-semibold mb-2">NDCG@10 = {formatPercent(metrics.ndcg_at_10)}</p>
            <p className="text-xs text-gray-600">
              <strong>Was bedeutet das?</strong> Misst die Ranking-Qualität. Berücksichtigt, ob relevante Chunks oben stehen.
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {metrics.ndcg_at_10 < 0.5 ? '⚠️ Niedrige NDCG bedeutet: Relevante Chunks stehen nicht oben im Ranking.' : '✅ Gute NDCG bedeutet: Relevante Chunks stehen oben im Ranking.'}
            </p>
          </div>

          <div>
            <p className="font-semibold mb-2">MRR = {formatPercent(metrics.mrr)}</p>
            <p className="text-xs text-gray-600">
              <strong>Was bedeutet das?</strong> Misst an welcher Position das erste relevante Ergebnis steht.
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {metrics.mrr < 0.5 ? '⚠️ Niedrige MRR bedeutet: Das erste relevante Ergebnis steht weit unten.' : '✅ Gute MRR bedeutet: Das erste relevante Ergebnis steht oben.'}
            </p>
          </div>
        </div>
      </Collapsible>
    </div>
  )
}

