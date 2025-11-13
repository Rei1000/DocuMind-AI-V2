/**
 * Tests für Text-Highlighting in Source References (Phase 3)
 * 
 * TDD Phase 3 (RED): Tests für Text-Highlighting im Frontend.
 * Diese Tests schlagen ZUERST fehl, dann implementieren wir die Features.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import RAGTransparencyLayer from '@/components/RAGTransparencyLayer'
import { renderWithProviders } from '@/test/utils/render'
import { apiClient } from '@/lib/api/rag'
import { SourceReference } from '@/lib/api/rag'

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

// Mock SourceReference mit Query-Text für Highlighting
const mockSourceReferenceWithQuery: SourceReference = {
  document_id: 1,
  document_title: 'Test Document',
  page_number: 1,
  chunk_id: 'chunk_1',
  preview_image_path: null,
  relevance_score: 0.85,
  text_excerpt: 'Die Montage erfolgt in drei Schritten. Zuerst die Vorbereitung, dann die Montage selbst.',
  // NEU: Query-Text für Highlighting
  query_text: 'Montage Vorbereitung',  // Query die zu diesem Source Reference führte
}

describe('RAGChat - Text-Highlighting', () => {
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

  it('should highlight query words in text_excerpt in source reference', async () => {
    // RED: Dieser Test schlägt fehl, da Text-Highlighting noch nicht implementiert ist
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'assistant',
          content: 'Test answer',
          source_references: [mockSourceReferenceWithQuery],
          created_at: '2024-01-01T12:00:00Z',
        }],
        total_messages: 1,
      },
    })

    renderWithProviders(<RAGChat />)

    // Warte bis die Messages geladen sind
    await waitFor(() => {
      expect(screen.getByText('Test answer')).toBeInTheDocument()
    }, { timeout: 5000 })

    // Öffne den Transparency Layer
    const user = userEvent.setup()
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Warte bis der Layer geöffnet ist
    await waitFor(() => {
      expect(screen.getByText(/Verwendete Quellen/i)).toBeInTheDocument()
    }, { timeout: 2000 })

    // Prüfe dass Query-Wörter hervorgehoben sind
    await waitFor(() => {
      // Prüfe dass Highlighting-Markup vorhanden ist
      // Der Text kann durch <mark> Tags aufgeteilt sein, daher suchen wir nach dem HTML-Inhalt
      const excerptElements = screen.getAllByText(/Montage/i, { exact: false })
      expect(excerptElements.length).toBeGreaterThan(0)
      
      // Prüfe dass Highlighting-Markup vorhanden ist (suche in allen Containern)
      // SourceReferences werden im RAGTransparencyLayer angezeigt, nicht direkt in RAGChat
      const containers = document.querySelectorAll('.line-clamp-3, .leading-relaxed, p')
      let foundHighlight = false
      containers.forEach(container => {
        if (container.innerHTML.includes('rag-highlight')) {
          foundHighlight = true
        }
      })
      expect(foundHighlight).toBe(true)
    }, { timeout: 5000 })
  })

  it('should highlight query words case-insensitively', async () => {
    // RED: Dieser Test schlägt fehl, da Text-Highlighting noch nicht implementiert ist
    const sourceWithCaseVariation: SourceReference = {
      ...mockSourceReferenceWithQuery,
      text_excerpt: 'Die MONTAGE erfolgt in drei Schritten.',
      query_text: 'montage',
    }

    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'assistant',
          content: 'Test answer',
          source_references: [sourceWithCaseVariation],
          created_at: '2024-01-01T12:00:00Z',
        }],
        total_messages: 1,
      },
    })

    renderWithProviders(<RAGChat />)

    await waitFor(() => {
      expect(screen.getByText('Test answer')).toBeInTheDocument()
    }, { timeout: 5000 })

    const user = userEvent.setup()
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    await waitFor(() => {
      // "MONTAGE" sollte auch hervorgehoben werden (case-insensitive)
      const excerptElements = screen.getAllByText(/MONTAGE/i, { exact: false })
      expect(excerptElements.length).toBeGreaterThan(0)
      
      // Prüfe dass Highlighting-Markup vorhanden ist (suche in allen Containern)
      const containers = document.querySelectorAll('.line-clamp-3, p')
      let foundHighlight = false
      containers.forEach(container => {
        if (container.innerHTML.includes('rag-highlight')) {
          foundHighlight = true
        }
      })
      expect(foundHighlight).toBe(true)
    }, { timeout: 3000 })
  })
})

describe('RAGTransparencyLayer - Text-Highlighting', () => {
  it('should highlight query words in text_excerpt in transparency layer', async () => {
    // RED: Dieser Test schlägt fehl, da Text-Highlighting noch nicht implementiert ist
    const user = userEvent.setup()
    
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[mockSourceReferenceWithQuery]}
        modelUsed="gpt-4o-mini"
      />
    )

    // Öffne den Transparency Layer
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Warte bis der Layer geöffnet ist
    await waitFor(() => {
      expect(screen.getByText(/Verwendete Quellen/i)).toBeInTheDocument()
    }, { timeout: 2000 })

    // Prüfe dass Query-Wörter hervorgehoben sind
    await waitFor(() => {
      // Prüfe dass Highlighting-Markup vorhanden ist
      const excerptElements = screen.getAllByText(/Montage/i, { exact: false })
      expect(excerptElements.length).toBeGreaterThan(0)
      
      // Prüfe dass Highlighting-Markup vorhanden ist (in einem der Container)
      const container = document.querySelector('.leading-relaxed')
      expect(container?.innerHTML).toContain('rag-highlight')
    }, { timeout: 3000 })
  })

  it('should handle missing query_text gracefully', async () => {
    // Wenn query_text fehlt, sollte text_excerpt normal angezeigt werden
    const sourceWithoutQuery: SourceReference = {
      ...mockSourceReferenceWithQuery,
      query_text: undefined,
    }

    const user = userEvent.setup()
    
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[sourceWithoutQuery]}
        modelUsed="gpt-4o-mini"
      />
    )

    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    await waitFor(() => {
      // Text sollte normal angezeigt werden (ohne Highlighting)
      const excerpt = screen.getByText(/Die Montage erfolgt/i)
      expect(excerpt).toBeInTheDocument()
      // Kein Highlighting-Markup erwartet
    }, { timeout: 3000 })
  })
})

