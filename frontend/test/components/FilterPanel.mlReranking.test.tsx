/**
 * Unit Tests für ML Re-Ranking Toggle in FilterPanel.
 * 
 * TDD: RED - Tests schreiben bevor Code existiert.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FilterPanel from '@/components/FilterPanel'

// Mock DashboardContext
const mockUpdateFilters = vi.fn()
const mockClearFilters = vi.fn()

vi.mock('@/lib/contexts/DashboardContext', () => ({
  useDashboard: () => ({
    searchFilters: {
      useHybridSearch: true,
      useMultiQuery: false,
      useMlRanking: false  // NEU: Learning-to-Rank ML-Ranking (v2.7.0)
    },
    updateFilters: mockUpdateFilters,
    clearFilters: mockClearFilters
  })
}))

describe('FilterPanel ML Re-Ranking Toggle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  it('renders ML Re-Ranking toggle checkbox', () => {
    render(<FilterPanel />)
    
    expect(screen.getByText(/ML Re-Ranking verwenden/i)).toBeInTheDocument()
  })
  
  it('shows ML Re-Ranking as deactivated when false', () => {
    render(<FilterPanel />)
    
    expect(screen.getByText(/ML Re-Ranking verwenden.*DEAKTIVIERT/i)).toBeInTheDocument()
  })
  
  it('calls updateFilter when ML Re-Ranking toggle is clicked', () => {
    render(<FilterPanel />)
    
    const checkbox = screen.getByLabelText(/ML Re-Ranking verwenden/i)
    fireEvent.click(checkbox)
    
    expect(mockUpdateFilters).toHaveBeenCalledWith('useMlRanking', true)
  })
  
  it('displays explanation text for ML Re-Ranking', () => {
    render(<FilterPanel />)
    
    expect(screen.getByText(/Learning-to-Rank/i)).toBeInTheDocument()
    expect(screen.getByText(/bessere Relevanz-Rankings/i)).toBeInTheDocument()
  })
})

