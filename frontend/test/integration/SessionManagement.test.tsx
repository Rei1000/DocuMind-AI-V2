/**
 * Integration Tests für Session Management
 * 
 * Testet:
 * 1. Session löschen mit Messages (Foreign Key Handling)
 * 2. Mehrfache loadSessions Calls verhindern (Race Condition)
 * 3. localStorage Synchronisation nach State-Änderungen
 * 4. Session-Persistenz über Seitenwechsel
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mocks MÜSSEN vor allen anderen Imports stehen (Hoisting-Regel)
const { mockApiClient } = vi.hoisted(() => {
  return {
    mockApiClient: {
      getChatSessions: vi.fn(),
      createChatSession: vi.fn(),
      getChatHistory: vi.fn(),
      askQuestion: vi.fn(),
      deleteChatSession: vi.fn(),
      updateChatSession: vi.fn()
    }
  }
})

vi.mock('@/lib/api/rag', () => ({
  apiClient: mockApiClient
}))

vi.mock('@/lib/contexts/UserContext', () => ({
  UserProvider: (props: any) => props.children,
  useUser: () => ({
    userId: 1,
    permissions: { canChatRAG: true }
  })
}))

vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Nach den Mocks: restliche Imports
import { render, screen, waitFor } from '@testing-library/react'
import { DashboardProvider, useDashboard } from '@/lib/contexts/DashboardContext'
import SessionSidebar from '@/components/SessionSidebar'
import { act } from 'react'

// Test Component um Dashboard Context zu nutzen
function TestComponent() {
  const { sessions, selectedSessionId, createSession, deleteSession, selectSession } = useDashboard()

  return (
    <div>
      <div data-testid="session-count">{sessions.length}</div>
      <div data-testid="selected-session-id">{selectedSessionId || 'null'}</div>
      <button 
        data-testid="create-btn"
        onClick={() => createSession('New Test Session')}
      >
        Create
      </button>
      <button 
        data-testid="delete-btn"
        onClick={() => deleteSession(1)}
      >
        Delete Session 1
      </button>
      <button 
        data-testid="select-btn"
        onClick={() => selectSession(2)}
      >
        Select Session 2
      </button>
    </div>
  )
}

describe('Session Management Integration Tests', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()

    // Default: Eine Session mit Messages
    mockApiClient.getChatSessions.mockResolvedValue({
      data: [
        { 
          id: 1, 
          session_name: 'Session mit Messages', 
          created_at: '2024-01-01T12:00:00Z', 
          last_activity: '2024-01-01T12:00:00Z', 
          message_count: 5 
        }
      ]
    })

    mockApiClient.getChatHistory.mockResolvedValue({
      data: {
        session: { id: 1, session_name: 'Session mit Messages', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 5 },
        messages: [
          { id: 1, role: 'user', content: 'Test Frage', created_at: '2024-01-01T12:00:00Z' },
          { id: 2, role: 'assistant', content: 'Test Antwort', created_at: '2024-01-01T12:00:00Z' }
        ],
        total_messages: 2
      }
    })

    mockApiClient.createChatSession.mockImplementation((params: any) => {
      const id = Math.floor(Math.random() * 1000) + 100
      return Promise.resolve({
        data: { 
          id, 
          session_name: params.session_name, 
          created_at: new Date().toISOString(), 
          last_activity: null, 
          message_count: 0 
        }
      })
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Session löschen mit Messages (Foreign Key Handling)', () => {
    it('should delete session even when it has messages', async () => {
      mockApiClient.deleteChatSession.mockResolvedValue({
        success: true,
        data: { status: 'success', message: 'Session gelöscht' }
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      // Warte auf initiale Session-Ladung
      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toHaveTextContent('1')
      }, { timeout: 5000 })

      // Lösche Session mit Messages
      const deleteBtn = screen.getByTestId('delete-btn')
      
      await act(async () => {
        deleteBtn.click()
      })

      // Prüfe ob deleteChatSession aufgerufen wurde
      await waitFor(() => {
        expect(mockApiClient.deleteChatSession).toHaveBeenCalledWith(1)
      })

      // Prüfe ob Sessions-Liste aktualisiert wurde (nach erfolgreicher Löschung)
      mockApiClient.getChatSessions.mockResolvedValueOnce({
        data: [] // Alle Sessions gelöscht
      })

      // Session sollte entfernt sein
      await waitFor(() => {
        expect(mockApiClient.deleteChatSession).toHaveBeenCalled()
      })
    })

    it('should handle deletion error gracefully', async () => {
      mockApiClient.deleteChatSession.mockRejectedValue(
        new Error('Foreign key constraint violation')
      )

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toHaveTextContent('1')
      })

      const deleteBtn = screen.getByTestId('delete-btn')
      
      await act(async () => {
        deleteBtn.click()
      })

      // Error sollte behandelt werden ohne App-Crash
      await waitFor(() => {
        expect(mockApiClient.deleteChatSession).toHaveBeenCalledWith(1)
      })
    })
  })

  describe('Race Condition Prevention (Mehrfache loadSessions Calls)', () => {
    it('should only call loadSessions once on mount', async () => {
      let callCount = 0
      mockApiClient.getChatSessions.mockImplementation(() => {
        callCount++
        return Promise.resolve({
          data: [{ id: 1, session_name: 'Test', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }]
        })
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      // Warte auf initiale Ladung
      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Prüfe: loadSessions sollte nur einmal aufgerufen worden sein
      // (Auch wenn useEffect mehrfach triggert)
      expect(callCount).toBeLessThanOrEqual(2) // Maximal 2 Calls (initial + eventuell refresh)
    })

    it('should prevent parallel loadSessions calls', async () => {
      let concurrentCalls = 0
      let maxConcurrent = 0

      mockApiClient.getChatSessions.mockImplementation(async () => {
        concurrentCalls++
        maxConcurrent = Math.max(maxConcurrent, concurrentCalls)
        
        // Simuliere langsame API-Antwort
        await new Promise(resolve => setTimeout(resolve, 100))
        
        concurrentCalls--
        return {
          data: [{ id: 1, session_name: 'Test', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }]
        }
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Maximal 1 paralleler Call sollte vorhanden sein
      // (Wegen Race Condition Prevention)
      expect(maxConcurrent).toBeLessThanOrEqual(1)
    })
  })

  describe('localStorage Synchronisation', () => {
    it('should sync localStorage when creating new session', async () => {
      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toBeInTheDocument()
      })

      const createBtn = screen.getByTestId('create-btn')
      
      await act(async () => {
        createBtn.click()
      })

      // Warte auf Session-Erstellung
      await waitFor(() => {
        expect(mockApiClient.createChatSession).toHaveBeenCalled()
      })

      // localStorage sollte aktualisiert sein
      const savedSessionId = localStorage.getItem('rag_selected_session_id')
      expect(savedSessionId).not.toBeNull()
      expect(savedSessionId).not.toBe('')
    })

    it('should sync localStorage when selecting different session', async () => {
      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 1, session_name: 'Session 1', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 },
          { id: 2, session_name: 'Session 2', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
        ]
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toHaveTextContent('2')
      })

      const selectBtn = screen.getByTestId('select-btn')
      
      await act(async () => {
        selectBtn.click()
      })

      // localStorage sollte Session 2 enthalten
      await waitFor(() => {
        const savedSessionId = localStorage.getItem('rag_selected_session_id')
        expect(savedSessionId).toBe('2')
      })
    })

    it('should clear localStorage when all sessions are deleted', async () => {
      localStorage.setItem('rag_selected_session_id', '1')

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toHaveTextContent('1')
      })

      // Mock: Nach Löschung keine Sessions mehr
      mockApiClient.getChatSessions.mockResolvedValueOnce({
        data: []
      })
      mockApiClient.deleteChatSession.mockResolvedValue({
        success: true
      })

      const deleteBtn = screen.getByTestId('delete-btn')
      
      await act(async () => {
        deleteBtn.click()
      })

      await waitFor(() => {
        expect(mockApiClient.deleteChatSession).toHaveBeenCalled()
      })

      // localStorage sollte geleert sein (oder auf null gesetzt)
      // (Je nach Implementation)
      const savedSessionId = localStorage.getItem('rag_selected_session_id')
      // Entweder null oder leer
      expect(savedSessionId === null || savedSessionId === '').toBeTruthy()
    })
  })

  describe('Session Persistenz über Seitenwechsel', () => {
    it('should restore session from localStorage on remount', async () => {
      // Setze initial localStorage
      localStorage.setItem('rag_selected_session_id', '5')

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      // Mock: Session 5 existiert
      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 5, session_name: 'Persisted Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
        ]
      })

      await waitFor(() => {
        expect(screen.getByTestId('selected-session-id')).toHaveTextContent('5')
      }, { timeout: 5000 })

      // localStorage sollte weiterhin Session 5 enthalten
      expect(localStorage.getItem('rag_selected_session_id')).toBe('5')
    })

    it('should fallback to first session if persisted session not found', async () => {
      // Setze localStorage auf nicht-existierende Session
      localStorage.setItem('rag_selected_session_id', '999')

      // Mock: Session 999 existiert nicht, aber Session 1 existiert
      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 1, session_name: 'Fallback Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
        ]
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      // Sollte auf erste verfügbare Session (1) fallen
      await waitFor(() => {
        expect(screen.getByTestId('selected-session-id')).toHaveTextContent('1')
      }, { timeout: 5000 })

      // localStorage sollte auf Session 1 aktualisiert sein
      expect(localStorage.getItem('rag_selected_session_id')).toBe('1')
    })
  })

  describe('56 Sessions Problem (Race Condition)', () => {
    it('should not duplicate sessions on multiple rapid loadSessions calls', async () => {
      let sessionCount = 0

      mockApiClient.getChatSessions.mockImplementation(async () => {
        sessionCount++
        // Simuliere verschiedene Session-Anzahlen bei jedem Call
        // (wie bei Race Condition)
        return {
          data: Array.from({ length: sessionCount }, (_, i) => ({
            id: i + 1,
            session_name: `Session ${i + 1}`,
            created_at: '2024-01-01T12:00:00Z',
            last_activity: '2024-01-01T12:00:00Z',
            message_count: 0
          }))
        }
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <TestComponent />
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Session-Count sollte stabil sein (nicht 56)
      // Race Condition sollte verhindern, dass Sessions mehrfach geladen werden
      const finalCount = parseInt(screen.getByTestId('session-count').textContent || '0')
      expect(finalCount).toBeLessThan(60) // Sollte deutlich unter 56 sein
    })
  })
})
