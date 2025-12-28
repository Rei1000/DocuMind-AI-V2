'use client'

import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Info, ExternalLink } from 'lucide-react'
import Tooltip from './ui/Tooltip'
import SHAPFeatureDetailModal from './SHAPFeatureDetailModal'

interface SHAPFeature {
  feature_name: string
  shap_value: number
}

interface SHAPBarChartProps {
  features: SHAPFeature[]
  title?: string
  showPositiveOnly?: boolean
  maxFeatures?: number
  query?: string
  chunkText?: string
}

export default function SHAPBarChart({
  features,
  title = 'SHAP Feature Importance',
  showPositiveOnly = false,
  maxFeatures = 10,
  query,
  chunkText
}: SHAPBarChartProps) {
  const [selectedFeature, setSelectedFeature] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Extrahiere Keyword Matches
  const extractKeywordMatches = (query?: string, chunkText?: string): string[] => {
    if (!chunkText || !query) return []
    const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 2)
    const chunkWords = chunkText.toLowerCase()
    return queryWords.filter(word => chunkWords.includes(word))
  }

  const handleFeatureClick = (featureName: string, shapValue: number) => {
    const keywordMatches = extractKeywordMatches(query, chunkText)
    
    setSelectedFeature({
      feature_name: featureName,
      shap_value: shapValue,
      keyword_matches: keywordMatches,
      query: query,
      chunk_text: chunkText,
      responsible_text: featureName === 'text_score' && keywordMatches.length > 0
        ? `Diese Wörter tragen zum Text-Score bei: ${keywordMatches.join(', ')}`
        : undefined
    })
    setIsModalOpen(true)
  }
  if (!features || features.length === 0) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900">Keine SHAP-Daten verfügbar</h3>
            <p className="text-sm text-blue-800 mt-1">
              Es wurden keine SHAP-Feature-Importance-Daten für diese Analyse gefunden.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Sortiere Features nach absoluten SHAP-Werten (höchste zuerst)
  const sortedFeatures = [...features]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, maxFeatures)

  // Filtere nur positive Features wenn gewünscht
  const displayFeatures = showPositiveOnly
    ? sortedFeatures.filter(f => f.shap_value > 0)
    : sortedFeatures

  // Bereite Daten für Recharts vor
  const chartData = displayFeatures.map(feature => ({
    feature: feature.feature_name.replace(/_/g, ' '),
    shapValue: feature.shap_value,
    absValue: Math.abs(feature.shap_value),
    isPositive: feature.shap_value >= 0
  }))

  // Sortiere für Chart: Positive oben, negative unten
  chartData.sort((a, b) => {
    if (a.isPositive && !b.isPositive) return -1
    if (!a.isPositive && b.isPositive) return 1
    return b.absValue - a.absValue
  })

  // Farben für positive/negative Werte
  const getColor = (isPositive: boolean) => {
    return isPositive ? '#3b82f6' : '#ef4444' // blue-500 : red-500
  }

  const formatFeatureName = (name: string) => {
    // Kürze lange Feature-Namen
    if (name.length > 20) {
      return name.substring(0, 17) + '...'
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
                <p className="font-semibold">SHAP Feature Importance Bar Chart</p>
                <p className="text-xs">
                  Zeigt die Beiträge einzelner Features zum Ranking-Score.
                  Positive Werte (blau) erhöhen den Score, negative Werte (rot) senken ihn.
                </p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li><strong>Positive SHAP-Werte:</strong> Feature erhöht den Score</li>
                  <li><strong>Negative SHAP-Werte:</strong> Feature senkt den Score</li>
                  <li><strong>Größe des Balkens:</strong> Stärke des Beitrags</li>
                </ul>
                <p className="text-xs text-gray-300 mt-2">
                  Diese Visualisierung hilft zu verstehen, welche Features am meisten zum Ranking beitragen.
                </p>
              </div>
            }
          />
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>Positiv</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>Negativ</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={Math.max(300, displayFeatures.length * 40)}>
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
            dataKey="feature"
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
          <Legend
            formatter={(value) => {
              if (value === 'shapValue') return 'SHAP-Wert'
              return value
            }}
          />
          <Bar
            dataKey="shapValue"
            name="SHAP-Wert"
            radius={[0, 4, 4, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.isPositive)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Zusammenfassung mit klickbaren Links */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-900">Positivste Features</span>
          </div>
          <div className="text-xs text-blue-800 space-y-1">
            {chartData
              .filter(f => f.isPositive)
              .slice(0, 2)
              .map((f, index) => {
                const originalFeature = displayFeatures.find(feat => feat.feature_name.replace(/_/g, ' ') === f.feature)
                return (
                  <div key={index} className="flex items-center gap-2 group">
                    <span>{f.feature}</span>
                    {originalFeature && (
                      <button
                        onClick={() => handleFeatureClick(originalFeature.feature_name, originalFeature.shap_value)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-800"
                        title="Details anzeigen"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                )
              })}
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-3 border border-red-200">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="w-4 h-4 text-red-600" />
            <span className="text-sm font-semibold text-red-900">Negativste Features</span>
          </div>
          <div className="text-xs text-red-800 space-y-1">
            {chartData
              .filter(f => !f.isPositive)
              .slice(0, 2)
              .map((f, index) => {
                const originalFeature = displayFeatures.find(feat => feat.feature_name.replace(/_/g, ' ') === f.feature)
                return originalFeature ? (
                  <div key={index} className="flex items-center gap-2 group">
                    <span>{f.feature}</span>
                    <button
                      onClick={() => handleFeatureClick(originalFeature.feature_name, originalFeature.shap_value)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-red-600 hover:text-red-800"
                      title="Details anzeigen"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <span key={index}>{f.feature}</span>
                )
              }) || <span>Keine</span>}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="text-sm font-semibold text-gray-900 mb-1">Gesamt-Features</div>
          <div className="text-xs text-gray-700">
            {displayFeatures.length} von {features.length} Features angezeigt
          </div>
        </div>
      </div>

      {/* Feature Detail Modal */}
      {selectedFeature && (
        <SHAPFeatureDetailModal
          feature={selectedFeature}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false)
            setSelectedFeature(null)
          }}
        />
      )}
    </div>
  )
}

