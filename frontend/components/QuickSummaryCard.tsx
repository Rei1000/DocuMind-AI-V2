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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Top 3 Metriken - Fokus auf Metriken, Query wird oben angezeigt */}
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
                  <p className="font-semibold">NDCG@10 - Was bedeutet das?</p>
                  <p className="text-xs">
                    <strong>Einfach erklärt:</strong> Diese Zahl zeigt, wie gut die Suchergebnisse sortiert sind.
                    Je höher, desto besser stehen die relevanten Ergebnisse oben.
                  </p>
                  <p className="text-xs">
                    <strong>Beispiel:</strong><br />
                    Wenn du nach "Montageanleitung" suchst und die besten Anleitungen an Position 1, 2, 3 stehen,
                    dann ist NDCG@10 hoch (z.B. 0.85 = 85%).
                  </p>
                  <p className="text-xs">
                    <strong>Was bedeutet das für mich?</strong><br />
                    &gt; 70% = Sehr gut - Die besten Ergebnisse stehen ganz oben<br />
                    50-70% = Gut - Meistens findest du was du suchst<br />
                    &lt; 50% = Verbesserung nötig - Ergebnisse könnten besser sortiert sein
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
                  <p className="font-semibold">Precision@10 - Was bedeutet das?</p>
                  <p className="text-xs">
                    <strong>Einfach erklärt:</strong> Von den 10 besten Suchergebnissen, wie viele sind wirklich hilfreich?
                    Diese Zahl zeigt den Anteil der relevanten Ergebnisse.
                  </p>
                  <p className="text-xs">
                    <strong>Beispiel:</strong><br />
                    Wenn du nach "Wartung" suchst und 7 von 10 Ergebnissen wirklich über Wartung handeln,
                    dann ist Precision@10 = 70% (7/10).
                  </p>
                  <p className="text-xs">
                    <strong>Was bedeutet das für mich?</strong><br />
                    &gt; 50% = Gut - Mehr als die Hälfte der Ergebnisse ist hilfreich<br />
                    30-50% = Akzeptabel - Einige Ergebnisse sind hilfreich<br />
                    &lt; 30% = Verbesserung nötig - Viele Ergebnisse passen nicht zur Frage
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
                  <p className="font-semibold">MRR - Was bedeutet das?</p>
                  <p className="text-xs">
                    <strong>Einfach erklärt:</strong> An welcher Position steht das erste wirklich hilfreiche Ergebnis?
                    Diese Zahl zeigt, wie schnell du ein relevantes Ergebnis findest.
                  </p>
                  <p className="text-xs">
                    <strong>Beispiel:</strong><br />
                    Wenn das erste hilfreiche Ergebnis an Position 1 steht: MRR = 100% (1/1 = perfekt)<br />
                    Wenn es an Position 2 steht: MRR = 50% (1/2 = gut)<br />
                    Wenn es erst an Position 5 steht: MRR = 20% (1/5 = könnte besser sein)
                  </p>
                  <p className="text-xs">
                    <strong>Was bedeutet das für mich?</strong><br />
                    &gt; 50% = Sehr gut - Das erste hilfreiche Ergebnis steht meist ganz oben<br />
                    30-50% = Gut - Du findest schnell was du suchst<br />
                    &lt; 30% = Verbesserung nötig - Du musst länger scrollen bis zum ersten hilfreichen Ergebnis
                  </p>
                </div>
              }
            />
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

