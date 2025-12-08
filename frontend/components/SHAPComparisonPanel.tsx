/**
 * SHAP Comparison Panel Component
 * 
 * Vergleicht Hybrid-SHAP (7 Features) vs ML-SHAP (11 Features)
 * Zeigt Feature Importance und Waterfall Charts nebeneinander
 */

'use client'

import { useState } from 'react'
import SHAPFeatureDetailModal from './SHAPFeatureDetailModal'
import { ExternalLink, Info } from 'lucide-react'

interface SHAPExplanation {
  feature_importance: Record<string, number>
  base_value: number
  prediction: number
  shap_values: number[]
  feature_names: string[]
}

interface SHAPComparisonPanelProps {
  hybridShap?: SHAPExplanation
  mlShap?: SHAPExplanation
  query: string
  chunkText?: string
  chunkMetadata?: any
}

// Helper function to format scores
const formatScore = (score: number) => (score * 100).toFixed(1) + '%'

export default function SHAPComparisonPanel({
  hybridShap,
  mlShap,
  query,
  chunkText,
  chunkMetadata
}: SHAPComparisonPanelProps) {
  const [activeTab, setActiveTab] = useState<'hybrid' | 'ml' | 'comparison'>('comparison')
  const [selectedFeature, setSelectedFeature] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (!hybridShap && !mlShap) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-600">Keine SHAP-Daten verfügbar. Stelle eine Query um SHAP-Analysen zu sehen.</p>
      </div>
    )
  }

  // Extrahiere Keyword Matches aus Query und Chunk-Text
  const extractKeywordMatches = (query: string, chunkText?: string): string[] => {
    if (!chunkText || !query) return []
    const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 2)
    const chunkWords = chunkText.toLowerCase()
    return queryWords.filter(word => chunkWords.includes(word))
  }

  // Hole Feature-Wert aus Metadaten
  const getFeatureValue = (featureName: string, shap: SHAPExplanation): number | string | undefined => {
    const featureIndex = shap.feature_names?.indexOf(featureName)
    if (featureIndex !== undefined && featureIndex >= 0 && shap.shap_values) {
      // Feature-Wert ist nicht direkt verfügbar, aber wir können den SHAP-Wert verwenden
      return shap.shap_values[featureIndex]
    }
    return shap.feature_importance[featureName]
  }

  const handleFeatureClick = (featureName: string, shap: SHAPExplanation, shapValue: number) => {
    const featureValue = getFeatureValue(featureName, shap)
    const keywordMatches = extractKeywordMatches(query, chunkText)
    
    setSelectedFeature({
      feature_name: featureName,
      shap_value: shapValue,
      feature_value: featureValue,
      keyword_matches: keywordMatches,
      query: query,
      chunk_text: chunkText,
      responsible_text: featureName === 'text_score' && keywordMatches.length > 0
        ? `Diese Wörter tragen zum Text-Score bei: ${keywordMatches.join(', ')}`
        : undefined
    })
    setIsModalOpen(true)
  }

  const renderFeatureImportance = (shap: SHAPExplanation, title: string, color: string) => {
    const sortedFeatures = Object.entries(shap.feature_importance)
      .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
      .slice(0, 10)  // Top 10

    return (
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900">{title}</h4>
        {sortedFeatures.map(([feature, importance], index) => {
          const isPositive = importance >= 0
          const keywordMatches = feature === 'keyword_matches' || feature === 'text_score'
            ? extractKeywordMatches(query, chunkText)
            : []
          
          // Benutzerfreundliche Anzeige
          const getDisplayValue = (featureName: string, value: number): string => {
            switch (featureName) {
              case 'user_level':
                const level = Math.round(value * 5)
                return `Level ${level} von 5`
              case 'keyword_matches':
                return keywordMatches.length > 0 
                  ? `${keywordMatches.length} Keywords: ${keywordMatches.slice(0, 3).join(', ')}${keywordMatches.length > 3 ? '...' : ''}`
                  : `${Math.round(value)} Keywords`
              case 'chunk_length':
                return `${Math.round(value)} Zeichen`
              case 'text_score':
              case 'vector_score':
              case 'bm25_score':
              case 'jaccard_score':
              case 'hybrid_score':
                return `${(value * 100).toFixed(1)}%`
              default:
                return value.toFixed(4)
            }
          }

          return (
            <div key={feature} className="group">
              <div className="flex justify-between items-center mb-1">
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-sm text-gray-700">
                    #{index + 1} {feature.replace(/_/g, ' ')}
                  </span>
                  {keywordMatches.length > 0 && (feature === 'keyword_matches' || feature === 'text_score') && (
                    <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded">
                      {keywordMatches.length} Keywords
                    </span>
                  )}
                  <button
                    onClick={() => handleFeatureClick(feature, shap, importance)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-800"
                    title="Details anzeigen"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">
                    {getDisplayValue(feature, importance)}
                  </span>
                  <span className={`text-sm font-semibold ${isPositive ? 'text-green-700' : 'text-red-700'}`}>
                    {isPositive ? '+' : ''}{(importance * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full bg-gradient-to-r ${isPositive ? color : 'from-red-500 to-red-600'}`}
                  style={{ width: `${Math.min(Math.abs(importance) * 100, 100)}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clipRule="evenodd" />
          </svg>
          SHAP Comparison
        </h3>
        <p className="text-sm text-gray-600">
          Query: <span className="font-medium">&quot;{query}&quot;</span>
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('hybrid')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'hybrid'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Hybrid SHAP (7 Features)
        </button>
        <button
          onClick={() => setActiveTab('ml')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'ml'
              ? 'border-b-2 border-green-600 text-green-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          ML SHAP (11 Features)
        </button>
        <button
          onClick={() => setActiveTab('comparison')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'comparison'
              ? 'border-b-2 border-purple-600 text-purple-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Vergleich
        </button>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'hybrid' && hybridShap && (
          renderFeatureImportance(hybridShap, 'Hybrid SHAP Feature Importance', 'from-blue-500 to-blue-600')
        )}

        {activeTab === 'ml' && mlShap && (
          renderFeatureImportance(mlShap, 'ML SHAP Feature Importance', 'from-green-500 to-green-600')
        )}

        {activeTab === 'comparison' && (
          <div className="grid grid-cols-2 gap-6">
            {hybridShap && (
              <div>
                {renderFeatureImportance(hybridShap, 'Hybrid (7 Features)', 'from-blue-500 to-blue-600')}
              </div>
            )}
            {mlShap && (
              <div>
                {renderFeatureImportance(mlShap, 'ML (11 Features)', 'from-green-500 to-green-600')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Comparison Summary */}
      {activeTab === 'comparison' && hybridShap && mlShap && (
        <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
          <h4 className="font-semibold text-gray-900 mb-2">Vergleich</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Hybrid Prediction:</span>
              <span className="ml-2 font-bold text-blue-700">
                {formatScore(hybridShap.prediction)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">ML Prediction:</span>
              <span className="ml-2 font-bold text-green-700">
                {formatScore(mlShap.prediction)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Hybrid Features:</span>
              <span className="ml-2 font-bold">7</span>
            </div>
            <div>
              <span className="text-gray-600">ML Features:</span>
              <span className="ml-2 font-bold">11</span>
            </div>
          </div>
        </div>
      )}
      
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

