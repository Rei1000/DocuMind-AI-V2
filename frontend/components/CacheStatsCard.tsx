/**
 * Cache Stats Card Component
 * 
 * Zeigt SHAP Cache Performance-Statistiken
 */

'use client'

interface CacheStatsCardProps {
  cacheSize: number
  maxSize: number
  hits: number
  misses: number
  hitRatePercent: number
  estimatedTimeSavedMinutes: number
}

export default function CacheStatsCard({
  cacheSize,
  maxSize,
  hits,
  misses,
  hitRatePercent,
  estimatedTimeSavedMinutes
}: CacheStatsCardProps) {
  const totalRequests = hits + misses

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
          <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
        </svg>
        Cache Performance
      </h3>

      <div className="space-y-4">
        {/* Hit Rate */}
        <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
          <div className="text-sm text-gray-600 mb-1">Cache Hit Rate</div>
          <div className="text-3xl font-bold text-green-700">{hitRatePercent.toFixed(1)}%</div>
          <div className="text-xs text-gray-600 mt-1">
            {hits} hits / {totalRequests} total requests
          </div>
        </div>

        {/* Cache Size */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-700">Cache Size</span>
          <span className="font-semibold text-gray-900">
            {cacheSize} / {maxSize}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              cacheSize / maxSize > 0.9 ? 'bg-red-500' : 'bg-blue-500'
            }`}
            style={{ width: `${(cacheSize / maxSize) * 100}%` }}
          />
        </div>

        {/* Time Saved */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-600 mb-1">Geschätzte Zeit gespart</div>
          <div className="text-2xl font-bold text-blue-700">
            {estimatedTimeSavedMinutes.toFixed(1)} min
          </div>
          <div className="text-xs text-gray-600 mt-1">
            ≈ {(estimatedTimeSavedMinutes * 60).toFixed(0)} Sekunden
          </div>
        </div>

        {/* Hits vs Misses */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="text-xs text-gray-600">Hits</div>
            <div className="text-xl font-bold text-green-700">{hits}</div>
          </div>
          <div className="p-3 bg-red-50 rounded-lg">
            <div className="text-xs text-gray-600">Misses</div>
            <div className="text-xl font-bold text-red-700">{misses}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

