/**
 * RAG Analytics Dashboard - v2.9.3
 * 
 * WICHTIG: Diese Seite macht KEINE API-Requests!
 * Sie zeigt nur die Analytics-Daten der letzten Chat-Anfrage.
 * 
 * Datenfluss:
 * 1. User stellt Frage im Chat
 * 2. POST /api/rag/chat/ask liefert response.analytics
 * 3. Chat speichert analytics in localStorage
 * 4. Diese Seite liest analytics aus localStorage
 * 5. Visualisierung der Daten
 * 
 * KEINE FAKE-DATEN - Nur echte RAG-Pipeline-Daten!
 * 
 * NEU v2.9.0:
 * - Search Quality Metrics (Precision@k, Recall@k, NDCG@k, MRR)
 * - Hybrid vs ML Ranking Vergleich
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { BarChart3, MessageSquare, AlertCircle, TrendingUp, Zap, Calendar, Info, Settings, Layers } from 'lucide-react'

// Importiere Komponenten
import ScoreOverviewCard from '@/components/ScoreOverviewCard'
import SHAPComparisonPanel from '@/components/SHAPComparisonPanel'
import ModelInfoCard from '@/components/ModelInfoCard'
import CacheStatsCard from '@/components/CacheStatsCard'
import BackgroundStatsCard from '@/components/BackgroundStatsCard'
import SearchQualityMetricsPanel from '@/components/SearchQualityMetricsPanel'
// import SearchQualityDebugPanel from '@/components/SearchQualityDebugPanel'  // NEU v2.10.3: Nicht mehr verwendet
import ScoreCharts from '@/components/ScoreCharts'
import ChunkAnalysisPanel from '@/components/ChunkAnalysisPanel'
import SHAPBarChart from '@/components/SHAPBarChart'
import SHAPWaterfallChartImproved from '@/components/SHAPWaterfallChartImproved'
import SHAPBeeswarmPlot from '@/components/SHAPBeeswarmPlot'
import SHAPDependencePlot from '@/components/SHAPDependencePlot'
import SHAPSummaryPlot from '@/components/SHAPSummaryPlot'
import SHAPHistoryPanel from '@/components/SHAPHistoryPanel'
import AnalyticsOnboarding from '@/components/AnalyticsOnboarding'
import AutomatedInsightsPanel from '@/components/AutomatedInsightsPanel'
import AnalyticsExport from '@/components/AnalyticsExport'
import AnalyticsAuditTrail from '@/components/AnalyticsAuditTrail'
import Tooltip from '@/components/ui/Tooltip'
import AnalyticsStoryMode from '@/components/AnalyticsStoryMode'

interface AnalyticsData {
  query?: string  // NEU v2.9.0: Query prominent speichern
  scores: AnalyticsScore[]
  background_data_stats: any
  cache_stats: any
  model_info: any
  search_quality_metrics?: SearchQualityMetricsResponse  // NEU v2.9.0: Search Quality Metrics
  message_id?: number  // NEU: Message-ID für Feedback-Prüfung
}

interface SearchQualityMetricsResponse {
  query: string
  timestamp: string

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

  session_id?: number | null
  user_id?: number | null
  document_type?: string | null

  /** Chat-Message-ID (assistant) der für diese Metriken verwendet wurde. */
  message_id?: number

  filters_applied?: Record<string, unknown> | null
  score_threshold?: number | null
  top_k_limit?: number | null
  feedback_coverage?: number | null

  // AI-Modell-Einstellungen (optional)
  temperature?: number | null
  max_tokens?: number | null
  top_p?: number | null

  normalized_relevance_scores?: Record<string, number>
}

interface AnalyticsExtendedMetadata {
  query?: string
  document_id?: number
  document_title?: string
  page_number?: number
  page_numbers?: number[]
  text_excerpt?: string
  chunk_metadata?: unknown
  feedback_rating?: 'positive' | 'negative' | 'neutral' | null
  referenced_in_rag_answer?: boolean
  rag_reference_position?: number | null
  relevance_score?: number
  normalized_relevance_score?: number
  chunk_text_source?: string
  chunk_text_length?: number
  query_term_matches?: number
  query_match_ratio?: number
  chunk_text?: string
  chunk_text_db?: string
  shap_explanation?: unknown
  [key: string]: unknown
}

interface AnalyticsScore {
  chunk_id: string
  vector_score?: number
  text_score?: number
  hybrid_score?: number
  ml_score?: number
  ml_score_raw?: number
  final_score?: number
  rank_position?: number
  _extended_metadata?: AnalyticsExtendedMetadata
}

type FeedbackRating = 'positive' | 'negative' | 'neutral'

const isFeedbackRating = (v: unknown): v is FeedbackRating => {
  return v === 'positive' || v === 'negative' || v === 'neutral'
}

const asRecord = (v: unknown): Record<string, unknown> | undefined => {
  if (!v || typeof v !== 'object' || Array.isArray(v)) return undefined
  return v as Record<string, unknown>
}

type SHAPExplanation = {
  feature_importance: Record<string, number>
  base_value: number
  prediction: number
  shap_values: number[]
  feature_names: string[]
}

const asShapExplanation = (v: unknown): SHAPExplanation | undefined => {
  if (!v || typeof v !== 'object') return undefined
  const o = v as Record<string, unknown>
  const base_value = o.base_value
  const prediction = o.prediction
  const feature_importance = o.feature_importance
  const shap_values = o.shap_values
  const feature_names = o.feature_names

  if (typeof base_value !== 'number' || !Number.isFinite(base_value)) return undefined
  if (typeof prediction !== 'number' || !Number.isFinite(prediction)) return undefined
  if (!feature_importance || typeof feature_importance !== 'object' || Array.isArray(feature_importance)) return undefined
  if (!Array.isArray(shap_values) || !Array.isArray(feature_names)) return undefined

  const fi: Record<string, number> = {}
  for (const [k, val] of Object.entries(feature_importance as Record<string, unknown>)) {
    if (typeof val === 'number' && Number.isFinite(val)) fi[k] = val
  }

  const sv = (shap_values as unknown[]).filter((x): x is number => typeof x === 'number' && Number.isFinite(x))
  const fn = (feature_names as unknown[]).filter((x): x is string => typeof x === 'string')
  if (!sv.length || !fn.length) return undefined

  return {
    feature_importance: fi,
    base_value,
    prediction,
    shap_values: sv,
    feature_names: fn
  }
}

interface LiveModelInfoResponse {
  enabled: boolean
  ready: boolean
  model_path: string
  model_exists: boolean
  model_info: {
    model_type: string
    model_version: string
    model_path: string
    is_ready: boolean
    hybrid_weight: number
    ml_weight: number
    feature_names: string[]
  }
  feature_names: string[]
  training_data_stats: Record<string, unknown>
}

// NEU v2.10.7: Multi-Faktor Relevanz-Bewertung (Lösung 4)
interface RelevanceResult {
  is_relevant: boolean
  relevance_reason: string
}

interface ChunkForRelevance {
  chunk_id: string
  rank_position: number
  hybrid_score: number
  feedback_rating?: 'positive' | 'negative' | 'neutral' | null
  referenced_in_rag_answer?: boolean
  rag_reference_position?: number | null
}

/**
 * Berechnet Relevanz-Bewertung basierend auf Multi-Faktor-Ansatz (Lösung 4).
 * 
 * Priorität:
 * 1. Explizites Feedback (höchste Priorität)
 * 2. RAG-Antwort-Referenz (Ground Truth)
 * 3. Top-K Ranking (relative Relevanz)
 * 4. Absoluter Threshold (Fallback)
 */
function calculateRelevance(
  chunk: ChunkForRelevance,
  allChunks: ChunkForRelevance[]
): RelevanceResult {
  // 1. Explizites Feedback (höchste Priorität)
  if (chunk.feedback_rating === 'positive') {
    return { 
      is_relevant: true, 
      relevance_reason: 'Explizites positives Feedback' 
    }
  }
  if (chunk.feedback_rating === 'negative') {
    return { 
      is_relevant: false, 
      relevance_reason: 'Explizites negatives Feedback' 
    }
  }
  
  // 2. RAG-Antwort-Referenz (Ground Truth)
  if (chunk.referenced_in_rag_answer) {
    const position = chunk.rag_reference_position || chunk.rank_position
    return { 
      is_relevant: true, 
      relevance_reason: `Referenziert in RAG-Antwort (Rang ${position})` 
    }
  }
  
  // 3. Top-K Ranking (relative Relevanz)
  const topK = 3
  if (chunk.rank_position <= topK) {
    const topKScores = allChunks
      .filter(c => c.rank_position <= topK)
      .map(c => c.hybrid_score || 0)
      .sort((a, b) => b - a)
    const medianTopK = topKScores.length > 0 
      ? topKScores[Math.floor(topKScores.length / 2)] 
      : 0.5
    const relativeThreshold = Math.max(0.35, medianTopK * 0.7)
    
    if (chunk.hybrid_score >= relativeThreshold) {
      return { 
        is_relevant: true, 
        relevance_reason: `Top-${topK} Ranking (Rang ${chunk.rank_position}, Score ${(chunk.hybrid_score * 100).toFixed(1)}% >= ${(relativeThreshold * 100).toFixed(1)}%)` 
      }
    }
  }
  
  // 4. Absoluter Threshold (Fallback)
  const absoluteThreshold = 0.4  // 40%
  if (chunk.hybrid_score >= absoluteThreshold) {
    return { 
      is_relevant: true, 
      relevance_reason: `Absoluter Threshold (Score ${(chunk.hybrid_score * 100).toFixed(1)}% >= ${(absoluteThreshold * 100).toFixed(1)}%)` 
    }
  }
  
  return { 
    is_relevant: false, 
    relevance_reason: `Score ${(chunk.hybrid_score * 100).toFixed(1)}% < absoluter Threshold ${(absoluteThreshold * 100).toFixed(1)}%` 
  }
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMetrics, setLoadingMetrics] = useState(false)
  const [liveModelInfo, setLiveModelInfo] = useState<LiveModelInfoResponse | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'scores' | 'shap' | 'system'>('overview')
  const [viewMode, setViewMode] = useState<'simple' | 'pro'>('simple')
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const router = useRouter()

  // NEU v2.10.5: Authentifizierungsprüfung - Analytics-Seite nur für eingeloggte User
  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
      setIsCheckingAuth(false)
    } else {
      // Nicht eingeloggt, weiterleiten zur Login-Seite
      setIsCheckingAuth(false)
      router.push('/login')
    }
  }, [router])

  useEffect(() => {
    // Nur laden wenn eingeloggt
    if (!isLoggedIn || isCheckingAuth) {
      return
    }

    // Prüfe ob Onboarding bereits abgeschlossen wurde
    const onboardingCompleted = localStorage.getItem('analytics_onboarding_completed')
    if (!onboardingCompleted && analytics) {
      // Zeige Onboarding nur wenn Analytics-Daten vorhanden sind
      setShowOnboarding(true)
    }

    // Lade Analytics-Daten aus localStorage (vom Chat gespeichert)
    // NEU v2.10.3: Nur einmal beim Laden, nicht kontinuierlich (verhindert ständiges Ein-/Ausblenden)
    loadAnalyticsFromStorage()
  }, [isLoggedIn, isCheckingAuth])

  // NEU: Lade ML Model Info live (damit System-Tab nicht von storedAnalytics-Fallbacks abhängt)
  useEffect(() => {
    if (!isLoggedIn || isCheckingAuth) return

    const loadLiveModelInfo = async () => {
      try {
        const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
        const headers: HeadersInit = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch('/api/rag/ml/model-info', { headers })
        if (!response.ok) return

        const data = await response.json()
        setLiveModelInfo(data)
      } catch {
        // ignore
      }
    }

    loadLiveModelInfo()
  }, [isLoggedIn, isCheckingAuth])

  // NEU v2.10.3: Konsolidierter useEffect - lade Metriken einmalig, wenn Query vorhanden ist
  // Verhindert mehrfache Aufrufe und ständiges Ein-/Ausblenden
  useEffect(() => {
    // Nur laden, wenn:
    // 1. Query vorhanden ist
    // 2. Metriken noch nicht geladen wurden
    // 3. Nicht bereits am Laden
    // Lade Metriken auch dann, wenn message_id fehlt (wichtig für Chunk-Feedback in Analytics/Scores).
    if (analytics?.query && (!analytics?.search_quality_metrics || !analytics?.message_id) && !loadingMetrics) {
      loadMetricsForQuery(analytics.query)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analytics?.query])  // Nur auf Query-Änderung reagieren, nicht auf search_quality_metrics

  // NEU v2.10.3: Event-basierte Metriken-Aktualisierung (statt Polling)
  // Höre auf Feedback-Events und lade Metriken automatisch neu
  useEffect(() => {
    const handleFeedbackSubmitted = (event: CustomEvent) => {
      const { messageId: feedbackMessageId } = event.detail
      
      // Nur neu laden, wenn Feedback für die aktuelle Query gegeben wurde
      if (analytics?.message_id === feedbackMessageId && analytics?.query && !loadingMetrics) {
        console.log('Feedback submitted, reloading metrics for query:', analytics.query)
        loadMetricsForQuery(analytics.query)
      }
    }
    
    window.addEventListener('feedbackSubmitted', handleFeedbackSubmitted as EventListener)
    
    return () => {
      window.removeEventListener('feedbackSubmitted', handleFeedbackSubmitted as EventListener)
    }
  }, [analytics?.message_id, analytics?.query, loadingMetrics])

  const loadAnalyticsFromStorage = () => {
    try {
      // WICHTIG: Analytics-Daten kommen aus dem Chat, nicht von API!
      const storedAnalytics = localStorage.getItem('lastAnalytics')
      
      if (storedAnalytics) {
        const data = JSON.parse(storedAnalytics)
        setAnalytics(data)
      } else {
        setAnalytics(null)
      }
    } catch (error) {
      console.error('Failed to load analytics from storage:', error)
      setAnalytics(null)
    } finally {
      setLoading(false)
    }
  }

  // NEU: Lade Metriken vom Backend, wenn Feedback vorhanden ist
  const loadMetricsForQuery = async (query: string) => {
    if (loadingMetrics) return  // Verhindere mehrfache Requests
    
    try {
      setLoadingMetrics(true)
      
      // Hole Token für Authentifizierung
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      // NEU v2.10.1: Hole auch Chunk-Level Feedback und merge es in analytics.scores
      const messageId = analytics?.message_id
      if (messageId && analytics?.scores) {
        try {
          // Hole Chunk-Level Feedback für alle Chunks
          const chunkFeedbackMap: Record<string, FeedbackRating> = {}
          for (const score of analytics.scores) {
            const chunkId = score.chunk_id
            if (chunkId) {
              const feedbackResponse = await fetch(
                `/api/rag/chat/chunks/${encodeURIComponent(chunkId)}/feedback?chat_message_id=${messageId}`,
                { headers }
              )
              if (feedbackResponse.ok) {
                const feedbacks = await feedbackResponse.json()
                if (feedbacks && feedbacks.length > 0) {
                  const rating = feedbacks?.[0]?.rating
                  if (isFeedbackRating(rating)) {
                    chunkFeedbackMap[chunkId] = rating
                  }
                }
              }
            }
          }
          
          // Hole Message-Level Feedback
          let messageFeedback: FeedbackRating | null = null
          if (messageId) {
            const messageFeedbackResponse = await fetch(
              `/api/rag/chat/messages/${messageId}/feedback`,
              { headers }
            )
            if (messageFeedbackResponse.ok) {
              const messageFeedbacks = await messageFeedbackResponse.json()
              if (messageFeedbacks && messageFeedbacks.length > 0) {
                const rating = messageFeedbacks?.[0]?.rating
                messageFeedback = isFeedbackRating(rating) ? rating : null
              }
            }
          }
          
          // Merge Feedback in analytics.scores (immutable, typ-sicher)
          const updatedScores = analytics.scores.map((score: AnalyticsScore) => {
            const chunkId = score.chunk_id
            const feedbackRating: FeedbackRating | null = chunkFeedbackMap[chunkId] ?? messageFeedback ?? null

            if (!feedbackRating) {
              return score
            }

            return {
              ...score,
              _extended_metadata: {
                ...(score._extended_metadata ?? {}),
                feedback_rating: feedbackRating
              }
            }
          })
          
          // Aktualisiere analytics mit Feedback
          setAnalytics({
            ...analytics,
            scores: updatedScores
          })
        } catch (error) {
          console.error('Fehler beim Laden von Feedback:', error)
        }
      }

      // Rufe den /analytics/search-quality Endpoint auf
      const response = await fetch(`/api/rag/analytics/search-quality?query=${encodeURIComponent(query)}`, { headers })
      
      if (!response.ok) {
        if (response.status === 404) {
          // Keine Metriken gefunden (kein Feedback vorhanden) - das ist OK
          console.log('No metrics found for query (no feedback yet):', query)
          return
        }
        throw new Error(`Failed to load metrics: ${response.status}`)
      }
      
      const metrics: SearchQualityMetricsResponse = await response.json()
      
      // Aktualisiere Analytics-Daten mit Metriken
      // NEU v2.10.3: Nur aktualisieren, wenn Metriken sich geändert haben (verhindert unnötige Re-Renders)
      setAnalytics((prevAnalytics) => {
        if (!prevAnalytics) return prevAnalytics
        
        // Prüfe, ob Metriken sich geändert haben
        // WICHTIG: Wenn message_id fehlt, dürfen wir NICHT early-returnen, sonst bleibt Chunk-Feedback kaputt.
        const prevMetrics = prevAnalytics.search_quality_metrics
        const nextMessageId = prevAnalytics.message_id ?? metrics.message_id
        if (
          prevMetrics &&
          prevMetrics.precision_at_10 === metrics.precision_at_10 &&
          prevMetrics.recall_at_10 === metrics.recall_at_10 &&
          prevMetrics.ndcg_at_10 === metrics.ndcg_at_10 &&
          prevMetrics.mrr === metrics.mrr &&
          prevAnalytics.message_id === nextMessageId
        ) {
          // Metriken haben sich nicht geändert (inkl. message_id) - kein Update nötig
          return prevAnalytics
        }
        
        // NEU v2.10.4: Integriere normalisierte Scores aus Metriken in analytics.scores
        // Die normalisierten Scores werden als Mapping (chunk_id -> score) zurückgegeben
        const normalizedScores = metrics.normalized_relevance_scores || {}
        const updatedScores = prevAnalytics.scores?.map((score: AnalyticsScore) => {
          const chunkId = score.chunk_id
          const normalizedScore = normalizedScores[chunkId]
          if (normalizedScore === undefined) {
            return score
          }
          return {
            ...score,
            _extended_metadata: {
              ...(score._extended_metadata ?? {}),
              normalized_relevance_score: normalizedScore
            }
          }
        }) || prevAnalytics.scores
        
        const updatedAnalytics = {
          ...prevAnalytics,
          // Falls `lastAnalytics` aus dem Chat keine message_id enthielt, übernehmen wir sie von diesem Endpoint.
          message_id: prevAnalytics.message_id ?? metrics.message_id,
          search_quality_metrics: metrics,
          scores: updatedScores
        }
        
        // Speichere aktualisierte Analytics in localStorage
        localStorage.setItem('lastAnalytics', JSON.stringify(updatedAnalytics))
        
        console.log('Metrics loaded and saved with normalized scores:', metrics)
        return updatedAnalytics
      })
    } catch (error) {
      console.error('Error loading metrics:', error)
      // Fehler ist nicht kritisch - Metriken werden einfach nicht angezeigt
    } finally {
      setLoadingMetrics(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-pulse text-gray-400">
            <BarChart3 className="w-16 h-16 mx-auto mb-4" />
          </div>
          <p className="text-gray-600">Prüfe Analytics-Daten...</p>
        </div>
      </div>
    )
  }

  // Falls keine Analytics-Daten vorhanden
  if (!analytics) {
    return (
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
            <BarChart3 className="w-10 h-10 text-blue-600" />
            Analytics Dashboard
            <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
              v2.7.0
            </span>
          </h1>
          <p className="text-gray-600 text-lg">
            Noch keine Daten • Stelle eine Frage im RAG Chat, damit hier erklärt werden kann, warum etwas oben ist.
          </p>
        </div>

        <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-8">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-8 h-8 text-yellow-700 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-yellow-900">Keine Analytics-Daten verfügbar</h2>
              <p className="text-sm text-yellow-900 mt-2">
                Dieses Dashboard erklärt dir die <strong>letzte</strong> RAG‑Suche. Stelle zuerst eine Frage im RAG Chat,
                dann komm hierher zurück.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  onClick={() => router.push('/rag-chat')}
                  className="px-5 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Zum RAG Chat
                </button>
                <button
                  onClick={() => router.push('/trends')}
                  className="px-5 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors"
                >
                  Trend-Analyse
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">Kurz erklärt</h3>
              <p className="text-sm text-blue-800">
                Stelle im Chat eine Frage → die Antwort enthält Analytics → hier wird daraus eine verständliche Erklärung gebaut.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Falls Analytics-Daten vorhanden - Visualisierung
  return (
    <div className="relative">
      {/* Onboarding Tour */}
      {showOnboarding && (
        <AnalyticsOnboarding onComplete={() => setShowOnboarding(false)} />
      )}

      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
              <BarChart3 className="w-10 h-10 text-blue-600" />
              Analytics Dashboard
              <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
                v2.9.3
              </span>
            </h1>
            <p className="text-gray-600 text-lg">
              Analytics der letzten Chat-Anfrage • {analytics.scores?.length || 0} Chunks analysiert
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-1">
            <button
              type="button"
              onClick={() => {
                setViewMode('simple')
                setActiveTab('overview')
              }}
              className={`px-3 py-2 rounded-md text-sm font-semibold transition-colors ${
                viewMode === 'simple' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              Einfach erklärt
            </button>
            <button
              type="button"
              onClick={() => setViewMode('pro')}
              className={`px-3 py-2 rounded-md text-sm font-semibold transition-colors ${
                viewMode === 'pro' ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              Pro / Details
            </button>
          </div>
        </div>
        
        {/* NEU v2.10.3: "Bewertete Frage" entfernt - wird bereits in SearchQualityMetricsPanel angezeigt */}
      </div>

      {/* Status-Badge: Daten werden gesammelt */}
      {analytics.query && !analytics.search_quality_metrics && (
        <div className="mb-6 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
          <div className="flex items-start gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mt-0.5"></div>
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">Daten werden gesammelt...</h3>
              <p className="text-sm text-blue-800">
                Die Metriken werden automatisch berechnet. Falls du Feedback gegeben hast, werden die Metriken 
                basierend darauf berechnet. Ansonsten werden die Scores der Suchergebnisse verwendet.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State für Metriken */}
      {loadingMetrics && (
        <div className="mb-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
            <span className="text-sm text-gray-700">Lade Metriken...</span>
          </div>
        </div>
      )}

      {/* NEU v2.10.3: QuickSummaryCard entfernt - Metriken werden bereits in SearchQualityMetricsPanel angezeigt (verhindert doppelte Anzeige) */}
      {/* Info: Feedback-Status wird jetzt in SearchQualityMetricsPanel angezeigt */}

      {/* Simple Mode: Story statt Tabs */}
      {viewMode === 'simple' && (
        <AnalyticsStoryMode
          query={analytics.query || analytics.scores?.[0]?._extended_metadata?.query || 'Unbekannte Frage'}
          scores={analytics.scores}
          liveModelInfo={liveModelInfo}
          onGoChat={() => router.push('/rag-chat')}
          onShowDetails={() => setViewMode('pro')}
          onShowShap={() => {
            setViewMode('pro')
            setActiveTab('shap')
          }}
        />
      )}

      {/* Pro Mode: Tabs */}
      {viewMode === 'pro' && (
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Übersicht
              </div>
            </button>
            <button
              onClick={() => setActiveTab('scores')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'scores'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Scores
              </div>
            </button>
            <button
              onClick={() => setActiveTab('shap')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'shap'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                SHAP
              </div>
            </button>
            <button
              onClick={() => setActiveTab('system')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'system'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                System
              </div>
            </button>
          </nav>
        </div>
      )}

      {/* Tab Content */}
      {viewMode === 'pro' && (
        <>
          <div className="mt-6">
        {/* Tab 1: Übersicht */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Info Box */}
            <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-900 mb-2">Wie funktioniert das Analytics Dashboard?</h3>
                  <p className="text-sm text-blue-800 mb-2">
                    Dieses Dashboard zeigt <strong>automatisch</strong> die Analytics-Daten deiner letzten RAG-Chat-Anfrage.
                    Die Daten werden vom Chat gespeichert und hier visualisiert.
                  </p>
                  <p className="text-sm text-blue-800">
                    <strong>Wichtig:</strong> Stelle eine neue Frage im Chat, um die Analytics zu aktualisieren.
                    Diese Seite macht keine eigenen API-Requests!
                  </p>
                </div>
              </div>
            </div>

            {/* Search Quality Metrics */}
            {analytics.search_quality_metrics ? (
              <div className="space-y-6">
                <SearchQualityMetricsPanel
                  metrics={analytics.search_quality_metrics}
                  query={analytics.query || analytics.scores?.[0]?._extended_metadata?.query || 'Unbekannte Query'}
                />
              </div>
            ) : null}

            {/* Automatische Insights */}
            <details className="bg-white rounded-xl border border-gray-200 p-4">
              <summary className="cursor-pointer select-none font-semibold text-gray-900">
                Automatische Hinweise (optional)
              </summary>
              <div className="mt-4">
                <AutomatedInsightsPanel
                  metrics={analytics.search_quality_metrics}
                  scores={analytics.scores.map(s => ({
                    hybrid_score: s.hybrid_score ?? 0,
                    vector_score: s.vector_score ?? 0,
                    text_score: s.text_score ?? 0
                  }))}
                  query={analytics.query}
                />
              </div>
            </details>

            {/* NEU v2.10.4: Audit Trail - Nachvollziehbar & Transparent */}
            <details className="bg-white rounded-xl border border-gray-200 p-4">
              <summary className="cursor-pointer select-none font-semibold text-gray-900">
                Audit Trail (Details)
              </summary>
              <div className="mt-4">
                <AnalyticsAuditTrail
                  analytics={analytics}
                  searchQualityMetrics={analytics.search_quality_metrics}
                />
              </div>
            </details>
          </div>
        )}

        {/* Tab 2: Detaillierte Scores */}
        {activeTab === 'scores' && (
          <div className="space-y-8">
            {/* Interaktive Charts */}
            {analytics.scores && analytics.scores.length > 0 && (
              <div>
                <ScoreCharts
                  scores={analytics.scores.map((s: AnalyticsScore, index: number) => ({
                    chunk_id: s.chunk_id || '',
                    rank_position: s.rank_position || index + 1,
                    vector_score: s.vector_score || 0,
                    text_score: s.text_score || 0,
                    hybrid_score: s.hybrid_score || 0,
                    ml_score: s.ml_score,
                    ml_score_raw: s.ml_score_raw,
                    final_score: s.final_score
                  }))}
                />
              </div>
            )}

            {/* Score Overview Cards */}
            {analytics.scores && analytics.scores.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <Zap className="w-7 h-7 text-blue-600" />
                  <h2 className="text-2xl font-bold text-gray-900">Score Overview Cards</h2>
                  <Tooltip
                    icon
                    content={
                      <div className="space-y-2">
                        <p className="font-semibold">Score Overview</p>
                        <p className="text-xs">
                          Zeigt die verschiedenen Scores für jedes Suchergebnis:
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                          <li><strong>Vector Score:</strong> Semantische Ähnlichkeit (Embedding-basiert)</li>
                          <li><strong>Text Score:</strong> Keyword-Matching (BM25/Jaccard)</li>
                          <li><strong>Hybrid Score:</strong> Kombination aus Vector + Text (70% + 30%)</li>
                          <li><strong>ML Score:</strong> Machine-Learning-basierter Score (falls aktiviert)</li>
                          <li><strong>Final Score:</strong> Finale Kombination für Ranking</li>
                        </ul>
                        <p className="text-xs text-gray-300 mt-2">
                          Höhere Scores = relevantere Ergebnisse. Die Ergebnisse sind nach Final Score sortiert.
                        </p>
                      </div>
                    }
                  />
                </div>
                
                {/* ML Normalisierung: Min/Max der Rohwerte (für "So entsteht der Wert") */}
                {(() => {
                  const rawValues = analytics.scores
                    .map(s => s.ml_score_raw)
                    .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
                  const mlRawMin = rawValues.length > 0 ? Math.min(...rawValues) : undefined
                  const mlRawMax = rawValues.length > 0 ? Math.max(...rawValues) : undefined
                  const hybridWeight = liveModelInfo?.model_info?.hybrid_weight
                    ?? analytics.model_info?.hybrid_weight
                    ?? 0.6
                  const mlWeight = liveModelInfo?.model_info?.ml_weight
                    ?? analytics.model_info?.ml_weight
                    ?? 0.4

                  return (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {analytics.scores.slice(0, 9).map((score: AnalyticsScore) => (
                    <ScoreOverviewCard
                      key={score.chunk_id}
                      vectorScore={score.vector_score || 0}
                      textScore={score.text_score || 0}
                      hybridScore={score.hybrid_score || 0}
                      mlScore={score.ml_score}
                      mlScoreRaw={score.ml_score_raw}
                      mlRawMin={mlRawMin}
                      mlRawMax={mlRawMax}
                      hybridWeight={hybridWeight}
                      mlWeight={mlWeight}
                      finalScore={score.final_score}
                      rankPosition={score.rank_position || 1}
                    />
                  ))}
                </div>
                  )
                })()}
              </div>
            )}

            {/* NEU v2.10.4: Audit Trail auch in Detaillierte Scores */}
            {Boolean(analytics.search_quality_metrics) && (
              <div className="mb-8">
                <AnalyticsAuditTrail
                  analytics={analytics}
                  searchQualityMetrics={analytics.search_quality_metrics}
                />
              </div>
            )}

            {/* Chunk-Analyse (NEU) - Zeigt detaillierte Chunk-Informationen */}
            {analytics.query && analytics.scores && analytics.scores.length > 0 && (
              <details className="bg-white rounded-xl border border-gray-200 p-4">
                <summary className="cursor-pointer select-none font-semibold text-gray-900">
                  Chunk-Analyse (Details)
                </summary>
                <div className="mt-4">
                  {(() => {
                // NEU v2.10.7: Berechne Relevanz für alle Chunks (Multi-Faktor)
                const sortedScores = [...analytics.scores].sort(
                  (a: AnalyticsScore, b: AnalyticsScore) => (a.rank_position ?? 999) - (b.rank_position ?? 999)
                )
                
                const chunksForRelevance: ChunkForRelevance[] = sortedScores.map((score: AnalyticsScore, index: number) => ({
                  chunk_id: score.chunk_id || '',
                  rank_position: score.rank_position || index + 1,
                  hybrid_score: score.hybrid_score ?? score.final_score ?? 0.5,
                  feedback_rating: score._extended_metadata?.feedback_rating ?? null,
                  referenced_in_rag_answer: score._extended_metadata?.referenced_in_rag_answer ?? false,
                  rag_reference_position: score._extended_metadata?.rag_reference_position ?? null
                }))
                
                return (
                  <ChunkAnalysisPanel
                    query={analytics.query}
                    chunks={sortedScores.map((score: AnalyticsScore, index: number) => {
                      const chunkForRelevance = chunksForRelevance[index]
                      const relevance = calculateRelevance(chunkForRelevance, chunksForRelevance)
                      
                      return {
                        chunk_id: score.chunk_id || '',
                        document_id: score._extended_metadata?.document_id || 0,
                        document_title: score._extended_metadata?.document_title || 'Unbekanntes Dokument',
                        page_number: score._extended_metadata?.page_number || 1,
                        page_numbers: score._extended_metadata?.page_numbers || [score._extended_metadata?.page_number || 1],
                        // NEU v2.10.6: Verwende hybrid_score/final_score für Relevance (nicht normalisiert)
                        // Normalisierte Scores sind für Metriken, nicht für Ranking!
                        relevance_score: score._extended_metadata?.relevance_score || score.final_score || score.hybrid_score || score.vector_score || 0.5,
                        vector_score: score.vector_score,
                        text_score: score.text_score,
                        hybrid_score: score.hybrid_score,
                        ml_score: score.ml_score,
                        final_score: score.final_score,
                        rank_position: score.rank_position || 0,
                        text_excerpt: score._extended_metadata?.text_excerpt || score._extended_metadata?.chunk_text?.substring(0, 200),
                        chunk_metadata: asRecord(score._extended_metadata?.chunk_metadata),
                        feedback_rating: score._extended_metadata?.feedback_rating ?? undefined,
                        // NEU v2.10.7: Multi-Faktor Relevanz-Bewertung (Lösung 4)
                        is_relevant: relevance.is_relevant,
                        relevance_reason: relevance.relevance_reason,
                        referenced_in_rag_answer: score._extended_metadata?.referenced_in_rag_answer || false,
                        rag_reference_position: score._extended_metadata?.rag_reference_position || null,
                        // NEU v2.10.6: Speichere auch normalisierten Score für Vergleich
                        normalized_relevance_score: score._extended_metadata?.normalized_relevance_score
                      }
                    })}
                    messageId={analytics.message_id}
                  />
                )
                  })()}
                </div>
              </details>
            )}

            {/* Chunk Details Table */}
            {analytics.scores && analytics.scores.length > 0 && (
              <details className="bg-white rounded-xl border border-gray-200 p-4">
                <summary className="cursor-pointer select-none font-semibold text-gray-900">
                  Alle Chunks (Tabelle)
                </summary>
                <div className="mt-4">
                <div className="flex items-center gap-3 mb-6">
                  <Layers className="w-7 h-7 text-gray-600" />
                  <h2 className="text-2xl font-bold text-gray-900">Alle Chunks (Detailliert)</h2>
                  <Tooltip
                    icon
                    content={
                      <div className="space-y-2">
                        <p className="font-semibold">Chunk Details Table</p>
                        <p className="text-xs">
                          Detaillierte Übersicht aller Suchergebnisse (Chunks) mit ihren Scores.
                          Sortiert nach Final Score (beste zuerst).
                        </p>
                        <p className="text-xs">
                          <strong>Rank:</strong> Position im Ranking (1 = bestes Ergebnis)<br />
                          <strong>Chunk ID:</strong> Eindeutige Identifikation des Chunks<br />
                          <strong>Scores:</strong> Vector, Text, Hybrid, ML, Final Scores
                        </p>
                        <p className="text-xs text-gray-300 mt-2">
                          Diese Tabelle zeigt alle gefundenen Chunks, nicht nur die Top-Ergebnisse.
                        </p>
                      </div>
                    }
                  />
                </div>
                
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rank
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Chunk ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Vector
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Text
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Hybrid
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ML
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Final
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {analytics.scores.map((score: AnalyticsScore, index: number) => (
                        <tr key={score.chunk_id || index} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-lg font-bold text-gray-900">
                              #{score.rank_position || index + 1}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-700 font-mono">
                              {String(score.chunk_id).substring(0, 20)}...
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-blue-700 font-semibold">
                              {typeof score.vector_score === 'number' ? (score.vector_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-purple-700 font-semibold">
                              {typeof score.text_score === 'number' ? (score.text_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-indigo-700 font-semibold">
                              {typeof score.hybrid_score === 'number' ? (score.hybrid_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-green-700 font-bold">
                              {score.ml_score !== undefined && score.ml_score !== null
                                ? (score.ml_score * 100).toFixed(1) + '%'
                                : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-pink-700 font-bold">
                              {score.final_score ? (score.final_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                </div>
              </details>
            )}
          </div>
        )}

        {/* Tab 3: SHAP Analyse */}
        {activeTab === 'shap' && (
          <div className="space-y-8">
            {/* NEU v2.10.4: Audit Trail auch in SHAP Analyse */}
            {Boolean(analytics.search_quality_metrics) && (
              <div className="mb-8">
                <AnalyticsAuditTrail
                  analytics={analytics}
                  searchQualityMetrics={analytics.search_quality_metrics}
                />
              </div>
            )}

            {/* SHAP Comparison - PROMINENT */}
            {analytics.scores?.[0]?._extended_metadata &&
             (Boolean(asShapExplanation(analytics.scores[0]._extended_metadata.hybrid_shap)) ||
              Boolean(asShapExplanation(analytics.scores[0]._extended_metadata.ml_shap))) && (
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border-2 border-purple-200 p-6 shadow-lg">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="w-8 h-8 text-purple-600" />
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-900">SHAP Feature Importance</h2>
                    <p className="text-sm text-gray-600 mt-1">
                      Erklärt, welche Features zum Ranking-Score beitragen
                    </p>
                  </div>
                    <Tooltip
                      icon
                      content={
                        <div className="space-y-2 max-w-md">
                          <p className="font-semibold">Was ist SHAP?</p>
                          <p className="text-xs">
                            <strong>Einfach erklärt:</strong> SHAP zeigt dir, warum ein Suchergebnis oben oder unten steht.
                            Es erklärt, welche Faktoren zum Ranking beitragen.
                          </p>
                          <p className="text-xs">
                            <strong>Beispiel:</strong><br />
                            Wenn ein Ergebnis einen hohen Score hat, zeigt SHAP:
                            "Dieses Ergebnis steht oben, weil es viele passende Keywords hat (positiver Beitrag)
                            und die richtige Dokumentart ist (positiver Beitrag)."
                          </p>
                          <p className="text-xs">
                            <strong>Positive Werte (blau):</strong> Dieser Faktor macht das Ergebnis relevanter<br />
                            <strong>Negative Werte (rot):</strong> Dieser Faktor macht das Ergebnis weniger relevant
                          </p>
                          <p className="text-xs">
                            <strong>Was bedeuten die Features?</strong><br />
                            • <strong>vector_score:</strong> Wie ähnlich ist der Text zur Frage?<br />
                            • <strong>text_score:</strong> Wie viele Keywords wurden gefunden?<br />
                            • <strong>keyword_matches:</strong> Anzahl der übereinstimmenden Wörter<br />
                            • <strong>chunk_length:</strong> Länge des Text-Abschnitts<br />
                            • <strong>user_level:</strong> Dein Zugriffs-Level (1-5)
                          </p>
                        </div>
                      }
                    />
                </div>
                
                {/* SHAP Visualisierungen - Tabs für verschiedene Darstellungen */}
                {analytics.scores && analytics.scores.length > 0 && (
                  <div className="space-y-6">
                    {/* Top Chunk mit SHAP-Daten */}
                    {analytics.scores
                      .filter(score => score._extended_metadata?.shap_explanation)
                      .slice(0, 1) // Zeige nur Top Chunk
                      .map((score, index) => {
                        const rawShap = score._extended_metadata?.shap_explanation
                        if (!rawShap || typeof rawShap !== 'object') {
                          return null
                        }

                        const shapData = rawShap as {
                          base_value?: number
                          prediction?: number
                          feature_importance?: Record<string, unknown>
                          shap_values?: unknown
                          feature_names?: unknown
                        }

                        const rawFeatureImportance = shapData.feature_importance ?? {}
                        const featureImportance: Record<string, number> = {}
                        for (const [k, v] of Object.entries(rawFeatureImportance)) {
                          if (typeof v === 'number' && Number.isFinite(v)) {
                            featureImportance[k] = v
                          }
                        }

                        const shapValues: number[] = Array.isArray(shapData.shap_values)
                          ? (shapData.shap_values as unknown[]).filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
                          : []

                        const featureNames: string[] = Array.isArray(shapData.feature_names)
                          ? (shapData.feature_names as unknown[]).filter((v): v is string => typeof v === 'string')
                          : Object.keys(featureImportance)
                        
                        // Erstelle Features-Array für Bar Chart
                        const features = shapValues.length > 0 && featureNames.length === shapValues.length
                          ? featureNames.map((name: string, i: number) => ({
                              feature_name: name,
                              shap_value: shapValues[i]
                            }))
                          : Object.entries(featureImportance).map(([name, value]) => ({
                              feature_name: name,
                              shap_value: typeof value === 'number' ? value : 0
                            }))
                        
                        return (
                          <div key={index} className="space-y-6">
                            {/* Waterfall Plot */}
                            <SHAPWaterfallChartImproved
                              shapData={{
                                base_value: shapData.base_value,
                                prediction: shapData.prediction,
                                feature_importance: featureImportance,
                                shap_values: shapValues.length > 0 ? shapValues : undefined,
                                feature_names: featureNames.length > 0 ? featureNames : undefined
                              }}
                              title={`SHAP Waterfall Plot (Chunk #${score.rank_position || index + 1})`}
                            />
                            
                            {/* Beeswarm Plot */}
                            <SHAPBeeswarmPlot
                              shapData={{
                                feature_importance: featureImportance,
                                shap_values: shapValues.length > 0 ? shapValues : undefined,
                                feature_names: featureNames.length > 0 ? featureNames : undefined
                              }}
                              title={`SHAP Beeswarm Plot (Chunk #${score.rank_position || index + 1})`}
                            />
                            
                            {/* Summary Plot - Übersicht aller Features */}
                            <SHAPSummaryPlot
                              shapData={{
                                feature_importance: featureImportance,
                                shap_values: shapValues.length > 0 ? shapValues : undefined,
                                feature_names: featureNames.length > 0 ? featureNames : undefined
                              }}
                              title={`SHAP Summary Plot - Alle Features (Chunk #${score.rank_position || index + 1})`}
                            />
                            
                            {/* Beeswarm Plot */}
                            <SHAPBeeswarmPlot
                              shapData={{
                                feature_importance: featureImportance,
                                shap_values: shapValues.length > 0 ? shapValues : undefined,
                                feature_names: featureNames.length > 0 ? featureNames : undefined
                              }}
                              title={`SHAP Beeswarm Plot (Chunk #${score.rank_position || index + 1})`}
                            />
                            
                            {/* Dependence Plot */}
                            <SHAPDependencePlot
                              shapData={{
                                feature_importance: featureImportance,
                                shap_values: shapValues.length > 0 ? shapValues : undefined,
                                feature_names: featureNames.length > 0 ? featureNames : undefined
                              }}
                              title={`SHAP Dependence Plot (Chunk #${score.rank_position || index + 1})`}
                            />
                            
                            {/* Bar Chart - Detailliert */}
                            <SHAPBarChart
                              features={features}
                              title={`SHAP Feature Importance - Top Features (Chunk #${score.rank_position || index + 1})`}
                              maxFeatures={10}
                              query={analytics.query || analytics.scores[0]._extended_metadata?.query}
                              chunkText={
                                (typeof score._extended_metadata?.chunk_text === 'string'
                                  ? score._extended_metadata.chunk_text
                                  : undefined) ?? score._extended_metadata?.text_excerpt
                              }
                            />
                          </div>
                        )
                      })}
                  </div>
                )}

                <div className="bg-white rounded-lg p-4 border border-purple-200">
                  <SHAPComparisonPanel
                    hybridShap={asShapExplanation(analytics.scores[0]._extended_metadata?.hybrid_shap)}
                    mlShap={asShapExplanation(analytics.scores[0]._extended_metadata?.ml_shap)}
                    query={analytics.query || analytics.scores[0]._extended_metadata?.query || 'Unknown'}
                    chunkText={
                      (typeof analytics.scores[0]._extended_metadata?.chunk_text === 'string'
                        ? analytics.scores[0]._extended_metadata.chunk_text
                        : undefined) ?? analytics.scores[0]._extended_metadata?.text_excerpt
                    }
                    chunkMetadata={analytics.scores[0]._extended_metadata}
                  />
                </div>
              </div>
            )}
            
            {/* SHAP-Historie Panel */}
            <div className="mt-8">
              <SHAPHistoryPanel
                query={undefined}
                limit={50}
              />
            </div>
            
            {/* Fallback wenn keine SHAP-Daten */}
            {analytics.scores && analytics.scores[0]?._extended_metadata && 
             !analytics.scores[0]._extended_metadata.hybrid_shap && 
             !analytics.scores[0]._extended_metadata.ml_shap && 
             !analytics.scores[0]._extended_metadata.shap_explanation && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-900 mb-2">Keine SHAP-Daten für diese Anfrage verfügbar</h3>
                    <p className="text-sm text-yellow-800 mb-3">
                      SHAP-Daten werden automatisch bei jeder Chat-Anfrage berechnet und gespeichert.
                      Siehe unten für die Historie aller gespeicherten SHAP-Daten.
                    </p>
                    <div className="mt-3">
                      <button
                        onClick={() => router.push('/rag-chat')}
                        className="text-sm text-yellow-900 hover:text-yellow-700 font-semibold underline flex items-center gap-2"
                      >
                        <MessageSquare className="w-4 h-4" />
                        Zum RAG Chat gehen
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: System Info */}
        {activeTab === 'system' && (
          <div className="space-y-8">
            {/* NEU v2.10.4: Audit Trail auch in System Info */}
            {Boolean(analytics.search_quality_metrics) && (
              <div className="mb-8">
                <AnalyticsAuditTrail
                  analytics={analytics}
                  searchQualityMetrics={analytics.search_quality_metrics}
                />
              </div>
            )}

            <div className="flex items-center gap-3 mb-6">
              <Settings className="w-7 h-7 text-gray-600" />
              <h2 className="text-2xl font-bold text-gray-900">System Metrics</h2>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <p className="font-semibold">System Metrics</p>
                    <p className="text-xs">
                      Zeigt technische Informationen über das RAG-System:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li><strong>Model Info:</strong> ML-Modell-Status, Features, Training-Daten</li>
                      <li><strong>Cache Stats:</strong> SHAP-Cache Performance (Hit Rate, Zeit gespart)</li>
                      <li><strong>Background Stats:</strong> Historische Daten für SHAP-Berechnungen</li>
                    </ul>
                    <p className="text-xs text-gray-300 mt-2">
                      Diese Metriken helfen, die Performance und Effizienz des Systems zu verstehen.
                    </p>
                  </div>
                }
              />
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Model Info */}
              {(liveModelInfo || analytics.model_info) && (
                <ModelInfoCard
                  modelType={
                    liveModelInfo?.model_info?.model_type
                    || analytics.model_info?.model_type
                    || 'none'
                  }
                  modelVersion={
                    liveModelInfo?.model_info?.model_version
                    || analytics.model_info?.model_version
                    || '1.0.0'
                  }
                  isReady={
                    liveModelInfo?.ready
                    || analytics.model_info?.ready
                    || analytics.model_info?.ml_enabled
                    || false
                  }
                  featureNames={
                    liveModelInfo?.feature_names
                    || liveModelInfo?.model_info?.feature_names
                    || analytics.model_info?.feature_names
                    || []
                  }
                  trainingDataStats={
                    liveModelInfo?.training_data_stats
                    || analytics.model_info?.training_data_stats
                  }
                />
              )}

              {/* Cache Stats */}
              {analytics.cache_stats && (
                <CacheStatsCard
                  cacheSize={analytics.cache_stats.cache_size || 0}
                  maxSize={analytics.cache_stats.max_size || 100}
                  hits={analytics.cache_stats.hits || 0}
                  misses={analytics.cache_stats.misses || 0}
                  hitRatePercent={analytics.cache_stats.hit_rate_percent || 0}
                  estimatedTimeSavedMinutes={analytics.cache_stats.estimated_time_saved_minutes || 0}
                />
              )}

              {/* Background Stats */}
              {analytics.background_data_stats && (
                <BackgroundStatsCard
                  totalRecords={analytics.background_data_stats.total_records || 0}
                  backgroundDataShape={analytics.background_data_stats.background_data_shape}
                  lastUpdate={analytics.background_data_stats.last_update}
                  oldestRecord={analytics.background_data_stats.oldest_record}
                  newestRecord={analytics.background_data_stats.newest_record}
                />
              )}
            </div>
          </div>
        )}
          </div>

      {/* Export & Footer (nur Pro-Modus) */}
      {viewMode === 'pro' && (
        <div className="mt-8 space-y-4">
          <details className="bg-white rounded-xl border border-gray-200 p-4">
            <summary className="cursor-pointer select-none font-semibold text-gray-900">
              Export (CSV/PDF)
            </summary>
            <div className="mt-4">
              <AnalyticsExport analytics={analytics} metrics={analytics.search_quality_metrics} />
            </div>
          </details>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm text-blue-900 font-medium mb-2">
                  ✅ <strong>Analytics-Daten geladen!</strong>
                </p>
                <p className="text-xs text-blue-800">
                  Diese Daten stammen aus der letzten RAG-Chat-Anfrage. Stelle eine neue Frage im Chat, um die Analytics zu aktualisieren.
                </p>
                <div className="flex gap-4 mt-3">
                  <button
                    onClick={() => router.push('/rag-chat')}
                    className="text-sm text-blue-700 hover:text-blue-900 font-semibold underline"
                  >
                    → Zum RAG Chat
                  </button>
                  <button
                    onClick={() => router.push('/trends')}
                    className="text-sm text-purple-700 hover:text-purple-900 font-semibold underline"
                  >
                    → Trend-Analyse
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
        </>
      )}
    </div>
    </div>
  )
}
