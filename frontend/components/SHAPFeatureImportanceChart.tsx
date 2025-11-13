/**
 * SHAP Feature Importance Chart Component.
 * 
 * Visualisiert die Feature-Importance aus SHAP-Erklärungen.
 * 
 * TDD Phase 3: GREEN - Minimaler Code für Tests.
 */

'use client'

import { SHAPExplanationResponse } from '@/lib/api/rag'

interface SHAPFeatureImportanceChartProps {
  explanation: {
    feature_importance: Record<string, number>
    base_value: number
    prediction: number
    query: string
    chunk_id: string
    timestamp: string
    features: Record<string, number>
  }
}

export default function SHAPFeatureImportanceChart({ explanation }: SHAPFeatureImportanceChartProps) {
  const { feature_importance } = explanation
  
  // Sortiere Features nach Importance (höchste zuerst)
  const sortedFeatures = Object.entries(feature_importance)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
  
  if (sortedFeatures.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600">Keine Features verfügbar</p>
      </div>
    )
  }
  
  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">SHAP Feature Importance</h3>
      
      <div className="space-y-2">
        {sortedFeatures.map(([feature, importance]) => (
          <div key={feature} className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">{feature}</span>
                <span className="text-sm text-gray-600">
                  {(Math.abs(importance) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    importance >= 0 ? 'bg-blue-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.abs(importance) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

