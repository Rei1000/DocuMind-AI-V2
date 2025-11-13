/**
 * Search Quality Analysis Component
 * 
 * Zeigt detaillierte Analyse der Suchqualität:
 * - Dokument-Typ-Verteilung in Suchergebnissen
 * - Score-Verteilung
 * - Warum wurden bestimmte Dokumente gefunden/nicht gefunden
 * - SHAP-basierte Erklärungen
 */

'use client'

import { useState } from 'react'
import { BarChart3, TrendingDown, TrendingUp, AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface SearchQualityAnalysisProps {
  data: {
    documentTypeDistribution: Array<{
      document_type: string
      count: number
      average_score: number
      found_in_top_k: number
    }>
    scoreDistribution: {
      min: number
      max: number
      average: number
      median: number
    }
    topQueries: Array<{
      query: string
      document_types_found: string[]
      missing_document_types: string[]
      average_score: number
    }>
    shapInsights: Array<{
      feature: string
      impact: number
      explanation: string
    }>
  }
}

export default function SearchQualityAnalysis({ data }: SearchQualityAnalysisProps) {
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null)

  // Fallback für leere Daten
  if (!data || !data.documentTypeDistribution || data.documentTypeDistribution.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600">Keine Search Quality Daten verfügbar</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          Search Quality Analysis
        </h2>
      </div>

      {/* Dokument-Typ-Verteilung */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Dokument-Typ-Verteilung in Suchergebnissen
        </h3>
        <div className="space-y-4">
          {data.documentTypeDistribution.map((item, index) => (
            <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-900">{item.document_type}</span>
                  <span className="text-sm text-gray-500">
                    {item.found_in_top_k} von {item.count} in Top-K
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Ø Score</div>
                    <div className="text-lg font-bold text-gray-900">
                      {(item.average_score * 100).toFixed(2)}%
                    </div>
                  </div>
                  {item.found_in_top_k === 0 && item.count > 0 && (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                  {item.found_in_top_k > 0 && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(item.found_in_top_k / item.count) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Score-Verteilung */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Min Score</div>
          <div className="text-2xl font-bold text-gray-900">
            {(data.scoreDistribution.min * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Max Score</div>
          <div className="text-2xl font-bold text-gray-900">
            {(data.scoreDistribution.max * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Ø Score</div>
          <div className="text-2xl font-bold text-gray-900">
            {(data.scoreDistribution.average * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-1">Median Score</div>
          <div className="text-2xl font-bold text-gray-900">
            {(data.scoreDistribution.median * 100).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Top Queries Analysis */}
      {data.topQueries.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Query-Analyse: Gefundene vs. Fehlende Dokument-Typen
          </h3>
          <div className="space-y-4">
            {data.topQueries.map((query, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedQuery === query.query
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedQuery(selectedQuery === query.query ? null : query.query)}
              >
                <div className="font-medium text-gray-900 mb-2">"{query.query}"</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Gefundene Typen:</div>
                    <div className="flex flex-wrap gap-1">
                      {query.document_types_found.length > 0 ? (
                        query.document_types_found.map((type, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded"
                          >
                            <CheckCircle className="w-3 h-3" />
                            {type}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">Keine</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Fehlende Typen:</div>
                    <div className="flex flex-wrap gap-1">
                      {query.missing_document_types.length > 0 ? (
                        query.missing_document_types.map((type, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-800 text-xs rounded"
                          >
                            <XCircle className="w-3 h-3" />
                            {type}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">Keine</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  Ø Score: {(query.average_score * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SHAP Insights */}
      {data.shapInsights.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            SHAP-basierte Insights: Warum wurden Dokumente gefunden/nicht gefunden?
          </h3>
          <div className="space-y-3">
            {data.shapInsights.map((insight, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900">{insight.feature}</span>
                  <span className="text-sm text-gray-600">
                    Impact: {(insight.impact * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-gray-600">{insight.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

