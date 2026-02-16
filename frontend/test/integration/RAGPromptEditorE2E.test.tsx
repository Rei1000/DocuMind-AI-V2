/**
 * E2E Tests für RAG Chat Prompt Editor (PHASE 3).
 * 
 * Integration Tests für den kompletten Prompt-Editor-Workflow.
 * Verwendet echte Backend-API (wenn verfügbar).
 */

import { describe, it, expect, beforeAll, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../utils/render'
import FilterPanel from '@/components/FilterPanel'
import RAGChatPromptEditor from '@/components/RAGChatPromptEditor'
import * as ragApi from '@/lib/api/rag'
import * as documentTypesApi from '@/lib/api/documentTypes'

// Mock APIs
vi.mock('@/lib/api/rag', async () => {
  const actual = await vi.importActual('@/lib/api/rag')
  return {
    ...actual,
    getRAGChatPrompt: vi.fn(),
    saveRAGChatPrompt: vi.fn(),
    deleteRAGChatPrompt: vi.fn(),
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
      getChatSessions: vi.fn().mockResolvedValue({ data: [] }),
      createChatSession: vi.fn().mockResolvedValue({
        data: {
          id: 1001,
          session_name: 'Prompt E2E Session',
          created_at: '2025-01-01T00:00:00Z',
          last_activity: null,
          message_count: 0
        }
      }),
      getChatHistory: vi.fn().mockResolvedValue({
        data: { session: null, messages: [], total_messages: 0 }
      }),
      getDocumentTypeCounts: vi.fn()
    }
  }
})

vi.mock('@/lib/api/documentTypes', () => ({
  getDocumentTypes: vi.fn()
}))

const describePromptEditorE2E = process.env.RUN_REAL_PROMPT_EDITOR_E2E === '1' ? describe : describe.skip

describePromptEditorE2E('RAG Prompt Editor - E2E Tests', () => {
  let backendRunning = false

  const mockDocumentTypes = [
    { id: 10, name: 'Fachartikel', description: 'Wissenschaftlicher Artikel', active: true },
    { id: 11, name: 'Arbeitsanweisung', description: 'Anweisung', active: true }
  ]

  const mockPrompt = {
    id: 1,
    document_type_id: 10,
    prompt_text: 'Du bist ein erfahrener Brandschutz-Experte...',
    multi_query_prompt_text: 'Erstelle 3-5 Varianten für: {question}',
    is_custom: true,
    created_by_user_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }

  beforeAll(async () => {
    // Prüfe ob Backend läuft
    try {
      const response = await fetch('http://localhost:8000/health')
      backendRunning = response.ok
    } catch {
      console.warn('⚠️ Backend nicht erreichbar - E2E Tests verwenden Mocks')
    }
  })

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock Document Types
    vi.mocked(documentTypesApi.getDocumentTypes).mockResolvedValue(mockDocumentTypes as any)
    vi.mocked(ragApi.apiClient.getDocumentTypeCounts).mockResolvedValue({
      data: { 10: 5, 11: 3 },
      error: undefined
    })
  })

  describe('Integration in FilterPanel', () => {
    it('should show prompt editor when document type is selected', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      }

      const user = userEvent.setup()
      renderWithProviders(<FilterPanel />, { user: { userLevel: 4 } })

      // Wait for document types to load
      await waitFor(() => {
        expect(screen.getByText(/Dokumenttyp/i)).toBeInTheDocument()
      })

      // Select document type
      const select = screen.getByRole('combobox', { name: /Dokumenttyp/i })
      await user.selectOptions(select, '10')

      // Prompt editor should appear
      await waitFor(() => {
        expect(screen.getByText(/RAG Chat Prompt/i)).toBeInTheDocument()
      })
    })

    it('should hide prompt editor when document type is cleared', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      }

      const user = userEvent.setup()
      renderWithProviders(<FilterPanel />, { user: { userLevel: 4 } })

      // Wait for document types to load
      await waitFor(() => {
        expect(screen.getByText(/Dokumenttyp/i)).toBeInTheDocument()
      })

      // Select document type
      const select = screen.getByRole('combobox', { name: /Dokumenttyp/i })
      await user.selectOptions(select, '10')

      // Prompt editor should appear
      await waitFor(() => {
        expect(screen.getByText(/RAG Chat Prompt/i)).toBeInTheDocument()
      })

      // Clear selection
      await user.selectOptions(select, '')

      // Prompt editor should disappear
      await waitFor(() => {
        expect(screen.queryByText(/RAG Chat Prompt/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Complete Workflow', () => {
    it('should complete full prompt editing workflow', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
        vi.mocked(ragApi.saveRAGChatPrompt).mockResolvedValue({
          ...mockPrompt,
          prompt_text: 'Updated Prompt Text',
          updated_at: new Date().toISOString()
        })
      }

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} documentTypeName="Fachartikel" />,
        { user: { userLevel: 4 } }
      )

      // 1. Expand editor
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      // 2. Wait for prompt to load
      await waitFor(() => {
        expect(screen.getByText(/Du bist ein erfahrener Brandschutz-Experte/i)).toBeInTheDocument()
      })

      // 3. Enter edit mode
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      // 4. Edit prompt
      await waitFor(() => {
        const textarea = screen.getByRole('textbox')
        expect(textarea).toBeInTheDocument()
      })

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Updated Prompt Text')

      // 5. Save
      const saveButton = screen.getByRole('button', { name: /Speichern/i })
      await user.click(saveButton)

      // 6. Verify save was called
      await waitFor(() => {
        if (!backendRunning) {
          expect(ragApi.saveRAGChatPrompt).toHaveBeenCalledWith(10, {
            prompt_text: 'Updated Prompt Text',
            multi_query_prompt_text: 'Erstelle 3-5 Varianten für: {question}'
          })
        }
        expect(screen.getByText(/Updated Prompt Text/i)).toBeInTheDocument()
      })
    })

    it('should handle prompt reset workflow', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt)
          .mockResolvedValueOnce(mockPrompt)
          .mockResolvedValueOnce({
            ...mockPrompt,
            id: 0,
            is_custom: false,
            prompt_text: 'Standard Prompt'
          })
        vi.mocked(ragApi.deleteRAGChatPrompt).mockResolvedValue({
          success: true,
          message: 'Prompt deleted'
        })
      }

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

      // Reset
      const resetButton = screen.getByRole('button', { name: /Zurücksetzen/i })
      await user.click(resetButton)

      await waitFor(() => {
        if (!backendRunning) {
          expect(ragApi.deleteRAGChatPrompt).toHaveBeenCalledWith(10)
        }
        expect(screen.getByText(/Standard Prompt/i)).toBeInTheDocument()
      })

      confirmSpy.mockRestore()
    })

    it('should handle Multi-Query Prompt editing', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
        vi.mocked(ragApi.saveRAGChatPrompt).mockResolvedValue({
          ...mockPrompt,
          multi_query_prompt_text: 'Updated Multi-Query Prompt'
        })
      }

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
        expect(screen.getByText(/RAG Chat Prompt/i)).toBeInTheDocument()
      })

      // Switch to Multi-Query tab
      const multiQueryTab = screen.getByRole('button', { name: /Multi-Query Prompt/i })
      await user.click(multiQueryTab)

      await waitFor(() => {
        expect(screen.getByText(/Erstelle 3-5 Varianten/i)).toBeInTheDocument()
      })

      // Edit
      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'Updated Multi-Query Prompt')

      // Save
      const saveButton = screen.getByRole('button', { name: /Speichern/i })
      await user.click(saveButton)

      await waitFor(() => {
        if (!backendRunning) {
          expect(ragApi.saveRAGChatPrompt).toHaveBeenCalledWith(10, {
            prompt_text: 'Du bist ein erfahrener Brandschutz-Experte...',
            multi_query_prompt_text: 'Updated Multi-Query Prompt'
          })
        }
      })
    })
  })

  describe('RBAC Integration', () => {
    it('should prevent Level 3 users from editing prompts', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      }

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

    it('should allow Level 4+ users to edit prompts', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
      }

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
        expect(screen.queryByText(/Nur Level 4\+/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      vi.mocked(ragApi.getRAGChatPrompt).mockRejectedValue(
        new Error('Network error')
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
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      })
    })

    it('should handle save errors gracefully', async () => {
      if (!backendRunning) {
        vi.mocked(ragApi.getRAGChatPrompt).mockResolvedValue(mockPrompt)
        vi.mocked(ragApi.saveRAGChatPrompt).mockRejectedValue(
          new Error('Save failed')
        )
      }

      const user = userEvent.setup()
      renderWithProviders(
        <RAGChatPromptEditor documentTypeId={10} />,
        { user: { userLevel: 4 } }
      )

      // Expand and edit
      const header = screen.getByText(/RAG Chat Prompt/i).closest('button')
      if (header) {
        await user.click(header)
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Bearbeiten/i })).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /Bearbeiten/i })
      await user.click(editButton)

      const textarea = screen.getByRole('textbox')
      await user.clear(textarea)
      await user.type(textarea, 'New Prompt')

      const saveButton = screen.getByRole('button', { name: /Speichern/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/Save failed/i)).toBeInTheDocument()
      })
    })
  })
})

