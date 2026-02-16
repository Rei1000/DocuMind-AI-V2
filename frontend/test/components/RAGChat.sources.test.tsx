import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'
import { mockAssistantMessage, mockMultiSourceMessage } from '@/test/fixtures/ragChatMessages'

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

describe('RAGChat - Source References', () => {
  const mockSession = {
    id: 1,
    session_name: 'Test Session',
    created_at: '2024-01-01T12:00:00Z',
    last_activity: null,
    message_count: 1,
  }

  const setChatHistory = (messages: unknown[]) => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: mockSession,
        messages,
        total_messages: messages.length,
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [mockSession],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('rendert Referenz-Link inline in Assistant-Nachrichten', async () => {
    setChatHistory([mockAssistantMessage])

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(
        screen.getByRole('link', {
          name: /Arbeitsanweisung Freilaufwelle Montage \(Seite 2\)/i,
        })
      ).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('behält den Assistant-Text mit injizierter Referenz bei', async () => {
    setChatHistory([mockAssistantMessage])

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(
        screen.getByText(/Die Artikelnummer der Freilaufwelle lautet 26-10-204/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/Referenz/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('rendert mehrere Referenzen als mehrere Inline-Links', async () => {
    setChatHistory([mockMultiSourceMessage])

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      const sourceLinks = screen.getAllByRole('link', {
        name: /Arbeitsanweisung Freilaufwelle \(Seite [23]\)/i,
      })
      expect(sourceLinks).toHaveLength(2)
    }, { timeout: 5000 })
  })

  it('zeigt keine Quellen-Box mehr an (nur Inline-Referenzen)', async () => {
    setChatHistory([mockAssistantMessage])

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.queryByText(/Quellen \(\d+\)/i)).not.toBeInTheDocument()
      expect(screen.getByText(/Referenz/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('zeigt Warnung wenn Assistant-Antwort ohne Quellen kommt', async () => {
    setChatHistory([
      {
        id: 2,
        role: 'assistant',
        content: 'Allgemeine Antwort ohne Dokumentbezug.',
        created_at: '2024-01-01T12:05:00Z',
        source_references: [],
      },
    ])

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByText(/Keine Dokument-Auszüge gefunden/i)).toBeInTheDocument()
      expect(screen.getByText(/keine relevanten Informationen/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('öffnet Prompt-Viewer für Assistant-Nachrichten', async () => {
    setChatHistory([mockAssistantMessage])
    const user = userEvent.setup()

    renderWithProviders(<RAGChat />)

    const promptButton = await screen.findByRole('button', { name: /Prompt/i })
    await user.click(promptButton)

    expect(promptButton).toBeInTheDocument()
  })
})
