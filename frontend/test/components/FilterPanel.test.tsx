import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/utils/render'
import FilterPanel from '@/components/FilterPanel'
import { getDocumentTypes } from '@/lib/api/documentTypes'

// Mock Document Types API
vi.mock('@/lib/api/documentTypes', () => ({
  getDocumentTypes: vi.fn()
}))

describe('FilterPanel Backend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should load document types from API on mount', async () => {
    const mockDocumentTypes = [
      {
        id: 1,
        name: 'Arbeitsanweisungen',
        code: 'WORK_INSTRUCTIONS',
        description: 'Standard Arbeitsanweisungen',
        allowed_file_types: ['.pdf'],
        max_file_size_mb: 10,
        requires_ocr: false,
        requires_vision: false,
        default_prompt_template_id: null,
        is_active: true,
        sort_order: 1,
        created_at: '2024-01-01T12:00:00Z',
        updated_at: '2024-01-01T12:00:00Z'
      },
      {
        id: 2,
        name: 'Sicherheitshinweise',
        code: 'SAFETY_INSTRUCTIONS',
        description: 'Sicherheitshinweise und -regeln',
        allowed_file_types: ['.pdf'],
        max_file_size_mb: 10,
        requires_ocr: false,
        requires_vision: false,
        default_prompt_template_id: null,
        is_active: true,
        sort_order: 2,
        created_at: '2024-01-01T12:00:00Z',
        updated_at: '2024-01-01T12:00:00Z'
      }
    ]

    vi.mocked(getDocumentTypes).mockResolvedValue(mockDocumentTypes)

    renderWithProviders(<FilterPanel />)

    // Wait for API call to complete
    await waitFor(() => {
      expect(getDocumentTypes).toHaveBeenCalledWith(true) // active_only = true
    })

    // Check if document types are displayed
    await waitFor(() => {
      expect(screen.getByText('Arbeitsanweisungen (0)')).toBeInTheDocument()
      expect(screen.getByText('Sicherheitshinweise (0)')).toBeInTheDocument()
    })
  })

  it('should handle API error gracefully', async () => {
    vi.mocked(getDocumentTypes).mockRejectedValue(new Error('API Error'))

    renderWithProviders(<FilterPanel />)

    // Wait for API call to complete
    await waitFor(() => {
      expect(getDocumentTypes).toHaveBeenCalledWith(true)
    })

    // Should show empty state (no document types)
    await waitFor(() => {
      expect(screen.getByText('Alle Typen')).toBeInTheDocument()
    })

    // Should not show any document type options
    expect(screen.queryByText(/Arbeitsanweisungen/)).not.toBeInTheDocument()
  })

  it('should show loading state while fetching document types', async () => {
    // Mock a slow API call
    vi.mocked(getDocumentTypes).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve([]), 100))
    )

    renderWithProviders(<FilterPanel />)

    // Should show loading state
    expect(screen.getByText('Lade...')).toBeInTheDocument()

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Lade...')).not.toBeInTheDocument()
    })
  })

  it('should allow selecting document types', async () => {
    const user = userEvent.setup()
    const mockDocumentTypes = [
      {
        id: 1,
        name: 'Arbeitsanweisungen',
        code: 'WORK_INSTRUCTIONS',
        description: 'Standard Arbeitsanweisungen',
        allowed_file_types: ['.pdf'],
        max_file_size_mb: 10,
        requires_ocr: false,
        requires_vision: false,
        default_prompt_template_id: null,
        is_active: true,
        sort_order: 1,
        created_at: '2024-01-01T12:00:00Z',
        updated_at: '2024-01-01T12:00:00Z'
      }
    ]

    vi.mocked(getDocumentTypes).mockResolvedValue(mockDocumentTypes)

    renderWithProviders(<FilterPanel />)

    // Wait for document types to load
    await waitFor(() => {
      expect(screen.getByText('Arbeitsanweisungen (0)')).toBeInTheDocument()
    })

    // Select a document type
    const select = screen.getByDisplayValue('Alle Typen')
    await user.selectOptions(select, '1')

    // Check if the selection is applied
    expect(select).toHaveValue('1')
  })

  it('should clear filters when clear button is clicked', async () => {
    const user = userEvent.setup()
    const mockDocumentTypes = [
      {
        id: 1,
        name: 'Arbeitsanweisungen',
        code: 'WORK_INSTRUCTIONS',
        description: 'Standard Arbeitsanweisungen',
        allowed_file_types: ['.pdf'],
        max_file_size_mb: 10,
        requires_ocr: false,
        requires_vision: false,
        default_prompt_template_id: null,
        is_active: true,
        sort_order: 1,
        created_at: '2024-01-01T12:00:00Z',
        updated_at: '2024-01-01T12:00:00Z'
      }
    ]

    vi.mocked(getDocumentTypes).mockResolvedValue(mockDocumentTypes)

    renderWithProviders(<FilterPanel />)

    // Wait for document types to load
    await waitFor(() => {
      expect(screen.getByText('Arbeitsanweisungen (0)')).toBeInTheDocument()
    })

    // Select a document type
    const select = screen.getByDisplayValue('Alle Typen')
    await user.selectOptions(select, '1')

    // Click clear button
    const clearButton = screen.getByText('Filter zurücksetzen')
    await user.click(clearButton)

    // Check if filters are cleared
    expect(select).toHaveValue('')
  })

  it('should show advanced filters when toggle is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(getDocumentTypes).mockResolvedValue([])

    renderWithProviders(<FilterPanel />)

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Alle Typen')).toBeInTheDocument()
    })

    // Click advanced toggle
    const advancedToggle = screen.getByText('Erweitert')
    await user.click(advancedToggle)

    // Check if advanced filters are shown
    expect(screen.getByText('Seitenzahlen')).toBeInTheDocument()
    expect(screen.getByText(/Mindest-Vertrauen/)).toBeInTheDocument()
  })
})
