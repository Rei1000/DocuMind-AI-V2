'use client'

import { useState, useEffect } from 'react'
import { FileText, AlertCircle, CheckCircle, XCircle, Info, ExternalLink, ChevronDown, ChevronUp, Layers, MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react'
import Tooltip from './ui/Tooltip'
import toast from 'react-hot-toast'

interface ChunkAnalysisData {
  chunk_id: string
  document_id: number
  document_title: string
  page_number: number
  page_numbers?: number[]  // NEU: Alle Seiten des Chunks
  relevance_score: number
  vector_score?: number
  text_score?: number
  hybrid_score?: number
  ml_score?: number
  final_score?: number
  rank_position: number
  text_excerpt?: string
  chunk_metadata?: Record<string, unknown>
  feedback_rating?: 'positive' | 'negative' | 'neutral'
  feedback_comment?: string
  // NEU v2.10.7: Multi-Faktor Relevanz-Bewertung
  is_relevant?: boolean
  relevance_reason?: string
  referenced_in_rag_answer?: boolean
  rag_reference_position?: number | null
}

interface ChunkAnalysisPanelProps {
  query: string
  chunks: ChunkAnalysisData[]
  messageId?: number
}

export default function ChunkAnalysisPanel({ query, chunks, messageId }: ChunkAnalysisPanelProps) {
  const [expandedChunks, setExpandedChunks] = useState<Set<string>>(new Set())
  const [chunkFeedback, setChunkFeedback] = useState<Record<string, { rating: string, comment?: string }>>({})

  // Lade Chunk-Level Feedback (falls vorhanden)
  useEffect(() => {
    if (messageId) {
      loadChunkFeedback(messageId)
    }
  }, [messageId])

  const loadChunkFeedback = async (msgId: number) => {
    try {
      const token =
        localStorage.getItem('token') ||
        localStorage.getItem('access_token') ||
        sessionStorage.getItem('token') ||
        sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // Lade Chunk-Level Feedback für alle Chunks dieser Message
      for (const chunk of chunks) {
        const response = await fetch(`/api/rag/chat/chunks/${encodeURIComponent(chunk.chunk_id)}/feedback?chat_message_id=${msgId}`, { headers })
        if (response.ok) {
          const feedbacks = await response.json()
          if (feedbacks && feedbacks.length > 0) {
            // Nimm das neueste Feedback
            const latestFeedback = feedbacks[0]
            setChunkFeedback(prev => ({
              ...prev,
              [chunk.chunk_id]: {
                rating: latestFeedback.rating,
                comment: latestFeedback.comment
              }
            }))
          }
        }
      }
    } catch (error) {
      console.error('Error loading chunk feedback:', error)
    }
  }

  const submitChunkFeedback = async (
    chunkId: string,
    documentId: number,
    rating: 'positive' | 'negative' | 'neutral',
    comment?: string
  ) => {
    if (!messageId) {
      toast.error('Message ID fehlt')
      return
    }

    try {
      const token =
        localStorage.getItem('token') ||
        localStorage.getItem('access_token') ||
        sessionStorage.getItem('token') ||
        sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/rag/chat/chunks/feedback', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          chunk_id: chunkId,
          chat_message_id: messageId,
          document_id: documentId,
          rating,
          comment: comment || null
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Fehler beim Speichern des Feedbacks')
      }

      const savedFeedback = await response.json()
      
      // Update local state
      setChunkFeedback(prev => ({
        ...prev,
        [chunkId]: {
          rating: savedFeedback.rating,
          comment: savedFeedback.comment
        }
      }))

      // NEU v2.10.3: Event-basierte Metriken-Aktualisierung (statt Polling)
      // Dispatch Event für Analytics-Seite, damit Metriken automatisch neu geladen werden
      window.dispatchEvent(new CustomEvent('feedbackSubmitted', {
        detail: { 
          messageId, 
          rating,
          chunkId,
          feedbackType: 'chunk' // Chunk-Level Feedback
        }
      }));

      toast.success('✅ Chunk-Feedback erfolgreich abgegeben!')
    } catch (error: unknown) {
      console.error('Error submitting chunk feedback:', error)
      const message = error instanceof Error ? error.message : 'Feedback konnte nicht gespeichert werden'
      toast.error(`❌ Fehler: ${message}`)
    }
  }

  const toggleChunk = (chunkId: string) => {
    const newExpanded = new Set(expandedChunks)
    if (newExpanded.has(chunkId)) {
      newExpanded.delete(chunkId)
    } else {
      newExpanded.add(chunkId)
    }
    setExpandedChunks(newExpanded)
  }

  const getRelevanceColor = (score: number) => {
    if (score >= 0.7) return 'text-green-700 bg-green-50 border-green-200'
    if (score >= 0.4) return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    return 'text-red-700 bg-red-50 border-red-200'
  }

  const getFeedbackIcon = (rating?: string) => {
    if (!rating) return null
    if (rating === 'positive') return <CheckCircle className="w-5 h-5 text-green-600" />
    if (rating === 'negative') return <XCircle className="w-5 h-5 text-red-600" />
    return <Info className="w-5 h-5 text-blue-600" />
  }

  if (!chunks || chunks.length === 0) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900">Keine Chunk-Daten verfügbar</h3>
            <p className="text-sm text-blue-800 mt-1">
              Es wurden keine Chunk-Details für diese Query gefunden.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Layers className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Chunk-Analyse</h2>
          <Tooltip
            icon
            content={
              <div className="space-y-2 max-w-md">
                <p className="font-semibold">Chunk-Analyse</p>
                <p className="text-xs">
                  Zeigt detaillierte Informationen über alle verwendeten Chunks:
                </p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li><strong>Relevanz-Scores:</strong> Wie relevant ist jeder Chunk für die Query?</li>
                  <li><strong>Seitenverlinkung:</strong> Welche Seiten wurden verlinkt?</li>
                  <li><strong>Chunk-Inhalt:</strong> Was steht tatsächlich in den Chunks?</li>
                  <li><strong>Ranking-Position:</strong> An welcher Position wurde der Chunk gefunden?</li>
                </ul>
                <p className="text-xs text-gray-300 mt-2">
                  <strong>Problem:</strong> Wenn falsche Chunks verwendet wurden, prüfe hier die Scores und Inhalte.
                </p>
              </div>
            }
          />
        </div>
        <div className="text-sm text-gray-600">
          {chunks.length} Chunk{chunks.length !== 1 ? 's' : ''} analysiert
        </div>
      </div>

      {/* Query-Info */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-600 rounded-r-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <MessageSquare className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-1">
              Analysierte Query
            </div>
            <div className="text-lg font-bold text-gray-900">
              &quot;{query}&quot;
            </div>
            <div className="text-sm text-gray-600 mt-2">
              Diese Analyse zeigt, welche Chunks für diese Query gefunden und verwendet wurden.
              Prüfe die Relevanz-Scores und Chunk-Inhalte, um zu verstehen, warum bestimmte Chunks ausgewählt wurden.
            </div>
          </div>
        </div>
      </div>

      {/* Chunk-Liste */}
      <div className="space-y-4">
        {chunks.map((chunk, index) => {
          const isExpanded = expandedChunks.has(chunk.chunk_id)
          const feedback = chunkFeedback[chunk.chunk_id] || { rating: chunk.feedback_rating }
          const hasMultiplePages = chunk.page_numbers && chunk.page_numbers.length > 1
          const pageDisplay = hasMultiplePages 
            ? `Seiten ${chunk.page_numbers?.join(', ')} (verwendet: ${chunk.page_number})`
            : `Seite ${chunk.page_number}`

          return (
            <div
              key={chunk.chunk_id}
              className={`border-2 rounded-lg transition-all ${
                feedback.rating === 'negative'
                  ? 'border-red-300 bg-red-50'
                  : feedback.rating === 'positive'
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              {/* Chunk-Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleChunk(chunk.chunk_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 flex-wrap mb-2">
                      <span className="text-lg font-bold text-gray-900">
                        #{chunk.rank_position}
                      </span>
                      <span className="text-sm font-semibold text-blue-900">
                        {chunk.document_title}
                      </span>
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                        getRelevanceColor(chunk.relevance_score)
                      }`}>
                        {Math.round(chunk.relevance_score * 100)}% Relevanz
                      </span>
                      {/* NEU v2.10.7: Zeige is_relevant Status */}
                      {chunk.is_relevant !== undefined && (
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                          chunk.is_relevant ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {chunk.is_relevant ? '✅ Relevant' : '❌ Nicht relevant'}
                        </span>
                      )}
                      {getFeedbackIcon(feedback.rating)}
                      {feedback.rating === 'negative' && (
                        <span className="text-xs text-red-700 font-semibold">
                          ❌ Falscher Chunk
                        </span>
                      )}
                      {/* NEU v2.10.7: Zeige RAG-Referenz-Status */}
                      {chunk.referenced_in_rag_answer && (
                        <span className="text-xs text-blue-700 font-semibold">
                          📄 In RAG-Antwort referenziert
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        <span>{pageDisplay}</span>
                        {hasMultiplePages && (
                          <Tooltip
                            icon
                            content={
                              <div className="space-y-1">
                                <p className="font-semibold">Multi-Page Chunk</p>
                                <p className="text-xs">
                                  Dieser Chunk umfasst mehrere Seiten: {chunk.page_numbers?.join(', ')}.
                                  Aktuell wird nur Seite {chunk.page_number} verlinkt.
                                </p>
                              </div>
                            }
                          />
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <span>Chunk ID:</span>
                        <span className="font-mono text-xs">{chunk.chunk_id.substring(0, 20)}...</span>
                      </div>
                      {/* NEU v2.10.7: Zeige Relevanz-Grund (Audit-Trail) */}
                      {chunk.relevance_reason && (
                        <div className="flex items-center gap-1 text-xs text-gray-500 italic">
                          <Info className="w-3 h-3" />
                          <span>{chunk.relevance_reason}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Score-Übersicht (immer sichtbar) */}
                <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-2">
                  {chunk.vector_score !== undefined && (
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs text-gray-600">Vector (70%)</div>
                      <div className="text-sm font-bold text-blue-700">
                        {(chunk.vector_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {chunk.text_score !== undefined && (
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs text-gray-600">Text (30%)</div>
                      <div className="text-sm font-bold text-purple-700">
                        {(chunk.text_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {chunk.hybrid_score !== undefined && (
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs text-gray-600">Hybrid (Ranking)</div>
                      <div className="text-sm font-bold text-indigo-700">
                        {(chunk.hybrid_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        = Vector×0.7 + Text×0.3
                      </div>
                    </div>
                  )}
                  {chunk.ml_score !== undefined && (
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs text-gray-600">ML (30%)</div>
                      <div className="text-sm font-bold text-orange-700">
                        {(chunk.ml_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {chunk.final_score !== undefined && (
                    <div className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs text-gray-600">Final (Ranking)</div>
                      <div className="text-sm font-bold text-green-700">
                        {(chunk.final_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        = Hybrid×0.7 + ML×0.3
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Erweiterte Details (ausklappbar) */}
              {isExpanded && (
                <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-4">
                  {/* Chunk-Inhalt */}
                  {chunk.text_excerpt && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Chunk-Inhalt (Auszug)</h4>
                      <div className="bg-white rounded p-3 border border-gray-200 text-sm text-gray-700 max-h-40 overflow-y-auto">
                        {chunk.text_excerpt}
                        {chunk.text_excerpt.length >= 200 && '...'}
                      </div>
                    </div>
                  )}

                  {/* Seiten-Info */}
                  {hasMultiplePages && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-3">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-yellow-900 mb-1">
                            Multi-Page Chunk
                          </h4>
                          <p className="text-xs text-yellow-800">
                            Dieser Chunk umfasst mehrere Seiten: <strong>{chunk.page_numbers?.join(', ')}</strong>.
                            Aktuell wird nur <strong>Seite {chunk.page_number}</strong> in der Verlinkung verwendet.
                            Dies könnte problematisch sein, wenn der relevante Inhalt auf einer anderen Seite liegt.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Chunk-Metadaten */}
                  {chunk.chunk_metadata && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Chunk-Metadaten</h4>
                      <div className="bg-white rounded p-3 border border-gray-200 text-xs">
                        <div className="grid grid-cols-2 gap-2">
                          {chunk.chunk_metadata.chunk_type && (
                            <div>
                              <span className="text-gray-600">Typ:</span>{' '}
                              <span className="font-medium">{chunk.chunk_metadata.chunk_type}</span>
                            </div>
                          )}
                          {chunk.chunk_metadata.document_type && (
                            <div>
                              <span className="text-gray-600">Dokumenttyp:</span>{' '}
                              <span className="font-medium">{chunk.chunk_metadata.document_type}</span>
                            </div>
                          )}
                          {chunk.chunk_metadata.heading_hierarchy && chunk.chunk_metadata.heading_hierarchy.length > 0 && (
                            <div className="col-span-2">
                              <span className="text-gray-600">Überschriften:</span>{' '}
                              <span className="font-medium">{chunk.chunk_metadata.heading_hierarchy.join(' → ')}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Chunk-Level Feedback */}
                  <div className="mt-4 border-t border-gray-200 pt-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">Chunk bewerten</h4>
                    
                    {feedback.rating ? (
                      // Feedback bereits vorhanden
                      <div className={`rounded-lg p-3 ${
                        feedback.rating === 'negative'
                          ? 'bg-red-50 border border-red-200'
                          : feedback.rating === 'positive'
                          ? 'bg-green-50 border border-green-200'
                          : 'bg-blue-50 border border-blue-200'
                      }`}>
                        <div className="flex items-start gap-2">
                          {getFeedbackIcon(feedback.rating)}
                          <div className="flex-1">
                            <h5 className="text-sm font-semibold mb-1">
                              {feedback.rating === 'positive' ? 'Positives Feedback' : 
                               feedback.rating === 'negative' ? 'Negatives Feedback' : 
                               'Neutrales Feedback'}
                            </h5>
                            {feedback.comment && (
                              <p className="text-xs text-gray-700">{feedback.comment}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      // Feedback-Formular
                      <div className="space-y-3">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => submitChunkFeedback(chunk.chunk_id, chunk.document_id, 'positive')}
                            className="flex items-center gap-2 px-3 py-2 bg-green-50 hover:bg-green-100 border border-green-300 rounded-lg transition-colors"
                            title="Chunk ist relevant und hilfreich"
                          >
                            <ThumbsUp className="w-4 h-4 text-green-600" />
                            <span className="text-sm font-medium text-green-700">Relevant</span>
                          </button>
                          <button
                            onClick={() => submitChunkFeedback(chunk.chunk_id, chunk.document_id, 'negative')}
                            className="flex items-center gap-2 px-3 py-2 bg-red-50 hover:bg-red-100 border border-red-300 rounded-lg transition-colors"
                            title="Chunk ist nicht relevant oder falsch"
                          >
                            <ThumbsDown className="w-4 h-4 text-red-600" />
                            <span className="text-sm font-medium text-red-700">Nicht relevant</span>
                          </button>
                          <button
                            onClick={() => submitChunkFeedback(chunk.chunk_id, chunk.document_id, 'neutral')}
                            className="flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-300 rounded-lg transition-colors"
                            title="Chunk ist weder besonders relevant noch irrelevant"
                          >
                            <Info className="w-4 h-4 text-gray-600" />
                            <span className="text-sm font-medium text-gray-700">Neutral</span>
                          </button>
                        </div>
                        <p className="text-xs text-gray-500">
                          Bewerte diesen Chunk, um die Suche zu verbessern. Dein Feedback hilft dem System, relevantere Ergebnisse zu finden.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Link zum Dokument */}
                  <div className="flex items-center gap-2">
                    <a
                      href={`/documents/${chunk.document_id}?page=${chunk.page_number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Zum Dokument (Seite {chunk.page_number})
                    </a>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Zusammenfassung */}
      <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900 mb-2">Wie interpretiere ich diese Analyse?</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li><strong>Relevanz-Scores:</strong> Höhere Scores bedeuten, dass der Chunk semantisch ähnlicher zur Query ist.</li>
              <li><strong>Vector vs Text:</strong> Vector-Score misst semantische Ähnlichkeit, Text-Score misst Keyword-Übereinstimmung.</li>
              <li><strong>Seitenverlinkung:</strong> Prüfe, ob die verlinkte Seite tatsächlich den relevanten Inhalt enthält.</li>
              <li><strong>Multi-Page Chunks:</strong> Wenn ein Chunk mehrere Seiten umfasst, wird nur die erste Seite verlinkt. Dies könnte problematisch sein.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

