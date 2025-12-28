/**
 * SHAP Beeswarm Plot Component
 * 
 * Visualisiert die Verteilung der SHAP-Werte für alle Features.
 * Zeigt sowohl die Bedeutung als auch den Effekt jedes Features.
 * 
 * NEU v2.10.0
 */

'use client'

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts'
import { Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface SHAPBeeswarmPlotProps {
  shapData: {
    feature_importance?: Record<string, number>
    shap_values?: number[]
    feature_names?: string[]
  }
  title?: string
}

export default function SHAPBeeswarmPlot({ shapData, title = 'SHAP Beeswarm Plot' }: SHAPBeeswarmPlotProps) {
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
  let features: Array<{ name: string; value: number; featureValue?: number }> = []
  
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

  // Bereite Daten für Scatter Plot vor
  // Für Beeswarm: X = Feature Index, Y = SHAP Value
  const scatterData = features.map((feature, index) => ({
    x: index,
    y: feature.value,
    name: feature.name.replace(/_/g, ' '),
    absValue: Math.abs(feature.value),
    isPositive: feature.value >= 0
  }))

  const formatFeatureName = (name: string) => {
    if (name.length > 30) {
      return name.substring(0, 27) + '...'
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

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          <Tooltip
            icon
            content={
              <div className="space-y-2 max-w-md">
                <p className="font-semibold">SHAP Beeswarm Plot</p>
                <p className="text-xs">
                  Zeigt die Verteilung der SHAP-Werte für alle Features. 
                  Jeder Punkt repräsentiert ein Feature.
                </p>
                <p className="text-xs">
                  <strong>X-Achse:</strong> Features (sortiert nach Wichtigkeit)<br />
                  <strong>Y-Achse:</strong> SHAP-Wert (positiv = erhöht Score, negativ = senkt Score)
                </p>
                <p className="text-xs">
                  <strong>Farben:</strong><br />
                  • Grün: Starker positiver Beitrag<br />
                  • Blau: Positiver Beitrag<br />
                  • Gelb: Negativer Beitrag<br />
                  • Rot: Starker negativer Beitrag
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  Diese Visualisierung hilft zu verstehen, welche Features am wichtigsten sind.
                </p>
              </div>
            }
          />
        </div>
      </div>

      <ResponsiveContainer width="100%" height={Math.max(400, features.length * 30)}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 60, left: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="x"
            domain={[-0.5, features.length - 0.5]}
            tick={false}
            label={{ value: 'Features (sortiert nach Wichtigkeit)', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={['auto', 'auto']}
            label={{ value: 'SHAP-Wert', angle: -90, position: 'insideLeft' }}
            tickFormatter={(value) => value.toFixed(2)}
          />
          <RechartsTooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload
                return (
                  <div className="bg-white border border-gray-300 rounded-lg p-3 shadow-lg">
                    <p className="font-semibold text-gray-900 mb-1">{data.name}</p>
                    <p className="text-sm text-gray-700">
                      <strong>SHAP-Wert:</strong> {data.y.toFixed(4)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {data.isPositive ? 'Erhöht den Score' : 'Senkt den Score'}
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Scatter
            name="Features"
            data={scatterData}
            fill="#8884d8"
          >
            {scatterData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.y)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Feature Labels */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 text-xs">
        {features.slice(0, 12).map((feature, index) => (
          <div
            key={index}
            className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200"
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getColor(feature.value) }}
            />
            <span className="text-gray-700 truncate" title={feature.name}>
              {formatFeatureName(feature.name)}
            </span>
            <span className={`font-semibold ${feature.value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {feature.value >= 0 ? '+' : ''}{feature.value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded-full"></div>
          <span>Starker positiver Beitrag (&gt; 0.1)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
          <span>Positiver Beitrag (0.05 - 0.1)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-amber-500 rounded-full"></div>
          <span>Negativer Beitrag (-0.05 - 0)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded-full"></div>
          <span>Starker negativer Beitrag (&lt; -0.05)</span>
        </div>
      </div>
    </div>
  )
}

