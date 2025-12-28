/**
 * Background Stats Card Component
 * 
 * Zeigt Background Data Statistics (historische Search-Daten für SHAP)
 */

'use client'

interface BackgroundStatsCardProps {
  totalRecords: number
  backgroundDataShape: number[] | null
  lastUpdate: string | null
  oldestRecord: string | null
  newestRecord: string | null
}

export default function BackgroundStatsCard({
  totalRecords,
  backgroundDataShape,
  lastUpdate,
  oldestRecord,
  newestRecord
}: BackgroundStatsCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
        </svg>
        Background Data
      </h3>

      <div className="space-y-4">
        {/* Total Records */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-600 mb-1">Total Records</div>
          <div className="text-3xl font-bold text-blue-700">{totalRecords}</div>
          <div className="text-xs text-gray-600 mt-1">
            Historische Search-Daten für SHAP
          </div>
        </div>

        {/* Data Shape */}
        {backgroundDataShape && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-700">Data Shape</span>
            <span className="font-mono font-semibold text-gray-900">
              {backgroundDataShape[0]} × {backgroundDataShape[1]}
            </span>
          </div>
        )}

        {/* Timestamps */}
        {lastUpdate && (
          <div className="space-y-2 text-xs text-gray-600">
            <div className="flex justify-between">
              <span>Letztes Update:</span>
              <span className="font-medium text-gray-900">
                {new Date(lastUpdate).toLocaleString('de-DE')}
              </span>
            </div>
            {oldestRecord && (
              <div className="flex justify-between">
                <span>Ältester Record:</span>
                <span className="font-medium text-gray-900">
                  {new Date(oldestRecord).toLocaleDateString('de-DE')}
                </span>
              </div>
            )}
            {newestRecord && (
              <div className="flex justify-between">
                <span>Neuester Record:</span>
                <span className="font-medium text-gray-900">
                  {new Date(newestRecord).toLocaleDateString('de-DE')}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Status */}
        {totalRecords === 0 && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              ℹ️ Noch keine Background-Daten gesammelt. Stelle Fragen im RAG-Chat um Daten zu sammeln.
            </p>
          </div>
        )}

        {totalRecords >= 1000 && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              ✅ Rolling Window voll (max 1000 Records). Älteste Daten werden automatisch entfernt.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

