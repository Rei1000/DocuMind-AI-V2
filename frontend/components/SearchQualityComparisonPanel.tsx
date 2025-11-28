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
  // NEU v2.10.5: Debug-Informationen für Chunk-Text
  chunk_text_source?: 'metadata' | 'text_excerpt' | 'database' | 'none'
  chunk_text_length?: number
  query_term_matches?: number
  query_match_ratio?: number
  chunk_text_metadata?: string  // Text aus Metadaten
  chunk_text_db?: string  // Text aus Datenbank
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
  // NEU v2.10.3: Nur prüfen, wenn chatChunks nicht leer ist (sonst falsche Warnung)
  if (chatChunks.length > 0) {
    const analyticsOnlyChunks = analyticsChunks.filter(c => !chatChunkMap.has(c.chunk_id))
    if (analyticsOnlyChunks.length > 0) {
      discrepancies.push(`${analyticsOnlyChunks.length} Chunk(s) in Analytics, aber nicht im Chat: ${analyticsOnlyChunks.map(c => c.chunk_id).join(', ')}`)
    }
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
        <h2 className="text-2xl font-bold text-gray-900">Chunk-Analyse</h2>
        <Tooltip
          icon
          content={
            <div className="space-y-2">
              <p className="font-semibold">Was zeigt diese Analyse?</p>
              <p className="text-xs">
                Diese Analyse zeigt alle Chunks mit ihren Scores, Feedback und Relevanz-Bewertung.
                Die Chunks sind identisch mit denen im Chat.
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

      {/* NEU v2.10.3: Chat Chunks werden nicht mehr angezeigt, da sie identisch mit Analytics Chunks sind */}
      
      {/* Analytics Chunks (einzige Anzeige) - NEU v2.10.3: Chat Chunks wurden entfernt, da identisch */}
      <Collapsible
        title={`Chunk-Analyse (${analyticsChunks.length} Chunks, ${metrics.num_relevant_results} relevant)`}
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
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          chunk.feedback_rating === 'positive' ? 'bg-green-200 text-green-800' :
                          chunk.feedback_rating === 'negative' ? 'bg-red-200 text-red-800' :
                          'bg-gray-200 text-gray-800'
                        }`}>
                          Feedback: {chunk.feedback_rating === 'positive' ? '👍 Positiv' : 
                                     chunk.feedback_rating === 'negative' ? '👎 Negativ' : 
                                     '➖ Neutral'}
                        </span>
                      )}
                    </div>
                    
                  <div className="text-sm text-gray-700 mb-2">
                    <strong>Dokument:</strong> {chunk.document_title || 'Unbekannt'}
                    {chunk.page_number && ` • Seite ${chunk.page_number}`}
                  </div>

                  {/* NEU v2.10.5: Debug-Informationen für Chunk-Text */}
                  {chunk.chunk_text_source && (
                    <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <Info className="w-3 h-3 text-blue-600" />
                        <strong className="text-blue-900">Chunk-Text Quelle:</strong>
                        <span className={`px-2 py-0.5 rounded ${
                          chunk.chunk_text_source === 'metadata' ? 'bg-green-100 text-green-800' :
                          chunk.chunk_text_source === 'text_excerpt' ? 'bg-yellow-100 text-yellow-800' :
                          chunk.chunk_text_source === 'database' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {chunk.chunk_text_source === 'metadata' ? '✅ Metadaten' :
                           chunk.chunk_text_source === 'text_excerpt' ? '⚠️ Text-Auszug' :
                           chunk.chunk_text_source === 'database' ? '💾 Datenbank' :
                           '❌ Keine'}
                        </span>
                      </div>
                      {chunk.chunk_text_length !== undefined && (
                        <div className="text-blue-700">
                          Text-Länge: {chunk.chunk_text_length} Zeichen
                        </div>
                      )}
                      {chunk.query_term_matches !== undefined && chunk.query_match_ratio !== undefined && (
                        <div className="text-blue-700">
                          Query-Term-Matches: {chunk.query_term_matches} ({Math.round(chunk.query_match_ratio * 100)}%)
                        </div>
                      )}
                      {/* Vergleich Metadaten vs. DB */}
                      {chunk.chunk_text_metadata && chunk.chunk_text_db && (
                        <div className={`mt-2 p-2 rounded ${
                          chunk.chunk_text_metadata !== chunk.chunk_text_db 
                            ? 'bg-yellow-50 border border-yellow-300' 
                            : 'bg-green-50 border border-green-300'
                        }`}>
                          <div className={`font-semibold mb-1 ${
                            chunk.chunk_text_metadata !== chunk.chunk_text_db 
                              ? 'text-yellow-900' 
                              : 'text-green-900'
                          }`}>
                            {chunk.chunk_text_metadata !== chunk.chunk_text_db 
                              ? '⚠️ Unterschied zwischen Metadaten und DB:' 
                              : '✅ Metadaten und DB identisch:'}
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <div className={`font-semibold mb-1 ${
                                chunk.chunk_text_metadata !== chunk.chunk_text_db 
                                  ? 'text-yellow-800' 
                                  : 'text-green-800'
                              }`}>
                                Metadaten ({chunk.chunk_text_metadata.length} Zeichen):
                              </div>
                              <div className={`bg-white p-2 rounded border max-h-20 overflow-y-auto ${
                                chunk.chunk_text_metadata !== chunk.chunk_text_db 
                                  ? 'border-yellow-200' 
                                  : 'border-green-200'
                              }`}>
                                {chunk.chunk_text_metadata.substring(0, 200)}
                                {chunk.chunk_text_metadata.length > 200 && '...'}
                              </div>
                            </div>
                            <div>
                              <div className={`font-semibold mb-1 ${
                                chunk.chunk_text_metadata !== chunk.chunk_text_db 
                                  ? 'text-yellow-800' 
                                  : 'text-green-800'
                              }`}>
                                Datenbank ({chunk.chunk_text_db.length} Zeichen):
                              </div>
                              <div className={`bg-white p-2 rounded border max-h-20 overflow-y-auto ${
                                chunk.chunk_text_metadata !== chunk.chunk_text_db 
                                  ? 'border-yellow-200' 
                                  : 'border-green-200'
                              }`}>
                                {chunk.chunk_text_db.substring(0, 200)}
                                {chunk.chunk_text_db.length > 200 && '...'}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      {/* Nur Metadaten verfügbar */}
                      {chunk.chunk_text_metadata && !chunk.chunk_text_db && (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-300 rounded text-xs">
                          <div className="text-blue-900 font-semibold mb-1">ℹ️ Nur Metadaten verfügbar:</div>
                          <div className="bg-white p-2 rounded border border-blue-200 max-h-20 overflow-y-auto">
                            {chunk.chunk_text_metadata.substring(0, 200)}
                            {chunk.chunk_text_metadata.length > 200 && '...'}
                          </div>
                        </div>
                      )}
                      {/* Nur DB verfügbar */}
                      {!chunk.chunk_text_metadata && chunk.chunk_text_db && (
                        <div className="mt-2 p-2 bg-purple-50 border border-purple-300 rounded text-xs">
                          <div className="text-purple-900 font-semibold mb-1">ℹ️ Nur Datenbank verfügbar:</div>
                          <div className="bg-white p-2 rounded border border-purple-200 max-h-20 overflow-y-auto">
                            {chunk.chunk_text_db.substring(0, 200)}
                            {chunk.chunk_text_db.length > 200 && '...'}
                          </div>
                        </div>
                      )}
                      {chunk.chunk_text_source === 'none' && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-300 rounded text-red-900">
                          ⚠️ Keine Chunk-Text-Daten verfügbar (weder Metadaten noch DB)
                        </div>
                      )}
                    </div>
                  )}
                    
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
        title="Wie wird die Relevanz bewertet?"
        defaultOpen={false}
        icon={<Info className="w-4 h-4" />}
      >
        <div className="space-y-3 text-sm text-gray-700">
          <div>
            <p className="font-semibold mb-2">Relevanz-Bewertung:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li><strong>Positives Feedback (👍):</strong> Chunk wird <strong>immer</strong> als relevant eingestuft, unabhängig vom Score</li>
              <li><strong>Negatives Feedback (👎):</strong> Chunk wird <strong>immer</strong> als nicht relevant eingestuft</li>
              <li><strong>Kein Feedback:</strong> Relevanz wird basierend auf dem Relevance Score bewertet (Score &gt; 0.5 = relevant)</li>
              <li><strong>Feedback hat Priorität:</strong> Wenn Feedback vorhanden ist, wird es für die Bewertung verwendet, nicht der Score</li>
            </ul>
          </div>
          
          <div className="bg-blue-50 rounded p-3 mt-4">
            <p className="text-xs text-blue-800">
              <strong>💡 Tipp:</strong> Gib Feedback für alle relevanten/nicht-relevanten Chunks, um präzisere Metriken zu erhalten.
              Feedback verbessert die Qualität der Search Quality Metrics erheblich!
            </p>
          </div>
        </div>
      </Collapsible>
    </div>
  )
}

