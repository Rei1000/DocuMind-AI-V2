'use client'

import { useState, useEffect } from 'react'
import { Plus, MessageSquare, Trash2, Edit3, MoreVertical } from 'lucide-react'

interface ChatSession {
  id: number
  session_name: string
  created_at: string
  last_activity: string
  message_count: number
}

interface SessionSidebarProps {
  className?: string
  onSessionSelect?: (sessionId: number) => void
  selectedSessionId?: number
}

export default function SessionSidebar({ 
  className = '', 
  onSessionSelect,
  selectedSessionId 
}: SessionSidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showNewSessionForm, setShowNewSessionForm] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      // TODO: Implementiere echten API Call
      const response = await fetch('/api/rag/chat/sessions', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      } else {
        // Fallback: Mock data für Entwicklung
        setSessions([
          {
            id: 1,
            session_name: 'Montage-Anleitung',
            created_at: new Date().toISOString(),
            last_activity: new Date().toISOString(),
            message_count: 5
          },
          {
            id: 2,
            session_name: 'Sicherheitshinweise',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            last_activity: new Date(Date.now() - 3600000).toISOString(),
            message_count: 3
          },
          {
            id: 3,
            session_name: 'Wartungsprotokoll',
            created_at: new Date(Date.now() - 172800000).toISOString(),
            last_activity: new Date(Date.now() - 7200000).toISOString(),
            message_count: 8
          }
        ])
      }
    } catch (error) {
      console.error('Fehler beim Laden der Sessions:', error)
      // Fallback: Mock data
      setSessions([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateSession = async () => {
    if (!newSessionName.trim() || isCreating) return

    try {
      setIsCreating(true)
      
      const response = await fetch('/api/rag/chat/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          session_name: newSessionName.trim()
        })
      })

      if (response.ok) {
        const newSession = await response.json()
        setSessions(prev => [newSession, ...prev])
        setNewSessionName('')
        setShowNewSessionForm(false)
        
        // Automatisch die neue Session auswählen
        if (onSessionSelect) {
          onSessionSelect(newSession.id)
        }
      } else {
        throw new Error('Fehler beim Erstellen der Session')
      }
    } catch (error) {
      console.error('Fehler beim Erstellen der Session:', error)
      // TODO: Zeige Fehler-Toast
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteSession = async (sessionId: number) => {
    if (!confirm('Möchten Sie diese Session wirklich löschen?')) return

    try {
      const response = await fetch(`/api/rag/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })

      if (response.ok) {
        setSessions(prev => prev.filter(session => session.id !== sessionId))
        
        // Wenn die gelöschte Session ausgewählt war, wähle die erste verfügbare aus
        if (selectedSessionId === sessionId && sessions.length > 1) {
          const remainingSessions = sessions.filter(session => session.id !== sessionId)
          if (remainingSessions.length > 0 && onSessionSelect) {
            onSessionSelect(remainingSessions[0].id)
          }
        }
      } else {
        throw new Error('Fehler beim Löschen der Session')
      }
    } catch (error) {
      console.error('Fehler beim Löschen der Session:', error)
      // TODO: Zeige Fehler-Toast
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      return 'Heute'
    } else if (diffDays === 1) {
      return 'Gestern'
    } else if (diffDays < 7) {
      return `${diffDays} Tage`
    } else {
      return date.toLocaleDateString('de-DE')
    }
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900">Chat Sessions</h2>
          <button
            onClick={() => setShowNewSessionForm(true)}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        {/* New Session Form */}
        {showNewSessionForm && (
          <div className="space-y-2">
            <input
              type="text"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              placeholder="Session Name..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleCreateSession()
                } else if (e.key === 'Escape') {
                  setShowNewSessionForm(false)
                  setNewSessionName('')
                }
              }}
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateSession}
                disabled={!newSessionName.trim() || isCreating}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {isCreating ? 'Erstelle...' : 'Erstellen'}
              </button>
              <button
                onClick={() => {
                  setShowNewSessionForm(false)
                  setNewSessionName('')
                }}
                className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
              >
                Abbrechen
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Lade Sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center">
            <MessageSquare className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Keine Sessions vorhanden</p>
            <p className="text-xs text-gray-400 mt-1">
              Erstellen Sie eine neue Session
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedSessionId === session.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => onSessionSelect?.(session.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-gray-900 truncate">
                      {session.session_name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {formatDate(session.last_activity)}
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">
                        {formatTime(session.last_activity)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <MessageSquare className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {session.message_count} Nachrichten
                      </span>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // TODO: Implementiere Session bearbeiten
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
                      >
                        <Edit3 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSession(session.id)
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          {sessions.length} Session{sessions.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
