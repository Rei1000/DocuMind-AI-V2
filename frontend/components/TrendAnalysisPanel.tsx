/**
 * Trend Analysis Panel Component
 * 
 * Zeigt Trend-Analyse der Search Quality Metrics über Zeit.
 * Best Practice UX mit interaktiven Charts, Vorher/Nachher Vergleich und Undo-Funktionalität.
 * 
 * Version: 2.9.0
 */

'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Minus, Calendar, MessageSquare, AlertCircle, RotateCcw, Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface TrendDataPoint {
  date: string
  query: string
  precision_at_10: number
  recall_at_10: number
  ndcg_at_10: number
  mrr: number
  session_id?: number
  user_id?: number
  document_type?: string
}

interface TrendAnalysisData {
  start_date: string
  end_date: string
  data_points: TrendDataPoint[]
  aggregated_metrics: any
  trends: Record<string, string>
  alerts: Array<{
    type: string
    severity: string
    message: string
    query?: string
    timestamp: string
    metrics?: any
    actionable: boolean
    undo_available: boolean
  }>
}

interface TrendAnalysisPanelProps {
  startDate?: string
  endDate?: string
  documentType?: string
  userId?: number
}

export default function TrendAnalysisPanel({
  startDate,
  endDate,
  documentType,
  userId
}: TrendAnalysisPanelProps) {
  const [data, setData] = useState<TrendAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null)
  const [beforeAfterData, setBeforeAfterData] = useState<any>(null)
  const [showBeforeAfter, setShowBeforeAfter] = useState(false)

  useEffect(() => {
    loadTrendData()
  }, [startDate, endDate, documentType, userId])

  const loadTrendData = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (documentType) params.append('document_type', documentType)
      if (userId) params.append('user_id', userId.toString())

      // Hole Token für Authentifizierung
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/rag/analytics/trends?${params.toString()}`, { headers })
      if (!response.ok) throw new Error('Failed to load trend data')
      
      const trendData = await response.json()
      setData(trendData)
    } catch (error) {
      console.error('Error loading trend data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadBeforeAfter = async (query: string) => {
    try {
      const params = new URLSearchParams({ query })
      if (startDate) params.append('before_date', startDate)
      if (endDate) params.append('after_date', endDate)

      // Hole Token für Authentifizierung
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/rag/analytics/before-after?${params.toString()}`, { headers })
      if (!response.ok) throw new Error('Failed to load before/after data')
      
      const beforeAfter = await response.json()
      setBeforeAfterData(beforeAfter)
      setShowBeforeAfter(true)
    } catch (error) {
      console.error('Error loading before/after data:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const formatPercent = (value: number) => {
    return (value * 100).toFixed(1) + '%'
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-600" />
      case 'degrading':
        return <TrendingDown className="w-5 h-5 text-red-600" />
      case 'stable':
        return <Minus className="w-5 h-5 text-gray-600" />
      default:
        return null
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'degrading':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'stable':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse text-gray-400">Lade Trend-Daten...</div>
      </div>
    )
  }

  if (!data || !data.data_points || data.data_points.length === 0) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Keine Trend-Daten verfügbar</h3>
            <p className="text-sm text-blue-800 mb-3">
              Es wurden noch keine Search Quality Metrics für den ausgewählten Zeitraum gespeichert.
            </p>
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <p className="text-sm text-gray-700 mb-2 font-semibold">
                So sammelst du Trend-Daten:
              </p>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600 mb-3">
                <li>Stelle Fragen im RAG Chat</li>
                <li>Das System berechnet automatisch Search Quality Metrics</li>
                <li>Die Metriken werden in der Datenbank gespeichert</li>
                <li>Nach mehreren Fragen siehst du hier Trends und Entwicklungen</li>
              </ol>
              <p className="text-xs text-gray-500">
                💡 <strong>Tipp:</strong> Stelle mindestens 3-5 Fragen, um erste Trends zu sehen.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Bereite Chart-Daten vor
  const chartData = data.data_points.map(point => ({
    date: formatDate(point.date),
    dateFull: point.date,
    query: point.query,
    'Precision@10': point.precision_at_10,
    'Recall@10': point.recall_at_10,
    'NDCG@10': point.ndcg_at_10,
    'MRR': point.mrr
  }))

  // Eindeutige Queries für Filter
  const uniqueQueries = Array.from(new Set(data.data_points.map(p => p.query)))

  return (
    <div className="space-y-6">
      {/* Header mit Info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Calendar className="w-7 h-7 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Trend-Analyse</h2>
          <Tooltip
            icon
            content={
              <div className="space-y-2">
                <p className="font-semibold">Trend-Analyse</p>
                <p className="text-xs">
                  Zeigt die Entwicklung der Search Quality Metrics über Zeit.
                  Du kannst sehen, wie sich die Qualität der Suchergebnisse entwickelt hat.
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  <strong>Zeitraum:</strong> {formatDate(data.start_date)} - {formatDate(data.end_date)}
                </p>
              </div>
            }
          />
        </div>
        <div className="text-sm text-gray-600">
          {data.data_points.length} Datenpunkte
        </div>
      </div>

      {/* Zeitraum Info */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
        <div className="flex items-center gap-3">
          <Info className="w-5 h-5 text-blue-600" />
          <div>
            <p className="text-sm text-blue-900">
              <strong>Zeitraum:</strong> {formatDate(data.start_date)} - {formatDate(data.end_date)}
            </p>
            <p className="text-xs text-blue-800 mt-1">
              Alle Queries in diesem Zeitraum werden analysiert. Klicke auf eine Query, um Details zu sehen.
            </p>
          </div>
        </div>
      </div>

      {/* Trend-Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(data.trends).map(([metric, trend]) => (
          <div key={metric} className={`border rounded-lg p-4 ${getTrendColor(trend)}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{metric}</div>
                <div className="text-xs mt-1">
                  {trend === 'improving' && 'Verbesserung erkannt'}
                  {trend === 'degrading' && 'Verschlechterung erkannt'}
                  {trend === 'stable' && 'Stabil'}
                  {trend === 'insufficient_data' && 'Nicht genug Daten'}
                </div>
              </div>
              {getTrendIcon(trend)}
            </div>
          </div>
        ))}
      </div>

      {/* Query Filter */}
      {uniqueQueries.length > 1 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter nach Query:
          </label>
          <select
            value={selectedQuery || ''}
            onChange={(e) => {
              setSelectedQuery(e.target.value || null)
              if (e.target.value) {
                loadBeforeAfter(e.target.value)
              } else {
                setShowBeforeAfter(false)
              }
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Alle Queries</option>
            {uniqueQueries.map(query => (
              <option key={query} value={query}>
                {query.length > 60 ? query.substring(0, 60) + '...' : query}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Metriken über Zeit</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              domain={[0, 1]}
              tickFormatter={(value) => formatPercent(value)}
            />
            <RechartsTooltip 
              formatter={(value: number) => formatPercent(value)}
              labelFormatter={(label) => `Datum: ${label}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="Precision@10" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="Recall@10" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="NDCG@10" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="MRR" 
              stroke="#f59e0b" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Vorher/Nachher Vergleich */}
      {showBeforeAfter && beforeAfterData && (
        <BeforeAfterComparison data={beforeAfterData} onClose={() => setShowBeforeAfter(false)} />
      )}

      {/* Alerts */}
      {data.alerts && data.alerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            Alerts
          </h3>
          {data.alerts.map((alert, index) => (
            <AlertCard key={index} alert={alert} />
          ))}
        </div>
      )}

      {/* Aggregierte Metriken */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Aggregierte Metriken</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-600">Precision@10</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatPercent(data.aggregated_metrics.average_precision_at_10 || 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Recall@10</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatPercent(data.aggregated_metrics.average_recall_at_10 || 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">NDCG@10</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatPercent(data.aggregated_metrics.average_ndcg_at_10 || 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">MRR</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatPercent(data.aggregated_metrics.average_mrr || 0)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Vorher/Nachher Vergleich Komponente
function BeforeAfterComparison({ data, onClose }: { data: any, onClose: () => void }) {
  return (
    <div className="bg-white rounded-lg border-2 border-blue-200 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-blue-600" />
          Vorher/Nachher Vergleich
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-sm font-medium text-blue-900">
          <strong>Query:</strong> "{data.query}"
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Vorher */}
        <div className="border-2 border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
            <h4 className="font-semibold text-gray-900">Vorher</h4>
            <span className="text-xs text-gray-500">
              {new Date(data.before_date).toLocaleDateString('de-DE')}
            </span>
          </div>
          <MetricComparison metrics={data.before_metrics} />
        </div>

        {/* Nachher */}
        <div className="border-2 border-blue-400 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <h4 className="font-semibold text-gray-900">Nachher</h4>
            <span className="text-xs text-gray-500">
              {new Date(data.after_date).toLocaleDateString('de-DE')}
            </span>
          </div>
          <MetricComparison metrics={data.after_metrics} />
        </div>
      </div>

      {/* Verbesserungen */}
      {data.changes && data.changes.length > 0 && (
        <div className="mt-6 space-y-2">
          <h4 className="font-semibold text-gray-900">Detaillierte Änderungen:</h4>
          {data.changes.map((change: any, index: number) => (
            <div
              key={index}
              className={`p-3 rounded-lg ${
                change.direction === 'improved'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{change.metric}</span>
                <span className={`font-bold ${
                  change.direction === 'improved' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {change.delta > 0 ? '+' : ''}{formatPercent(change.delta)}
                  {' '}({change.delta_percent > 0 ? '+' : ''}{change.delta_percent.toFixed(1)}%)
                </span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {formatPercent(change.before)} → {formatPercent(change.after)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function MetricComparison({ metrics }: { metrics: any }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-sm text-gray-600">Precision@10:</span>
        <span className="text-sm font-semibold text-gray-900">{formatPercent(metrics.precision_at_10)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm text-gray-600">Recall@10:</span>
        <span className="text-sm font-semibold text-gray-900">{formatPercent(metrics.recall_at_10)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm text-gray-600">NDCG@10:</span>
        <span className="text-sm font-semibold text-gray-900">{formatPercent(metrics.ndcg_at_10)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm text-gray-600">MRR:</span>
        <span className="text-sm font-semibold text-gray-900">{formatPercent(metrics.mrr)}</span>
      </div>
    </div>
  )
}

function AlertCard({ alert }: { alert: any }) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-300 text-red-900'
      case 'high':
        return 'bg-orange-50 border-orange-300 text-orange-900'
      case 'medium':
        return 'bg-yellow-50 border-yellow-300 text-yellow-900'
      default:
        return 'bg-blue-50 border-blue-300 text-blue-900'
    }
  }

  return (
    <div className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">{alert.severity.toUpperCase()}</span>
          </div>
          <p className="text-sm mb-2">{alert.message}</p>
          {alert.query && (
            <p className="text-xs opacity-75">
              <strong>Query:</strong> {alert.query.length > 80 ? alert.query.substring(0, 80) + '...' : alert.query}
            </p>
          )}
        </div>
        {alert.undo_available && (
          <button
            className="ml-4 px-3 py-1 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50 flex items-center gap-2"
            onClick={() => {
              // TODO: Implementiere Undo
              alert('Undo-Funktionalität wird implementiert...')
            }}
          >
            <RotateCcw className="w-4 h-4" />
            Rückgängig
          </button>
        )}
      </div>
    </div>
  )
}

function formatPercent(value: number): string {
  return (value * 100).toFixed(1) + '%'
}

