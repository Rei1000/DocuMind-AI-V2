import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithUser } from '@/test/utils/render'
import RAGIndexing from '@/components/RAGIndexing'
import { apiClient } from '@/lib/api/rag'

// Mock API Client
vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getIndexedDocuments: vi.fn(),
    indexDocument: vi.fn(),
    reindexDocument: vi.fn()
  }
}))

// Mock Next.js router
const mockPush = vi.fn()
const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn()
  })
}))

describe('RAGIndexing Permission Guard', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock für getIndexedDocuments
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: []
    })

    // Default mock für indexDocument
    vi.mocked(apiClient.indexDocument).mockResolvedValue({
      success: true,
      data: { id: 1, status: 'processing' }
    })

    // Mock window.alert
    Object.defineProperty(window, 'alert', {
      value: vi.fn(),
      writable: true
    })
  })

  it('should render indexing button for QM users with approved document', async () => {
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /in rag indexieren/i })).toBeInTheDocument()
    })
  })

  it('should disable indexing button for non-QM users', async () => {
    const mockUser = {
      permissions: {
        canIndexDocuments: false,
        permissionLevel: 2
      }
    }

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /keine berechtigung/i })
      expect(button).toBeDisabled()
    })
  })

  it('should disable indexing button for unapproved documents', async () => {
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={false}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /dokument nicht freigegeben/i })
      expect(button).toBeDisabled()
    })
  })

  it('should show "Wird indexiert..." during indexing', async () => {
    const user = userEvent.setup()
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    // Mock für processing status - überschreibe den beforeEach Mock
    vi.mocked(apiClient.indexDocument).mockResolvedValue({
      success: true,
      data: { id: 1, status: 'processing' }
    })

    // Mock für getIndexedDocuments - sollte processing status zurückgeben
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: [{
        id: 1,
        upload_document_id: 1,
        status: 'processing',
        created_at: '2024-01-01T12:00:00Z'
      }]
    })

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    // Wait for API call to complete and button to appear
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /verarbeitung läuft/i })).toBeInTheDocument()
    })

    const button = screen.getByRole('button', { name: /verarbeitung läuft/i })
    await user.click(button)

    // Wait for indexing status to update
    await waitFor(() => {
      expect(screen.getByText('Wird indexiert...')).toBeInTheDocument()
    })

    expect(screen.getByText('Wird indexiert...')).toBeInTheDocument()
  })

  it('should show "Indexiert" for indexed documents', async () => {
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    // Mock für indexed status
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: [{
        id: 1,
        upload_document_id: 1,
        status: 'indexed',
        created_at: '2024-01-01T12:00:00Z',
        total_chunks: 5,
        document_type: 'SOP',
        indexed_at: '2024-01-01T12:00:00Z',
        last_updated: '2024-01-01T12:00:00Z'
      }]
    })

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByText('Indexiert')).toBeInTheDocument()
    })
  })

  it('should call indexDocument with correct parameters', async () => {
    const user = userEvent.setup()
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /in rag indexieren/i })).toBeInTheDocument()
    })

    const button = screen.getByRole('button', { name: /in rag indexieren/i })
    await user.click(button)

    expect(apiClient.indexDocument).toHaveBeenCalledWith({
      upload_document_id: 1,
      force_reindex: false
    })
  })
})

describe('RAGIndexing Dashboard Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock für indexed status
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: [{
        id: 1,
        upload_document_id: 1,
        status: 'indexed',
        created_at: '2024-01-01T12:00:00Z',
        total_chunks: 5,
        document_type: 'SOP',
        indexed_at: '2024-01-01T12:00:00Z',
        last_updated: '2024-01-01T12:00:00Z'
      }]
    })
  })

  it('should navigate to dashboard with pre-filled question when "Im Chat fragen" is clicked', async () => {
    const user = userEvent.setup()
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByText('Indexiert')).toBeInTheDocument()
    })

    const chatButton = screen.getByRole('button', { name: /im chat fragen/i })
    await user.click(chatButton)

    // Should navigate to dashboard with pre-filled question
    expect(mockPush).toHaveBeenCalledWith('/?question=Was%20sind%20die%20wichtigsten%20Schritte%20und%20Verfahren%20in%20dem%20SOP%20%22Test%20Document%22%3F&documentType=SOP')
  })

  it('should generate appropriate question for different document types', async () => {
    const user = userEvent.setup()
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    // Mock für indexed status für Manual document
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: [{
        id: 2,
        upload_document_id: 2,
        status: 'indexed',
        created_at: '2024-01-01T12:00:00Z',
        total_chunks: 5,
        document_type: 'Manual',
        indexed_at: '2024-01-01T12:00:00Z',
        last_updated: '2024-01-01T12:00:00Z'
      }]
    })

    renderWithUser(
      <RAGIndexing
        documentId={2}
        documentTitle="Safety Manual"
        documentType="Manual"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByText('Indexiert')).toBeInTheDocument()
    })

    const chatButton = screen.getByRole('button', { name: /im chat fragen/i })
    await user.click(chatButton)

    // Should generate appropriate question for Manual type
    expect(mockPush).toHaveBeenCalledWith('/?question=Welche%20Anweisungen%20und%20Richtlinien%20sind%20in%20dem%20Handbuch%20%22Safety%20Manual%22%20beschrieben%3F&documentType=Manual')
  })

  it('should handle special characters in document title', async () => {
    const user = userEvent.setup()
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    // Mock für indexed status für document with special characters
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: [{
        id: 3,
        upload_document_id: 3,
        status: 'indexed',
        created_at: '2024-01-01T12:00:00Z',
        total_chunks: 5,
        document_type: 'SOP',
        indexed_at: '2024-01-01T12:00:00Z',
        last_updated: '2024-01-01T12:00:00Z'
      }]
    })

    renderWithUser(
      <RAGIndexing
        documentId={3}
        documentTitle="Test & Safety Protocol (v2.1)"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByText('Indexiert')).toBeInTheDocument()
    })

    const chatButton = screen.getByRole('button', { name: /im chat fragen/i })
    await user.click(chatButton)

    // Should properly encode special characters
    expect(mockPush).toHaveBeenCalledWith('/?question=Was%20sind%20die%20wichtigsten%20Schritte%20und%20Verfahren%20in%20dem%20SOP%20%22Test%20%26%20Safety%20Protocol%20(v2.1)%22%3F&documentType=SOP')
  })

  it('should not show "Im Chat fragen" button for non-indexed documents', async () => {
    const mockUser = {
      permissions: {
        canIndexDocuments: true,
        permissionLevel: 4
      }
    }

    // Mock für not indexed status
    vi.mocked(apiClient.getIndexedDocuments).mockResolvedValue({
      success: true,
      data: []
    })

    renderWithUser(
      <RAGIndexing
        documentId={1}
        documentTitle="Test Document"
        documentType="SOP"
        isApproved={true}
      />,
      { user: mockUser }
    )

    await waitFor(() => {
      expect(screen.getByText('Nicht indexiert')).toBeInTheDocument()
    })

    expect(screen.queryByRole('button', { name: /im chat fragen/i })).not.toBeInTheDocument()
  })
})