import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/utils/render'
import SessionSidebar from '@/components/SessionSidebar'
import { apiClient } from '@/lib/api/rag'

// Mock API Client
vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    deleteChatSession: vi.fn(),
    getChatHistory: vi.fn(),
    askQuestion: vi.fn(),
  },
}))

describe('SessionSidebar', () => {
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    vi.clearAllMocks()
    user = userEvent.setup()
    
    // Mock sessionStorage
    const sessionStorageMock = (() => {
      let store: Record<string, string> = {}
      return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => { store[key] = value },
        clear: () => { store = {} },
        removeItem: (key: string) => { delete store[key] }
      }
    })()
    Object.defineProperty(global, 'sessionStorage', { value: sessionStorageMock })
    sessionStorage.setItem('access_token', 'test-token')
    
    // Mock default API responses
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: [] })
    vi.mocked(apiClient.createChatSession).mockResolvedValue({ 
      data: { 
        id: 1, 
        session_name: 'Test Session',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T00:00:00Z',
        message_count: 0
      } 
    })
    vi.mocked(apiClient.deleteChatSession).mockResolvedValue({ data: {} })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({ data: { messages: [] } })
    
    // Mock window.confirm
    Object.defineProperty(window, 'confirm', {
      value: vi.fn(() => true),
      writable: true
    })
  })

  // Initial Render
  it('should auto-create default session when no sessions exist', async () => {
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: []
    })
    
    // Mock the createSession call that will be triggered
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: { 
        id: 1, 
        session_name: 'Chat - 08.01.2025', 
        created_at: '2024-01-01T12:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 0
      }
    })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for auto-creation of default session
    await waitFor(() => {
      expect(screen.getByText(/Chat - \d{2}\.\d{2}\.\d{4}/)).toBeInTheDocument()
    })
    
    expect(screen.getByText('1 Session')).toBeInTheDocument()
  })

  it('should render sessions list when sessions exist', async () => {
    const mockSessions = [
      {
        id: 1,
        session_name: 'Test Session 1',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 5
      },
      {
        id: 2,
        session_name: 'Test Session 2',
        created_at: '2024-01-02T00:00:00Z',
        last_activity: '2024-01-02T12:00:00Z',
        message_count: 3
      }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('Test Session 1')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Test Session 2')).toBeInTheDocument()
    expect(screen.getByText('5 Nachrichten')).toBeInTheDocument()
    expect(screen.getByText('3 Nachrichten')).toBeInTheDocument()
  })

  it('should show loading state', async () => {
    // Mock a delayed response to test loading state
    vi.mocked(apiClient.getChatSessions).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
    )
    
    renderWithProviders(<SessionSidebar />)
    
    expect(screen.getByText('Lade Sessions...')).toBeInTheDocument()
  })

  // Session Creation
  it('should create new session', async () => {
    const mockSession = {
      id: 1,
      session_name: 'New Session',
      created_at: '2024-01-01T00:00:00Z',
      last_activity: '2024-01-01T00:00:00Z',
      message_count: 0
    }
    
    vi.mocked(apiClient.createChatSession).mockResolvedValue({ data: mockSession })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Chat Sessions')).toBeInTheDocument()
    })
    
    // Click create button
    await user.click(screen.getByLabelText('Neue Session erstellen'))
    
    // Type session name
    const input = screen.getByPlaceholderText('Session Name...')
    await user.type(input, 'New Session')
    
    // Click create button
    await user.click(screen.getByText('Erstellen'))
    
    // Wait for session to be created
    await waitFor(() => {
      expect(apiClient.createChatSession).toHaveBeenCalledWith({
        session_name: 'Chat - 28.10.2025',
        user_id: 1
      })
    })
  })

  it('should not create session with empty name', async () => {
    renderWithProviders(<SessionSidebar />)
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Chat Sessions')).toBeInTheDocument()
    })
    
    // Click create button
    await user.click(screen.getByLabelText('Neue Session erstellen'))
    
    // Try to create without typing anything
    const createButton = screen.getByText('Erstellen')
    expect(createButton).toBeDisabled()
  })

  it('should cancel session creation', async () => {
    renderWithProviders(<SessionSidebar />)
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Chat Sessions')).toBeInTheDocument()
    })
    
    // Click create button
    await user.click(screen.getByLabelText('Neue Session erstellen'))
    
    // Click cancel button
    await user.click(screen.getByText('Abbrechen'))
    
    // Form should be hidden
    expect(screen.queryByPlaceholderText('Session Name...')).not.toBeInTheDocument()
  })

  it('should handle Escape key to cancel session creation', async () => {
    renderWithProviders(<SessionSidebar />)
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Chat Sessions')).toBeInTheDocument()
    })
    
    // Click create button
    await user.click(screen.getByLabelText('Neue Session erstellen'))
    
    // Press Escape key
    await user.keyboard('{Escape}')
    
    // Form should be hidden
    expect(screen.queryByPlaceholderText('Session Name...')).not.toBeInTheDocument()
  })

  // Session Selection
  it('should select session when clicked', async () => {
    const mockSessions = [
      {
        id: 1,
        session_name: 'Test Session',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 5
      }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('Test Session')).toBeInTheDocument()
    })
    
    // Click on session
    await user.click(screen.getByText('Test Session'))
    
    // Should call selectSession
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalledWith(1)
    })
  })

  it('should highlight selected session', async () => {
    const mockSessions = [
      {
        id: 1,
        session_name: 'Test Session',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 5
      }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('Test Session')).toBeInTheDocument()
    })
    
    // Click on session to select it
    await user.click(screen.getByText('Test Session'))
    
    // Wait for selection
    await waitFor(() => {
      const sessionElement = screen.getByText('Test Session').closest('.group')
      expect(sessionElement).toHaveClass('bg-blue-50', 'border', 'border-blue-200')
    })
  })

  // Session Deletion
  it('should delete session', async () => {
    const mockSessions = [
      {
        id: 1,
        session_name: 'Test Session',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 5
      }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('Test Session')).toBeInTheDocument()
    })
    
    // Hover over session to show delete button
    const sessionElement = screen.getByText('Test Session').closest('.group')
    await user.hover(sessionElement!)
    
    // Wait for delete button to appear and click it
    await waitFor(() => {
      const deleteButton = screen.getByTitle('Session löschen')
      user.click(deleteButton)
    })
    
    // Should call deleteSession
    await waitFor(() => {
      expect(apiClient.deleteChatSession).toHaveBeenCalledWith(1)
    })
  })

  // Date Formatting
  it('should format dates correctly', async () => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
    
    const mockSessions = [
      {
        id: 1,
        session_name: 'Today Session',
        created_at: today.toISOString(),
        last_activity: today.toISOString(),
        message_count: 1
      },
      {
        id: 2,
        session_name: 'Yesterday Session',
        created_at: yesterday.toISOString(),
        last_activity: yesterday.toISOString(),
        message_count: 2
      },
      {
        id: 3,
        session_name: 'Last Week Session',
        created_at: lastWeek.toISOString(),
        last_activity: lastWeek.toISOString(),
        message_count: 3
      }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('Today Session')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Heute')).toBeInTheDocument()
    expect(screen.getByText('Gestern')).toBeInTheDocument()
    expect(screen.getByText('21.10.')).toBeInTheDocument() // Last week date
  })

  // Error Handling
  it('should handle error gracefully and create default session', async () => {
    vi.mocked(apiClient.getChatSessions).mockRejectedValue(new Error('API Error'))
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: { 
        id: 1, 
        session_name: 'Chat - 08.01.2025', 
        created_at: '2024-01-01T12:00:00Z',
        last_activity: '2024-01-01T12:00:00Z',
        message_count: 0
      }
    })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for default session to be created
    await waitFor(() => {
      expect(screen.getByText(/Chat - \d{2}\.\d{2}\.\d{4}/)).toBeInTheDocument()
    })
    
    expect(screen.getByText('1 Session')).toBeInTheDocument()
  })

  // Session Count
  it('should display correct session count', async () => {
    const mockSessions = [
      { id: 1, session_name: 'Session 1', created_at: '2024-01-01T00:00:00Z', last_activity: '2024-01-01T00:00:00Z', message_count: 1 },
      { id: 2, session_name: 'Session 2', created_at: '2024-01-02T00:00:00Z', last_activity: '2024-01-02T00:00:00Z', message_count: 2 }
    ]
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ data: mockSessions })
    
    renderWithProviders(<SessionSidebar />)
    
    // Wait for sessions to load
    await waitFor(() => {
      expect(screen.getByText('2 Sessions')).toBeInTheDocument()
    })
  })
})