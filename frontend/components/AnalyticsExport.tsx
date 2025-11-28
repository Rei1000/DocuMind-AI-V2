/**
 * Analytics Export Component
 * 
 * Export-Funktionalität für Analytics-Daten (PDF, CSV).
 * 
 * NEU v2.10.0
 */

'use client'

import { Download, FileText, FileSpreadsheet } from 'lucide-react'
import { useState } from 'react'

interface AnalyticsExportProps {
  analytics: any
  metrics?: any
}

export default function AnalyticsExport({ analytics, metrics }: AnalyticsExportProps) {
  const [exporting, setExporting] = useState(false)

  const exportToCSV = () => {
    try {
      setExporting(true)

      // Bereite CSV-Daten vor
      const csvRows: string[] = []

      // Header
      csvRows.push('Analytics Export - DocuMind-AI V2')
      csvRows.push(`Exportiert am: ${new Date().toLocaleString('de-DE')}`)
      csvRows.push('')

      // Query
      if (analytics.query) {
        csvRows.push('Query,')
        csvRows.push(`"${analytics.query}",`)
        csvRows.push('')
      }

      // Metriken
      if (metrics) {
        csvRows.push('Search Quality Metrics,')
        csvRows.push('Metrik,Wert')
        csvRows.push(`Precision@10,${metrics.precision_at_10 || 0}`)
        csvRows.push(`Recall@10,${metrics.recall_at_10 || 0}`)
        csvRows.push(`NDCG@10,${metrics.ndcg_at_10 || 0}`)
        csvRows.push(`MRR,${metrics.mrr || 0}`)
        csvRows.push('')
      }

      // Scores
      if (analytics.scores && analytics.scores.length > 0) {
        csvRows.push('Scores,')
        csvRows.push('Rank,Chunk ID,Vector Score,Text Score,Hybrid Score,ML Score,Final Score')
        analytics.scores.forEach((score: any) => {
          csvRows.push(
            `${score.rank_position || 0},"${score.chunk_id || ''}",${score.vector_score || 0},${score.text_score || 0},${score.hybrid_score || 0},${score.ml_score || ''},${score.final_score || ''}`
          )
        })
      }

      // Erstelle CSV-String
      const csvContent = csvRows.join('\n')

      // Download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `analytics-export-${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      setExporting(false)
    } catch (error) {
      console.error('Error exporting to CSV:', error)
      setExporting(false)
    }
  }

  const exportToPDF = async () => {
    try {
      setExporting(true)

      // Für PDF-Export verwenden wir window.print() als einfache Lösung
      // In Production könnte man eine Bibliothek wie jsPDF verwenden
      const printWindow = window.open('', '_blank')
      if (!printWindow) {
        alert('Pop-up-Blocker verhindert PDF-Export. Bitte erlaube Pop-ups für diese Seite.')
        setExporting(false)
        return
      }

      // Erstelle HTML für PDF
      const htmlContent = `
        <!DOCTYPE html>
        <html>
          <head>
            <title>Analytics Export - ${analytics.query || 'Unbekannt'}</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; }
              h1 { color: #1f2937; }
              h2 { color: #374151; margin-top: 20px; }
              table { width: 100%; border-collapse: collapse; margin-top: 10px; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #f3f4f6; }
            </style>
          </head>
          <body>
            <h1>Analytics Export - DocuMind-AI V2</h1>
            <p>Exportiert am: ${new Date().toLocaleString('de-DE')}</p>
            
            ${analytics.query ? `<h2>Query</h2><p>"${analytics.query}"</p>` : ''}
            
            ${metrics ? `
              <h2>Search Quality Metrics</h2>
              <table>
                <tr><th>Metrik</th><th>Wert</th></tr>
                <tr><td>Precision@10</td><td>${(metrics.precision_at_10 * 100).toFixed(1)}%</td></tr>
                <tr><td>Recall@10</td><td>${(metrics.recall_at_10 * 100).toFixed(1)}%</td></tr>
                <tr><td>NDCG@10</td><td>${(metrics.ndcg_at_10 * 100).toFixed(1)}%</td></tr>
                <tr><td>MRR</td><td>${(metrics.mrr * 100).toFixed(1)}%</td></tr>
              </table>
            ` : ''}
            
            ${analytics.scores && analytics.scores.length > 0 ? `
              <h2>Scores</h2>
              <table>
                <tr>
                  <th>Rank</th>
                  <th>Chunk ID</th>
                  <th>Vector Score</th>
                  <th>Text Score</th>
                  <th>Hybrid Score</th>
                  <th>ML Score</th>
                  <th>Final Score</th>
                </tr>
                ${analytics.scores.map((score: any) => `
                  <tr>
                    <td>${score.rank_position || 0}</td>
                    <td>${(score.chunk_id || '').substring(0, 20)}...</td>
                    <td>${((score.vector_score || 0) * 100).toFixed(1)}%</td>
                    <td>${((score.text_score || 0) * 100).toFixed(1)}%</td>
                    <td>${((score.hybrid_score || 0) * 100).toFixed(1)}%</td>
                    <td>${score.ml_score ? ((score.ml_score * 100).toFixed(1) + '%') : '-'}</td>
                    <td>${score.final_score ? ((score.final_score * 100).toFixed(1) + '%') : '-'}</td>
                  </tr>
                `).join('')}
              </table>
            ` : ''}
          </body>
        </html>
      `

      printWindow.document.write(htmlContent)
      printWindow.document.close()

      // Warte kurz, dann öffne Print-Dialog
      setTimeout(() => {
        printWindow.print()
        setExporting(false)
      }, 250)
    } catch (error) {
      console.error('Error exporting to PDF:', error)
      setExporting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 mb-1">Export</h3>
          <p className="text-sm text-gray-600">Exportiere Analytics-Daten</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToCSV}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={exportToPDF}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-4 h-4" />
            PDF
          </button>
        </div>
      </div>
      {exporting && (
        <div className="mt-3 text-sm text-gray-600 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
          Exportiere...
        </div>
      )}
    </div>
  )
}

