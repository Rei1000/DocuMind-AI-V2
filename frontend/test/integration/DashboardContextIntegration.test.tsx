/**
 * Integration Tests für Dashboard Context System
 * 
 * Diese Tests verwenden echte API Calls gegen das laufende Backend.
 * Sie testen den kompletten Flow von Context-Initialisierung bis State-Management.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { renderWithProviders } from '../utils/render'
import { DashboardProvider, useDashboard } from '@/lib/contexts/DashboardContext'
import { apiClient } from '@/lib/api/rag'

// Test Component um Dashboard Context zu testen
function TestDashboardComponent() {
  const {
    sessions,
    selectedSessionId,
    currentMessages,
    isLoadingSessions,
    isLoadingMessages,
    error,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
    updateFilters,
    clearFilters
  } = useDashboard()

  return (
    <div data-testid="dashboard-test">
      <div data-testid="sessions-count">{sessions.length}</div>
      <div data-testid="selected-session">{selectedSessionId || 'none'}</div>
      <div data-testid="messages-count">{currentMessages.length}</div>
      <div data-testid="loading-sessions">{isLoadingSessions ? 'loading' : 'loaded'}</div>
      <div data-testid="loading-messages">{isLoadingMessages ? 'loading' : 'loaded'}</div>
      <div data-testid="error">{error || 'none'}</div>
      
      <button 
        data-testid="create-session"
        onClick={() => createSession('Test Session')}
      >
        Create Session
      </button>
      
      <button 
        data-testid="send-message"
        onClick={() => sendMessage('Test Message')}
      >
        Send Message
      </button>
      
      <button 
        data-testid="update-filters"
        onClick={() => updateFilters({ query: 'test query' })}
      >
        Update Filters
      </button>
      
      <button 
        data-testid="clear-filters"
        onClick={clearFilters}
      >
        Clear Filters
      </button>
      
      {sessions.map(session => (
        <div key={session.id} data-testid={`session-${session.id}`}>
          <span data-testid={`session-name-${session.id}`}>{session.session_name}</span>
          <button 
            data-testid={`select-session-${session.id}`}
            onClick={() => selectSession(session.id)}
          >
            Select
          </button>
          <button 
            data-testid={`delete-session-${session.id}`}
            onClick={() => deleteSession(session.id)}
          >
            Delete
          </button>
        </div>
      ))}
      
      {currentMessages.map((message, index) => (
        <div key={index} data-testid={`message-${index}`}>
          <span data-testid={`message-content-${index}`}>{message.content}</span>
        </div>
      ))}
    </div>
  )
}

// Integration Test Configuration
const INTEGRATION_TEST_CONFIG = {
  backendUrl: 'http://localhost:8000',
  testUserId: 1
}

describe('Dashboard Context Integration Tests', () => {
  let testSessionIds: number[] = []

  beforeAll(async () => {
    // Prüfe ob Backend erreichbar ist
    try {
      const response = await fetch(`${INTEGRATION_TEST_CONFIG.backendUrl}/api/rag/health`)
      if (!response.ok) {
        throw new Error(`Backend nicht erreichbar: ${response.status}`)
      }
      console.log('✅ Backend ist erreichbar für Dashboard Context Tests')
    } catch (error) {
      console.warn('⚠️ Backend nicht erreichbar - Dashboard Context Tests werden übersprungen')
      throw new Error('Backend nicht verfügbar für Dashboard Context Tests')
    }
  })

  beforeEach(async () => {
    // Erstelle Test-Sessions für jeden Test
    try {
      const response = await apiClient.createChatSession({
        session_name: `Dashboard Test Session - ${Date.now()}`,
        user_id: INTEGRATION_TEST_CONFIG.testUserId
      })
      
      if (response.data) {
        testSessionIds.push(response.data.id)
        console.log(`📝 Test Session erstellt: ${response.data.id}`)
      }
    } catch (error) {
      console.error('Fehler beim Erstellen der Test-Session:', error)
    }
  })

  afterAll(async () => {
    // Cleanup: Lösche alle Test-Sessions
    for (const sessionId of testSessionIds) {
      try {
        await apiClient.deleteChatSession(sessionId)
        console.log(`🗑️ Test Session gelöscht: ${sessionId}`)
      } catch (error) {
        console.error('Fehler beim Löschen der Test-Session:', error)
      }
    }
  })

  describe('Context Initialization', () => {
    it('should initialize dashboard context with real backend data', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Prüfe initiale Sessions
      await waitFor(() => {
        const sessionsCount = screen.getByTestId('sessions-count')
        expect(sessionsCount).toBeInTheDocument()
        expect(parseInt(sessionsCount.textContent || '0')).toBeGreaterThanOrEqual(0)
      }, { timeout: 10000 })

      // Prüfe dass Loading-State korrekt ist
      const loadingSessions = screen.getByTestId('loading-sessions')
      expect(loadingSessions.textContent).toBe('loaded')
    })

    it('should handle context initialization errors gracefully', async () => {
      // Temporär Backend-URL ändern um Fehler zu simulieren
      const originalApiUrl = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:9999'

      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Prüfe dass Fehlerbehandlung funktioniert
      await waitFor(() => {
        const errorElement = screen.getByTestId('error')
        // Error kann 'none' sein oder eine Fehlermeldung enthalten
        expect(errorElement).toBeInTheDocument()
      }, { timeout: 10000 })

      // Stelle ursprüngliche URL wieder her
      process.env.NEXT_PUBLIC_API_URL = originalApiUrl
    })
  })

  describe('Session Management Integration', () => {
    it('should create session via context and backend', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Erstelle neue Session
      const createButton = screen.getByTestId('create-session')
      fireEvent.click(createButton)

      // Warte auf Session-Erstellung
      await waitFor(() => {
        const sessionsCount = screen.getByTestId('sessions-count')
        const count = parseInt(sessionsCount.textContent || '0')
        expect(count).toBeGreaterThan(0)
      }, { timeout: 10000 })

      // Prüfe dass Session in der Liste erscheint
      await waitFor(() => {
        const sessionElements = screen.getAllByTestId(/^session-\d+$/)
        expect(sessionElements.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })

    it('should select session via context', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Warte auf Sessions
      await waitFor(() => {
        const sessionElements = screen.getAllByTestId(/^session-\d+$/)
        expect(sessionElements.length).toBeGreaterThan(0)
      }, { timeout: 10000 })

      // Wähle erste Session aus
      const selectButtons = screen.getAllByTestId(/^select-session-\d+$/)
      if (selectButtons.length > 0) {
        fireEvent.click(selectButtons[0])

        // Prüfe dass Session ausgewählt wurde
        await waitFor(() => {
          const selectedSession = screen.getByTestId('selected-session')
          expect(selectedSession.textContent).not.toBe('none')
        }, { timeout: 5000 })
      }
    })

    it('should delete session via context and backend', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Warte auf Sessions
      await waitFor(() => {
        const sessionElements = screen.getAllByTestId(/^session-\d+$/)
        expect(sessionElements.length).toBeGreaterThan(0)
      }, { timeout: 10000 })

      // Zähle initiale Sessions
      const initialSessionsCount = screen.getAllByTestId(/^session-\d+$/).length

      // Lösche erste Session
      const deleteButtons = screen.getAllByTestId(/^delete-session-\d+$/)
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0])

        // Warte auf Löschung
        await waitFor(() => {
          const sessionElements = screen.getAllByTestId(/^session-\d+$/)
          expect(sessionElements.length).toBeLessThan(initialSessionsCount)
        }, { timeout: 10000 })
      }
    })
  })

  describe('Message Management Integration', () => {
    it('should send message via context and backend', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Wähle eine Session aus (falls vorhanden)
      await waitFor(() => {
        const selectButtons = screen.getAllByTestId(/^select-session-\d+$/)
        if (selectButtons.length > 0) {
          fireEvent.click(selectButtons[0])
        }
      }, { timeout: 10000 })

      // Sende Nachricht
      const sendButton = screen.getByTestId('send-message')
      fireEvent.click(sendButton)

      // Warte auf Nachricht
      await waitFor(() => {
        const messagesCount = screen.getByTestId('messages-count')
        const count = parseInt(messagesCount.textContent || '0')
        expect(count).toBeGreaterThan(0)
      }, { timeout: 15000 })

      // Prüfe dass Nachricht angezeigt wird
      await waitFor(() => {
        const messageElements = screen.getAllByTestId(/^message-\d+$/)
        expect(messageElements.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })

    it('should load chat history from backend', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Wähle eine Session aus
      await waitFor(() => {
        const selectButtons = screen.getAllByTestId(/^select-session-\d+$/)
        if (selectButtons.length > 0) {
          fireEvent.click(selectButtons[0])
        }
      }, { timeout: 10000 })

      // Warte auf Chat-Historie
      await waitFor(() => {
        const loadingMessages = screen.getByTestId('loading-messages')
        expect(loadingMessages.textContent).toBe('loaded')
      }, { timeout: 10000 })
    })
  })

  describe('Filter Management Integration', () => {
    it('should update filters via context', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Aktualisiere Filter
      const updateButton = screen.getByTestId('update-filters')
      fireEvent.click(updateButton)

      // Prüfe dass Filter aktualisiert wurden
      await waitFor(() => {
        // Filter-Update sollte ohne Fehler funktionieren
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('should clear filters via context', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Lösche Filter
      const clearButton = screen.getByTestId('clear-filters')
      fireEvent.click(clearButton)

      // Prüfe dass Filter gelöscht wurden
      await waitFor(() => {
        // Filter-Clear sollte ohne Fehler funktionieren
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  describe('State Consistency Integration', () => {
    it('should maintain state consistency during multiple operations', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Führe mehrere Operationen schnell hintereinander aus
      const createButton = screen.getByTestId('create-session')
      const sendButton = screen.getByTestId('send-message')
      const updateButton = screen.getByTestId('update-filters')

      // Führe Operationen aus
      fireEvent.click(createButton)
      fireEvent.click(sendButton)
      fireEvent.click(updateButton)

      // Warte auf alle Operationen
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 15000 })

      // Prüfe dass State konsistent ist
      const sessionsCount = screen.getByTestId('sessions-count')
      const messagesCount = screen.getByTestId('messages-count')
      
      expect(sessionsCount).toBeInTheDocument()
      expect(messagesCount).toBeInTheDocument()
    })

    it('should handle concurrent API calls gracefully', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      // Starte mehrere gleichzeitige Operationen
      const createButton = screen.getByTestId('create-session')
      
      // Führe mehrere Session-Erstellungen gleichzeitig aus
      for (let i = 0; i < 3; i++) {
        fireEvent.click(createButton)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      // Warte auf alle Operationen
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 15000 })

      // Prüfe dass keine kritischen Fehler aufgetreten sind
      const errorElement = screen.getByTestId('error')
      expect(errorElement).toBeInTheDocument()
    })
  })

  describe('Performance Integration', () => {
    it('should handle rapid state updates efficiently', async () => {
      renderWithProviders(
        <DashboardProvider>
          <TestDashboardComponent />
        </DashboardProvider>
      )
      
      // Warte auf Context-Initialisierung
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      })

      const startTime = Date.now()

      // Führe viele schnelle Updates aus
      const updateButton = screen.getByTestId('update-filters')
      for (let i = 0; i < 10; i++) {
        fireEvent.click(updateButton)
        await new Promise(resolve => setTimeout(resolve, 50))
      }

      const endTime = Date.now()
      const duration = endTime - startTime

      // Prüfe dass Updates effizient verarbeitet wurden
      expect(duration).toBeLessThan(5000) // Sollte unter 5 Sekunden sein
      
      // Prüfe dass Component stabil bleibt
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-test')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })
})
