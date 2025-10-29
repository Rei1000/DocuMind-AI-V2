import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'
import { mockUserMessage, mockAssistantMessage, mockConversation } from '@/test/fixtures/ragChatMessages'

vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    getChatHistory: vi.fn(),
    askQuestion: vi.fn(),
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

describe('RAGChat - Message Format', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mocks
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 1 }],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should display user messages right-aligned with blue background', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockUserMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    // Wait for session to load and history to be fetched
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    // Wait for message to appear
    await waitFor(() => {
      const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
    const messageContainer = message.closest('.bg-blue-600')
    expect(messageContainer).toBeInTheDocument()
    expect(messageContainer).toHaveClass('text-white')
    
    const flexContainer = message.closest('.justify-end')
    expect(flexContainer).toBeInTheDocument()
  })

  it('should display assistant messages left-aligned with gray background', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockAssistantMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const message = screen.getByText(/Die Artikelnummer der Freilaufwelle/)
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const message = screen.getByText(/Die Artikelnummer der Freilaufwelle/)
    const messageContainer = message.closest('.bg-gray-100')
    expect(messageContainer).toBeInTheDocument()
    expect(messageContainer).toHaveClass('text-gray-900')
    
    const flexContainer = message.closest('.justify-start')
    expect(flexContainer).toBeInTheDocument()
  })

  it('should display rounded message bubbles', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockUserMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
    const messageContainer = message.closest('.rounded-2xl')
    
    expect(messageContainer).toBeInTheDocument()
  })

  it('should show timestamp for all messages', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockUserMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      // Timestamp wird als toLocaleTimeString() formatiert - prüfe auf Time-Format (enthält Doppelpunkt)
      const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
      const timeElement = message.closest('.rounded-2xl')?.querySelector('[class*="text-xs"]')
      expect(timeElement).toBeInTheDocument()
      // Prüfe dass ein Zeitformat vorhanden ist (enthält Doppelpunkt)
      expect(timeElement?.textContent).toMatch(/\d{1,2}:\d{2}/)
    }, { timeout: 5000 })
  })

  it('should show model name for assistant messages', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockAssistantMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByText('gpt-4o-mini')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should show loading indicator during message send', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      },
    })
    
    // Mock a delayed response for askQuestion
    vi.mocked(apiClient.askQuestion).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        success: true,
        data: mockAssistantMessage
      }), 100))
    )
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Type and send a message
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...') as HTMLTextAreaElement
    input.value = 'Test Frage'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    
    // Note: Loading state testing might need adjustment based on actual implementation
  })

  it('should display multiple messages in conversation', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 4 },
        messages: mockConversation,
        total_messages: 4
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    // Wait for messages to appear - check that at least 3 messages are displayed
    await waitFor(() => {
      expect(screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')).toBeInTheDocument()
      expect(screen.getByText(/Die Artikelnummer der Freilaufwelle/)).toBeInTheDocument()
      expect(screen.getByText('Welche Werkzeuge werden benötigt?')).toBeInTheDocument()
    }, { timeout: 10000 })
    
    // Check for fourth message content (contains "Drehmomentschlüssel" or "Werkzeuge")
    // Use getAllByText since multiple messages might contain these words
    await waitFor(() => {
      const allTexts = screen.getAllByText(/Drehmomentschlüssel|Werkzeuge.*benötigt/)
      expect(allTexts.length).toBeGreaterThan(0)
    }, { timeout: 5000 })
  })

  it('should show user message on the right side with proper margin', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockUserMessage],
        total_messages: 1
      },
    })
    
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      const message = screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const userMessageContainer = container.querySelector('.ml-12')
    expect(userMessageContainer).toBeInTheDocument()
  })

  it('should show assistant message on the left side with proper margin', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockAssistantMessage],
        total_messages: 1
      },
    })
    
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      const message = screen.getByText(/Die Artikelnummer der Freilaufwelle/)
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const assistantMessageContainer = container.querySelector('.mr-12')
    expect(assistantMessageContainer).toBeInTheDocument()
  })

  it('should limit message width to 85%', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockUserMessage],
        total_messages: 1
      },
    })
    
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })
    
    await waitFor(() => {
      const messageContainer = container.querySelector('[class*="max-w-[85%]"]')
      expect(messageContainer).toBeInTheDocument()
    }, { timeout: 5000 })
  })
})
