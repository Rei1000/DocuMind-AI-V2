/**
 * SHAP Waterfall Chart Component (Improved)
 * 
 * Visualisiert SHAP-Werte als Waterfall-Chart.
 * Zeigt, wie jeder Feature zum finalen Score beiträgt.
 * 
 * NEU v2.10.0: Unterstützt Daten aus analytics.scores
 */

'use client'

import { Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface SHAPWaterfallChartProps {
  shapData: {
    base_value?: number
    prediction?: number
    feature_importance?: Record<string, number>
    shap_values?: number[]
    feature_names?: string[]
  }
  title?: string
}

export default function SHAPWaterfallChartImproved({ shapData, title = 'SHAP Waterfall Plot' }: SHAPWaterfallChartProps) {
  if (!shapData) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900">Keine SHAP-Daten verfügbar</h3>
            <p className="text-sm text-blue-800 mt-1">
              Es wurden keine SHAP-Daten für diese Analyse gefunden.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Extrahiere Daten
  const baseValue = shapData.base_value ?? 0.5
  const prediction =
    shapData.prediction ??
    (shapData.feature_importance
      ? Object.values(shapData.feature_importance).reduce(
          (sum, val) => sum + (typeof val === 'number' ? val : 0),
          baseValue
        )
      : baseValue)

  // Erstelle Features-Array
  let features: Array<{ name: string; value: number }> = []
  
  if (shapData.shap_values && shapData.feature_names && shapData.shap_values.length === shapData.feature_names.length) {
    // Verwende echte SHAP-Werte
    features = shapData.feature_names.map((name, i) => ({
      name,
      value: shapData.shap_values![i]
    }))
  } else if (shapData.feature_importance) {
    // Verwende feature_importance
    features = Object.entries(shapData.feature_importance).map(([name, value]) => ({
      name,
      value: typeof value === 'number' ? value : 0
    }))
  }

  // Sortiere Features nach absoluten SHAP-Werten (höchste zuerst)
  features.sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  // Berechne kumulative Werte für Waterfall
  let cumulative = baseValue
  const waterfallData = features.map(({ name, value }) => {
    const before = cumulative
    cumulative += value
    return {
      name: name.replace(/_/g, ' '),
      value,
      before,
      after: cumulative
    }
  })

  // Normalisiere für Visualisierung
  const allValues = [baseValue, ...features.map(f => f.value), prediction]
  const maxAbsValue = Math.max(...allValues.map(v => Math.abs(v)))
  const minValue = Math.min(...allValues)
  const maxValue = Math.max(...allValues)
  const range = maxValue - minValue || 1

  const formatFeatureName = (name: string) => {
    if (name.length > 25) {
      return name.substring(0, 22) + '...'
    }
    return name
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          <Tooltip
            icon
            content={
              <div className="space-y-2 max-w-md">
                <p className="font-semibold">SHAP Waterfall Plot</p>
                <p className="text-xs">
                  Zeigt, wie jeder Feature zum finalen Score beiträgt. 
                  Startet beim Base Value und zeigt die kumulativen Beiträge jedes Features.
                </p>
                <p className="text-xs">
                  <strong>Base Value:</strong> Durchschnittlicher Score (Referenzpunkt)<br />
                  <strong>Features:</strong> Beiträge einzelner Features (positiv/negativ)<br />
                  <strong>Prediction:</strong> Finaler Score = Base Value + Summe aller Features
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  Diese Visualisierung hilft zu verstehen, wie der finale Score zustande kommt.
                </p>
              </div>
            }
          />
        </div>
      </div>

      <div className="space-y-3">
        {/* Base Value */}
        <div className="flex items-center gap-4">
          <div className="w-40 text-sm font-medium text-gray-700">Base Value</div>
          <div className="flex-1 relative h-10 bg-gray-100 rounded-lg overflow-hidden border border-gray-300">
            <div
              className={`absolute h-full ${
                baseValue >= 0 ? 'bg-blue-500' : 'bg-red-500'
              }`}
              style={{
                width: `${((baseValue - minValue) / range) * 100}%`,
                left: '0%'
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white drop-shadow">
              {baseValue.toFixed(3)}
            </div>
          </div>
        </div>

        {/* Features */}
        {waterfallData.slice(0, 10).map((item, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="w-40 text-sm text-gray-700 truncate" title={item.name}>
              {formatFeatureName(item.name)}
            </div>
            <div className="flex-1 relative h-8">
              {/* Before (kumulativer Wert vor diesem Feature) */}
              <div
                className="absolute h-8 bg-gray-200 rounded-l-lg border-r-2 border-gray-400"
                style={{
                  width: `${((item.before - minValue) / range) * 100}%`,
                  left: '0%'
                }}
              />
              {/* Contribution (Beitrag dieses Features) */}
              <div
                className={`absolute h-8 rounded-r-lg ${
                  item.value >= 0 
                    ? 'bg-gradient-to-r from-green-400 to-green-500' 
                    : 'bg-gradient-to-r from-red-400 to-red-500'
                }`}
                style={{
                  width: `${(Math.abs(item.value) / range) * 100}%`,
                  left: `${((item.before - minValue) / range) * 100}%`
                }}
              />
              <div className="absolute inset-0 flex items-center justify-between px-3 text-xs">
                <span className="font-medium text-gray-700">→</span>
                <span className={`font-bold ${item.value >= 0 ? 'text-green-900' : 'text-red-900'} drop-shadow`}>
                  {item.value >= 0 ? '+' : ''}{item.value.toFixed(3)}
                </span>
              </div>
            </div>
          </div>
        ))}

        {/* Final Prediction */}
        <div className="flex items-center gap-4 pt-3 border-t-2 border-gray-400 mt-3">
          <div className="w-40 text-sm font-bold text-gray-900">Final Score</div>
          <div className="flex-1 relative h-12 bg-gray-100 rounded-lg overflow-hidden border-2 border-gray-400">
            <div
              className={`absolute h-full ${
                prediction >= 0 ? 'bg-gradient-to-r from-blue-600 to-blue-700' : 'bg-gradient-to-r from-red-600 to-red-700'
              }`}
              style={{
                width: `${((prediction - minValue) / range) * 100}%`,
                left: '0%'
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-base font-bold text-white drop-shadow-lg">
              {prediction.toFixed(3)}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded"></div>
          <span>Base Value (Referenzpunkt)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Positiver Beitrag</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Negativer Beitrag</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-200 rounded border border-gray-400"></div>
          <span>Kumulativer Wert</span>
        </div>
      </div>

      {/* Info */}
      <div className="mt-4 text-xs text-gray-500">
        <p>
          <strong>Formel:</strong> Final Score = Base Value ({baseValue.toFixed(3)}) + Summe aller Features ({features.reduce((sum, f) => sum + f.value, 0).toFixed(3)}) = {prediction.toFixed(3)}
        </p>
        {features.length > 10 && (
          <p className="mt-1">
            Zeige Top 10 von {features.length} Features. Die restlichen Features haben kleinere Beiträge.
          </p>
        )}
      </div>
    </div>
  )
}

