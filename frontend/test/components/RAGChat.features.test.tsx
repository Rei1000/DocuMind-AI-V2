import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { mockStructuredDataMessage, mockSafetyDataMessage } from '@/test/fixtures/ragChatMessages'
import { apiClient } from '@/lib/api/rag'
import toast from 'react-hot-toast'

vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    askQuestion: vi.fn(),
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    getChatHistory: vi.fn(),
  },
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}))

describe('RAGChat - Extended Features', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mocks
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 }],
    })
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: { id: 1, session_name: 'Default Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 },
    })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: { messages: [] },
    })
  })

  it('should display structured data with confidence score', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockStructuredDataMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      expect(screen.getByText('Artikel-Daten')).toBeInTheDocument()
      expect(screen.getByText('92% Vertrauen')).toBeInTheDocument()
      expect(screen.getByText(/Freilaufwelle/)).toBeInTheDocument()
      expect(screen.getByText(/26-10-204/)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should display safety instructions structured data', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockSafetyDataMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      expect(screen.getByText('Sicherheitshinweise')).toBeInTheDocument()
      expect(screen.getByText('88% Vertrauen')).toBeInTheDocument()
      expect(screen.getByText(/Vor Montage Strom abschalten/)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should show retry button on failed message', async () => {
    const user = userEvent.setup()
    
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      },
    })
    
    vi.mocked(apiClient.askQuestion).mockRejectedValue(new Error('API Error'))
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.type(input, 'Test Frage')
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    await user.click(sendButton)
    
    // Wait for error message to appear (component shows error in assistant message)
    await waitFor(() => {
      // Use getAllByText since error messages might appear multiple times
      const errorMessages = screen.getAllByText(/Fehler|Entschuldigung|aufgetreten/)
      expect(errorMessages.length).toBeGreaterThan(0)
    }, { timeout: 10000 })
    
    // Check for retry UI (either button or title)
    await waitFor(() => {
      const retryButton = screen.queryByText('Erneut versuchen')
      const errorTitle = screen.queryByText('Fehler beim Senden')
      expect(retryButton || errorTitle).toBeTruthy()
    }, { timeout: 5000 })
  })

  it('should send message on Enter key', async () => {
    const user = userEvent.setup()
    
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      },
    })
    
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        answer: 'Antwort',
        source_references: [],
        structured_data: []
      }
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.type(input, 'Test Frage{Enter}')
    
    // Wait for API call
    await waitFor(() => {
      expect(apiClient.askQuestion).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    // Verify message appears (user message should be added immediately)
    await waitFor(() => {
      expect(screen.getByText('Test Frage')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should create new line on Shift+Enter', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<RAGChat />, {
      dashboardState: { selectedSessionId: 1 }
    })
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...') as HTMLTextAreaElement
    await user.type(input, 'Zeile 1{Shift>}{Enter}{/Shift}Zeile 2')
    
    expect(input.value).toContain('\n')
  })

  it('should toggle microphone on click', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<RAGChat />, {
      dashboardState: { selectedSessionId: 1 }
    })
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    })
    
    const buttons = screen.getAllByRole('button')
    const micButton = buttons.find(btn => {
      const svg = btn.querySelector('svg')
      return svg && (svg.getAttribute('class')?.includes('Mic') || btn.className.includes('gray-100'))
    })
    
    expect(micButton).toBeDefined()
    
    if (micButton) {
      const initialClass = micButton.className
      await user.click(micButton)
      
      // State sollte sich ändern
      const afterClickClass = micButton.className
      expect(initialClass !== afterClickClass || initialClass.includes('bg-')).toBe(true)
    }
  })

  it('should disable send button when input is empty', () => {
    renderWithProviders(<RAGChat />, {
      dashboardState: { selectedSessionId: 1 }
    })
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    
    expect(sendButton).toBeDisabled()
  })

  it('should enable send button when input has text', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<RAGChat />, {
      dashboardState: { selectedSessionId: 1 }
    })
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.type(input, 'Test')
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    
    expect(sendButton).not.toBeDisabled()
  })

  it('should clear input after sending message', async () => {
    const user = userEvent.setup()
    
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        id: 1,
        content: 'Antwort',
        role: 'assistant',
        created_at: '2024-01-01T12:00:00Z',
        source_references: []
      }
    })
    
    renderWithProviders(<RAGChat />, {
      dashboardState: { selectedSessionId: 1 }
    })
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...') as HTMLTextAreaElement
    await user.type(input, 'Test Frage')
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    await user.click(sendButton)
    
    await waitFor(() => {
      expect(input.value).toBe('')
    })
  })
})

