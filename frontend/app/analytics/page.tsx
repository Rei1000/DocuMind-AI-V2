/**
 * RAG Analytics Dashboard
 * 
 * PHASE 4.2: Umfassendes Analytics Dashboard für RAG-Performance
 */

'use client'

import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, MessageSquare, ThumbsUp, ThumbsDown, Clock, CheckCircle, XCircle, AlertCircle, Search, Zap } from 'lucide-react'
import { getRAGAnalytics, getSearchQualityAnalytics, RAGAnalyticsResponse, SearchQualityAnalyticsResponse } from '@/lib/api/rag'
import Spinner from '@/components/ui/Spinner'
import Tooltip from '@/components/ui/Tooltip'
import toast from 'react-hot-toast'
import SHAPFeatureImportanceChart from '@/components/SHAPFeatureImportanceChart'
import SHAPWaterfallChart from '@/components/SHAPWaterfallChart'
import SearchQualityAnalysis from '@/components/SearchQualityAnalysis'

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<RAGAnalyticsResponse | null>(null)
  const [searchQuality, setSearchQuality] = useState<SearchQualityAnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQualityLoading, setSearchQualityLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d')

  useEffect(() => {
    loadAnalytics()
    loadSearchQuality()
  }, [timeRange])

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      const startDate = getStartDate(timeRange)
      const data = await getRAGAnalytics(
        startDate ? startDate.toISOString() : undefined,
        undefined
      )
      setAnalytics(data)
    } catch (error: any) {
      console.error('Failed to load analytics:', error)
      toast.error(`❌ Fehler beim Laden der Analytics: ${error.message || 'Unbekannter Fehler'}`)
    } finally {
      setLoading(false)
    }
  }

  const loadSearchQuality = async () => {
    setSearchQualityLoading(true)
    try {
      const startDate = getStartDate(timeRange)
      const data = await getSearchQualityAnalytics(
        startDate ? startDate.toISOString() : undefined,
        undefined,
        5  // top_k = 5
      )
      setSearchQuality(data)
    } catch (error: any) {
      console.error('Failed to load search quality analytics:', error)
      // Nicht als Fehler anzeigen, da Search Quality optional ist
      toast.error(`⚠️ Search Quality Analytics konnten nicht geladen werden: ${error.message || 'Unbekannter Fehler'}`)
    } finally {
      setSearchQualityLoading(false)
    }
  }

  const getStartDate = (range: string): Date | null => {
    const now = new Date()
    switch (range) {
      case '7d':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      case '30d':
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      case '90d':
        return new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
          Keine Analytics-Daten verfügbar
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <BarChart3 className="w-8 h-8" />
          RAG Analytics Dashboard
        </h1>
        <p className="text-gray-600">
          Umfassende Statistiken und Metriken für RAG-Performance
        </p>
      </div>

      {/* Time Range Selector */}
      <div className="mb-6 flex gap-2">
        {(['7d', '30d', '90d', 'all'] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              timeRange === range
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            {range === '7d' ? '7 Tage' : range === '30d' ? '30 Tage' : range === '90d' ? '90 Tage' : 'Alle'}
          </button>
        ))}
      </div>

      {/* Quality Score Card */}
      <div className="mb-6 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div>
              <h2 className="text-lg font-semibold mb-1">Quality Score</h2>
              <p className="text-blue-100 text-sm">Basierend auf User Feedback</p>
            </div>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <div>
                    <strong className="text-white">Datenquelle:</strong>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                      <li>Berechnet aus: <code className="bg-gray-800 px-1 rounded">rag_feedback</code> Tabelle</li>
                      <li>Formel: <code className="bg-gray-800 px-1 rounded">AVG(rating) * 100</code> (0-100 Skala)</li>
                      <li>Rating-Mapping: positive=1.0, negative=0.0, neutral=0.5</li>
                    </ul>
                  </div>
                  <div>
                    <strong className="text-white">Berechnung:</strong>
                    <p className="text-gray-300 mt-1">Alle Feedback-Einträge werden aggregiert und der Durchschnitt wird auf 0-100 Skala skaliert.</p>
                  </div>
                  <div>
                    <strong className="text-white">ML-Verwendung:</strong>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                      <li>✅ Aktuell: Quality Score wird direkt aus Feedback berechnet</li>
                      <li>🔜 Zukünftig: Gewichtung basierend auf User-Level, zeitliche Gewichtung, Sentiment-Analyse</li>
                    </ul>
                  </div>
                  <div>
                    <strong className="text-white">Audit-Trail:</strong>
                    <p className="text-gray-300 mt-1">Jedes Feedback wird in <code className="bg-gray-800 px-1 rounded">rag_audit_logs</code> mit <code className="bg-gray-800 px-1 rounded">action='feedback_submitted'</code> protokolliert.</p>
                  </div>
                </div>
              }
            />
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold">{analytics.quality.score.toFixed(1)}</div>
            <div className="text-blue-100 text-sm">von 100</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="w-full bg-blue-400 rounded-full h-2">
            <div
              className="bg-white rounded-full h-2 transition-all"
              style={{ width: `${analytics.quality.score}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Feedback Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-600">Feedback</h3>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <div>
                      <strong className="text-white">Datenquelle:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Tabelle: <code className="bg-gray-800 px-1 rounded">rag_feedback</code></li>
                        <li>Zeitstempel: <code className="bg-gray-800 px-1 rounded">submitted_at</code></li>
                        <li>Filter: Optional nach <code className="bg-gray-800 px-1 rounded">user_id</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">Berechnung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Gesamt: <code className="bg-gray-800 px-1 rounded">COUNT(*)</code></li>
                        <li>Positiv: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE rating = 'positive'</code></li>
                        <li>Negativ: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE rating = 'negative'</code></li>
                        <li>Durchschnitt: <code className="bg-gray-800 px-1 rounded">AVG(rating)</code> (positive=1.0, negative=0.0, neutral=0.5)</li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">ML-Verwendung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>✅ Aktuell: Feedback wird für Quality Score verwendet</li>
                        <li>🔜 Zukünftig: Sentiment-Analyse, Prompt-Optimierung, Chunk-Relevanz-Learning</li>
                      </ul>
                    </div>
                  </div>
                }
              />
            </div>
            <ThumbsUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Gesamt:</span>
              <span className="font-semibold">{analytics.feedback.total}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-600">Positiv:</span>
              <span className="font-semibold">{analytics.feedback.positive}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-600">Negativ:</span>
              <span className="font-semibold">{analytics.feedback.negative}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Durchschnitt:</span>
              <span className="font-semibold">{(analytics.feedback.average_rating * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Query Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-600">Queries</h3>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <div>
                      <strong className="text-white">Datenquelle:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Tabelle: <code className="bg-gray-800 px-1 rounded">rag_audit_logs</code></li>
                        <li>Filter: <code className="bg-gray-800 px-1 rounded">action = 'query_executed'</code></li>
                        <li>Zeitfilter: Optional <code className="bg-gray-800 px-1 rounded">start_date</code> / <code className="bg-gray-800 px-1 rounded">end_date</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">Berechnung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Gesamt: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'query_executed'</code></li>
                        <li>Ø Dauer: <code className="bg-gray-800 px-1 rounded">AVG(duration_ms)</code></li>
                        <li>Erfolgsrate: <code className="bg-gray-800 px-1 rounded">success / total * 100</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">ML-Verwendung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>✅ Aktuell: Performance-Monitoring</li>
                        <li>🔜 Zukünftig: Query-Optimierung, Embedding-Modell-Auswahl, Query-Pattern-Learning</li>
                      </ul>
                    </div>
                  </div>
                }
              />
            </div>
            <MessageSquare className="w-5 h-5 text-blue-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Gesamt:</span>
              <span className="font-semibold">{analytics.queries.total}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Ø Dauer:</span>
              <span className="font-semibold">{analytics.queries.average_duration_ms.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Erfolgsrate:</span>
              <span className="font-semibold text-green-600">{(analytics.queries.success_rate * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Chunking Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-600">Chunking</h3>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <div>
                      <strong className="text-white">Datenquelle:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Tabelle: <code className="bg-gray-800 px-1 rounded">rag_audit_logs</code></li>
                        <li>Filter: <code className="bg-gray-800 px-1 rounded">action LIKE 'chunking_%'</code></li>
                        <li>Actions: <code className="bg-gray-800 px-1 rounded">chunking_started</code>, <code className="bg-gray-800 px-1 rounded">chunking_completed</code>, <code className="bg-gray-800 px-1 rounded">chunking_failed</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">Berechnung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Gestartet: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'chunking_started'</code></li>
                        <li>Erfolgreich: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'chunking_completed'</code></li>
                        <li>Fehlgeschlagen: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'chunking_failed'</code></li>
                        <li>Erfolgsrate: <code className="bg-gray-800 px-1 rounded">completed / started * 100</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">ML-Verwendung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>✅ Aktuell: Monitoring der Chunking-Performance</li>
                        <li>🔜 Zukünftig: Automatische Chunk-Größen-Optimierung, Fehleranalyse</li>
                      </ul>
                    </div>
                  </div>
                }
              />
            </div>
            <CheckCircle className="w-5 h-5 text-purple-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Gestartet:</span>
              <span className="font-semibold">{analytics.chunking.started}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-600">Erfolgreich:</span>
              <span className="font-semibold">{analytics.chunking.completed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-600">Fehlgeschlagen:</span>
              <span className="font-semibold">{analytics.chunking.failed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Erfolgsrate:</span>
              <span className="font-semibold">{analytics.chunking.success_rate.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Indexing Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-600">Indexing</h3>
              <Tooltip
                icon
                content={
                  <div className="space-y-2">
                    <div>
                      <strong className="text-white">Datenquelle:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Tabelle: <code className="bg-gray-800 px-1 rounded">rag_audit_logs</code></li>
                        <li>Filter: <code className="bg-gray-800 px-1 rounded">action LIKE 'indexing_%'</code></li>
                        <li>Actions: <code className="bg-gray-800 px-1 rounded">indexing_started</code>, <code className="bg-gray-800 px-1 rounded">indexing_completed</code>, <code className="bg-gray-800 px-1 rounded">indexing_failed</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">Berechnung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>Gestartet: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'indexing_started'</code></li>
                        <li>Erfolgreich: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'indexing_completed'</code></li>
                        <li>Fehlgeschlagen: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE action = 'indexing_failed'</code></li>
                        <li>Erfolgsrate: <code className="bg-gray-800 px-1 rounded">completed / started * 100</code></li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-white">ML-Verwendung:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                        <li>✅ Aktuell: Monitoring der Indexing-Performance</li>
                        <li>🔜 Zukünftig: Automatische Embedding-Modell-Auswahl, Batch-Größen-Optimierung</li>
                      </ul>
                    </div>
                  </div>
                }
              />
            </div>
            <TrendingUp className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Gestartet:</span>
              <span className="font-semibold">{analytics.indexing.started}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-600">Erfolgreich:</span>
              <span className="font-semibold">{analytics.indexing.completed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-600">Fehlgeschlagen:</span>
              <span className="font-semibold">{analytics.indexing.failed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Erfolgsrate:</span>
              <span className="font-semibold">{analytics.indexing.success_rate.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Stats */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Chat Messages
          <Tooltip
            icon
            content={
              <div className="space-y-2">
                <div>
                  <strong className="text-white">Datenquelle:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                    <li>Tabelle: <code className="bg-gray-800 px-1 rounded">rag_chat_messages</code></li>
                    <li>Filter: Optional nach <code className="bg-gray-800 px-1 rounded">created_at</code> (Zeitbereich)</li>
                  </ul>
                </div>
                <div>
                  <strong className="text-white">Berechnung:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                    <li>Gesamt: <code className="bg-gray-800 px-1 rounded">COUNT(*)</code> aller Nachrichten</li>
                    <li>Assistant: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE role = 'assistant'</code></li>
                    <li>User: <code className="bg-gray-800 px-1 rounded">COUNT(*) WHERE role = 'user'</code></li>
                  </ul>
                </div>
                <div>
                  <strong className="text-white">ML-Verwendung:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1 text-gray-300">
                    <li>✅ Aktuell: Statistische Auswertung</li>
                    <li>🔜 Zukünftig: Query-Pattern-Analyse, FAQ-Generierung, Konversations-Qualität-Metriken</li>
                  </ul>
                </div>
              </div>
            }
          />
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{analytics.messages.total}</div>
            <div className="text-sm text-gray-600">Gesamt</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{analytics.messages.assistant}</div>
            <div className="text-sm text-gray-600">Assistant</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{analytics.messages.user}</div>
            <div className="text-sm text-gray-600">User</div>
          </div>
        </div>
      </div>
      
      {/* NEU: SHAP Statistics Section */}
      {analytics.shap && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            SHAP Statistiken
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Gesamt-Erklärungen</div>
              <div className="text-2xl font-bold text-gray-900">{analytics.shap.total_explanations}</div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Ø Features pro Erklärung</div>
              <div className="text-2xl font-bold text-gray-900">
                {analytics.shap.average_feature_count.toFixed(1)}
              </div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Top Features</div>
              <div className="text-2xl font-bold text-gray-900">{analytics.shap.top_features.length}</div>
            </div>
          </div>
          
          {/* Top Features Chart */}
          {analytics.shap.top_features.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Features nach Importance</h3>
              <div className="space-y-2">
                {analytics.shap.top_features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700">{feature.feature}</span>
                        <span className="text-sm text-gray-600">
                          {(feature.average_importance * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${feature.average_importance * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* NEU: ML Performance Section */}
      {analytics.ml_performance && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            ML Model Performance
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Model Accuracy</div>
              <div className="text-2xl font-bold text-gray-900">
                {(analytics.ml_performance.model_accuracy * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Precision</div>
              <div className="text-2xl font-bold text-gray-900">
                {(analytics.ml_performance.precision * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Recall</div>
              <div className="text-2xl font-bold text-gray-900">
                {(analytics.ml_performance.recall * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">F1-Score</div>
              <div className="text-2xl font-bold text-gray-900">
                {(analytics.ml_performance.f1_score * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-600">Trainings-Samples</div>
            <div className="text-xl font-semibold text-gray-900">{analytics.ml_performance.training_samples}</div>
          </div>
        </div>
      )}
      
      {/* NEU: Optimization History Section */}
      {analytics.optimization_history && analytics.optimization_history.length > 0 && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-6 h-6" />
            Optimization History
          </h2>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="space-y-4">
              {analytics.optimization_history.map((entry, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-semibold text-gray-900">{entry.action}</div>
                      <div className="text-sm text-gray-600">{entry.date}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600">Verbesserung</div>
                      <div className="text-lg font-bold text-green-600">
                        +{(entry.improvement * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Vorher: </span>
                      <span className="font-medium">{(entry.before_score * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Nachher: </span>
                      <span className="font-medium">{(entry.after_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* NEU: Search Quality Analysis Section */}
      <div className="mt-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Search className="w-6 h-6" />
          Search Quality Analysis
        </h2>
        {searchQualityLoading ? (
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
          </div>
        ) : searchQuality ? (
          <SearchQualityAnalysis
            data={{
              documentTypeDistribution: searchQuality.document_type_distribution,
              scoreDistribution: searchQuality.score_distribution,
              topQueries: searchQuality.top_queries,
              shapInsights: searchQuality.shap_insights
            }}
          />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <div className="font-semibold text-yellow-900 mb-1">
                  Keine Search Quality Daten verfügbar
                </div>
                <p className="text-sm text-yellow-800">
                  Es wurden noch keine Search Quality Analytics gesammelt. Führen Sie einige RAG-Queries durch, um Daten zu generieren.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* NEU: Erweiterte SHAP-Visualisierungen */}
      {analytics.shap && analytics.shap.top_features.length > 0 && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="w-6 h-6" />
            Detaillierte SHAP-Visualisierungen
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Feature Importance Chart (bereits vorhanden, aber erweitert) */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Feature Importance (Top 10)
              </h3>
              <div className="space-y-3">
                {analytics.shap.top_features.slice(0, 10).map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-8 text-sm text-gray-500 text-right">
                      #{index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700">{feature.feature}</span>
                        <span className="text-sm font-bold text-gray-900">
                          {(feature.average_importance * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all"
                          style={{ width: `${Math.min(feature.average_importance * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* SHAP Statistics Summary */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                SHAP Statistiken
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Gesamt-Erklärungen</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {analytics.shap.total_explanations}
                    </div>
                  </div>
                  <BarChart3 className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Ø Features pro Erklärung</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {analytics.shap.average_feature_count.toFixed(1)}
                    </div>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-600" />
                </div>
                <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Top Features identifiziert</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {analytics.shap.top_features.length}
                    </div>
                  </div>
                  <Zap className="w-8 h-8 text-purple-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

