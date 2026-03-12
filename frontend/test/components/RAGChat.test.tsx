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
  const mockSession = {
    id: 1,
    session_name: 'Test Session',
    created_at: '2024-01-01T12:00:00Z',
    last_activity: '2024-01-01T12:00:00Z',
    message_count: 0,
  }

  const getInputAndSendButton = async () => {
    const input = await screen.findByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    const sendButton = screen.getByRole('button', { name: /Senden/i })
    return { input, sendButton }
  }

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()

    // Default mocks for DashboardContext's internal API calls
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [mockSession],
    })
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: mockSession,
    })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: mockSession,
        messages: [],
        total_messages: 0,
      },
    })
  })

  it('zeigt Ladezustand beim Senden', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.askQuestion).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                success: true,
                data: { answer: 'Delayed response', source_references: [], structured_data: [] },
              }),
            250
          )
        })
    )

    renderWithProviders(<RAGChat />)

    const { input, sendButton } = await getInputAndSendButton()

    await user.type(input, 'Test question')
    await user.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Test question')).toBeInTheDocument()
      expect(screen.getByText(/Antwort wird generiert/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('zeigt Fehler-UI und Error-Toast bei fehlgeschlagenem Senden', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.askQuestion).mockRejectedValue(new Error('API Error'))

    renderWithProviders(<RAGChat />)
    const { input, sendButton } = await getInputAndSendButton()

    await user.type(input, 'Test question')
    await user.click(sendButton)

    await waitFor(() => {
      expect(
        screen.getByText(/Entschuldigung, es ist ein Fehler aufgetreten/i)
      ).toBeInTheDocument()
    }, { timeout: 10000 })

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Fehler beim Senden der Nachricht')
    }, { timeout: 3000 })
  })

  it('zeigt Success-Toast und Antwort bei erfolgreichem Senden', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        answer: 'Test response',
        source_references: [],
        structured_data: [],
      },
    })

    renderWithProviders(<RAGChat />)
    const { input, sendButton } = await getInputAndSendButton()

    await user.type(input, 'Test question')
    await user.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument()
      expect(toast.success).toHaveBeenCalledWith('Nachricht erfolgreich gesendet')
    }, { timeout: 5000 })
  })

  it('rendert Quellen als Inline-Link statt separatem Preview-Block', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        answer: 'Dies ist eine Antwort ohne explizite Referenz im Text.',
        source_references: [
          {
            document_id: 1,
            document_title: 'Test Document',
            page_number: 5,
            chunk_id: 1,
            preview_image_path: '/test/image.jpg',
            relevance_score: 0.95,
            text_excerpt: 'Test chunk text',
          },
        ],
        structured_data: [],
      },
    })

    renderWithProviders(<RAGChat />)
    const { input, sendButton } = await getInputAndSendButton()

    await user.type(input, 'Bitte gib Quelle an')
    await user.click(sendButton)

    await waitFor(() => {
      expect(
        screen.getByRole('link', { name: /Test Document \(Seite 5\)/i })
      ).toBeInTheDocument()
      expect(screen.queryByText(/^Vorschau$/i)).not.toBeInTheDocument()
    }, { timeout: 10000 })
  })
})