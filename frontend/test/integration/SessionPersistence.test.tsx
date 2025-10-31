/**
 * Integration Tests: Session Persistence
 * 
 * Testet dass Chat-Sessions beim Page-Wechsel erhalten bleiben.
 * TDD: RED → GREEN → REFACTOR
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DashboardProvider, useDashboard } from '@/lib/contexts/DashboardContext'

// Mock API Client - muss vor vi.mock() definiert werden
vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    getChatHistory: vi.fn(),
    askQuestion: vi.fn(),
    deleteChatSession: vi.fn()
  }
}))

// Mock User Context
vi.mock('@/lib/contexts/UserContext', () => ({
  UserProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useUser: () => ({
    userId: 1,
    permissions: { canChatRAG: true }
  })
}))

import { apiClient } from '@/lib/api/rag'

// Test Component
function TestComponent() {
  const { selectedSessionId, selectSession } = useDashboard()
  
  return (
    <div>
      <div data-testid="selected-session">{selectedSessionId || 'none'}</div>
      <button onClick={() => selectSession(123)}>Select Session 123</button>
    </div>
  )
}

describe('Session Persistence', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should persist selectedSessionId in localStorage', async () => {
    ;(apiClient.getChatSessions as any).mockResolvedValue({
      data: [
        { id: 123, session_name: 'Test Session', created_at: '2024-01-01', last_activity: null, message_count: 0 }
      ]
    })
    ;(apiClient.getChatHistory as any).mockResolvedValue({
      data: { messages: [] }
    })

    render(
      <DashboardProvider>
        <TestComponent />
      </DashboardProvider>
    )

    // Select a session
    const selectButton = screen.getByText('Select Session 123')
    selectButton.click()

    await waitFor(() => {
      expect(localStorage.getItem('rag_selected_session_id')).toBe('123')
    })
  })

  it('should restore selectedSessionId from localStorage on mount', async () => {
    // Pre-set localStorage
    localStorage.setItem('rag_selected_session_id', '456')

    ;(apiClient.getChatSessions as any).mockResolvedValue({
      data: [
        { id: 456, session_name: 'Restored Session', created_at: '2024-01-01', last_activity: null, message_count: 0 }
      ]
    })
    ;(apiClient.getChatHistory as any).mockResolvedValue({
      data: { messages: [] }
    })

    render(
      <DashboardProvider>
        <TestComponent />
      </DashboardProvider>
    )

    await waitFor(() => {
      const selectedSession = screen.getByTestId('selected-session')
      expect(selectedSession.textContent).toBe('456')
    })
  })

  it('should persist session selection across page navigation', async () => {
    // Simulate page navigation by unmounting and remounting
    ;(apiClient.getChatSessions as any).mockResolvedValue({
      data: [
        { id: 789, session_name: 'Persistent Session', created_at: '2024-01-01', last_activity: null, message_count: 0 }
      ]
    })
    ;(apiClient.getChatHistory as any).mockResolvedValue({
      data: { messages: [] }
    })

    const { unmount } = render(
      <DashboardProvider>
        <TestComponent />
      </DashboardProvider>
    )

    // Select session
    const selectButton = screen.getByText('Select Session 123')
    selectButton.click()

    await waitFor(() => {
      expect(localStorage.getItem('rag_selected_session_id')).toBe('123')
    })

    // Unmount (simulate page navigation)
    unmount()

    // Remount (simulate returning to page)
    render(
      <DashboardProvider>
        <TestComponent />
      </DashboardProvider>
    )

    // Session should be restored
    await waitFor(() => {
      const selectedSession = screen.getByTestId('selected-session')
      expect(selectedSession.textContent).toBe('123')
    })
  })
})

