/**
 * SHAP Waterfall Chart Component
 * 
 * Visualisiert SHAP-Werte als Waterfall-Chart.
 * Zeigt, wie jeder Feature zum finalen Score beiträgt.
 */

'use client'

import { SHAPExplanationResponse } from '@/lib/api/rag'

interface SHAPWaterfallChartProps {
  explanation: SHAPExplanationResponse
}

export default function SHAPWaterfallChart({ explanation }: SHAPWaterfallChartProps) {
  const { feature_importance, base_value, prediction } = explanation

  // Sortiere Features nach SHAP-Wert (höchste zuerst)
  const sortedFeatures = Object.entries(feature_importance)
    .map(([feature, value]) => ({ feature, value }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  // Berechne kumulative Werte für Waterfall
  let cumulative = base_value
  const waterfallData = sortedFeatures.map(({ feature, value }) => {
    const before = cumulative
    cumulative += value
    return {
      feature,
      value,
      before,
      after: cumulative
    }
  })

  // Normalisiere für Visualisierung (0-100%)
  const maxAbsValue = Math.max(
    Math.abs(base_value),
    ...Object.values(feature_importance).map(v => Math.abs(v)),
    Math.abs(prediction)
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        SHAP Waterfall Chart
      </h3>
      <div className="space-y-2">
        {/* Base Value */}
        <div className="flex items-center gap-4">
          <div className="w-32 text-sm text-gray-600">Base Value</div>
          <div className="flex-1 relative h-8 bg-gray-100 rounded">
            <div
              className={`absolute h-8 rounded ${
                base_value >= 0 ? 'bg-blue-500' : 'bg-red-500'
              }`}
              style={{
                width: `${(Math.abs(base_value) / maxAbsValue) * 100}%`,
                left: base_value >= 0 ? '0%' : 'auto',
                right: base_value < 0 ? '0%' : 'auto'
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
              {base_value.toFixed(3)}
            </div>
          </div>
        </div>

        {/* Features */}
        {waterfallData.map((item, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="w-32 text-sm text-gray-700 truncate" title={item.feature}>
              {item.feature}
            </div>
            <div className="flex-1 relative h-6">
              {/* Before */}
              <div
                className="absolute h-6 bg-gray-200 rounded-l"
                style={{
                  width: `${(Math.abs(item.before) / maxAbsValue) * 100}%`,
                  left: item.before >= 0 ? '0%' : 'auto',
                  right: item.before < 0 ? '0%' : 'auto'
                }}
              />
              {/* Contribution */}
              <div
                className={`absolute h-6 rounded-r ${
                  item.value >= 0 ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{
                  width: `${(Math.abs(item.value) / maxAbsValue) * 100}%`,
                  left: item.value >= 0 ? `${(Math.abs(item.before) / maxAbsValue) * 100}%` : 'auto',
                  right: item.value < 0 ? `${(Math.abs(item.before) / maxAbsValue) * 100}%` : 'auto'
                }}
              />
              <div className="absolute inset-0 flex items-center justify-end pr-2 text-xs font-medium text-gray-700">
                {item.value >= 0 ? '+' : ''}{item.value.toFixed(3)}
              </div>
            </div>
          </div>
        ))}

        {/* Final Prediction */}
        <div className="flex items-center gap-4 pt-2 border-t border-gray-300">
          <div className="w-32 text-sm font-semibold text-gray-900">Prediction</div>
          <div className="flex-1 relative h-10 bg-gray-100 rounded">
            <div
              className={`absolute h-10 rounded ${
                prediction >= 0 ? 'bg-blue-600' : 'bg-red-600'
              }`}
              style={{
                width: `${(Math.abs(prediction) / maxAbsValue) * 100}%`,
                left: prediction >= 0 ? '0%' : 'auto',
                right: prediction < 0 ? '0%' : 'auto'
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">
              {prediction.toFixed(3)}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500 rounded" />
          <span>Positiver Beitrag</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded" />
          <span>Negativer Beitrag</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-200 rounded" />
          <span>Vorheriger Wert</span>
        </div>
      </div>
    </div>
  )
}



