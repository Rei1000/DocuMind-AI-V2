/**
 * Automated Insights Panel Component
 * 
 * Generiert automatische Insights und Empfehlungen basierend auf Analytics-Daten.
 * 
 * NEU v2.10.0
 */

'use client'

import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react'

interface Insight {
  type: 'positive' | 'warning' | 'info' | 'recommendation'
  title: string
  message: string
  actionable?: boolean
  action?: string
}

interface AutomatedInsightsPanelProps {
  metrics?: {
    ndcg_at_10?: number
    precision_at_10?: number
    mrr?: number
    average_relevance_score?: number
  }
  scores?: Array<{
    hybrid_score: number
    vector_score: number
    text_score: number
  }>
  query?: string
}

export default function AutomatedInsightsPanel({ metrics, scores, query }: AutomatedInsightsPanelProps) {
  if (!metrics && !scores) {
    return null
  }

  const insights: Insight[] = []

  // Analyse der Metriken
  if (metrics) {
    // NDCG-Analyse
    if (metrics.ndcg_at_10 !== undefined) {
      if (metrics.ndcg_at_10 >= 0.8) {
        insights.push({
          type: 'positive',
          title: 'Exzellentes Ranking!',
          message: `Deine NDCG@10 von ${(metrics.ndcg_at_10 * 100).toFixed(1)}% zeigt, dass die relevanten Ergebnisse sehr gut sortiert sind.`,
        })
      } else if (metrics.ndcg_at_10 < 0.5) {
        insights.push({
          type: 'warning',
          title: 'Ranking könnte verbessert werden',
          message: `Deine NDCG@10 von ${(metrics.ndcg_at_10 * 100).toFixed(1)}% zeigt Verbesserungspotenzial. Relevante Ergebnisse stehen möglicherweise nicht weit genug oben.`,
          actionable: true,
          action: 'Prüfe die SHAP-Analyse, um zu sehen, welche Features das Ranking beeinflussen.',
        })
      }
    }

    // Precision-Analyse
    if (metrics.precision_at_10 !== undefined) {
      if (metrics.precision_at_10 < 0.3) {
        insights.push({
          type: 'warning',
          title: 'Niedrige Precision',
          message: `Nur ${(metrics.precision_at_10 * 100).toFixed(1)}% der Top-10 Ergebnisse sind relevant. Das System findet möglicherweise zu viele irrelevante Ergebnisse.`,
          actionable: true,
          action: 'Versuche präzisere Fragen zu stellen oder gib Feedback zu den Ergebnissen.',
        })
      } else if (metrics.precision_at_10 >= 0.7) {
        insights.push({
          type: 'positive',
          title: 'Hohe Precision!',
          message: `${(metrics.precision_at_10 * 100).toFixed(1)}% der Top-10 Ergebnisse sind relevant. Das System findet sehr präzise Ergebnisse.`,
        })
      }
    }

    // MRR-Analyse
    if (metrics.mrr !== undefined) {
      if (metrics.mrr < 0.3) {
        insights.push({
          type: 'warning',
          title: 'Erstes relevantes Ergebnis steht weit unten',
          message: `Das erste relevante Ergebnis steht durchschnittlich an Position ${Math.round(1 / metrics.mrr)}. Du musst länger scrollen, um hilfreiche Ergebnisse zu finden.`,
          actionable: true,
          action: 'Gib Feedback zu den Ergebnissen, damit das System lernt, relevante Ergebnisse höher zu ranken.',
        })
      } else if (metrics.mrr >= 0.7) {
        insights.push({
          type: 'positive',
          title: 'Schnelle Ergebnisse!',
          message: `Das erste relevante Ergebnis steht meist in den Top 2 Positionen. Du findest schnell, was du suchst.`,
        })
      }
    }
  }

  // Score-Analyse
  if (scores && scores.length > 0) {
    const avgHybridScore = scores.reduce((sum, s) => sum + (s.hybrid_score || 0), 0) / scores.length
    const avgVectorScore = scores.reduce((sum, s) => sum + (s.vector_score || 0), 0) / scores.length
    const avgTextScore = scores.reduce((sum, s) => sum + (s.text_score || 0), 0) / scores.length

    // Vector vs Text Score Vergleich
    if (avgVectorScore > avgTextScore * 1.5) {
      insights.push({
        type: 'info',
        title: 'Semantische Suche dominiert',
        message: `Vector-Score (${(avgVectorScore * 100).toFixed(1)}%) ist deutlich höher als Text-Score (${(avgTextScore * 100).toFixed(1)}%). Die Suche basiert hauptsächlich auf semantischer Ähnlichkeit.`,
      })
    } else if (avgTextScore > avgVectorScore * 1.5) {
      insights.push({
        type: 'info',
        title: 'Keyword-Matching dominiert',
        message: `Text-Score (${(avgTextScore * 100).toFixed(1)}%) ist deutlich höher als Vector-Score (${(avgVectorScore * 100).toFixed(1)}%). Die Suche basiert hauptsächlich auf Keyword-Matching.`,
      })
    }

    // Durchschnittlicher Score
    if (avgHybridScore < 0.3) {
      insights.push({
        type: 'warning',
        title: 'Niedrige durchschnittliche Scores',
        message: `Der durchschnittliche Hybrid-Score von ${(avgHybridScore * 100).toFixed(1)}% ist relativ niedrig. Die Suchergebnisse könnten besser zur Frage passen.`,
        actionable: true,
        action: 'Versuche die Frage umzuformulieren oder gib Feedback zu den Ergebnissen.',
      })
    }
  }

  // Allgemeine Empfehlungen
  if (insights.length === 0) {
    insights.push({
      type: 'info',
      title: 'Metriken im erwarteten Bereich',
      message: 'Deine Metriken sind im erwarteten Bereich. Gib Feedback zu den Ergebnissen, um noch präzisere Metriken zu erhalten.',
    })
  }

  // Füge generische Empfehlung hinzu
  insights.push({
    type: 'recommendation',
    title: '💡 Tipp',
    message: 'Gib regelmäßig Feedback zu den Suchergebnissen. Das hilft dem System, bessere Rankings zu lernen.',
    actionable: true,
    action: 'Nutze die 👍/👎 Buttons im Chat, um Feedback zu geben.',
  })

  const getInsightConfig = (type: string) => {
    switch (type) {
      case 'positive':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
        }
      case 'warning':
        return {
          icon: AlertTriangle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
        }
      case 'recommendation':
        return {
          icon: Lightbulb,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
        }
      default:
        return {
          icon: TrendingUp,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
        }
    }
  }

  if (insights.length === 0) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-4">
        <Lightbulb className="w-7 h-7 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Automatische Insights</h2>
      </div>

      {insights.map((insight, index) => {
        const config = getInsightConfig(insight.type)
        const Icon = config.icon

        return (
          <div
            key={index}
            className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-r-lg p-4`}
          >
            <div className="flex items-start gap-3">
              <Icon className={`w-5 h-5 ${config.color} mt-0.5 flex-shrink-0`} />
              <div className="flex-1">
                <h3 className={`font-semibold ${config.color} mb-1`}>{insight.title}</h3>
                <p className="text-sm text-gray-700 mb-2">{insight.message}</p>
                {insight.actionable && insight.action && (
                  <div className="flex items-center gap-2 mt-2">
                    <ArrowRight className="w-4 h-4 text-gray-500" />
                    <span className="text-xs text-gray-600 italic">{insight.action}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

