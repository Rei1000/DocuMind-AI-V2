/**
 * RAG Analytics Dashboard - v2.7.0 FINAL CORRECT
 * 
 * WICHTIG: Diese Seite macht KEINE API-Requests!
 * Sie zeigt nur die Analytics-Daten der letzten Chat-Anfrage.
 * 
 * Datenfluss:
 * 1. User stellt Frage im Chat
 * 2. POST /api/rag/chat/ask liefert response.analytics
 * 3. Chat speichert analytics in localStorage
 * 4. Diese Seite liest analytics aus localStorage
 * 5. Visualisierung der Daten
 * 
 * KEINE FAKE-DATEN - Nur echte RAG-Pipeline-Daten!
 */

'use client'

import { useState, useEffect } from 'react'
import { BarChart3, MessageSquare, AlertCircle, TrendingUp, Zap } from 'lucide-react'
import { useRouter } from 'next/navigation'

// Importiere Komponenten
import ScoreOverviewCard from '@/components/ScoreOverviewCard'
import SHAPComparisonPanel from '@/components/SHAPComparisonPanel'
import ModelInfoCard from '@/components/ModelInfoCard'
import CacheStatsCard from '@/components/CacheStatsCard'
import BackgroundStatsCard from '@/components/BackgroundStatsCard'

interface AnalyticsData {
  scores: any[]
  background_data_stats: any
  cache_stats: any
  model_info: any
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Lade Analytics-Daten aus localStorage (vom Chat gespeichert)
    loadAnalyticsFromStorage()
    
    // Poll localStorage alle 2 Sekunden für Updates
    const interval = setInterval(loadAnalyticsFromStorage, 2000)
    
    return () => clearInterval(interval)
  }, [])

  const loadAnalyticsFromStorage = () => {
    try {
      // WICHTIG: Analytics-Daten kommen aus dem Chat, nicht von API!
      const storedAnalytics = localStorage.getItem('lastAnalytics')
      
      if (storedAnalytics) {
        const data = JSON.parse(storedAnalytics)
        setAnalytics(data)
      } else {
        setAnalytics(null)
      }
    } catch (error) {
      console.error('Failed to load analytics from storage:', error)
      setAnalytics(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-pulse text-gray-400">
            <BarChart3 className="w-16 h-16 mx-auto mb-4" />
          </div>
          <p className="text-gray-600">Prüfe Analytics-Daten...</p>
        </div>
      </div>
    )
  }

  // Falls keine Analytics-Daten vorhanden
  if (!analytics) {
    return (
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
            <BarChart3 className="w-10 h-10 text-blue-600" />
            Analytics Dashboard
            <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
              v2.7.0
            </span>
          </h1>
        </div>

        {/* WICHTIGER HINWEIS - Keine Analytics verfügbar */}
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-400 rounded-xl p-12 shadow-xl">
          <div className="flex flex-col items-center text-center">
            <AlertCircle className="w-20 h-20 text-yellow-600 mb-6" />
            
            <h2 className="text-3xl font-bold text-yellow-900 mb-4">
              Keine Analytics-Daten verfügbar
            </h2>
            
            <p className="text-lg text-yellow-800 mb-6 max-w-2xl">
              Das Analytics-Dashboard zeigt die technischen Analysen deiner <strong>letzten RAG-Chat-Anfrage</strong>.
            </p>

            <div className="bg-white/70 backdrop-blur rounded-xl p-6 mb-8 max-w-3xl">
              <h3 className="font-bold text-yellow-900 mb-4 text-xl">📋 So funktioniert es:</h3>
              <ol className="text-left space-y-3 text-yellow-900">
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">1.</span>
                  <span>Gehe zum <strong>RAG Chat</strong></span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">2.</span>
                  <span>Stelle eine Frage (z.B. &quot;Wie montiere ich die Freilaufwelle?&quot;)</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">3.</span>
                  <span>Die Antwort enthält <strong>automatisch</strong> Analytics-Daten</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-2xl">4.</span>
                  <span>Komme zurück hierher - Analytics werden angezeigt!</span>
                </li>
              </ol>
            </div>

            <button
              onClick={() => router.push('/rag-chat')}
              className="px-12 py-5 bg-blue-600 text-white rounded-xl font-bold text-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-3"
            >
              <MessageSquare className="w-7 h-7" />
              Zum RAG Chat
            </button>

            <p className="mt-6 text-sm text-yellow-700">
              💡 <strong>Tipp:</strong> Analytics-Daten werden mit jeder Chat-Anfrage aktualisiert.
              Diese Seite macht <strong>keine eigenen API-Calls</strong>!
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Falls Analytics-Daten vorhanden - Visualisierung
  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
          <BarChart3 className="w-10 h-10 text-blue-600" />
          Analytics Dashboard
          <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
            v2.7.0
          </span>
        </h1>
        <p className="text-gray-600 text-lg">
          Analytics der letzten Chat-Anfrage • {analytics.scores?.length || 0} Chunks analysiert
        </p>
      </div>

      {/* 1️⃣ SCORE OVERVIEW */}
      {analytics.scores && analytics.scores.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Zap className="w-7 h-7 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Score Overview</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {analytics.scores.slice(0, 9).map((score: any) => (
              <ScoreOverviewCard
                key={score.chunk_id}
                vectorScore={score.vector_score || 0}
                textScore={score.text_score || 0}
                hybridScore={score.hybrid_score || 0}
                mlScore={score.ml_score}
                finalScore={score.final_score}
                rankPosition={score.rank_position || 1}
              />
            ))}
          </div>
        </div>
      )}

      {/* 2️⃣ SHAP COMPARISON (Hybrid vs ML) */}
      {analytics.scores && analytics.scores[0]?._extended_metadata && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-7 h-7 text-purple-600" />
            <h2 className="text-2xl font-bold text-gray-900">SHAP Comparison (Hybrid vs ML)</h2>
          </div>
          
          <SHAPComparisonPanel
            hybridShap={analytics.scores[0]._extended_metadata.hybrid_shap}
            mlShap={analytics.scores[0]._extended_metadata.ml_shap}
            query={analytics.scores[0]._extended_metadata.query || 'Unknown'}
          />
        </div>
      )}

      {/* 3️⃣ SYSTEM METRICS */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">System Metrics (aus Chat-Response)</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Model Info */}
          {analytics.model_info && (
            <ModelInfoCard
              modelType={analytics.model_info.model_type || 'none'}
              modelVersion={analytics.model_info.model_version || '1.0.0'}
              isReady={analytics.model_info.ml_enabled || false}
              featureNames={analytics.model_info.feature_names || []}
              trainingDataStats={analytics.model_info.training_data_stats}
            />
          )}

          {/* Cache Stats */}
          {analytics.cache_stats && (
            <CacheStatsCard
              cacheSize={analytics.cache_stats.cache_size || 0}
              maxSize={analytics.cache_stats.max_size || 100}
              hits={analytics.cache_stats.hits || 0}
              misses={analytics.cache_stats.misses || 0}
              hitRatePercent={analytics.cache_stats.hit_rate_percent || 0}
              estimatedTimeSavedMinutes={analytics.cache_stats.estimated_time_saved_minutes || 0}
            />
          )}

          {/* Background Stats */}
          {analytics.background_data_stats && (
            <BackgroundStatsCard
              totalRecords={analytics.background_data_stats.total_records || 0}
              backgroundDataShape={analytics.background_data_stats.background_data_shape}
              lastUpdate={analytics.background_data_stats.last_update}
              oldestRecord={analytics.background_data_stats.oldest_record}
              newestRecord={analytics.background_data_stats.newest_record}
            />
          )}
        </div>
      </div>

      {/* 4️⃣ CHUNK DETAILS TABLE */}
      {analytics.scores && analytics.scores.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Alle Chunks (Detailliert)</h2>
          
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Chunk ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vector
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Text
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hybrid
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ML
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Final
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.scores.map((score: any, index: number) => (
                  <tr key={score.chunk_id || index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-lg font-bold text-gray-900">
                        #{score.rank_position || index + 1}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-700 font-mono">
                        {String(score.chunk_id).substring(0, 20)}...
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-blue-700 font-semibold">
                        {score.vector_score ? (score.vector_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-purple-700 font-semibold">
                        {score.text_score ? (score.text_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-indigo-700 font-semibold">
                        {score.hybrid_score ? (score.hybrid_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-green-700 font-bold">
                        {score.ml_score ? (score.ml_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-pink-700 font-bold">
                        {score.final_score ? (score.final_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5️⃣ SYSTEM METRICS (aus Analytics-Block) */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">System Metrics (aus Chat-Response)</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Model Info */}
          {analytics.model_info && (
            <ModelInfoCard
              modelType={analytics.model_info.model_type || 'none'}
              modelVersion={analytics.model_info.model_version || '1.0.0'}
              isReady={analytics.model_info.ml_enabled || false}
              featureNames={analytics.model_info.feature_names || []}
              trainingDataStats={analytics.model_info.training_data_stats}
            />
          )}

          {/* Cache Stats */}
          {analytics.cache_stats && (
            <CacheStatsCard
              cacheSize={analytics.cache_stats.cache_size || 0}
              maxSize={analytics.cache_stats.max_size || 100}
              hits={analytics.cache_stats.hits || 0}
              misses={analytics.cache_stats.misses || 0}
              hitRatePercent={analytics.cache_stats.hit_rate_percent || 0}
              estimatedTimeSavedMinutes={analytics.cache_stats.estimated_time_saved_minutes || 0}
            />
          )}

          {/* Background Stats */}
          {analytics.background_data_stats && (
            <BackgroundStatsCard
              totalRecords={analytics.background_data_stats.total_records || 0}
              backgroundDataShape={analytics.background_data_stats.background_data_shape}
              lastUpdate={analytics.background_data_stats.last_update}
              oldestRecord={analytics.background_data_stats.oldest_record}
              newestRecord={analytics.background_data_stats.newest_record}
            />
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <svg className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="text-sm text-blue-900 font-medium mb-2">
              ✅ <strong>Analytics-Daten geladen!</strong>
            </p>
            <p className="text-xs text-blue-800">
              Diese Daten stammen aus der letzten RAG-Chat-Anfrage. Stelle eine neue Frage im Chat um die Analytics zu aktualisieren.
            </p>
            <button
              onClick={() => router.push('/rag-chat')}
              className="mt-3 text-sm text-blue-700 hover:text-blue-900 font-semibold underline"
            >
              → Zum RAG Chat
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
