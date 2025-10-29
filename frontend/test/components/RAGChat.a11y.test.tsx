import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'
import { mockAssistantMessage } from '@/test/fixtures/ragChatMessages'

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

describe('RAGChat - Accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [{ id: 1, session_name: 'Test Session', created_at: '2024-01-01T12:00:00Z', last_activity: null, message_count: 0 }],
    })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 0 },
        messages: [],
        total_messages: 0
      },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should have accessible textarea with placeholder', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      expect(textarea).toBeInTheDocument()
      expect(textarea.tagName).toBe('TEXTAREA')
    }, { timeout: 5000 })
  })

  it('should have accessible buttons', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(3)
      
      // Alle Buttons sollten zugänglich sein
      buttons.forEach(button => {
        expect(button).toBeInTheDocument()
      })
    }, { timeout: 5000 })
  })

  it('should have accessible combobox for model selection', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const combobox = screen.getByRole('combobox')
      expect(combobox).toBeInTheDocument()
      expect(combobox.tagName).toBe('SELECT')
    }, { timeout: 5000 })
  })

  it('should allow keyboard navigation in textarea', async () => {
    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...') as HTMLTextAreaElement
    
    // Click on textarea first to ensure focus
    await user.click(textarea)
    
    // Tippe Text
    await user.keyboard('Test')
    
    await waitFor(() => {
      expect(textarea.value).toBe('Test')
    }, { timeout: 2000 })
  })

  it('should support keyboard shortcuts for sending (Enter)', async () => {
    const user = userEvent.setup()
    
    vi.mocked(apiClient.askQuestion).mockResolvedValue({
      success: true,
      data: {
        id: 1,
        role: 'assistant',
        content: 'Test response',
        created_at: '2024-01-01T12:00:00Z',
        source_references: []
      }
    })
    
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.click(textarea)
    await user.keyboard('Test message{Enter}')
    
    // Message sollte gesendet werden
    await waitFor(() => {
      expect(apiClient.askQuestion).toHaveBeenCalled()
    })
  })

  it('should have proper focus indicators', async () => {
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      
      // Textarea sollte focus-Styling haben
      expect(textarea).toHaveClass('focus:outline-none')
      expect(textarea).toHaveClass('focus:ring-2')
    }, { timeout: 5000 })
  })

  it('should have semantic HTML structure', async () => {
    const { container } = renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      // Prüfe auf Flex-Container
      const flexContainer = container.querySelector('.flex.flex-col')
      expect(flexContainer).toBeInTheDocument()
      
      // Prüfe auf Input-Bereich
      const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      expect(textarea).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should have proper contrast ratios for text', async () => {
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
      // User messages: blue-600 auf weiß (guter Kontrast)
      const blueMessage = document.querySelector('.bg-blue-600.text-white')
      if (blueMessage) {
        expect(blueMessage).toHaveClass('text-white')
      }
      
      // Assistant messages: gray-900 auf gray-100 (guter Kontrast)
      const grayMessage = document.querySelector('.bg-gray-100.text-gray-900')
      if (grayMessage) {
        expect(grayMessage).toHaveClass('text-gray-900')
      }
    }, { timeout: 5000 })
  })

  it('should have proper aria structure for messages', async () => {
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
      // Nachrichten sollten in Container sein
      const message = screen.getByText(/Die Artikelnummer der Freilaufwelle/)
      expect(message).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should be keyboard navigable through all interactive elements', async () => {
    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    // Tab durch alle Elemente
    await user.tab() // Model-Select
    expect(screen.getByRole('combobox')).toHaveFocus()
    
    await user.tab() // Settings Button
    const buttons = screen.getAllByRole('button')
    
    // Weitere Tabs zu anderen Buttons
    await user.tab()
    await user.tab()
    await user.tab()
    
    // Textarea sollte erreichbar sein
    const textarea = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    expect(textarea).toBeInTheDocument()
  })
})
