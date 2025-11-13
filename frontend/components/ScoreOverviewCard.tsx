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

interface ScoreOverviewProps {
  vectorScore: number
  textScore: number
  hybridScore: number
  mlScore?: number
  finalScore?: number
  rankPosition: number
  oldRankPosition?: number  // Rank-Position ohne ML
}

export default function ScoreOverviewCard({
  vectorScore,
  textScore,
  hybridScore,
  mlScore,
  finalScore,
  rankPosition,
  oldRankPosition
}: ScoreOverviewProps) {
  // Berechne Deltas
  const mlDelta = mlScore ? mlScore - hybridScore : null
  const finalDelta = finalScore ? finalScore - hybridScore : null
  const rankDelta = oldRankPosition ? oldRankPosition - rankPosition : null

  const formatScore = (score: number) => (score * 100).toFixed(1) + '%'
  const formatDelta = (delta: number) => {
    const sign = delta >= 0 ? '+' : ''
    return sign + (delta * 100).toFixed(1) + '%'
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
        <p className="text-xs text-gray-600">
          <span className="font-semibold">Final Score</span> = 0.6 × Hybrid + 0.4 × ML
        </p>
      </div>
    </div>
  )
}

