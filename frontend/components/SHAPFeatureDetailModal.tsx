/**
 * SHAP Feature Detail Modal
 * 
 * Zeigt detaillierte Informationen zu einem SHAP-Feature:
 * - Benutzerfreundliche Erklärungen
 * - Verantwortliche Text-Abschnitte
 * - Keyword Matches
 * - Kontextuelle Informationen
 */

'use client'

import { useState } from 'react'
import { X, Info, Search, FileText, User, Hash, TrendingUp } from 'lucide-react'

interface FeatureDetail {
  feature_name: string
  shap_value: number
  feature_value?: number | string
  explanation?: string
  responsible_text?: string
  keyword_matches?: string[]
  query?: string
  chunk_text?: string
}

interface SHAPFeatureDetailModalProps {
  feature: FeatureDetail
  isOpen: boolean
  onClose: () => void
}

export default function SHAPFeatureDetailModal({
  feature,
  isOpen,
  onClose
}: SHAPFeatureDetailModalProps) {
  if (!isOpen) return null

  // Feature-spezifische Erklärungen
  const getFeatureExplanation = (featureName: string, value: number | string | undefined) => {
    switch (featureName) {
      case 'user_level':
        const level = typeof value === 'number' ? Math.round(value * 5) : 0
        return {
          title: 'Dein Zugriffs-Level',
          description: `Du hast Zugriffs-Level ${level} von 5.`,
          details: [
            'Level 1: Basis-Zugriff',
            'Level 2: Erweiterter Zugriff',
            'Level 3: QM-Zugriff',
            'Level 4: QM Admin',
            'Level 5: System Admin'
          ],
          impact: level >= 3 
            ? 'Höhere Level sehen mehr relevante Dokumente' 
            : 'Dein Level beeinflusst, welche Dokumente dir angezeigt werden'
        }
      
      case 'keyword_matches':
        const matches = typeof value === 'number' ? value : 0
        return {
          title: 'Gefundene Keywords',
          description: `${matches} Wörter aus deiner Frage wurden im Text gefunden.`,
          details: feature.keyword_matches 
            ? [`Gefundene Keywords: ${feature.keyword_matches.join(', ')}`]
            : ['Keine Keywords gefunden'],
          impact: matches > 0
            ? 'Je mehr Keywords gefunden werden, desto relevanter ist das Ergebnis'
            : 'Keine direkten Keyword-Übereinstimmungen'
        }
      
      case 'text_score':
        const score = typeof value === 'number' ? (value * 100).toFixed(1) : '0.0'
        return {
          title: 'Text-Ähnlichkeit',
          description: `Der Text hat eine Ähnlichkeit von ${score}% zu deiner Frage.`,
          details: feature.responsible_text
            ? [`Verantwortliche Text-Abschnitte: ${feature.responsible_text}`]
            : ['Text-Score basiert auf Keyword-Übereinstimmungen und Text-Ähnlichkeit'],
          impact: parseFloat(score) > 50
            ? 'Hohe Text-Ähnlichkeit bedeutet, dass der Text sehr relevant für deine Frage ist'
            : 'Niedrige Text-Ähnlichkeit - der Text passt weniger gut zu deiner Frage'
        }
      
      case 'vector_score':
        const vScore = typeof value === 'number' ? (value * 100).toFixed(1) : '0.0'
        return {
          title: 'Semantische Ähnlichkeit',
          description: `Der Text hat eine semantische Ähnlichkeit von ${vScore}% zu deiner Frage.`,
          details: [
            'Semantische Ähnlichkeit bedeutet: Der Text hat eine ähnliche Bedeutung wie deine Frage, auch wenn andere Wörter verwendet werden.',
            'Beispiel: "Montage" und "Zusammenbau" haben eine hohe semantische Ähnlichkeit.'
          ],
          impact: parseFloat(vScore) > 70
            ? 'Sehr hohe semantische Ähnlichkeit - der Text passt perfekt zur Bedeutung deiner Frage'
            : 'Mittlere semantische Ähnlichkeit - der Text hat teilweise ähnliche Bedeutung'
        }
      
      case 'chunk_length':
        const length = typeof value === 'number' ? value : 0
        return {
          title: 'Text-Länge',
          description: `Der Text-Abschnitt hat ${length} Zeichen.`,
          details: [
            length < 500 ? 'Kurzer Text-Abschnitt' : length < 1500 ? 'Mittlerer Text-Abschnitt' : 'Langer Text-Abschnitt',
            'Optimal sind Text-Abschnitte zwischen 500 und 1500 Zeichen.'
          ],
          impact: length >= 500 && length <= 1500
            ? 'Optimale Text-Länge für gute Relevanz-Bewertung'
            : 'Text-Länge kann die Relevanz-Bewertung beeinflussen'
        }
      
      case 'bm25_score':
        const bm25 = typeof value === 'number' ? (value * 100).toFixed(1) : '0.0'
        return {
          title: 'BM25 Keyword-Relevanz',
          description: `BM25-Score: ${bm25}%`,
          details: [
            'BM25 ist ein Algorithmus, der misst, wie relevant Keywords im Text sind.',
            'Höhere Werte bedeuten, dass wichtige Keywords aus deiner Frage im Text vorkommen.'
          ],
          impact: parseFloat(bm25) > 50
            ? 'Hohe BM25-Relevanz - wichtige Keywords wurden gefunden'
            : 'Niedrige BM25-Relevanz - wenige Keywords gefunden'
        }
      
      case 'jaccard_score':
        const jaccard = typeof value === 'number' ? (value * 100).toFixed(1) : '0.0'
        return {
          title: 'Jaccard-Ähnlichkeit',
          description: `Jaccard-Score: ${jaccard}%`,
          details: [
            'Jaccard misst, wie viele Wörter aus deiner Frage auch im Text vorkommen.',
            'Beispiel: Frage "Loctite 648" und Text "Loctite 648 Kleber" → hohe Jaccard-Ähnlichkeit'
          ],
          impact: parseFloat(jaccard) > 30
            ? 'Hohe Wort-Übereinstimmung zwischen Frage und Text'
            : 'Wenige gemeinsame Wörter'
        }
      
      default:
        return {
          title: featureName.replace(/_/g, ' '),
          description: `Feature-Wert: ${value}`,
          details: [],
          impact: 'Dieses Feature beeinflusst die Relevanz-Bewertung'
        }
    }
  }

  const explanation = getFeatureExplanation(feature.feature_name, feature.feature_value)
  const isPositive = feature.shap_value >= 0

  // Highlight Keywords im Chunk-Text
  const highlightKeywords = (text: string, keywords: string[]) => {
    if (!keywords || keywords.length === 0) return text
    
    let highlighted = text
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi')
      highlighted = highlighted.replace(regex, '<mark class="bg-yellow-200 font-semibold">$1</mark>')
    })
    return highlighted
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className={`px-6 py-4 border-b ${isPositive ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isPositive ? 'bg-green-100' : 'bg-red-100'}`}>
                  {isPositive ? (
                    <TrendingUp className={`w-6 h-6 ${isPositive ? 'text-green-600' : 'text-red-600'}`} />
                  ) : (
                    <TrendingUp className={`w-6 h-6 text-red-600 rotate-180`} />
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {explanation.title}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    SHAP-Wert: <span className={`font-semibold ${isPositive ? 'text-green-700' : 'text-red-700'}`}>
                      {isPositive ? '+' : ''}{feature.shap_value.toFixed(4)}
                    </span>
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {/* Beschreibung */}
            <div className="mb-6">
              <div className="flex items-start gap-3 mb-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-gray-700 font-medium mb-2">
                    {explanation.description}
                  </p>
                  <p className="text-sm text-gray-600">
                    {explanation.impact}
                  </p>
                </div>
              </div>
            </div>

            {/* Details */}
            {explanation.details.length > 0 && (
              <div className="mb-6 bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Details
                </h4>
                <ul className="space-y-2">
                  {explanation.details.map((detail, index) => (
                    <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Keyword Matches */}
            {feature.keyword_matches && feature.keyword_matches.length > 0 && (
              <div className="mb-6 bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Search className="w-4 h-4 text-yellow-600" />
                  Gefundene Keywords
                </h4>
                <div className="flex flex-wrap gap-2">
                  {feature.keyword_matches.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-yellow-200 text-yellow-900 rounded-full text-sm font-medium"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Verantwortlicher Text */}
            {feature.chunk_text && feature.keyword_matches && feature.keyword_matches.length > 0 && (
              <div className="mb-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  Text mit hervorgehobenen Keywords
                </h4>
                <div 
                  className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{
                    __html: highlightKeywords(
                      feature.chunk_text.substring(0, 1000),
                      feature.keyword_matches
                    ) + (feature.chunk_text.length > 1000 ? '...' : '')
                  }}
                />
              </div>
            )}

            {/* Query */}
            {feature.query && (
              <div className="mb-6 bg-purple-50 rounded-lg p-4 border border-purple-200">
                <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <Search className="w-4 h-4 text-purple-600" />
                  Deine Frage
                </h4>
                <p className="text-sm text-gray-700 font-medium">
                  "{feature.query}"
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              Schließen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}




