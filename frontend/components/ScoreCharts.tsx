/**
 * Score Charts Component
 * 
 * Interaktive Charts für Score-Übersicht:
 * - Bar Chart: Vergleich aller Scores (Vector, Text, Hybrid, ML, Final)
 * - Line Chart: Score-Verlauf über Rank-Position
 * - Radar Chart: Multi-Dimensional Score Comparison
 */

'use client'

import { BarChart, Bar, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Cell, Brush } from 'recharts'
import { Zap, TrendingUp, BarChart3 } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface ScoreData {
  chunk_id: string
  rank_position: number
  vector_score: number
  text_score: number
  hybrid_score: number
  ml_score?: number
  final_score?: number
}

interface ScoreChartsProps {
  scores: ScoreData[]
}

export default function ScoreCharts({ scores }: ScoreChartsProps) {
  if (!scores || scores.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500">Keine Score-Daten verfügbar</p>
      </div>
    )
  }

  // Top 10 Scores für bessere Übersicht
  const topScores = scores.slice(0, 10)

  // Daten für Bar Chart: Durchschnittliche Scores
  const averageScores = {
    vector: scores.reduce((sum, s) => sum + (s.vector_score || 0), 0) / scores.length,
    text: scores.reduce((sum, s) => sum + (s.text_score || 0), 0) / scores.length,
    hybrid: scores.reduce((sum, s) => sum + (s.hybrid_score || 0), 0) / scores.length,
    ml: scores.filter(s => s.ml_score !== undefined).length > 0
      ? scores.filter(s => s.ml_score !== undefined).reduce((sum, s) => sum + (s.ml_score || 0), 0) / scores.filter(s => s.ml_score !== undefined).length
      : null,
    final: scores.filter(s => s.final_score !== undefined).length > 0
      ? scores.filter(s => s.final_score !== undefined).reduce((sum, s) => sum + (s.final_score || 0), 0) / scores.filter(s => s.final_score !== undefined).length
      : null
  }

  const barChartData = [
    {
      name: 'Vector',
      score: averageScores.vector,
      color: '#3b82f6' // blue
    },
    {
      name: 'Text',
      score: averageScores.text,
      color: '#a855f7' // purple
    },
    {
      name: 'Hybrid',
      score: averageScores.hybrid,
      color: '#6366f1' // indigo
    },
    ...(averageScores.ml !== null ? [{
      name: 'ML',
      score: averageScores.ml,
      color: '#10b981' // green
    }] : []),
    ...(averageScores.final !== null ? [{
      name: 'Final',
      score: averageScores.final,
      color: '#ec4899' // pink
    }] : [])
  ]

  // Daten für Line Chart: Score-Verlauf über Rank
  const lineChartData = topScores.map(score => ({
    rank: score.rank_position,
    vector: (score.vector_score || 0) * 100,
    text: (score.text_score || 0) * 100,
    hybrid: (score.hybrid_score || 0) * 100,
    ml: score.ml_score ? score.ml_score * 100 : null,
    final: score.final_score ? score.final_score * 100 : null
  }))

  // Daten für Radar Chart: Top 5 Scores
  const radarChartData = topScores.slice(0, 5).map(score => ({
    rank: `#${score.rank_position}`,
    vector: (score.vector_score || 0) * 100,
    text: (score.text_score || 0) * 100,
    hybrid: (score.hybrid_score || 0) * 100
  }))

  const formatPercent = (value: number) => `${value.toFixed(1)}%`

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <BarChart3 className="w-7 h-7 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Interaktive Score-Visualisierung</h2>
        <Tooltip
          icon
          content={
            <div className="space-y-2">
              <p className="font-semibold">Interaktive Charts</p>
              <p className="text-xs">
                Diese Charts visualisieren die Score-Verteilung und -Verläufe:
              </p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li><strong>Bar Chart:</strong> Durchschnittliche Scores aller Score-Typen</li>
                <li><strong>Line Chart:</strong> Score-Verlauf über Rank-Position (Top 10)</li>
                <li><strong>Radar Chart:</strong> Multi-Dimensional Vergleich (Top 5)</li>
              </ul>
              <p className="text-xs text-gray-300 mt-2">
                Hover über die Charts für detaillierte Werte. Die Charts sind interaktiv und zeigen Tooltips.
              </p>
            </div>
          }
        />
      </div>

      {/* Chart Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart: Durchschnittliche Scores */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Durchschnittliche Scores</h3>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">Durchschnittliche Scores</p>
                  <p className="text-xs">
                    Zeigt die durchschnittlichen Scores aller Score-Typen über alle Suchergebnisse.
                    Höhere Werte = bessere durchschnittliche Relevanz.
                  </p>
                </div>
              }
            />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
              />
              <YAxis 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
                domain={[0, 1]}
                tickFormatter={(value) => formatPercent(value)}
              />
              <RechartsTooltip
                formatter={(value: number) => formatPercent(value)}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px'
                }}
              />
              <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                {barChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Line Chart: Score-Verlauf */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Score-Verlauf (Top 10)</h3>
            <Tooltip
              icon
              content={
                <div className="space-y-2">
                  <p className="font-semibold">Score-Verlauf</p>
                  <p className="text-xs">
                    Zeigt wie sich die verschiedenen Scores über die Rank-Positionen entwickeln.
                    Idealerweise sollten alle Scores mit besserem Rank (niedrigere Zahl) höher sein.
                  </p>
                </div>
              }
            />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={lineChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="rank" 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
                label={{ value: 'Rank Position', position: 'insideBottom', offset: -5, fill: '#6b7280', fontSize: 12 }}
              />
              <YAxis 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 12 }}
              />
              <RechartsTooltip
                formatter={(value: number) => `${value?.toFixed(1)}%`}
                labelFormatter={(label) => `Rank: ${label}`}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px'
                }}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              />
              <Line 
                type="monotone" 
                dataKey="vector" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Vector"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="text" 
                stroke="#a855f7" 
                strokeWidth={2}
                name="Text"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="hybrid" 
                stroke="#6366f1" 
                strokeWidth={2}
                name="Hybrid"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              {lineChartData.some(d => d.ml !== null) && (
                <Line 
                  type="monotone" 
                  dataKey="ml" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="ML"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {lineChartData.some(d => d.final !== null) && (
                <Line 
                  type="monotone" 
                  dataKey="final" 
                  stroke="#ec4899" 
                  strokeWidth={2}
                  name="Final"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {/* NEU v2.10.0: Brush für Zoom-Funktionalität */}
              <Brush 
                dataKey="rank" 
                height={30}
                stroke="#8884d8"
                tickFormatter={(value) => `#${value}`}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Radar Chart: Multi-Dimensional Comparison */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">Multi-Dimensional Score Comparison (Top 5)</h3>
          <Tooltip
            icon
            content={
              <div className="space-y-2">
                <p className="font-semibold">Radar Chart</p>
                <p className="text-xs">
                  Zeigt die Score-Verteilung für die Top 5 Ergebnisse in einem Radar-Diagramm.
                  Größere Fläche = bessere Scores über alle Dimensionen.
                </p>
              </div>
            }
          />
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarChartData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis 
              dataKey="rank" 
              tick={{ fill: '#6b7280', fontSize: 12 }}
            />
            <PolarRadiusAxis 
              angle={90} 
              domain={[0, 100]}
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickFormatter={(value) => `${value}%`}
            />
            <RechartsTooltip
              formatter={(value: number) => `${value.toFixed(1)}%`}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px'
              }}
            />
            <Radar 
              name="Vector" 
              dataKey="vector" 
              stroke="#3b82f6" 
              fill="#3b82f6" 
              fillOpacity={0.6}
            />
            <Radar 
              name="Text" 
              dataKey="text" 
              stroke="#a855f7" 
              fill="#a855f7" 
              fillOpacity={0.6}
            />
            <Radar 
              name="Hybrid" 
              dataKey="hybrid" 
              stroke="#6366f1" 
              fill="#6366f1" 
              fillOpacity={0.6}
            />
            <Legend 
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Score Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="text-sm font-medium text-blue-900 mb-1">Höchster Vector Score</div>
          <div className="text-2xl font-bold text-blue-700">
            {formatPercent(Math.max(...scores.map(s => s.vector_score || 0)))}
          </div>
          <div className="text-xs text-blue-600 mt-1">
            Rank #{scores.find(s => s.vector_score === Math.max(...scores.map(s => s.vector_score || 0)))?.rank_position}
          </div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="text-sm font-medium text-purple-900 mb-1">Höchster Hybrid Score</div>
          <div className="text-2xl font-bold text-purple-700">
            {formatPercent(Math.max(...scores.map(s => s.hybrid_score || 0)))}
          </div>
          <div className="text-xs text-purple-600 mt-1">
            Rank #{scores.find(s => s.hybrid_score === Math.max(...scores.map(s => s.hybrid_score || 0)))?.rank_position}
          </div>
        </div>
        <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
          <div className="text-sm font-medium text-indigo-900 mb-1">Durchschnittlicher Hybrid Score</div>
          <div className="text-2xl font-bold text-indigo-700">
            {formatPercent(averageScores.hybrid)}
          </div>
          <div className="text-xs text-indigo-600 mt-1">
            Über {scores.length} Ergebnisse
          </div>
        </div>
      </div>
    </div>
  )
}

