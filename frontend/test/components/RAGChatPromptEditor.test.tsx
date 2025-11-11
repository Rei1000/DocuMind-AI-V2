/**
 * Unit Tests für RAGChatPromptEditor Component (PHASE 3).
 * 
 * TDD: Tests für Prompt-Editor Funktionalität.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../utils/render'
import RAGChatPromptEditor from '@/components/RAGChatPromptEditor'
import * as ragApi from '@/lib/api/rag'

// Mock RAG API
vi.mock('@/lib/api/rag', async () => {
  const actual = await vi.importActual('@/lib/api/rag')
  return {
    ...actual,
    getRAGChatPrompt: vi.fn(),
    saveRAGChatPrompt: vi.fn(),
    deleteRAGChatPrompt: vi.fn()
  }
})

describe('RAGChatPromptEditor', () => {
  const mockPrompt = {
    id: 1,
    document_type_id: 10,
    prompt_text: 'Test RAG Chat Prompt',
    multi_query_prompt_text: 'Test Multi-Query Prompt',
    is_custom: true,
    created_by_user_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }

  const mockStandardPrompt = {
    id: 0,
    document_type_id: 10,
    prompt_text: 'Standard RAG Chat Prompt',
    multi_query_prompt_text: null,
    is_custom: false,
    created_by_user_id: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should not render when documentTypeId is null', () => {
      const { container } = renderWithProviders(
        <RAGChatPromptEditor documentTypeId={null} />
      )
      expect(container.firstChild).toBeNull()
    })

    it('should render collapsed by default', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} documentTypeName="Fachartikel" />
      )

      // Header should be visible
      expect(screen.getByText(/RAG Chat Prompt/i)).toBeInTheDocument()
      expect(screen.getByText(/Fachartikel/i)).toBeInTheDocument()

      // Content should not be visible (collapsed)
      expect(screen.queryByText(/Test RAG Chat Prompt/i)).not.toBeInTheDocument()
    })

    it('should show "Custom" badge when prompt is custom', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByText(/Custom/i)).toBeInTheDocument()
      })
    })

    it('should load and display prompt when expanded', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(ragApi.getRAGChatPrompt).toHaveBeenCalledWith(10)
        expect(screen.getByText(/Test RAG Chat Prompt/i)).toBeInTheDocument()
      })
    })

    it('should display loading state while fetching prompt', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockPrompt), 100))
      )

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      expect(screen.getByText(/Lade Prompt/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.queryByText(/Lade Prompt/i)).not.toBeInTheDocument()
      })
    })

    it('should display error message when prompt loading fails', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockRejectedValue(
        new Error('Failed to load prompt')
      )

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByText(/Failed to load prompt/i)).toBeInTheDocument()
      })
    })
  })

  describe('Tabs', () => {
    it('should show RAG Chat Prompt tab by default', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        // Check tabs exist
        const tabs = screen.getAllByRole('button', { name: /RAG Chat Prompt|Multi-Query Prompt/i })
        expect(tabs.length).toBeGreaterThan(0)
      })

      // RAG Chat Prompt tab should be active (find by class)
      const ragTab = screen.getAllByRole('button').find(btn => 
        btn.textContent?.includes('RAG Chat Prompt') && btn.className.includes('border-blue-600')
      )
      expect(ragTab).toBeDefined()
    })

    it('should switch to Multi-Query Prompt tab when clicked', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByText(/Test RAG Chat Prompt/i)).toBeInTheDocument()
      })

      // Click Multi-Query tab
      const multiQueryTab = screen.getByRole('button', { name: /Multi-Query Prompt/i })
      fireEvent.click(multiQueryTab)

      await waitFor(() => {
        expect(screen.getByText(/Test Multi-Query Prompt/i)).toBeInTheDocument()
      })
    })
  })

  describe('Edit Mode (Level 4+)', () => {
    it('should show edit button for Level 4+ users', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })
    })

    it('should not show edit button for Level 3 users', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 3 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /Bearbeiten/i })).not.toBeInTheDocument()
        expect(screen.getByText(/Nur Level 4\+/i)).toBeInTheDocument()
      })
    })

    it('should enter edit mode when edit button is clicked', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })

      // Click edit
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      fireEvent.click(editButton)

      // Should show textarea
      await waitFor(() => {
        const textarea = screen.getByRole('textbox')
        expect(textarea).toBeInTheDocument()
        expect(textarea).toHaveValue('Test RAG Chat Prompt')
      })
    })

    it('should save prompt when save button is clicked', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      vi.mocked(ragApi.saveRAGChatPrompt).mockResolvedValue({
        ...mockPrompt,
        prompt_text: 'Updated Prompt'
      })

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      // Edit text
      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Updated Prompt')

      // Save
      const saveButton = screen.getByRole('button', { name: /Speichern/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(ragApi.saveRAGChatPrompt).toHaveBeenCalledWith(10, {
          prompt_text: 'Updated Prompt',
          multi_query_prompt_text: 'Test Multi-Query Prompt'
        })
        expect(screen.getByText(/Updated Prompt/i)).toBeInTheDocument()
      })
    })

    it('should cancel edit mode when cancel button is clicked', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      // Edit text
      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Modified Prompt')

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /Abbrechen/i })
      await user.click(cancelButton)

      // Should revert to original
      await waitFor(() => {
        expect(screen.getByText(/Test RAG Chat Prompt/i)).toBeInTheDocument()
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      })
    })

    it('should show reset button only for custom prompts', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Zurücksetzen/i })).toBeInTheDocument()
      })
    })

    it('should not show reset button for standard prompts', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockStandardPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /Zurücksetzen/i })).not.toBeInTheDocument()
      })
    })

    it('should reset prompt when reset button is clicked', async () => {
      vi.mocked(ragApi.getRAGChatPrompt)
        .mockResolvedValueOnce(mockPrompt)
        .mockResolvedValueOnce(mockStandardPrompt)
      vi.mocked(ragApi.deleteRAGChatPrompt).mockResolvedValue({
        success: true,
        message: 'Prompt deleted'
      })

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Zurücksetzen/i })).toBeInTheDocument()
      })

      // Click reset
      const resetButton = screen.getByRole('button', { name: /Zurücksetzen/i })
      await user.click(resetButton)

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled()
        expect(ragApi.deleteRAGChatPrompt).toHaveBeenCalledWith(10)
        expect(screen.getByText(/Standard RAG Chat Prompt/i)).toBeInTheDocument()
      })

      confirmSpy.mockRestore()
    })
  })

  describe('Character Counter', () => {
    it('should display character count in edit mode', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      // Check character count (format: "XX Zeichen")
      await waitFor(() => {
        const charCount = screen.getByText(/\d+ Zeichen/i)
        expect(charCount).toBeInTheDocument()
        // "Test RAG Chat Prompt" = 20 chars (ohne Leerzeichen am Ende)
        expect(charCount.textContent).toMatch(/\d+ Zeichen/)
      })
    })
  })

  describe('Multi-Query Prompt', () => {
    it('should display "Kein Custom Multi-Query Prompt" when none exists', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockStandardPrompt)

      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        fireEvent.click(header)
      }

      await waitFor(() => {
        expect(screen.getByText(/RAG Chat Prompt/i)).toBeInTheDocument()
      })

      // Switch to Multi-Query tab
      const multiQueryTab = screen.getByRole('button', { name: /Multi-Query Prompt/i })
      fireEvent.click(multiQueryTab)

      await waitFor(() => {
        expect(screen.getByText(/Kein Custom Multi-Query Prompt/i)).toBeInTheDocument()
      })
    })

    it('should allow editing Multi-Query Prompt', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      vi.mocked(ragApi.saveRAGChatPrompt).mockResolvedValue({
        ...mockPrompt,
        multi_query_prompt_text: 'Updated Multi-Query'
      })

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        // Find tab buttons
        const allButtons = screen.getAllByRole('button')
        const multiQueryTab = allButtons.find(btn => btn.textContent?.includes('Multi-Query Prompt'))
        expect(multiQueryTab).toBeDefined()
      })

      // Switch to Multi-Query tab
      const allButtons = screen.getAllByRole('button')
      const multiQueryTab = allButtons.find(btn => btn.textContent?.includes('Multi-Query Prompt') && !btn.textContent?.includes('RAG Chat Prompt'))
      if (multiQueryTab) {
        await user.click(multiQueryTab)
      }

      await waitFor(() => {
        expect(screen.getByText(/Test Multi-Query Prompt/i)).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      // Edit
      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Updated Multi-Query')

      // Save
      const saveButton = screen.getByRole('button', { name: /Speichern/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(ragApi.saveRAGChatPrompt).toHaveBeenCalledWith(10, {
          prompt_text: 'Test RAG Chat Prompt',
          multi_query_prompt_text: 'Updated Multi-Query'
        })
      })
    })
  })
})

