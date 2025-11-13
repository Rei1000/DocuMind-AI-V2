/**
 * SHAP Comparison Panel Component
 * 
 * Vergleicht Hybrid-SHAP (7 Features) vs ML-SHAP (11 Features)
 * Zeigt Feature Importance und Waterfall Charts nebeneinander
 */

'use client'

import { useState } from 'react'

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
}

export default function SHAPComparisonPanel({
  hybridShap,
  mlShap,
  query
}: SHAPComparisonPanelProps) {
  const [activeTab, setActiveTab] = useState<'hybrid' | 'ml' | 'comparison'>('comparison')

  if (!hybridShap && !mlShap) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-600">Keine SHAP-Daten verfügbar. Stelle eine Query um SHAP-Analysen zu sehen.</p>
      </div>
    )
  }

  const renderFeatureImportance = (shap: SHAPExplanation, title: string, color: string) => {
    const sortedFeatures = Object.entries(shap.feature_importance)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)  // Top 10

    return (
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900">{title}</h4>
        {sortedFeatures.map(([feature, importance], index) => (
          <div key={feature}>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-700">
                #{index + 1} {feature.replace(/_/g, ' ')}
              </span>
              <span className="text-sm font-semibold text-gray-900">
                {(importance * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full bg-gradient-to-r ${color}`}
                style={{ width: `${Math.min(importance * 100, 100)}%` }}
              />
            </div>
          </div>
        ))}
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
    </div>
  )
}

