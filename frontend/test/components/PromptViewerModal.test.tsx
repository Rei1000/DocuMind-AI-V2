/**
 * Frontend Tests für Prompt Viewer Modal
 * 
 * Testet die UI-Komponente für die Anzeige von RAG-Prompts.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PromptViewerModal from '@/components/PromptViewerModal'
import { renderWithProviders } from '@/test/utils/render'
import { getPromptForMessage } from '@/lib/api/rag'

// Mock API
vi.mock('@/lib/api/rag', async () => {
  const actual = await vi.importActual('@/lib/api/rag')
  return {
    ...actual,
    getPromptForMessage: vi.fn(),
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      askQuestion: vi.fn(),
      getChatSessions: vi.fn(),
      createChatSession: vi.fn(),
      getChatHistory: vi.fn(),
    }
  }
})

describe('PromptViewerModal', () => {
  const mockPromptData = {
    message_id: 1,
    question: 'Was ist die Membranwirkung?',
    prompt_text: 'Dies ist der echte Prompt für die Frage.',
    context_chunks: [
      {
        chunk_id: 'doc_1_section_1',
        chunk_text: 'Dies ist ein Chunk-Text.',
        metadata: {
          page_numbers: [1],
          heading_hierarchy: ['Einleitung'],
          chunk_type: 'section'
        }
      }
    ],
    document_type: 'Fachartikel',
    model_used: 'gpt-4o-mini',
    tokens_used: 100
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should display prompt viewer when opened', async () => {
    vi.mocked(getPromptForMessage).mockResolvedValue(mockPromptData)

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    // Warte auf Loading
    await waitFor(() => {
      expect(screen.getByText('Prompt Viewer')).toBeInTheDocument()
    })

    // Prüfe dass Prompt angezeigt wird
    await waitFor(() => {
      expect(screen.getByText('Dies ist der echte Prompt für die Frage.')).toBeInTheDocument()
    })
  })

  it('should display question in prompt viewer', async () => {
    vi.mocked(getPromptForMessage).mockResolvedValue(mockPromptData)

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Was ist die Membranwirkung?')).toBeInTheDocument()
    })
  })

  it('should display context chunks in prompt viewer', async () => {
    vi.mocked(getPromptForMessage).mockResolvedValue(mockPromptData)

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Chunks verwendet:/)).toBeInTheDocument()
      expect(screen.getByText('Dies ist ein Chunk-Text.')).toBeInTheDocument()
    })
  })

  it('should display metadata (model, tokens) in prompt viewer', async () => {
    vi.mocked(getPromptForMessage).mockResolvedValue(mockPromptData)

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/gpt-4o-mini/)).toBeInTheDocument()
      expect(screen.getByText(/100/)).toBeInTheDocument()
    })
  })

  it('should call onClose when close button is clicked', async () => {
    vi.mocked(getPromptForMessage).mockResolvedValue(mockPromptData)
    const onClose = vi.fn()
    const user = userEvent.setup()

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={onClose}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Prompt Viewer')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /Schließen/i })
    await user.click(closeButton)

    expect(onClose).toHaveBeenCalled()
  })

  it('should handle error when prompt cannot be loaded', async () => {
    vi.mocked(getPromptForMessage).mockRejectedValue(new Error('Prompt nicht gefunden'))

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Prompt nicht gefunden/i)).toBeInTheDocument()
    })
  })

  it('should not render when isOpen is false', () => {
    renderWithProviders(
      <PromptViewerModal
        isOpen={false}
        messageId={1}
        onClose={() => {}}
      />
    )

    expect(screen.queryByText('Prompt Viewer')).not.toBeInTheDocument()
  })

  it('should use stored prompt from metadata (priority)', async () => {
    // Simuliere dass Prompt bereits in metadata gespeichert ist
    const storedPromptData = {
      ...mockPromptData,
      prompt_text: 'Dies ist der gespeicherte Prompt aus metadata.'
    }
    vi.mocked(getPromptForMessage).mockResolvedValue(storedPromptData)

    renderWithProviders(
      <PromptViewerModal
        isOpen={true}
        messageId={1}
        onClose={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Dies ist der gespeicherte Prompt aus metadata.')).toBeInTheDocument()
    })

    // Prüfe dass getPromptForMessage aufgerufen wurde
    expect(getPromptForMessage).toHaveBeenCalledWith(1)
  })
})

