/**
 * Score Overview Card Component
 * 
 * Zeigt alle Scores für einen Chunk:
 * - vector_score, text_score, hybrid_score
 * - ml_score, final_score (NEU v2.7.0)
 * - Deltas (ml vs hybrid, final vs hybrid)
 * - Rank-Position Änderung
 */

'use client'

import { useState } from 'react'

interface ScoreOverviewProps {
  vectorScore: number
  textScore: number
  hybridScore: number
  mlScore?: number
  mlScoreRaw?: number
  finalScore?: number
  rankPosition: number
  oldRankPosition?: number  // Rank-Position ohne ML
  mlRawMin?: number
  mlRawMax?: number
  hybridWeight?: number
  mlWeight?: number
}

export default function ScoreOverviewCard({
  vectorScore,
  textScore,
  hybridScore,
  mlScore,
  mlScoreRaw,
  finalScore,
  rankPosition,
  oldRankPosition,
  mlRawMin,
  mlRawMax,
  hybridWeight = 0.6,
  mlWeight = 0.4
}: ScoreOverviewProps) {
  // UI State: einfache Erklärung ein/ausklappen
  const [showExplanation, setShowExplanation] = useState(false)

  // Berechne Deltas
  const mlDelta = mlScore !== undefined ? mlScore - hybridScore : null
  const finalDelta = finalScore !== undefined ? finalScore - hybridScore : null
  const rankDelta = oldRankPosition ? oldRankPosition - rankPosition : null

  const formatScore = (score: number) => (score * 100).toFixed(1) + '%'
  const formatDelta = (delta: number) => {
    const sign = delta >= 0 ? '+' : ''
    return sign + (delta * 100).toFixed(1) + '%'
  }

  const hasMlRawInfo = typeof mlScoreRaw === 'number' && typeof mlRawMin === 'number' && typeof mlRawMax === 'number'
  const formatRaw = (value: number) => {
    // Rohwerte können >1 sein; wir zeigen sie als "Punkte" mit 3 Nachkommastellen
    return value.toFixed(3)
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
        </svg>
        Score Overview
      </h3>

      <div className="space-y-3">
        {/* Vector Score */}
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <span className="text-sm font-medium text-gray-700">Vector Score</span>
          <span className="text-lg font-bold text-blue-700">{formatScore(vectorScore)}</span>
        </div>

        {/* Text Score */}
        <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
          <span className="text-sm font-medium text-gray-700">Text Score</span>
          <span className="text-lg font-bold text-purple-700">{formatScore(textScore)}</span>
        </div>

        {/* Hybrid Score */}
        <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg border-2 border-indigo-300">
          <span className="text-sm font-medium text-gray-900">Hybrid Score</span>
          <span className="text-lg font-bold text-indigo-700">{formatScore(hybridScore)}</span>
        </div>

        {/* ML Score (falls vorhanden) */}
        {mlScore !== undefined && (
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-300">
            <div>
              <span className="text-sm font-medium text-gray-900">ML Score</span>
              {mlDelta !== null && (
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                  mlDelta >= 0 ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'
                }`}>
                  {formatDelta(mlDelta)} vs Hybrid
                </span>
              )}
            </div>
            <span className="text-lg font-bold text-green-700">{formatScore(mlScore)}</span>
          </div>
        )}

        {/* Final Score (falls vorhanden) */}
        {finalScore !== undefined && (
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-lg border-2 border-indigo-400">
            <div>
              <span className="text-base font-bold text-gray-900">Final Score</span>
              {finalDelta !== null && (
                <span className={`ml-2 text-xs px-2 py-1 rounded-full ${
                  finalDelta >= 0 ? 'bg-green-200 text-green-900' : 'bg-red-200 text-red-900'
                }`}>
                  {formatDelta(finalDelta)} vs Hybrid
                </span>
              )}
            </div>
            <span className="text-xl font-bold text-indigo-900">{formatScore(finalScore)}</span>
          </div>
        )}

        {/* Rank Position */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-300 mt-4">
          <span className="text-sm font-medium text-gray-700">Rank Position</span>
          <div className="flex items-center gap-2">
            {rankDelta !== null && rankDelta !== 0 && (
              <span className="text-xs text-gray-500">
                #{oldRankPosition} →
              </span>
            )}
            <span className="text-lg font-bold text-gray-900">#{rankPosition}</span>
            {rankDelta !== null && rankDelta !== 0 && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                rankDelta > 0 ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'
              }`}>
                {rankDelta > 0 ? '↑' : '↓'} {Math.abs(rankDelta)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-600">
            <span className="font-semibold">Final Score</span> = {hybridWeight} × Hybrid + {mlWeight} × ML
          </p>
          <button
            type="button"
            onClick={() => setShowExplanation(v => !v)}
            className="text-xs font-semibold text-blue-700 hover:text-blue-900 underline"
          >
            {showExplanation ? 'Erklärung ausblenden' : 'So entsteht der Wert'}
          </button>
        </div>

        {showExplanation && (
          <div className="mt-3 text-xs text-gray-700 space-y-2">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="font-semibold text-gray-900 mb-1">In 3 Schritten:</div>
              <ol className="list-decimal list-inside space-y-1">
                <li><span className="font-semibold">Hybrid</span> = 0.7 × Vector + 0.3 × Text</li>
                <li><span className="font-semibold">ML</span> wird pro Suche auf 0–100% umgerechnet (damit es fair vergleichbar ist)</li>
                <li><span className="font-semibold">Final</span> = {hybridWeight} × Hybrid + {mlWeight} × ML</li>
              </ol>
            </div>

            {hasMlRawInfo && mlScore !== undefined && finalScore !== undefined && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="font-semibold text-gray-900 mb-1">Warum braucht ML eine Umrechnung?</div>
                <p className="text-gray-700">
                  Das ML-Modell gibt erst <span className="font-semibold">Roh-Punkte</span> aus (können auch größer als 1 sein).
                  Damit man es wie Prozent lesen kann, skalieren wir innerhalb dieser Suche:
                  <span className="font-semibold"> min</span> → 0% und <span className="font-semibold">max</span> → 100%.
                </p>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  <div className="bg-white border border-green-200 rounded p-2">
                    <div className="text-[11px] text-gray-600">ML roh (dieser Chunk)</div>
                    <div className="font-bold text-gray-900">{formatRaw(mlScoreRaw)}</div>
                  </div>
                  <div className="bg-white border border-green-200 rounded p-2">
                    <div className="text-[11px] text-gray-600">Min roh (alle Chunks)</div>
                    <div className="font-bold text-gray-900">{formatRaw(mlRawMin)}</div>
                  </div>
                  <div className="bg-white border border-green-200 rounded p-2">
                    <div className="text-[11px] text-gray-600">Max roh (alle Chunks)</div>
                    <div className="font-bold text-gray-900">{formatRaw(mlRawMax)}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

