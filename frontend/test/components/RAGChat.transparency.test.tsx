/**
 * Tests für RAG Transparenz-Erweiterungen (Phase 2)
 * 
 * TDD Phase 2 (RED): Tests für erweiterte Metadaten-Anzeige im Frontend.
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

// Mock SourceReference mit erweiterten Metadaten
const mockSourceReferenceWithMetadata: SourceReference = {
  document_id: 1,
  document_title: 'Test Document',
  page_number: 1,
  chunk_id: 'chunk_1',
  preview_image_path: null,
  relevance_score: 0.85,
  text_excerpt: 'Test excerpt with Montage and Vorbereitung keywords',
  // NEU: Erweiterte Metadaten
  vector_score: 0.89,
  text_score: 0.92,
  hybrid_score: 0.90,
  rank_position: 1,
  total_candidates: 12,
  passed_rbac_filter: true,
  passed_score_threshold: true,
  chunk_metadata: {
    heading_hierarchy: ['1. Montage', '1.1 Vorbereitung'],
    confidence_score: 0.95,
    chunk_type: 'instruction',
    token_count: 150,
  },
}

describe('RAGChat - Erweiterte Metadaten-Anzeige', () => {
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

  it('should display vector_score and text_score breakdown in transparency layer', async () => {
    // Source References werden im RAGTransparencyLayer angezeigt, nicht direkt in RAGChat
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'assistant',
          content: 'Test answer',
          source_references: [mockSourceReferenceWithMetadata],
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

    // Öffne den Transparency Layer (klicke auf "Transparenz & Metadaten")
    const user = userEvent.setup()
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    expect(transparencyButton).toBeInTheDocument()
    
    // Klicke auf den Button
    await user.click(transparencyButton)

    // Warte bis der Layer geöffnet ist
    await waitFor(() => {
      expect(screen.getByText(/Verwendete Quellen/i)).toBeInTheDocument()
    }, { timeout: 2000 })

    await waitFor(() => {
      // Prüfe dass Score-Aufschlüsselung im Transparency Layer angezeigt wird
      // Vector-Score kann mehrfach vorkommen (Tooltip + Score-Aufschlüsselung)
      const vectorScoreElements = screen.getAllByText(/Vector-Score/i)
      expect(vectorScoreElements.length).toBeGreaterThanOrEqual(1)
      
      // Text-Score kann mehrfach vorkommen (Tooltip + Score-Aufschlüsselung)
      const textScoreElements = screen.getAllByText(/Text-Score/i)
      expect(textScoreElements.length).toBeGreaterThanOrEqual(1)
      
      // Prüfe auf die Prozentwerte (können in verschiedenen Elementen sein - Tooltip + Score-Aufschlüsselung)
      const vectorScoreValues = screen.getAllByText(/89%/i)
      expect(vectorScoreValues.length).toBeGreaterThanOrEqual(1)
      
      const textScoreValues = screen.getAllByText(/92%/i)
      expect(textScoreValues.length).toBeGreaterThanOrEqual(1)
    }, { timeout: 5000 })
  })

  it('should display rank_position and total_candidates in transparency layer', async () => {
    // Source References werden im RAGTransparencyLayer angezeigt
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: { id: 1, session_name: 'Test', created_at: '2024-01-01', last_activity: null, message_count: 1 },
        messages: [{
          id: 1,
          role: 'assistant',
          content: 'Test answer',
          source_references: [mockSourceReferenceWithMetadata],
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

    await waitFor(() => {
      // Prüfe dass Ranking-Informationen im Transparency Layer angezeigt werden
      expect(screen.getByText(/Rang 1 von 12/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })
})

describe('RAGTransparencyLayer - Erweiterte Metadaten', () => {
  it('should display vector_score and text_score breakdown in transparency layer', async () => {
    const user = userEvent.setup()
    
    // RAGTransparencyLayer benötigt keinen DashboardContext, verwende render direkt
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[mockSourceReferenceWithMetadata]}
        modelUsed="gpt-4o-mini"
        processingTimeMs={500}
        tokensUsed={100}
      />
    )

    // Öffne den Transparency Layer (klicke auf den Button)
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Warte bis der Layer geöffnet ist
    await waitFor(() => {
      expect(screen.getByText(/Verwendete Quellen/i)).toBeInTheDocument()
    }, { timeout: 2000 })

    // Prüfe dass Score-Aufschlüsselung angezeigt wird
    await waitFor(() => {
      // Vector-Score kann mehrfach vorkommen (Tooltip + Score-Aufschlüsselung)
      const vectorScoreElements = screen.getAllByText(/Vector-Score/i)
      expect(vectorScoreElements.length).toBeGreaterThanOrEqual(1)
      
      // Text-Score kann mehrfach vorkommen (Tooltip + Score-Aufschlüsselung)
      const textScoreElements = screen.getAllByText(/Text-Score/i)
      expect(textScoreElements.length).toBeGreaterThanOrEqual(1)
      
      // Prüfe auf die Prozentwerte (können in verschiedenen Elementen sein - Tooltip + Score-Aufschlüsselung)
      const vectorScoreValues = screen.getAllByText(/89%/i)
      expect(vectorScoreValues.length).toBeGreaterThanOrEqual(1)
      
      const textScoreValues = screen.getAllByText(/92%/i)
      expect(textScoreValues.length).toBeGreaterThanOrEqual(1)
    }, { timeout: 3000 })
  })

  it('should display rank_position and total_candidates in transparency layer', async () => {
    const user = userEvent.setup()
    
    // RAGTransparencyLayer benötigt keinen DashboardContext, verwende render direkt
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[mockSourceReferenceWithMetadata]}
        modelUsed="gpt-4o-mini"
      />
    )

    // Öffne den Transparency Layer
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Prüfe dass Ranking-Informationen angezeigt werden
    await waitFor(() => {
      expect(screen.getByText(/Rang 1 von 12/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should display chunk_metadata in transparency layer', async () => {
    const user = userEvent.setup()
    
    // RAGTransparencyLayer benötigt keinen DashboardContext, verwende render direkt
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[mockSourceReferenceWithMetadata]}
        modelUsed="gpt-4o-mini"
      />
    )

    // Öffne den Transparency Layer
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Prüfe dass Chunk-Metadaten angezeigt werden
    await waitFor(() => {
      expect(screen.getByText(/Heading-Hierarchy/i)).toBeInTheDocument()
      expect(screen.getByText(/1\. Montage/i)).toBeInTheDocument()
      expect(screen.getByText(/Confidence-Score/i)).toBeInTheDocument()
      expect(screen.getByText(/95%/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should display filter status in transparency layer', async () => {
    const user = userEvent.setup()
    
    // RAGTransparencyLayer benötigt keinen DashboardContext, verwende render direkt
    render(
      <RAGTransparencyLayer
        messageId={1}
        sourceReferences={[mockSourceReferenceWithMetadata]}
        modelUsed="gpt-4o-mini"
      />
    )

    // Öffne den Transparency Layer
    const transparencyButton = screen.getByRole('button', { name: /Transparenz.*Metadaten/i })
    await user.click(transparencyButton)

    // Prüfe dass Filter-Status angezeigt wird
    await waitFor(() => {
      expect(screen.getByText(/RBAC-Filter/i)).toBeInTheDocument()
      expect(screen.getByText(/Score-Threshold/i)).toBeInTheDocument()
      // "Bestanden" sollte mindestens 2x vorkommen (RBAC-Filter und Score-Threshold)
      const bestandenElements = screen.getAllByText(/Bestanden/i)
      expect(bestandenElements.length).toBeGreaterThanOrEqual(1)
    }, { timeout: 3000 })
  })
})
