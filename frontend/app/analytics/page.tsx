/**
 * RAG Analytics Dashboard - v2.9.0
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
import SearchQualityDebugPanel from '@/components/SearchQualityDebugPanel'
import SearchQualityComparisonPanel from '@/components/SearchQualityComparisonPanel'
import TrendAnalysisPanel from '@/components/TrendAnalysisPanel'
import QualityAlertsPanel from '@/components/QualityAlertsPanel'
import QuickSummaryCard from '@/components/QuickSummaryCard'
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
import Tooltip from '@/components/ui/Tooltip'

interface AnalyticsData {
  query?: string  // NEU v2.9.0: Query prominent speichern
  scores: any[]
  background_data_stats: any
  cache_stats: any
  model_info: any
  search_quality_metrics?: any  // NEU v2.9.0: Search Quality Metrics
  message_id?: number  // NEU: Message-ID für Feedback-Prüfung
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMetrics, setLoadingMetrics] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'scores' | 'shap' | 'system'>('overview')
  const [showOnboarding, setShowOnboarding] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Prüfe ob Onboarding bereits abgeschlossen wurde
    const onboardingCompleted = localStorage.getItem('analytics_onboarding_completed')
    if (!onboardingCompleted && analytics) {
      // Zeige Onboarding nur wenn Analytics-Daten vorhanden sind
      setShowOnboarding(true)
    }

    // Lade Analytics-Daten aus localStorage (vom Chat gespeichert)
    loadAnalyticsFromStorage()
    
    // Poll localStorage alle 2 Sekunden für Updates
    const interval = setInterval(loadAnalyticsFromStorage, 2000)
    
    return () => clearInterval(interval)
  }, [])

  // NEU v2.10.2: Lade Metriken automatisch, wenn Feedback vorhanden ist
  useEffect(() => {
    if (analytics?.query && !analytics?.search_quality_metrics && !loadingMetrics) {
      loadMetricsForQuery(analytics.query)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analytics?.query, analytics?.search_quality_metrics])

  // NEU v2.10.2: Auto-Reload Metriken alle 5 Sekunden, wenn Feedback vorhanden ist
  useEffect(() => {
    if (!analytics?.query || !analytics?.message_id) return
    
    // Lade Metriken sofort
    loadMetricsForQuery(analytics.query)
    
    // Dann alle 5 Sekunden neu laden (für Feedback-Updates)
    const interval = setInterval(() => {
      if (!loadingMetrics) {
        loadMetricsForQuery(analytics.query)
      }
    }, 5000)  // Alle 5 Sekunden
    
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analytics?.query, analytics?.message_id])

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
          const chunkFeedbackMap: Record<string, string> = {}
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
                  chunkFeedbackMap[chunkId] = feedbacks[0].rating
                }
              }
            }
          }
          
          // Hole Message-Level Feedback
          let messageFeedback: string | null = null
          if (messageId) {
            const messageFeedbackResponse = await fetch(
              `/api/rag/chat/messages/${messageId}/feedback`,
              { headers }
            )
            if (messageFeedbackResponse.ok) {
              const messageFeedbacks = await messageFeedbackResponse.json()
              if (messageFeedbacks && messageFeedbacks.length > 0) {
                messageFeedback = messageFeedbacks[0].rating
              }
            }
          }
          
          // Merge Feedback in analytics.scores
          const updatedScores = analytics.scores.map((score: any) => {
            const chunkId = score.chunk_id
            const chunkFeedback = chunkFeedbackMap[chunkId]
            const feedbackRating = chunkFeedback || messageFeedback || null
            
            // Füge feedback_rating zu _extended_metadata hinzu
            if (!score._extended_metadata) {
              score._extended_metadata = {}
            }
            if (feedbackRating) {
              score._extended_metadata.feedback_rating = feedbackRating
            }
            
            return score
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
      
      const metrics = await response.json()
      
      // Aktualisiere Analytics-Daten mit Metriken
      setAnalytics((prevAnalytics) => {
        if (!prevAnalytics) return prevAnalytics
        
        const updatedAnalytics = {
          ...prevAnalytics,
          search_quality_metrics: metrics
        }
        
        // Speichere aktualisierte Analytics in localStorage
        localStorage.setItem('lastAnalytics', JSON.stringify(updatedAnalytics))
        
        console.log('Metrics loaded and saved:', metrics)
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
        </div>

        {/* WICHTIGER HINWEIS - Keine Analytics verfügbar */}
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-400 rounded-xl p-12 shadow-xl">
          <div className="flex flex-col items-center text-center">
            <AlertCircle className="w-20 h-20 text-yellow-600 mb-6" />
            
            <h2 className="text-3xl font-bold text-yellow-900 mb-4">
              Keine Analytics-Daten verfügbar
            </h2>
            
            <p className="text-lg text-yellow-800 mb-6 max-w-2xl">
              Das Analytics-Dashboard zeigt die technischen Analysen deiner <strong>letzten RAG-Chat-Anfrage</strong>.
            </p>

            <div className="bg-white/70 backdrop-blur rounded-xl p-6 mb-8 max-w-3xl">
              <h3 className="font-bold text-yellow-900 mb-4 text-xl">📋 So funktioniert es:</h3>
              <ol className="text-left space-y-3 text-yellow-900">
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">1.</span>
                  <span>Gehe zum <strong>RAG Chat</strong></span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">2.</span>
                  <span>Stelle eine Frage (z.B. &quot;Wie montiere ich die Freilaufwelle?&quot;)</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">3.</span>
                  <span>Die Antwort enthält <strong>automatisch</strong> Analytics-Daten</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">4.</span>
                  <span>Komme zurück hierher - Analytics werden angezeigt!</span>
                </li>
              </ol>
            </div>

                        <div className="flex gap-4">
                          <button
                            onClick={() => router.push('/rag-chat')}
                            className="px-12 py-5 bg-blue-600 text-white rounded-xl font-bold text-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-3"
                          >
                            <MessageSquare className="w-7 h-7" />
                            Zum RAG Chat
                          </button>
                          <button
                            onClick={() => router.push('/trends')}
                            className="px-12 py-5 bg-purple-600 text-white rounded-xl font-bold text-xl hover:bg-purple-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-3"
                          >
                            <TrendingUp className="w-7 h-7" />
                            Trend-Analyse
                          </button>
                        </div>

            <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-900 mb-1">Wie funktioniert das Analytics Dashboard?</h3>
                  <p className="text-sm text-blue-800">
                    Dieses Dashboard zeigt <strong>automatisch</strong> die Analytics-Daten deiner letzten RAG-Chat-Anfrage.
                    Stelle eine neue Frage im Chat, um die Analytics zu aktualisieren.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Falls Analytics-Daten vorhanden - Visualisierung
  return (
    <>
      {/* Onboarding Tour */}
      {showOnboarding && (
        <AnalyticsOnboarding onComplete={() => setShowOnboarding(false)} />
      )}

      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
          <BarChart3 className="w-10 h-10 text-blue-600" />
          Analytics Dashboard
          <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
            v2.9.0
          </span>
        </h1>
        <p className="text-gray-600 text-lg">
          Analytics der letzten Chat-Anfrage • {analytics.scores?.length || 0} Chunks analysiert
        </p>
        
        {/* WICHTIG: Query prominent anzeigen (auch ohne Metriken) */}
        {analytics.query && (
          <div className="mt-4 bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-600 rounded-r-lg p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <MessageSquare className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-2">
                  Bewertete Frage
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-2">
                  &quot;{analytics.query}&quot;
                </div>
                <div className="text-sm text-gray-600">
                  Diese Analytics beziehen sich auf die oben genannte Frage. Alle Metriken wurden für diese spezifische Query berechnet.
                </div>
              </div>
            </div>
          </div>
        )}
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

      {/* Quick Summary Card - Nur anzeigen wenn Metriken vorhanden */}
      {analytics.query && analytics.search_quality_metrics && (
        <QuickSummaryCard
          query={analytics.query}
          ndcg={analytics.search_quality_metrics.ndcg_at_10}
          precision={analytics.search_quality_metrics.precision_at_10}
          mrr={analytics.search_quality_metrics.mrr}
        />
      )}

      {/* Info: Feedback-Status wird jetzt in SearchQualityMetricsPanel angezeigt */}

      {/* Tabs */}
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
              Detaillierte Scores
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
              SHAP Analyse
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
              System Info
            </div>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
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
            {analytics.search_quality_metrics && (
              <div className="space-y-6">
                <SearchQualityMetricsPanel
                  metrics={analytics.search_quality_metrics}
                  query={analytics.query || analytics.scores?.[0]?._extended_metadata?.query || 'Unbekannte Query'}
                />
                
                {/* Chat vs. Analytics Vergleich - Zeigt Diskrepanzen */}
                <SearchQualityComparisonPanel
                  query={analytics.query || analytics.scores?.[0]?._extended_metadata?.query || 'Unbekannte Query'}
                  chatChunks={analytics.scores?.map((score: any, index: number) => ({
                    chunk_id: score.chunk_id || '',
                    rank_position: score.rank_position || index + 1,
                    document_title: score._extended_metadata?.document_title || 'Unbekanntes Dokument',
                    page_number: score._extended_metadata?.page_number || score._extended_metadata?.page_numbers?.[0] || 1,
                    relevance_score: score.hybrid_score || score.vector_score || 0.5,
                    vector_score: score.vector_score,
                    text_score: score.text_score,
                    hybrid_score: score.hybrid_score
                  })) || []}
                  analyticsChunks={analytics.scores?.map((score: any, index: number) => ({
                    chunk_id: score.chunk_id || '',
                    rank_position: score.rank_position || index + 1,
                    document_title: score._extended_metadata?.document_title || 'Unbekanntes Dokument',
                    page_number: score._extended_metadata?.page_number || score._extended_metadata?.page_numbers?.[0] || 1,
                    relevance_score: score._extended_metadata?.relevance_score || (score.hybrid_score || 0.5),
                    feedback_rating: score._extended_metadata?.feedback_rating || null,
                    is_relevant: score._extended_metadata?.feedback_rating === 'positive' 
                      ? true 
                      : score._extended_metadata?.feedback_rating === 'negative'
                      ? false
                      : (score._extended_metadata?.relevance_score || (score.hybrid_score || 0.5)) > 0.5,
                    hybrid_score: score.hybrid_score,
                    ml_score: score.ml_score,
                    vector_score: score.vector_score,
                    text_score: score.text_score
                  })) || []}
                  metrics={analytics.search_quality_metrics}
                />
                
                {/* Search Quality Debug Panel - Zeigt detaillierte Analyse */}
                <SearchQualityDebugPanel
                  query={analytics.query || analytics.scores?.[0]?._extended_metadata?.query || 'Unbekannte Query'}
                  metrics={analytics.search_quality_metrics}
                  chunks={analytics.scores?.map((score: any, index: number) => ({
                    chunk_id: score.chunk_id || '',
                    rank_position: score.rank_position || index + 1,
                    feedback_rating: score._extended_metadata?.feedback_rating || null,
                    relevance_score: score._extended_metadata?.relevance_score || (score.hybrid_score || 0.5),
                    // is_relevant: WICHTIG - positive feedback = IMMER relevant, negative = IMMER nicht relevant, sonst basierend auf Score (> 0.5)
                    // Feedback hat IMMER Priorität über Scores!
                    is_relevant: score._extended_metadata?.feedback_rating === 'positive' 
                      ? true  // Positives Feedback = IMMER relevant, unabhängig vom Score!
                      : score._extended_metadata?.feedback_rating === 'negative'
                      ? false  // Negatives Feedback = IMMER nicht relevant
                      : (score._extended_metadata?.relevance_score || (score.hybrid_score || 0.5)) > 0.5,  // Kein Feedback: basierend auf Score
                    hybrid_score: score.hybrid_score,
                    ml_score: score.ml_score,
                    vector_score: score.vector_score,
                    text_score: score.text_score,
                    document_title: score._extended_metadata?.document_title || 'Unbekanntes Dokument',
                    page_number: score._extended_metadata?.page_number || score._extended_metadata?.page_numbers?.[0],
                    text_excerpt: score._extended_metadata?.text_excerpt || score._extended_metadata?.chunk_text?.substring(0, 200)
                  })) || []}
                />
              </div>
            )}

            {/* Automatische Insights */}
            <div>
              <AutomatedInsightsPanel
                metrics={analytics.search_quality_metrics}
                scores={analytics.scores}
                query={analytics.query}
              />
            </div>

            {/* Quality Alerts */}
            <div>
              <QualityAlertsPanel autoRefresh={true} />
            </div>
          </div>
        )}

        {/* Tab 2: Detaillierte Scores */}
        {activeTab === 'scores' && (
          <div className="space-y-8">
            {/* Interaktive Charts */}
            {analytics.scores && analytics.scores.length > 0 && (
              <div>
                <ScoreCharts scores={analytics.scores.map((s: any) => ({
                  chunk_id: s.chunk_id || '',
                  rank_position: s.rank_position || 1,
                  vector_score: s.vector_score || 0,
                  text_score: s.text_score || 0,
                  hybrid_score: s.hybrid_score || 0,
                  ml_score: s.ml_score,
                  final_score: s.final_score
                }))} />
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
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {analytics.scores.slice(0, 9).map((score: any) => (
                    <ScoreOverviewCard
                      key={score.chunk_id}
                      vectorScore={score.vector_score || 0}
                      textScore={score.text_score || 0}
                      hybridScore={score.hybrid_score || 0}
                      mlScore={score.ml_score}
                      finalScore={score.final_score}
                      rankPosition={score.rank_position || 1}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Chunk-Analyse (NEU) - Zeigt detaillierte Chunk-Informationen */}
            {analytics.query && analytics.scores && analytics.scores.length > 0 && (
              <ChunkAnalysisPanel
                query={analytics.query}
                chunks={analytics.scores.map((score: any) => ({
                  chunk_id: score.chunk_id || '',
                  document_id: score._extended_metadata?.document_id || 0,
                  document_title: score._extended_metadata?.document_title || 'Unbekanntes Dokument',
                  page_number: score._extended_metadata?.page_number || 1,
                  page_numbers: score._extended_metadata?.page_numbers || [score._extended_metadata?.page_number || 1],
                  relevance_score: score.hybrid_score || score.vector_score || 0.5,
                  vector_score: score.vector_score,
                  text_score: score.text_score,
                  hybrid_score: score.hybrid_score,
                  ml_score: score.ml_score,
                  final_score: score.final_score,
                  rank_position: score.rank_position || 0,
                  text_excerpt: score._extended_metadata?.text_excerpt || score._extended_metadata?.chunk_text?.substring(0, 200),
                  chunk_metadata: score._extended_metadata?.chunk_metadata,
                  feedback_rating: score._extended_metadata?.feedback_rating
                }))}
                messageId={analytics.message_id}
              />
            )}

            {/* Chunk Details Table */}
            {analytics.scores && analytics.scores.length > 0 && (
              <div>
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
                      {analytics.scores.map((score: any, index: number) => (
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
                              {score.vector_score ? (score.vector_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-purple-700 font-semibold">
                              {score.text_score ? (score.text_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-indigo-700 font-semibold">
                              {score.hybrid_score ? (score.hybrid_score * 100).toFixed(1) + '%' : '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-green-700 font-bold">
                              {score.ml_score ? (score.ml_score * 100).toFixed(1) + '%' : '-'}
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
            )}
          </div>
        )}

        {/* Tab 3: SHAP Analyse */}
        {activeTab === 'shap' && (
          <div className="space-y-8">
            {/* SHAP Comparison - PROMINENT */}
            {analytics.scores && analytics.scores[0]?._extended_metadata && 
             (analytics.scores[0]._extended_metadata.hybrid_shap || analytics.scores[0]._extended_metadata.ml_shap) && (
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
                        const shapData = score._extended_metadata.shap_explanation
                        const featureImportance = shapData.feature_importance || {}
                        const shapValues = shapData.shap_values || []
                        const featureNames = shapData.feature_names || Object.keys(featureImportance)
                        
                        // Erstelle Features-Array für Bar Chart
                        const features = shapValues.length > 0 && featureNames.length === shapValues.length
                          ? featureNames.map((name, i) => ({
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
                            />
                          </div>
                        )
                      })}
                  </div>
                )}

                <div className="bg-white rounded-lg p-4 border border-purple-200">
                  <SHAPComparisonPanel
                    hybridShap={analytics.scores[0]._extended_metadata.hybrid_shap}
                    mlShap={analytics.scores[0]._extended_metadata.ml_shap}
                    query={analytics.query || analytics.scores[0]._extended_metadata.query || 'Unknown'}
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
              {analytics.model_info && (
                <ModelInfoCard
                  modelType={analytics.model_info.model_type || 'none'}
                  modelVersion={analytics.model_info.model_version || '1.0.0'}
                  isReady={analytics.model_info.ml_enabled || false}
                  featureNames={analytics.model_info.feature_names || []}
                  trainingDataStats={analytics.model_info.training_data_stats}
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

      {/* Export & Footer */}
      <div className="mt-8 space-y-4">
        {/* Export */}
        <AnalyticsExport
          analytics={analytics}
          metrics={analytics.search_quality_metrics}
        />

        {/* Footer Info */}
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
                Diese Daten stammen aus der letzten RAG-Chat-Anfrage. Stelle eine neue Frage im Chat um die Analytics zu aktualisieren.
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
    </div>
    </>
  )
}
