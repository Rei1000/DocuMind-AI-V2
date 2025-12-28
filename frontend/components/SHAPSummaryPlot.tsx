/**
 * SHAP Summary Plot Component
 * 
 * Kombiniert Bar Chart und Beeswarm Plot.
 * Zeigt alle Features auf einen Blick, sortiert nach Wichtigkeit.
 * 
 * NEU v2.10.0
 */

'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts'
import { Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface SHAPSummaryPlotProps {
  shapData: {
    feature_importance?: Record<string, number>
    shap_values?: number[]
    feature_names?: string[]
  }
  title?: string
}

export default function SHAPSummaryPlot({ shapData, title = 'SHAP Summary Plot' }: SHAPSummaryPlotProps) {
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

  // Erstelle Features-Array
  let features: Array<{ name: string; value: number }> = []
  
  if (shapData.shap_values && shapData.feature_names && shapData.shap_values.length === shapData.feature_names.length) {
    features = shapData.feature_names.map((name, i) => ({
      name,
      value: shapData.shap_values![i]
    }))
  } else if (shapData.feature_importance) {
    features = Object.entries(shapData.feature_importance).map(([name, value]) => ({
      name,
      value: typeof value === 'number' ? value : 0
    }))
  }

  // Sortiere Features nach absoluten SHAP-Werten (höchste zuerst)
  features.sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  // Bereite Daten für Bar Chart vor
  const chartData = features.map(feature => ({
    name: feature.name.replace(/_/g, ' '),
    shapValue: feature.value,
    absValue: Math.abs(feature.value),
    isPositive: feature.value >= 0
  }))

  const formatFeatureName = (name: string) => {
    if (name.length > 20) {
      return name.substring(0, 17) + '...'
    }
    return name
  }

  // Farben basierend auf SHAP-Wert
  const getColor = (value: number) => {
    if (value >= 0.1) return '#10b981' // green-500
    if (value >= 0.05) return '#3b82f6' // blue-500
    if (value >= 0) return '#60a5fa' // blue-400
    if (value >= -0.05) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  // Statistiken
  const positiveFeatures = features.filter(f => f.value >= 0)
  const negativeFeatures = features.filter(f => f.value < 0)
  const totalContribution = features.reduce((sum, f) => sum + Math.abs(f.value), 0)
  const avgContribution = totalContribution / features.length

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          <Tooltip
            icon
            content={
              <div className="space-y-2 max-w-md">
                <p className="font-semibold">SHAP Summary Plot</p>
                <p className="text-xs">
                  Übersicht aller Features mit ihren SHAP-Werten.
                  Sortiert nach Wichtigkeit (höchste zuerst).
                </p>
                <p className="text-xs">
                  <strong>Interpretation:</strong><br />
                  • Größere Balken = wichtigeres Feature<br />
                  • Positive Werte (blau/grün) = erhöhen Score<br />
                  • Negative Werte (gelb/rot) = senken Score
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  Diese Visualisierung gibt einen schnellen Überblick über alle Features.
                </p>
              </div>
            }
          />
        </div>
      </div>

      {/* Statistiken */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <div className="text-xs text-blue-600 font-semibold mb-1">Gesamt Features</div>
          <div className="text-2xl font-bold text-blue-900">{features.length}</div>
        </div>
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <div className="text-xs text-green-600 font-semibold mb-1">Positive</div>
          <div className="text-2xl font-bold text-green-900">{positiveFeatures.length}</div>
        </div>
        <div className="bg-red-50 rounded-lg p-3 border border-red-200">
          <div className="text-xs text-red-600 font-semibold mb-1">Negative</div>
          <div className="text-2xl font-bold text-red-900">{negativeFeatures.length}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="text-xs text-gray-600 font-semibold mb-1">Ø Beitrag</div>
          <div className="text-2xl font-bold text-gray-900">{avgContribution.toFixed(3)}</div>
        </div>
      </div>

      {/* Bar Chart */}
      <ResponsiveContainer width="100%" height={Math.max(400, features.length * 35)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            domain={['auto', 'auto']}
            tickFormatter={(value) => value.toFixed(3)}
            label={{ value: 'SHAP-Wert', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fontSize: 12 }}
            tickFormatter={formatFeatureName}
          />
          <RechartsTooltip
            formatter={(value: number) => value.toFixed(4)}
            labelFormatter={(label) => `Feature: ${label}`}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '8px'
            }}
          />
          <Bar
            dataKey="shapValue"
            name="SHAP-Wert"
            radius={[0, 4, 4, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.shapValue)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Top Features */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <h4 className="font-semibold text-green-900 mb-3">Top Positive Features</h4>
          <div className="space-y-2">
            {positiveFeatures.slice(0, 5).map((feature, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-green-800">{formatFeatureName(feature.name)}</span>
                <span className="font-bold text-green-600">+{feature.value.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <h4 className="font-semibold text-red-900 mb-3">Top Negative Features</h4>
          <div className="space-y-2">
            {negativeFeatures.slice(0, 5).map((feature, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-red-800">{formatFeatureName(feature.name)}</span>
                <span className="font-bold text-red-600">{feature.value.toFixed(3)}</span>
              </div>
            ))}
            {negativeFeatures.length === 0 && (
              <p className="text-sm text-red-700 italic">Keine negativen Features</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

