import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'

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

describe('RAGChat - Layout & Design', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock API responses
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 }],
    })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: { messages: [] },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render chat header with AI Assistant branding', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Fragen Sie nach Ihren Dokumenten')).toBeInTheDocument()
    expect(screen.getByText('RAG')).toBeInTheDocument()
  })

  it('should render model selection dropdown', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const modelSelect = screen.getByRole('combobox')
      expect(modelSelect).toBeInTheDocument()
    })
    
    const modelSelect = screen.getByRole('combobox')
    expect(modelSelect).toHaveValue('gpt-4o-mini')
  })

  it('should render settings button in header', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })
    
    const buttons = screen.getAllByRole('button')
    const hasSettingsIcon = buttons.some(button => button.querySelector('svg'))
    expect(hasSettingsIcon).toBe(true)
  })

  it('should render input area at bottom with all controls', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    })
    
    // Prüfe Buttons (Mic, Paperclip, Send)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThanOrEqual(3)
  })

  it('should have proper styling for rounded corners', async () => {
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const chatContainer = container.querySelector('.rounded-lg')
      expect(chatContainer).toBeInTheDocument()
    })
  })

  it('should render with shadow for depth', async () => {
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const chatContainer = container.querySelector('.shadow-lg')
      expect(chatContainer).toBeInTheDocument()
    })
  })

  it('should have flex column layout', async () => {
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const chatContainer = container.querySelector('.flex.flex-col')
      expect(chatContainer).toBeInTheDocument()
    })
  })

  it('should have white background', async () => {
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const chatContainer = container.querySelector('.bg-white')
      expect(chatContainer).toBeInTheDocument()
    })
  })
})
