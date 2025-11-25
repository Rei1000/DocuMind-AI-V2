/**
 * Quality Alerts Panel Component
 * 
 * Zeigt aktuelle Alerts bei Qualitätsverschlechterung.
 * Best Practice UX mit Undo-Funktionalität und klaren Handlungsempfehlungen.
 * 
 * Version: 2.9.0
 */

'use client'

import { useState, useEffect } from 'react'
import { AlertCircle, RotateCcw, CheckCircle, XCircle, Info } from 'lucide-react'
import Tooltip from './ui/Tooltip'

interface Alert {
  id: number
  type: string
  severity: string
  message: string
  query?: string
  timestamp: string
  metrics?: any
  actionable: boolean
  undo_available: boolean
}

interface QualityAlertsPanelProps {
  severity?: string
  autoRefresh?: boolean
}

export default function QualityAlertsPanel({
  severity,
  autoRefresh = true
}: QualityAlertsPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [undoHistory, setUndoHistory] = useState<Array<{ alertId: number, timestamp: string }>>([])

  useEffect(() => {
    loadAlerts()
    if (autoRefresh) {
      const interval = setInterval(loadAlerts, 30000) // Alle 30 Sekunden
      return () => clearInterval(interval)
    }
  }, [severity, autoRefresh])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (severity) params.append('severity', severity)

      // Hole Token für Authentifizierung
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/rag/analytics/alerts?${params.toString()}`, { headers })
      if (!response.ok) throw new Error('Failed to load alerts')
      
      const alertsData = await response.json()
      setAlerts(alertsData)
    } catch (error) {
      console.error('Error loading alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = async (alert: Alert) => {
    try {
      // Bestimme Aktion basierend auf Alert-Typ
      let action = 'ignore_alert'
      if (alert.type === 'quality_degradation' && alert.metrics?.previous_ndcg_at_10) {
        // Prüfe ob ML-Modell vorhanden ist (für revert_model)
        action = 'revert_model'
      }
      
      // Hole Token für Authentifizierung
      const token = sessionStorage.getItem('token') || sessionStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/rag/analytics/undo?alert_id=${alert.id}&action=${action}`, {
        method: 'POST',
        headers
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Undo fehlgeschlagen')
      }
      
      const result = await response.json()
      
      // Markiere als "rückgängig gemacht"
      setUndoHistory([...undoHistory, { alertId: alert.id, timestamp: new Date().toISOString() }])
      
      // Zeige Erfolgsmeldung (verwende window.alert für einfache Benachrichtigung)
      window.alert(`✅ ${result.message}`)
      
      // Lade Alerts neu
      setTimeout(() => loadAlerts(), 1000)
    } catch (error: any) {
      window.alert(`❌ Fehler beim Undo: ${error.message}`)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-300',
          text: 'text-red-900',
          icon: 'text-red-600',
          badge: 'bg-red-600 text-white'
        }
      case 'high':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-300',
          text: 'text-orange-900',
          icon: 'text-orange-600',
          badge: 'bg-orange-600 text-white'
        }
      case 'medium':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-300',
          text: 'text-yellow-900',
          icon: 'text-yellow-600',
          badge: 'bg-yellow-600 text-white'
        }
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-300',
          text: 'text-blue-900',
          icon: 'text-blue-600',
          badge: 'bg-blue-600 text-white'
        }
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse text-gray-400">Lade Alerts...</div>
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-600" />
          <div>
            <h3 className="font-semibold text-green-900">Keine Alerts</h3>
            <p className="text-sm text-green-800 mt-1">
              Alle Metriken sind im erwarteten Bereich. Keine Qualitätsverschlechterungen erkannt.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-7 h-7 text-red-600" />
          <h2 className="text-2xl font-bold text-gray-900">Quality Alerts</h2>
          <Tooltip
            icon
            content={
              <div className="space-y-2">
                <p className="font-semibold">Quality Alerts</p>
                <p className="text-xs">
                  Alerts werden automatisch generiert wenn:
                </p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Qualität um &gt;10% verschlechtert</li>
                  <li>Metriken unter Schwellenwerte fallen</li>
                  <li>Signifikante Verbesserungen erkannt werden</li>
                </ul>
              </div>
            }
          />
        </div>
        <div className="text-sm text-gray-600">
          {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Alerts */}
      <div className="space-y-3">
        {alerts.map((alert) => {
          const colors = getSeverityColor(alert.severity)
          const isUndone = undoHistory.some(h => h.alertId === alert.id)
          
          return (
            <div
              key={alert.id}
              className={`border rounded-lg p-5 ${colors.bg} ${colors.border} ${isUndone ? 'opacity-60' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-3">
                    <AlertCircle className={`w-5 h-5 ${colors.icon}`} />
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${colors.badge}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-600">
                      {formatDate(alert.timestamp)}
                    </span>
                    {isUndone && (
                      <span className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs font-semibold">
                        RÜCKGÄNGIG GEMACHT
                      </span>
                    )}
                  </div>

                  {/* Message */}
                  <p className={`${colors.text} mb-3`}>{alert.message}</p>

                  {/* Query */}
                  {alert.query && (
                    <div className="mb-3 p-2 bg-white/50 rounded border border-gray-200">
                      <div className="text-xs font-semibold text-gray-700 mb-1">Betroffene Query:</div>
                      <div className="text-sm text-gray-900">
                        &quot;{alert.query.length > 100 ? alert.query.substring(0, 100) + '...' : alert.query}&quot;
                      </div>
                    </div>
                  )}

                  {/* Metrics */}
                  {alert.metrics && (
                    <div className="mb-3 p-2 bg-white/50 rounded border border-gray-200">
                      <div className="text-xs font-semibold text-gray-700 mb-1">Relevante Metriken:</div>
                      <div className="text-sm text-gray-900 space-y-1">
                        {Object.entries(alert.metrics).map(([key, value]: [string, any]) => (
                          <div key={key} className="flex justify-between">
                            <span>{key}:</span>
                            <span className="font-semibold">
                              {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actionable Info */}
                  {alert.actionable && !isUndone && (
                    <div className="mt-3 p-2 bg-white/70 rounded border border-gray-200">
                      <div className="flex items-start gap-2">
                        <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div className="text-xs text-gray-700">
                          <strong>Was kannst du tun?</strong>
                          <ul className="list-disc list-inside mt-1 space-y-1">
                            <li>Prüfe die betroffene Query und die Suchergebnisse</li>
                            <li>Gib Feedback zu den Ergebnissen (positive/negative)</li>
                            <li>Das ML-Modell wird beim nächsten Training automatisch angepasst</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4 flex flex-col gap-2">
                  {alert.undo_available && !isUndone && (
                    <button
                      onClick={() => handleUndo(alert)}
                      className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50 flex items-center gap-2 transition-colors"
                      title="Änderung rückgängig machen"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Rückgängig
                    </button>
                  )}
                  {isUndone && (
                    <div className="px-4 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm text-gray-600 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Erledigt
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

