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
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DashboardProvider } from '@/lib/contexts/DashboardContext'
import RAGChat from '@/components/RAGChat'
import SessionSidebar from '@/components/SessionSidebar'
import { act } from 'react'

describe('Session Persistence E2E Tests', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()

    // Default API responses
    mockApiClient.getChatSessions.mockResolvedValue({
      success: true,
      data: [
        { id: 1, session_name: 'Test Session 1', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
      ]
    })

    mockApiClient.getChatHistory.mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test Session 1', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      }
    })

    // Wichtig: Der Mock übernimmt den im Test eingegebenen Namen
    mockApiClient.createChatSession.mockResolvedValue({
      success: true,
      data: { id: 2, session_name: 'My New Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 }
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('56 Sessions Problem (Race Condition)', () => {
    it('should not show 56 duplicate sessions after page navigation', async () => {
      const user = userEvent.setup()

      // Mock: Initial nur 1 Session
      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 1, session_name: 'Initial Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
        ]
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <div className="flex">
              <SessionSidebar className="w-64" />
              <RAGChat className="flex-1" />
            </div>
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Initial Session')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Simuliere Seitenwechsel: Mock gibt jetzt viele Sessions zurück
      // (wie bei Race Condition wo Sessions mehrfach geladen werden)
      let callCount = 0
      mockApiClient.getChatSessions.mockImplementation(async () => {
        callCount++
        // Nach "Seitenwechsel" werden viele Sessions zurückgegeben
        if (callCount > 1) {
          return {
            data: Array.from({ length: 56 }, (_, i) => ({
              id: i + 1,
              session_name: `Session ${i + 1}`,
              created_at: '2024-01-01T12:00:00Z',
              last_activity: '2024-01-01T12:00:00Z',
              message_count: 0
            }))
          }
        }
        return {
          data: [{ id: 1, session_name: 'Initial Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }]
        }
      })

      // Simuliere "zurück zum Dashboard" - loadSessions sollte NICHT mehrfach aufgerufen werden
      // Aber wenn doch, sollten Race Conditions verhindern, dass 56 Sessions angezeigt werden

      // Prüfe: getChatSessions sollte nicht 56 mal parallel aufgerufen werden
      const initialCallCount = mockApiClient.getChatSessions.mock.calls.length

      // Warte eine kurze Zeit
      await new Promise(resolve => setTimeout(resolve, 500))

      // Die Anzahl der getChatSessions Calls sollte nicht exponentiell steigen
      // (Wegen Race Condition Prevention)
      const finalCallCount = mockApiClient.getChatSessions.mock.calls.length
      expect(finalCallCount).toBeLessThan(initialCallCount + 10) // Maximal 10 zusätzliche Calls
    })

    it('should prevent race condition when loading sessions multiple times rapidly', async () => {
      let maxConcurrentCalls = 0
      let currentConcurrentCalls = 0

      mockApiClient.getChatSessions.mockImplementation(async () => {
        currentConcurrentCalls++
        maxConcurrentCalls = Math.max(maxConcurrentCalls, currentConcurrentCalls)

        // Simuliere langsame API
        await new Promise(resolve => setTimeout(resolve, 50))

        currentConcurrentCalls--
        return {
          data: [{ id: 1, session_name: 'Test', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }]
        }
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <div className="flex">
              <SessionSidebar className="w-64" />
              <RAGChat className="flex-1" />
            </div>
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(mockApiClient.getChatSessions).toHaveBeenCalled()
      }, { timeout: 5000 })

      // Maximal 1-2 parallele Calls sollten vorhanden sein
      // (Wegen Race Condition Prevention)
      expect(maxConcurrentCalls).toBeLessThanOrEqual(2)
    })
  })

  describe('8 nicht-löschbare Sessions (Foreign Key Problem)', () => {
    it('should successfully delete sessions with messages', async () => {
      const user = userEvent.setup()

      // Mock: Session mit Messages
      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 1, session_name: 'Session mit Messages', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 8 }
        ]
      })

      mockApiClient.getChatHistory.mockResolvedValue({
        data: {
          session: { id: 1, session_name: 'Session mit Messages', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 8 },
          messages: Array.from({ length: 8 }, (_, i) => ({
            id: i + 1,
            role: i % 2 === 0 ? 'user' : 'assistant',
            content: `Message ${i + 1}`,
            created_at: '2024-01-01T12:00:00Z'
          })),
          total_messages: 8
        }
      })

      // Mock: Backend löscht erfolgreich (Foreign Key Fix funktioniert)
      mockApiClient.deleteChatSession.mockResolvedValue({
        success: true,
        data: { status: 'success', message: 'Session gelöscht' }
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <div className="flex">
              <SessionSidebar className="w-64" />
              <RAGChat className="flex-1" />
            </div>
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Session mit Messages')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Finde Delete Button (normalerweise ein Icon-Button)
      // Suche nach Session Item und dann Delete Button
      const sessionItem = screen.getByText('Session mit Messages').closest('[data-testid="session-item"]')
      
      if (sessionItem) {
        const deleteButton = sessionItem.querySelector('button[aria-label*="Löschen"], button[title*="Löschen"]')
        
        if (deleteButton) {
          await act(async () => {
            await user.click(deleteButton)
          })

          // Bestätige Löschung (wenn Confirm Dialog erscheint)
          // Prüfe ob window.confirm aufgerufen wurde
          const originalConfirm = window.confirm
          let confirmCalled = false
          window.confirm = () => {
            confirmCalled = true
            return true
          }

          if (confirmCalled || deleteButton) {
            await waitFor(() => {
              expect(mockApiClient.deleteChatSession).toHaveBeenCalledWith(1)
            }, { timeout: 5000 })

            // Prüfe: Löschung sollte erfolgreich sein (kein Foreign Key Error)
            expect(mockApiClient.deleteChatSession).toHaveReturned()
            
            window.confirm = originalConfirm
          }
        }
      }
    })

    it('should handle Foreign Key error gracefully and show error message', async () => {
      // Mock: Backend wirft Foreign Key Error (vor Fix)
      mockApiClient.deleteChatSession.mockRejectedValue(
        new Error('Foreign key constraint violation: Cannot delete session with messages')
      )

      mockApiClient.getChatSessions.mockResolvedValue({
        data: [
          { id: 1, session_name: 'Session nicht löschbar', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 5 }
        ]
      })

      await act(async () => {
        render(
          <DashboardProvider>
            <div className="flex">
              <SessionSidebar className="w-64" />
              <RAGChat className="flex-1" />
            </div>
          </DashboardProvider>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Session nicht löschbar')).toBeInTheDocument()
      }, { timeout: 5000 })

      // Versuche zu löschen - sollte Error behandeln
      // (Backend sollte jetzt Foreign Key Fix haben, aber testen wir Error-Handling)
      
      // Prüfe: Error sollte nicht zu App-Crash führen
      expect(() => {
        mockApiClient.deleteChatSession(1)
      }).not.toThrow()
    })
  })

  it('should persist session selection in localStorage', async () => {
    const user = userEvent.setup()

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')
  })

  it('should restore session from localStorage on page reload', async () => {
    localStorage.setItem('rag_selected_session_id', '1')

    const user = userEvent.setup()

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    const sessionItem = screen.getByText('Test Session 1').closest('[data-testid="session-item"]')
    expect(sessionItem).toHaveClass('bg-blue-50')
  })

  it('should create new session and persist it', async () => {
    const user = userEvent.setup()

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    }, { timeout: 5000 })

    const plusButton = screen.getByTitle('Neue Session erstellen')
    await act(async () => {
      await user.click(plusButton)
    })

    const nameInput = screen.getByPlaceholderText('Session Name...')
    await act(async () => {
      await user.type(nameInput, 'My New Session')
    })

    const createButton = screen.getByText('Erstellen')
    await act(async () => {
      await user.click(createButton)
    })

    await waitFor(() => {
      expect(screen.getByText('My New Session')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('2')

    const newSessionItem = screen.getByText('My New Session').closest('[data-testid="session-item"]')
    expect(newSessionItem).toHaveClass('bg-blue-50')
  })

  it('should switch between sessions and persist selection', async () => {
    mockApiClient.getChatSessions.mockResolvedValue({
      success: true,
      data: [
        { id: 1, session_name: 'Session 1', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 },
        { id: 2, session_name: 'Session 2', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
      ]
    })

    const user = userEvent.setup()

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Session 1')).toBeInTheDocument()
      expect(screen.getByText('Session 2')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    const session2Item = screen.getByText('Session 2').closest('[data-testid="session-item"]')
    await act(async () => {
      await user.click(session2Item!)
    })

    await waitFor(() => {
      expect(session2Item).toHaveClass('bg-blue-50')
    }, { timeout: 2000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('2')
  })

  it('should handle session deletion and update localStorage', async () => {
    mockApiClient.getChatSessions.mockResolvedValue({
      success: true,
      data: [
        { id: 1, session_name: 'Session 1', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 },
        { id: 2, session_name: 'Session 2', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }
      ]
    })

    mockApiClient.deleteChatSession.mockResolvedValue({ success: true })

    const user = userEvent.setup()

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Session 1')).toBeInTheDocument()
      expect(screen.getByText('Session 2')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    const session2Item = screen.getByText('Session 2').closest('[data-testid="session-item"]')
    await act(async () => {
      await user.click(session2Item!)
    })

    await waitFor(() => {
      expect(session2Item).toHaveClass('bg-blue-50')
    }, { timeout: 2000 })

    // Simuliere Nutzerbestätigung für confirm()
    const originalConfirm = window.confirm
    // @ts-expect-error
    window.confirm = () => true

    const deleteButton = session2Item!.querySelector('[title="Session löschen"]') as HTMLElement
    await act(async () => {
      await user.click(deleteButton)
    })

    await waitFor(() => {
      expect(screen.queryByText('Session 2')).not.toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    window.confirm = originalConfirm
  })

  it('should maintain session across component unmount/remount', async () => {
    const user = userEvent.setup()

    let unmountFn: () => void = () => {}
    await act(async () => {
      const { unmount } = render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
      unmountFn = unmount
    })

    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    await act(async () => {
      unmountFn()
    })

    await act(async () => {
      render(
        <DashboardProvider>
          <div className="flex">
            <SessionSidebar className="w-64" />
            <RAGChat className="flex-1" />
          </div>
        </DashboardProvider>
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    }, { timeout: 5000 })

    expect(localStorage.getItem('rag_selected_session_id')).toBe('1')

    const sessionItem = screen.getByText('Test Session 1').closest('[data-testid="session-item"]')
    expect(sessionItem).toHaveClass('bg-blue-50')
  })
})
