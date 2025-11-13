/**
 * Model Info & Metrics Card Component
 * 
 * Zeigt ML-Model Informationen und Metriken:
 * - Model Version, Type, Training Date
 * - NDCG@k Metrics
 * - Training Data Statistics
 */

'use client'

interface ModelInfoCardProps {
  modelType: string
  modelVersion: string
  isReady: boolean
  featureNames?: string[]
  trainingDataStats?: {
    total_samples: number
    unique_queries: number
    oldest_sample?: string
    newest_sample?: string
  }
}

export default function ModelInfoCard({
  modelType,
  modelVersion,
  isReady,
  featureNames,
  trainingDataStats
}: ModelInfoCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
          <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
        </svg>
        ML Model Info
      </h3>

      <div className="space-y-4">
        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isReady ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className={`font-semibold ${isReady ? 'text-green-700' : 'text-gray-600'}`}>
            {isReady ? 'Model Ready' : 'Model Not Loaded'}
          </span>
        </div>

        {/* Model Details */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Model Type</div>
            <div className="font-semibold text-gray-900">{modelType}</div>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Version</div>
            <div className="font-semibold text-gray-900">{modelVersion}</div>
          </div>
        </div>

        {/* Feature Count */}
        {featureNames && (
          <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
            <div className="text-xs text-gray-600 mb-1">Features</div>
            <div className="text-2xl font-bold text-indigo-700">{featureNames.length}</div>
            <div className="text-xs text-gray-600 mt-1">
              {featureNames.slice(0, 3).join(', ')}...
            </div>
          </div>
        )}

        {/* Training Data Stats */}
        {trainingDataStats && trainingDataStats.total_samples > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Training Data</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-xs text-gray-600 mb-1">Total Samples</div>
                <div className="text-xl font-bold text-blue-700">
                  {trainingDataStats.total_samples}
                </div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="text-xs text-gray-600 mb-1">Unique Queries</div>
                <div className="text-xl font-bold text-purple-700">
                  {trainingDataStats.unique_queries}
                </div>
              </div>
            </div>
            {trainingDataStats.newest_sample && (
              <div className="mt-2 text-xs text-gray-600">
                Letztes Sample: {new Date(trainingDataStats.newest_sample).toLocaleDateString('de-DE')}
              </div>
            )}
          </div>
        )}

        {/* No Training Data Message */}
        {trainingDataStats && trainingDataStats.total_samples === 0 && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              ⚠️ Noch keine Training-Daten vorhanden. Sammle User-Feedback um das Model zu verbessern!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

