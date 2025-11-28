/**
 * Query Comparison Panel Component
 * 
 * Vergleicht SHAP-Daten zwischen zwei Queries.
 * 
 * NEU v2.10.0
 */

'use client'

import { useState } from 'react'
import { MessageSquare, TrendingUp, TrendingDown, Minus, X } from 'lucide-react'
import SHAPSummaryPlot from './SHAPSummaryPlot'

interface QueryComparisonPanelProps {
  query1?: string
  query2?: string
  onClose?: () => void
}

export default function QueryComparisonPanel({ query1, query2, onClose }: QueryComparisonPanelProps) {
  const [data1, setData1] = useState<any>(null)
  const [data2, setData2] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // TODO: Lade Daten für beide Queries
  // Für jetzt: Placeholder

  return (
    <div className="bg-white rounded-xl border-2 border-blue-200 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-blue-600" />
          Query-Vergleich
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Query 1 */}
        <div className="border-2 border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <h4 className="font-semibold text-gray-900">Query 1</h4>
          </div>
          {query1 ? (
            <div>
              <p className="text-sm text-gray-700 mb-2">&quot;{query1}&quot;</p>
              {data1 ? (
                <SHAPSummaryPlot
                  shapData={data1}
                  title="SHAP-Analyse"
                />
              ) : (
                <p className="text-sm text-gray-500">Keine Daten verfügbar</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Wähle eine Query aus</p>
          )}
        </div>

        {/* Query 2 */}
        <div className="border-2 border-purple-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <h4 className="font-semibold text-gray-900">Query 2</h4>
          </div>
          {query2 ? (
            <div>
              <p className="text-sm text-gray-700 mb-2">&quot;{query2}&quot;</p>
              {data2 ? (
                <SHAPSummaryPlot
                  shapData={data2}
                  title="SHAP-Analyse"
                />
              ) : (
                <p className="text-sm text-gray-500">Keine Daten verfügbar</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Wähle eine Query aus</p>
          )}
        </div>
      </div>

      {/* Vergleich */}
      {data1 && data2 && (
        <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-3">Vergleich</h4>
          <p className="text-sm text-gray-600">
            Vergleichs-Funktionalität wird implementiert...
          </p>
        </div>
      )}
    </div>
  )
}

