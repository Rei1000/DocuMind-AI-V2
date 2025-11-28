/**
 * Search Quality Comparison Panel
 * 
 * Vergleicht Chunks aus Chat vs. Analytics:
 * - Welche Chunks wurden im Chat verwendet?
 * - Welche Chunks werden in Analytics angezeigt?
 * - Gibt es Diskrepanzen?
 * 
 * Version: 2.10.0
 */

'use client'

import { AlertTriangle, CheckCircle, XCircle, FileText, BarChart3, Info } from 'lucide-react'
import Collapsible from './ui/Collapsible'
import Tooltip from './ui/Tooltip'

interface ChatChunk {
  chunk_id: string
  rank_position: number
  document_title: string
  page_number: number
  relevance_score: number
  vector_score?: number
  text_score?: number
  hybrid_score?: number
}

interface AnalyticsChunk {
  chunk_id: string
  rank_position: number
  document_title: string
  page_number: number
  relevance_score: number
  feedback_rating?: 'positive' | 'negative' | 'neutral' | null
  is_relevant: boolean
  vector_score?: number
  text_score?: number
  hybrid_score?: number
}

interface SearchQualityComparisonPanelProps {
  query: string
  chatChunks: ChatChunk[]
  analyticsChunks: AnalyticsChunk[]
  metrics: {
    precision_at_10: number
    recall_at_10: number
    num_relevant_results: number
    num_total_results: number
  }
}

export default function SearchQualityComparisonPanel({
  query,
  chatChunks,
  analyticsChunks,
  metrics
}: SearchQualityComparisonPanelProps) {
  
  // Erstelle Maps für schnellen Zugriff
  const chatChunkMap = new Map(chatChunks.map(c => [c.chunk_id, c]))
  const analyticsChunkMap = new Map(analyticsChunks.map(c => [c.chunk_id, c]))
  
  // Finde Diskrepanzen
  const discrepancies: string[] = []
  
  // Prüfe: Gibt es Chunks im Chat, die nicht in Analytics sind?
  const chatOnlyChunks = chatChunks.filter(c => !analyticsChunkMap.has(c.chunk_id))
  if (chatOnlyChunks.length > 0) {
    discrepancies.push(`${chatOnlyChunks.length} Chunk(s) im Chat, aber nicht in Analytics: ${chatOnlyChunks.map(c => c.chunk_id).join(', ')}`)
  }
  
  // Prüfe: Gibt es Chunks in Analytics, die nicht im Chat sind?
  const analyticsOnlyChunks = analyticsChunks.filter(c => !chatChunkMap.has(c.chunk_id))
  if (analyticsOnlyChunks.length > 0) {
    discrepancies.push(`${analyticsOnlyChunks.length} Chunk(s) in Analytics, aber nicht im Chat: ${analyticsOnlyChunks.map(c => c.chunk_id).join(', ')}`)
  }
  
  // Prüfe: Unterschiedliche Rank-Positionen?
  const rankMismatches: Array<{chunk_id: string, chatRank: number, analyticsRank: number}> = []
  for (const chatChunk of chatChunks) {
    const analyticsChunk = analyticsChunkMap.get(chatChunk.chunk_id)
    if (analyticsChunk && chatChunk.rank_position !== analyticsChunk.rank_position) {
      rankMismatches.push({
        chunk_id: chatChunk.chunk_id,
        chatRank: chatChunk.rank_position,
        analyticsRank: analyticsChunk.rank_position
      })
    }
  }
  if (rankMismatches.length > 0) {
    discrepancies.push(`${rankMismatches.length} Chunk(s) haben unterschiedliche Rank-Positionen zwischen Chat und Analytics`)
  }
  
  // Prüfe: Feedback vorhanden, aber Metriken zeigen niedrige Scores?
  const positiveFeedbackChunks = analyticsChunks.filter(c => c.feedback_rating === 'positive')
  if (positiveFeedbackChunks.length > 0 && metrics.precision_at_10 < 0.5) {
    discrepancies.push(`⚠️ ${positiveFeedbackChunks.length} Chunk(s) haben positives Feedback, aber Precision@10 ist nur ${(metrics.precision_at_10 * 100).toFixed(1)}%`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <BarChart3 className="w-7 h-7 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Chat vs. Analytics Vergleich</h2>
        <Tooltip
          icon
          content={
            <div className="space-y-2">
              <p className="font-semibold">Was zeigt dieser Vergleich?</p>
              <p className="text-xs">
                Dieser Vergleich zeigt, ob die Chunks im Chat mit den Chunks in Analytics übereinstimmen.
                Diskrepanzen können auf Datenkonsistenz-Probleme hinweisen.
              </p>
            </div>
          }
        />
      </div>

      {/* Diskrepanzen-Warnung */}
      {discrepancies.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Diskrepanzen gefunden</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
                {discrepancies.map((disc, idx) => (
                  <li key={idx}>{disc}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Vergleich: Chat Chunks */}
      <Collapsible
        title={`Chat Chunks (${chatChunks.length} Chunks)`}
        defaultOpen={true}
        icon={<FileText className="w-4 h-4" />}
      >
        <div className="space-y-3">
          {chatChunks.map((chunk) => {
            const analyticsChunk = analyticsChunkMap.get(chunk.chunk_id)
            const hasMismatch = analyticsChunk && (
              analyticsChunk.rank_position !== chunk.rank_position ||
              analyticsChunk.relevance_score !== chunk.relevance_score
            )
            
            return (
              <div
                key={chunk.chunk_id}
                className={`border rounded-lg p-4 ${
                  hasMismatch ? 'bg-yellow-50 border-yellow-300' : 'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-lg font-bold text-gray-900">
                        #{chunk.rank_position}
                      </span>
                      <span className="text-sm font-semibold text-blue-900">
                        {chunk.document_title}
                      </span>
                      <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                        Seite {chunk.page_number}
                      </span>
                      {hasMismatch && (
                        <span className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded-full">
                          ⚠️ Unterschied zu Analytics
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-gray-600">Relevance:</span>{' '}
                        <span className="font-semibold">{(chunk.relevance_score * 100).toFixed(1)}%</span>
                      </div>
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
                    </div>
                    
                    {analyticsChunk && hasMismatch && (
                      <div className="mt-3 text-xs text-yellow-700 bg-yellow-100 rounded p-2">
                        <strong>Unterschied zu Analytics:</strong>
                        {analyticsChunk.rank_position !== chunk.rank_position && (
                          <div>Rank: Chat #{chunk.rank_position} vs. Analytics #{analyticsChunk.rank_position}</div>
                        )}
                        {Math.abs(analyticsChunk.relevance_score - chunk.relevance_score) > 0.01 && (
                          <div>Relevance: Chat {(chunk.relevance_score * 100).toFixed(1)}% vs. Analytics {(analyticsChunk.relevance_score * 100).toFixed(1)}%</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Collapsible>

      {/* Vergleich: Analytics Chunks */}
      <Collapsible
        title={`Analytics Chunks (${analyticsChunks.length} Chunks, ${metrics.num_relevant_results} relevant)`}
        defaultOpen={true}
        icon={<BarChart3 className="w-4 h-4" />}
      >
        <div className="space-y-3">
          {analyticsChunks.map((chunk) => {
            const chatChunk = chatChunkMap.get(chunk.chunk_id)
            const isInChat = chatChunk !== undefined
            
            return (
              <div
                key={chunk.chunk_id}
                className={`border rounded-lg p-4 ${
                  chunk.is_relevant
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                } ${!isInChat ? 'opacity-60' : ''}`}
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
                      {!isInChat && (
                        <span className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded-full">
                          ⚠️ Nicht im Chat
                        </span>
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-2">
                      <strong>Dokument:</strong> {chunk.document_title || 'Unbekannt'}
                      {chunk.page_number && ` • Seite ${chunk.page_number}`}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-gray-600">Relevance:</span>{' '}
                        <span className="font-semibold">{(chunk.relevance_score * 100).toFixed(1)}%</span>
                      </div>
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
                    </div>
                    
                    {/* Warum relevant/nicht relevant? */}
                    <div className="mt-3 text-xs">
                      {chunk.feedback_rating ? (
                        <div className="text-gray-700">
                          <strong>Bewertung:</strong> {chunk.feedback_rating === 'positive' ? 'Positives Feedback (👍)' : chunk.feedback_rating === 'negative' ? 'Negatives Feedback (👎)' : 'Neutrales Feedback'}
                        </div>
                      ) : (
                        <div className="text-gray-700">
                          <strong>Bewertung:</strong> Automatisch basierend auf Score ({(chunk.relevance_score * 100).toFixed(1)}%)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Collapsible>

      {/* Erklärung */}
      <Collapsible
        title="Warum gibt es Diskrepanzen?"
        defaultOpen={false}
        icon={<Info className="w-4 h-4" />}
      >
        <div className="space-y-3 text-sm text-gray-700">
          <div>
            <p className="font-semibold mb-2">Mögliche Ursachen:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li><strong>Chunks im Chat, aber nicht in Analytics:</strong> Chunks wurden möglicherweise nach der Chat-Erstellung gefiltert oder entfernt</li>
              <li><strong>Chunks in Analytics, aber nicht im Chat:</strong> Chunks wurden möglicherweise nach der Analytics-Erstellung hinzugefügt</li>
              <li><strong>Unterschiedliche Rank-Positionen:</strong> Das Ranking könnte sich zwischen Chat-Erstellung und Analytics-Berechnung geändert haben</li>
              <li><strong>Niedrige Metriken trotz positivem Feedback:</strong> Nur wenige Chunks haben Feedback bekommen, oder Feedback wurde nicht richtig zugeordnet</li>
            </ul>
          </div>
          
          <div className="bg-blue-50 rounded p-3 mt-4">
            <p className="text-xs text-blue-800">
              <strong>💡 Tipp:</strong> Wenn du positives Feedback gegeben hast, aber die Metriken niedrig sind, 
              prüfe, ob das Feedback richtig zugeordnet wurde. Gib Feedback für <strong>alle</strong> relevanten/nicht-relevanten Chunks.
            </p>
          </div>
        </div>
      </Collapsible>
    </div>
  )
}

