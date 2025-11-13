/**
 * SHAP Analytics Dashboard Component
 * 
 * Umfassendes Dashboard für SHAP-basierte Explainability.
 * Nutzt die neuen /api/rag/analytics/shap Endpoints.
 * 
 * Features:
 * - Feature Importance Bar Chart
 * - SHAP Waterfall Visualisierung
 * - Background Data Statistics
 * - Model Information
 */

'use client'

import { useState, useEffect } from 'react'
import { Card } from './ui/Card'
import { Spinner } from './ui/Spinner'

// Types
interface SHAPFeatureImportance {
  feature_name: string
  importance: number
  normalized_importance: number
  description: string
}

interface SHAPWaterfallFeature {
  name: string
  value: number
  shap_value: number
}

interface SHAPWaterfallData {
  base_value: number
  expected_value: number
  prediction: number
  features: SHAPWaterfallFeature[]
}

interface BackgroundDataStats {
  total_records: number
  background_data_shape: number[] | null
  last_update: string | null
  oldest_record: string | null
  newest_record: string | null
}

interface SHAPAnalyticsData {
  feature_importance: SHAPFeatureImportance[]
  waterfall_data: SHAPWaterfallData
  background_data_stats: BackgroundDataStats
  model_info: {
    model_type: string
    explainer_type: string
    n_features: number
    feature_names: string[]
  }
}

interface SHAPAnalyticsDashboardProps {
  query: string
  chunkId?: string
}

export default function SHAPAnalyticsDashboard({ query, chunkId }: SHAPAnalyticsDashboardProps) {
  const [data, setData] = useState<SHAPAnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSHAPAnalytics()
  }, [query, chunkId])

  const fetchSHAPAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({ query })
      if (chunkId) {
        params.append('chunk_id', chunkId)
      }

      const response = await fetch(`/api/rag/analytics/shap?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`)
      }

      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Laden der SHAP Analytics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex flex-col items-center justify-center gap-4">
          <Spinner size="lg" />
          <p className="text-gray-600">Lade SHAP Analytics...</p>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6 bg-red-50 border-red-200">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-semibold text-red-900">Fehler beim Laden</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card className="p-6">
        <p className="text-gray-600">Keine SHAP Analytics verfügbar</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">SHAP Analytics Dashboard</h2>
            <p className="text-gray-600">
              Explainability für Query: <span className="font-medium text-gray-900">&quot;{query}&quot;</span>
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Model</div>
            <div className="font-semibold text-gray-900">{data.model_info.explainer_type}</div>
          </div>
        </div>
      </Card>

      {/* Feature Importance */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
          </svg>
          Feature Importance
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Zeigt welche Features am meisten zum Ranking-Score beitragen
        </p>

        <div className="space-y-4">
          {data.feature_importance.map((item, index) => (
            <div key={item.feature_name}>
              <div className="flex justify-between items-center mb-2">
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    #{index + 1} {item.feature_name.replace(/_/g, ' ')}
                  </span>
                  <span className="ml-2 text-xs text-gray-500">
                    {item.description}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-gray-700">
                    {(item.normalized_importance * 100).toFixed(1)}%
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    item.importance >= 0 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {item.importance >= 0 ? '+' : ''}{item.importance.toFixed(3)}
                  </span>
                </div>
              </div>
              <div className="relative w-full h-8 bg-gray-200 rounded-lg overflow-hidden">
                <div
                  className={`absolute h-full transition-all duration-500 ${
                    item.importance >= 0 
                      ? 'bg-gradient-to-r from-green-500 to-green-600' 
                      : 'bg-gradient-to-r from-red-500 to-red-600'
                  }`}
                  style={{ width: `${item.normalized_importance * 100}%` }}
                />
                <div className="absolute inset-0 flex items-center px-3 text-xs font-medium text-white">
                  {item.feature_name}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Waterfall Chart */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clipRule="evenodd" />
          </svg>
          SHAP Waterfall Chart
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Zeigt wie jedes Feature zur finalen Prediction beiträgt (Base Value → Prediction)
        </p>

        <div className="space-y-3">
          {/* Base Value */}
          <div className="flex items-center gap-4">
            <div className="w-36 text-sm font-semibold text-gray-700">Base Value</div>
            <div className="flex-1 relative h-10 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className="absolute h-full bg-gradient-to-r from-blue-500 to-blue-600"
                style={{ width: `${(data.waterfall_data.base_value / data.waterfall_data.prediction) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white drop-shadow">
                {data.waterfall_data.base_value.toFixed(3)}
              </div>
            </div>
          </div>

          {/* Features */}
          {data.waterfall_data.features
            .filter(f => Math.abs(f.shap_value) > 0.001)
            .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
            .map((feature, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className="w-36 text-sm text-gray-700 truncate" title={feature.name}>
                  {feature.name.replace(/_/g, ' ')}
                </div>
                <div className="flex-1 relative h-8 bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
                  <div
                    className={`absolute h-full ${
                      feature.shap_value >= 0 
                        ? 'bg-gradient-to-r from-green-400 to-green-500' 
                        : 'bg-gradient-to-r from-red-400 to-red-500'
                    }`}
                    style={{
                      width: `${Math.abs(feature.shap_value) / Math.abs(data.waterfall_data.prediction) * 100}%`,
                      [feature.shap_value >= 0 ? 'left' : 'right']: '0'
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-between px-3 text-xs">
                    <span className="font-medium text-gray-700">Value: {feature.value.toFixed(2)}</span>
                    <span className="font-bold text-white drop-shadow">
                      {feature.shap_value >= 0 ? '+' : ''}{feature.shap_value.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
            ))}

          {/* Final Prediction */}
          <div className="flex items-center gap-4 pt-3 border-t-2 border-gray-300 mt-3">
            <div className="w-36 text-sm font-bold text-gray-900">Final Prediction</div>
            <div className="flex-1 relative h-12 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-lg overflow-hidden border-2 border-indigo-300">
              <div
                className="absolute h-full bg-gradient-to-r from-indigo-600 to-purple-600"
                style={{ width: '100%' }}
              />
              <div className="absolute inset-0 flex items-center justify-center text-lg font-bold text-white drop-shadow-lg">
                {data.waterfall_data.prediction.toFixed(3)}
              </div>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center gap-6 text-xs text-gray-600 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gradient-to-r from-green-400 to-green-500 rounded" />
            <span>Positiver Beitrag (erhöht Score)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gradient-to-r from-red-400 to-red-500 rounded" />
            <span>Negativer Beitrag (senkt Score)</span>
          </div>
        </div>
      </Card>

      {/* Background Data Stats */}
      <Card className="p-6 bg-gradient-to-br from-gray-50 to-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
          </svg>
          Background Data Statistics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Total Records</div>
            <div className="text-2xl font-bold text-gray-900">
              {data.background_data_stats.total_records}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Data Shape</div>
            <div className="text-xl font-semibold text-gray-900">
              {data.background_data_stats.background_data_shape 
                ? `${data.background_data_stats.background_data_shape[0]} × ${data.background_data_stats.background_data_shape[1]}`
                : 'N/A'}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Features</div>
            <div className="text-2xl font-bold text-gray-900">
              {data.model_info.n_features}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Model Type</div>
            <div className="text-sm font-semibold text-gray-900">
              {data.model_info.model_type}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

