/**
 * Quick Summary Card Component
 * 
 * Zeigt eine kompakte Zusammenfassung der Analytics:
 * - Query
 * - Top 3 Metriken (NDCG@10, Precision@10, MRR)
 * - Status (gut/schlecht/neutral)
 * - Trend-Pfeile (↑↓)
 */

'use client'

import { MessageSquare, TrendingUp, TrendingDown, Minus, CheckCircle, AlertCircle, XCircle } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface QuickSummaryProps {
  query: string
  ndcg?: number
  precision?: number
  mrr?: number
  status?: 'good' | 'neutral' | 'bad'
}

export default function QuickSummaryCard({
  query,
  ndcg,
  precision,
  mrr,
  status
}: QuickSummaryProps) {
  // Bestimme Status basierend auf Metriken
  const getStatus = (): 'good' | 'neutral' | 'bad' => {
    if (status) return status
    
    // Automatische Status-Bestimmung
    const hasGoodNDCG = ndcg !== undefined && ndcg >= 0.7
    const hasGoodPrecision = precision !== undefined && precision >= 0.5
    const hasGoodMRR = mrr !== undefined && mrr >= 0.5
    
    if (hasGoodNDCG && hasGoodPrecision && hasGoodMRR) return 'good'
    if (hasGoodNDCG || hasGoodPrecision || hasGoodMRR) return 'neutral'
    return 'bad'
  }

  const currentStatus = getStatus()

  const statusConfig = {
    good: {
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      text: 'Gut',
      description: 'Alle Metriken sind im erwarteten Bereich'
    },
    neutral: {
      icon: AlertCircle,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      text: 'Neutral',
      description: 'Einige Metriken könnten verbessert werden'
    },
    bad: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      text: 'Verbesserung nötig',
      description: 'Metriken zeigen Verbesserungspotenzial'
    }
  }

  const StatusIcon = statusConfig[currentStatus].icon

  const formatPercent = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A'
    return (value * 100).toFixed(1) + '%'
  }

  const getTrendIcon = (value?: number) => {
    if (value === undefined || value === null) return null
    if (value >= 0.7) return <TrendingUp className="w-4 h-4 text-green-600" />
    if (value >= 0.5) return <Minus className="w-4 h-4 text-yellow-600" />
    return <TrendingDown className="w-4 h-4 text-red-600" />
  }

  return (
    <div className={`bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border-2 ${statusConfig[currentStatus].borderColor} p-6 shadow-lg mb-8`}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Query Section */}
        <div className="lg:col-span-1">
          <div className="flex items-start gap-3">
            <MessageSquare className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-2">
                Bewertete Frage
              </div>
              <div className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                &quot;{query}&quot;
              </div>
            </div>
          </div>
        </div>

        {/* Top 3 Metriken */}
        <div className="lg:col-span-2 grid grid-cols-3 gap-4">
          {/* NDCG@10 */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600 uppercase">NDCG@10</span>
              {getTrendIcon(ndcg)}
            </div>
            <div className="text-2xl font-bold text-indigo-700 mb-1">
              {formatPercent(ndcg)}
            </div>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">NDCG@10 (Normalized Discounted Cumulative Gain)</p>
                  <p className="text-xs">
                    Misst die Ranking-Qualität. Berücksichtigt sowohl Relevanz als auch Position.
                    Höhere Werte = besseres Ranking.
                  </p>
                  <p className="text-xs">
                    <strong>Interpretation:</strong><br />
                    &gt; 0.7 = Sehr gut<br />
                    0.5 - 0.7 = Gut<br />
                    &lt; 0.5 = Verbesserung nötig
                  </p>
                </div>
              }
            />
          </div>

          {/* Precision@10 */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600 uppercase">Precision@10</span>
              {getTrendIcon(precision)}
            </div>
            <div className="text-2xl font-bold text-blue-700 mb-1">
              {formatPercent(precision)}
            </div>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">Precision@10</p>
                  <p className="text-xs">
                    Anteil der relevanten Ergebnisse in den Top 10. Zeigt, wie viele der gefundenen Ergebnisse tatsächlich relevant sind.
                  </p>
                  <p className="text-xs">
                    <strong>Interpretation:</strong><br />
                    &gt; 0.5 = Gut (mehr als die Hälfte ist relevant)<br />
                    0.3 - 0.5 = Akzeptabel<br />
                    &lt; 0.3 = Verbesserung nötig
                  </p>
                </div>
              }
            />
          </div>

          {/* MRR */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600 uppercase">MRR</span>
              {getTrendIcon(mrr)}
            </div>
            <div className="text-2xl font-bold text-purple-700 mb-1">
              {formatPercent(mrr)}
            </div>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">MRR (Mean Reciprocal Rank)</p>
                  <p className="text-xs">
                    Durchschnittlicher Kehrwert der Position des ersten relevanten Ergebnisses.
                    Höhere Werte = relevantes Ergebnis steht weiter oben.
                  </p>
                  <p className="text-xs">
                    <strong>Interpretation:</strong><br />
                    &gt; 0.5 = Sehr gut (erstes relevantes Ergebnis meist in Top 2)<br />
                    0.3 - 0.5 = Gut<br />
                    &lt; 0.3 = Verbesserung nötig
                  </p>
                </div>
              }
            />
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className={`mt-4 flex items-center gap-3 ${statusConfig[currentStatus].bgColor} rounded-lg p-3 border ${statusConfig[currentStatus].borderColor}`}>
        <StatusIcon className={`w-5 h-5 ${statusConfig[currentStatus].color} flex-shrink-0`} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${statusConfig[currentStatus].color}`}>
              Status: {statusConfig[currentStatus].text}
            </span>
          </div>
          <p className="text-xs text-gray-700 mt-1">
            {statusConfig[currentStatus].description}
          </p>
        </div>
      </div>
    </div>
  )
}

