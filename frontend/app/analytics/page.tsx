/**
 * RAG Analytics Dashboard
 * 
 * PHASE 4.2: Umfassendes Analytics Dashboard für RAG-Performance
 */

'use client'

import { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, MessageSquare, ThumbsUp, ThumbsDown, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { getRAGAnalytics, RAGAnalyticsResponse } from '@/lib/api/rag'
import Spinner from '@/components/ui/Spinner'
import toast from 'react-hot-toast'

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<RAGAnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d')

  useEffect(() => {
    loadAnalytics()
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
          Keine Analytics-Daten verfügbar
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
          <div>
            <h2 className="text-lg font-semibold mb-1">Quality Score</h2>
            <p className="text-blue-100 text-sm">Basierend auf User Feedback</p>
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
            <h3 className="text-sm font-medium text-gray-600">Feedback</h3>
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
            <h3 className="text-sm font-medium text-gray-600">Queries</h3>
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
            <h3 className="text-sm font-medium text-gray-600">Chunking</h3>
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
            <h3 className="text-sm font-medium text-gray-600">Indexing</h3>
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
    </div>
  )
}

