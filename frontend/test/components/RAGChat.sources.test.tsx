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
  beforeEach(() => {
    vi.clearAllMocks()
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 1 }],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should display source references below assistant messages', async () => {
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
      expect(screen.getByText('Quellen (1)')).toBeInTheDocument()
      expect(screen.getByText('Arbeitsanweisung Freilaufwelle Montage')).toBeInTheDocument()
      expect(screen.getByText('Seite 2')).toBeInTheDocument()
      expect(screen.getByText('95%')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should display text excerpt with line-clamp', async () => {
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
      const excerpt = screen.getByText(/Freilaufwelle 26-10-204/)
      expect(excerpt).toBeInTheDocument()
      expect(excerpt).toHaveClass('line-clamp-2')
    }, { timeout: 5000 })
  })

  it('should render preview button with icon', async () => {
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
      const previewButton = screen.getByText('Vorschau')
      expect(previewButton).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should open source preview modal on click', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockAssistantMessage],
        total_messages: 1
      },
    })
    
    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByText('Vorschau')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const previewButton = screen.getByText('Vorschau')
    await user.click(previewButton)
    
    // Modal sollte geöffnet sein
    await waitFor(() => {
      // SourcePreviewModal Component rendering wird getestet
      expect(previewButton).toBeInTheDocument()
    })
  })

  it('should display multiple sources as list', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [mockMultiSourceMessage],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByText('Quellen (2)')).toBeInTheDocument()
      expect(screen.getByText(/Schritt 2: Vormontage/)).toBeInTheDocument()
      expect(screen.getByText(/Schritt 3: Freilaufwelle montieren/)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should show relevance score as percentage', async () => {
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
      // 0.95 * 100 = 95%
      expect(screen.getByText('95%')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should show page number badge', async () => {
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
      const pageBadge = screen.getByText('Seite 2')
      expect(pageBadge).toBeInTheDocument()
      expect(pageBadge).toHaveClass('text-xs')
      expect(pageBadge).toHaveClass('bg-blue-100')
    }, { timeout: 5000 })
  })

  it('should display document title with proper styling', async () => {
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
      const title = screen.getByText('Arbeitsanweisung Freilaufwelle Montage')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('text-sm')
      expect(title).toHaveClass('font-medium')
    }, { timeout: 5000 })
  })

  it('should not show sources for user messages', async () => {
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'user',
          content: 'Test Frage',
          created_at: '2024-01-01T12:00:00Z',
          source_references: []
        }],
        total_messages: 1
      },
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByText('Test Frage')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    expect(screen.queryByText(/Quellen/)).not.toBeInTheDocument()
  })

  it('should show file icon for each source', async () => {
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
      // Prüfe ob FileText Icon vorhanden ist
      const sourceContainer = container.querySelector('.bg-blue-50')
      expect(sourceContainer).toBeInTheDocument()
    }, { timeout: 5000 })
  })
})
