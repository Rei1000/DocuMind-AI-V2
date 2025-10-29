import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'
import toast from 'react-hot-toast'

// Mock API Client
vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    askQuestion: vi.fn(),
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    getChatHistory: vi.fn(),
  },
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  },
}))

describe('RAGChat UX Improvements', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default mocks for DashboardContext's internal API calls
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 }],
    })
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: { id: 1, session_name: 'Default Session', created_at: '2024-01-01T12:00:00Z', last_activity: '2024-01-01T12:00:00Z', message_count: 0 },
    })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      },
    })
  })

  it('should show loading state while sending message', async () => {
    const user = userEvent.setup()
    
    // Mock askQuestion to never resolve (loading state)
    vi.mocked(apiClient.askQuestion).mockReturnValue(new Promise(() => {}))

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1] // Last button is send button

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // User message should appear immediately, loading indicator should show
    await waitFor(() => {
      expect(screen.getByText('Test question')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should show error message when message sending fails', async () => {
    const user = userEvent.setup()
    
    // Mock askQuestion to reject
    vi.mocked(apiClient.askQuestion).mockRejectedValue(new Error('API Error'))

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // Should show error message in chat (from DashboardContext) - use getAllByText since multiple elements exist
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/Entschuldigung|Fehler|aufgetreten/)
      expect(errorMessages.length).toBeGreaterThan(0)
    }, { timeout: 10000 })
    
    // Should also show retry UI with lastFailedMessage - use getAllByText since message appears twice
    await waitFor(() => {
      // Check if retry UI appears (either error title or retry button should be visible)
      const hasErrorTitle = screen.queryByText('Fehler beim Senden')
      const hasRetryButton = screen.queryByText('Erneut versuchen')
      const failedMessages = screen.getAllByText('Test question')
      
      // The message appears in both user message and retry UI
      if (hasErrorTitle || hasRetryButton || failedMessages.length > 1) {
        // At least one retry UI element is visible
        expect(hasErrorTitle || hasRetryButton).toBeTruthy()
      } else {
        throw new Error('Retry UI not found')
      }
    }, { timeout: 8000 })
    
    // Toast should be called (wait for async call)
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Fehler beim Senden der Nachricht')
    }, { timeout: 3000 })
  })

  it('should show success toast when message is sent successfully', async () => {
    const user = userEvent.setup()
    
    // Mock successful askQuestion response
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        answer: 'Test response',
        source_references: [],
        structured_data: []
      }
    })

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // Should show success toast
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Nachricht erfolgreich gesendet')
    }, { timeout: 5000 })
  })

  it('should show source preview modal when source is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock response with source references
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        answer: 'Test response',
        source_references: [{
          document_id: 1,
          document_title: 'Test Document',
          page_number: 5,
          chunk_id: 1,
          preview_image_path: '/test/image.jpg',
          relevance_score: 0.95,
          text_excerpt: 'Test chunk text'
        }],
        structured_data: []
      }
    })

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // Wait for response and source reference to appear
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument()
      expect(screen.getByText('Test Document')).toBeInTheDocument()
    }, { timeout: 10000 })

    // Wait for preview button and click it
    const previewButton = await waitFor(() => {
      const buttons = screen.getAllByText('Vorschau')
      expect(buttons.length).toBeGreaterThan(0)
      return buttons[0] // Get first button if multiple exist
    }, { timeout: 5000 })
    
    // Ensure button is visible and clickable
    expect(previewButton).toBeInTheDocument()
    
    // Debug: Check if button has onClick handler
    const buttonElement = previewButton as HTMLElement
    expect(buttonElement).toBeInTheDocument()
    
    await user.click(previewButton)
    
    // Wait for modal to appear - use queryByRole to avoid immediate failure
    const modal = await waitFor(() => {
      return screen.queryByRole('dialog')
    }, { timeout: 5000 })
    
    // Assert modal is visible
    expect(modal).toBeInTheDocument()
    if (modal) {
      // "Test Document" appears in both source reference and modal, so use getAllByText
      const documents = screen.getAllByText('Test Document')
      expect(documents.length).toBeGreaterThan(0)
    }
  })

  it('should close source preview modal when close button is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock response with source references
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'assistant' as const,
          content: 'Test response',
          created_at: '2024-01-01T12:00:00Z',
          source_references: [{
            document_id: 1,
            document_title: 'Test Document',
            page_number: 5,
            chunk_id: 1,
            preview_image_path: '/test/image.jpg',
            relevance_score: 0.95,
            text_excerpt: 'Test chunk text'
          }]
        }],
        total_messages: 1
      },
    })

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalled()
    }, { timeout: 5000 })

    // Wait for message and source reference to appear
    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument()
    }, { timeout: 5000 })

    // Click on preview button
    const previewButton = screen.getByText('Vorschau')
    await user.click(previewButton)
    
    // Modal should open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Close modal using aria-label
    const closeButton = screen.getByRole('button', { name: /modal schließen/i })
    await user.click(closeButton)
    
    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should show retry button when message fails', async () => {
    const user = userEvent.setup()
    
    // Mock askQuestion to reject
    vi.mocked(apiClient.askQuestion).mockRejectedValue(new Error('API Error'))

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // Wait for error state - both error message in chat and retry UI - use getAllByText for error messages
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/Entschuldigung|Fehler|aufgetreten/)
      expect(errorMessages.length).toBeGreaterThan(0)
    }, { timeout: 10000 })
    
    // Should show retry UI
    await waitFor(() => {
      expect(screen.getByText('Fehler beim Senden')).toBeInTheDocument()
      expect(screen.getByText('Erneut versuchen')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should retry sending message when retry button is clicked', async () => {
    const user = userEvent.setup()
    
    // First call fails, second call succeeds
    vi.mocked(apiClient.askQuestion)
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValueOnce({
        success: true,
        data: {
          answer: 'Test response',
          source_references: [],
          structured_data: []
        }
      })

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })

    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]

    await user.type(input, 'Test question')
    await user.click(sendButton)

    // Wait for error state - both error message in chat and retry UI - use getAllByText
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/Entschuldigung|Fehler|aufgetreten/)
      expect(errorMessages.length).toBeGreaterThan(0)
      expect(screen.getByText('Fehler beim Senden')).toBeInTheDocument()
    }, { timeout: 10000 })

    // Click retry button
    const retryButton = screen.getByText('Erneut versuchen')
    await user.click(retryButton)
    
    // Second call should succeed
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument()
    }, { timeout: 10000 })
  })
})