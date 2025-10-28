'use client'

import { useState } from 'react'
import { Plus, MessageSquare, Trash2, Edit3 } from 'lucide-react'
import { useDashboard } from '@/lib/contexts/DashboardContext'

interface SessionSidebarProps {
  className?: string
}

export default function SessionSidebar({ 
  className = ''
}: SessionSidebarProps) {
  const {
    sessions,
    selectedSessionId,
    isLoadingSessions,
    createSession,
    selectSession,
    deleteSession
  } = useDashboard()

  const [showNewSessionForm, setShowNewSessionForm] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const handleCreateSession = async () => {
    if (!newSessionName.trim() || isCreating) return

    try {
      setIsCreating(true)
      await createSession(newSessionName.trim())
      setNewSessionName('')
      setShowNewSessionForm(false)
    } catch (error) {
      console.error('Fehler beim Erstellen der Session:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteSession = async (sessionId: number) => {
    if (!confirm('Möchten Sie diese Session wirklich löschen?')) return

    try {
      await deleteSession(sessionId)
    } catch (error) {
      console.error('Fehler beim Löschen der Session:', error)
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
      return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
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
            aria-label="Neue Session erstellen"
            title="Neue Session erstellen"
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
              onKeyDown={(e) => {
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
                disabled={isCreating}
                className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 disabled:opacity-50"
              >
                Abbrechen
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingSessions ? (
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
                onClick={() => selectSession(session.id)}
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

                  {/* Action Buttons (Edit, Delete) */}
                  <div className="flex-shrink-0 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // TODO: Implement session renaming
                          alert('Session umbenennen (noch nicht implementiert)')
                        }}
                        className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-100 rounded"
                        title="Session umbenennen"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSession(session.id)
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-100 rounded"
                        title="Session löschen"
                      >
                        <Trash2 className="w-4 h-4" />
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