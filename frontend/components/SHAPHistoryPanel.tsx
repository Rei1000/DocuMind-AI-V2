/**
 * SHAP History Panel Component
 * 
 * Zeigt die Historie der SHAP-Erklärungen aus Training Data.
 * 
 * NEU v2.10.0
 */

'use client'

import { useState, useEffect } from 'react'
import { Calendar, MessageSquare, TrendingUp, Info, RefreshCw } from 'lucide-react'
import Tooltip from './ui/Tooltip'
import SHAPSummaryPlot from './SHAPSummaryPlot'

interface SHAPExplanationSummary {
  feature_names?: string[]
  feature_importance?: Record<string, number>
  shap_values?: number[]
}

interface SHAPHistoryEntry {
  id: number
  query: string
  chunk_id: string
  document_id: number
  created_at: string
  shap_explanation?: SHAPExplanationSummary
  user_feedback?: 'positive' | 'negative' | 'neutral'
  feedback_comment?: string
  hybrid_score: number
}

interface SHAPHistoryData {
  entries: SHAPHistoryEntry[]
  total: number
  has_more: boolean
}

interface SHAPHistoryPanelProps {
  query?: string
  chunkId?: string
  limit?: number
}

export default function SHAPHistoryPanel({ query, chunkId, limit = 50 }: SHAPHistoryPanelProps) {
  const [data, setData] = useState<SHAPHistoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedEntry, setSelectedEntry] = useState<SHAPHistoryEntry | null>(null)

  useEffect(() => {
    loadHistory()
  }, [query, chunkId, limit])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (query) params.append('query', query)
      if (chunkId) params.append('chunk_id', chunkId)
      params.append('limit', limit.toString())

      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/rag/analytics/shap/history?${params.toString()}`, { headers })
      if (!response.ok) throw new Error('Failed to load SHAP history')
      
      const historyData = await response.json()
      setData(historyData)
    } catch (error) {
      console.error('Error loading SHAP history:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('de-DE', { 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFeedbackColor = (feedback?: string) => {
    switch (feedback) {
      case 'positive': return 'text-green-600 bg-green-50 border-green-200'
      case 'negative': return 'text-red-600 bg-red-50 border-red-200'
      case 'neutral': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Lade SHAP-Historie...</span>
      </div>
    )
  }

  if (!data || data.entries.length === 0) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900 mb-2">Keine SHAP-Historie verfügbar</h3>
            <p className="text-sm text-blue-800 mb-3">
              Es wurden noch keine SHAP-Daten in der Datenbank gespeichert.
            </p>
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <p className="text-sm text-gray-700 mb-2 font-semibold">
                So sammelst du SHAP-Historie:
              </p>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                <li>Stelle Fragen im RAG Chat</li>
                <li>Das System berechnet automatisch SHAP-Erklärungen</li>
                <li>Die Daten werden in der Datenbank gespeichert</li>
                <li>Nach mehreren Fragen siehst du hier die Historie</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Calendar className="w-7 h-7 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">SHAP-Historie</h2>
          <Tooltip
            icon
            content={
              <div className="space-y-2">
                <p className="font-semibold">SHAP-Historie</p>
                <p className="text-xs">
                  Zeigt alle gespeicherten SHAP-Erklärungen aus der Datenbank.
                  Klicke auf einen Eintrag, um Details zu sehen.
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  <strong>Gesamt:</strong> {data.total} Einträge
                </p>
              </div>
            }
          />
        </div>
        <button
          onClick={loadHistory}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Aktualisieren
        </button>
      </div>

      {/* Einträge-Liste */}
      <div className="space-y-3">
        {data.entries.map((entry) => (
          <div
            key={entry.id}
            className={`bg-white rounded-lg border-2 p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedEntry?.id === entry.id ? 'border-blue-500 shadow-md' : 'border-gray-200'
            }`}
            onClick={() => setSelectedEntry(selectedEntry?.id === entry.id ? null : entry)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <MessageSquare className="w-5 h-5 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900 line-clamp-1">
                    &quot;{entry.query}&quot;
                  </span>
                  {entry.user_feedback && (
                    <span className={`px-2 py-1 rounded text-xs font-semibold border ${getFeedbackColor(entry.user_feedback)}`}>
                      {entry.user_feedback === 'positive' ? '👍' : entry.user_feedback === 'negative' ? '👎' : '➖'} {entry.user_feedback}
                    </span>
                  )}
                </div>
                {/* Kommentar anzeigen falls vorhanden */}
                {entry.feedback_comment && (
                  <div className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700">
                    <span className="font-medium">Kommentar:</span> {entry.feedback_comment}
                  </div>
                )}
                {/* NEU: Zeige wichtigste Feature-Namen (falls vorhanden) */}
                {entry.shap_explanation?.feature_names && entry.shap_explanation.feature_names.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {entry.shap_explanation.feature_names.slice(0, 3).map((featureName: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium border border-blue-200"
                        title={`Feature: ${featureName}`}
                      >
                        {featureName.length > 20 ? `${featureName.substring(0, 20)}...` : featureName}
                      </span>
                    ))}
                    {entry.shap_explanation.feature_names.length > 3 && (
                      <span className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs">
                        +{entry.shap_explanation.feature_names.length - 3} weitere
                      </span>
                    )}
                  </div>
                )}
                {/* Fallback: Zeige Feature-Namen aus feature_importance.keys() wenn feature_names fehlt */}
                {(() => {
                  const featureNames = entry.shap_explanation?.feature_names
                  const importance = entry.shap_explanation?.feature_importance
                  if (featureNames && featureNames.length > 0) return null
                  if (!importance) return null
                  const keys = Object.keys(importance)
                  if (keys.length === 0) return null

                  const topKeys = keys
                    .sort((a, b) => Math.abs(importance[b] ?? 0) - Math.abs(importance[a] ?? 0))
                    .slice(0, 3)

                  return (
                    <div className="flex flex-wrap gap-2 mb-2">
                      {topKeys.map((featureName: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium border border-blue-200"
                          title={`Feature: ${featureName} (Impact: ${(((importance[featureName] ?? 0) as number) * 100).toFixed(1)}%)`}
                        >
                          {featureName.length > 20 ? `${featureName.substring(0, 20)}...` : featureName}
                        </span>
                      ))}
                      {keys.length > 3 && (
                        <span className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs">
                          +{keys.length - 3} weitere
                        </span>
                      )}
                    </div>
                  )
                })()}
                <div className="flex items-center gap-4 text-xs text-gray-600">
                  <span>Chunk: {entry.chunk_id.substring(0, 20)}...</span>
                  <span>Score: {(entry.hybrid_score * 100).toFixed(1)}%</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(entry.created_at)}
                  </span>
                </div>
              </div>
              <TrendingUp className={`w-5 h-5 text-gray-400 transition-transform ${selectedEntry?.id === entry.id ? 'rotate-180' : ''}`} />
            </div>

            {/* Erweiterte Details (wenn ausgewählt) */}
            {selectedEntry?.id === entry.id && entry.shap_explanation && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <SHAPSummaryPlot
                  shapData={{
                    feature_importance: entry.shap_explanation.feature_importance,
                    shap_values: entry.shap_explanation.shap_values,
                    feature_names: entry.shap_explanation.feature_names
                  }}
                  title={`SHAP-Analyse für diese Query`}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Info */}
      {data.has_more && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
          <p className="text-sm text-blue-800">
            Es gibt weitere Einträge. Erhöhe das Limit, um mehr zu sehen.
          </p>
        </div>
      )}
    </div>
  )
}

