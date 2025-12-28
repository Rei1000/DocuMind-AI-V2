/**
 * SHAP Dependence Plot Component
 * 
 * Visualisiert die Beziehung zwischen Feature-Werten und SHAP-Werten.
 * Zeigt nichtlineare Effekte und Feature-Interaktionen.
 * 
 * NEU v2.10.0
 */

'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, Cell } from 'recharts'
import { Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface SHAPDependencePlotProps {
  shapData: {
    feature_importance?: Record<string, number>
    shap_values?: number[]
    feature_names?: string[]
    feature_values?: number[] // Optional: Feature-Werte
  }
  title?: string
}

export default function SHAPDependencePlot({ shapData, title = 'SHAP Dependence Plot' }: SHAPDependencePlotProps) {
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
  let features: Array<{ name: string; shapValue: number; featureValue?: number }> = []
  
  if (shapData.shap_values && shapData.feature_names && shapData.shap_values.length === shapData.feature_names.length) {
    features = shapData.feature_names.map((name, i) => ({
      name,
      shapValue: shapData.shap_values![i],
      featureValue: shapData.feature_values?.[i]
    }))
  } else if (shapData.feature_importance) {
    features = Object.entries(shapData.feature_importance).map(([name, value]) => ({
      name,
      shapValue: typeof value === 'number' ? value : 0
    }))
  }

  // Sortiere Features nach absoluten SHAP-Werten
  features.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue))

  // Bereite Daten für Scatter Plot vor
  // X = Feature Value (normalisiert), Y = SHAP Value
  const scatterData = features.map((feature) => {
    // Normalisiere Feature-Wert (falls vorhanden) oder verwende Index
    const featureValue = feature.featureValue !== undefined 
      ? feature.featureValue 
      : Math.abs(feature.shapValue) // Fallback: verwende absoluten SHAP-Wert als Proxy
    
    return {
      x: featureValue,
      y: feature.shapValue,
      name: feature.name.replace(/_/g, ' '),
      absShapValue: Math.abs(feature.shapValue),
      isPositive: feature.shapValue >= 0
    }
  })

  const formatFeatureName = (name: string) => {
    if (name.length > 25) {
      return name.substring(0, 22) + '...'
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
                <p className="font-semibold">SHAP Dependence Plot</p>
                <p className="text-xs">
                  Zeigt die Beziehung zwischen Feature-Werten und SHAP-Werten.
                  Hilft zu verstehen, wie Feature-Werte den Score beeinflussen.
                </p>
                <p className="text-xs">
                  <strong>X-Achse:</strong> Feature-Wert (normalisiert)<br />
                  <strong>Y-Achse:</strong> SHAP-Wert (Beitrag zum Score)
                </p>
                <p className="text-xs">
                  <strong>Interpretation:</strong><br />
                  • Steigende Linie: Höhere Feature-Werte = höherer Score<br />
                  • Fallende Linie: Höhere Feature-Werte = niedrigerer Score<br />
                  • Nichtlinear: Komplexe Beziehung
                </p>
                <p className="text-xs text-gray-300 mt-2">
                  Diese Visualisierung hilft zu verstehen, welche Feature-Werte optimal sind.
                </p>
              </div>
            }
          />
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="x"
            domain={['auto', 'auto']}
            label={{ value: 'Feature-Wert (normalisiert)', position: 'insideBottom', offset: -5 }}
            tickFormatter={(value) => value.toFixed(2)}
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
                      <strong>Feature-Wert:</strong> {data.x.toFixed(3)}
                    </p>
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

      {/* Feature-Liste mit Werten */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
        {features.slice(0, 8).map((feature, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: getColor(feature.shapValue) }}
              />
              <span className="text-sm text-gray-700 font-medium">
                {formatFeatureName(feature.name)}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              {feature.featureValue !== undefined && (
                <span className="text-gray-600">
                  Wert: <strong>{feature.featureValue.toFixed(2)}</strong>
                </span>
              )}
              <span className={`font-bold ${feature.shapValue >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                SHAP: {feature.shapValue >= 0 ? '+' : ''}{feature.shapValue.toFixed(3)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3 border border-blue-200">
        <p className="font-semibold text-blue-900 mb-1">💡 Hinweis:</p>
        <p className="text-blue-800">
          Dieser Plot zeigt die Beziehung zwischen Feature-Werten und SHAP-Werten für diesen spezifischen Chunk.
          Für eine vollständige Dependence-Analyse benötigt man Daten von mehreren Instanzen.
        </p>
      </div>
    </div>
  )
}

