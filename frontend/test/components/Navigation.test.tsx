import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { usePathname } from 'next/navigation'
import Navigation from '@/app/components/Navigation'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/'),
  useRouter: vi.fn(() => ({
    push: vi.fn()
  }))
}))

vi.mock('@/lib/contexts/UserContext', () => ({
  useUser: () => ({
    userLevel: 5,
    canAccess: () => true,
    isLoading: false,
    interestGroupsWithLevels: []
  })
}))

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage })

describe('Unified Navigation (Dashboard Style)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSessionStorage.getItem.mockReturnValue('mock-token')
  })

  it('should render Dashboard-style navigation (white background, no blue buttons)', () => {
    vi.mocked(usePathname).mockReturnValue('/users')
    render(<Navigation />)
    const nav = screen.getByRole('navigation')
    
    expect(nav).toBeInTheDocument()
    expect(nav).toHaveClass('bg-white')
    expect(nav).toHaveClass('border-b')
    expect(nav).toHaveClass('border-gray-200')
    expect(nav).not.toHaveClass('bg-primary')
  })

  it('should render schlichte Links (text-gray-600 hover:text-gray-900)', () => {
    vi.mocked(usePathname).mockReturnValue('/users')
    render(<Navigation />)
    
    const analyticsLink = screen.getByText('Analytics')
    expect(analyticsLink.closest('a')).toHaveClass('text-gray-600')
    expect(analyticsLink.closest('a')).toHaveClass('hover:text-gray-900')
    expect(analyticsLink.closest('a')).not.toHaveClass('bg-primary')
    expect(analyticsLink.closest('a')).not.toHaveClass('text-white')
  })

  it('should highlight active route with darker text (no background)', () => {
    vi.mocked(usePathname).mockReturnValue('/users')
    render(<Navigation />)
    
    const usersLink = screen.getByText('Benutzer')
    const linkElement = usersLink.closest('a')
    
    // Active route should be darker, but NO background color
    expect(linkElement).toHaveClass('text-gray-900')
    expect(linkElement).not.toHaveClass('bg-primary')
    expect(linkElement).not.toHaveClass('text-white')
  })

  it('should show user email and logout button in Dashboard style', () => {
    vi.mocked(usePathname).mockReturnValue('/users')
    localStorage.setItem('user_email', 'test@example.com')
    render(<Navigation />)
    
    const userEmail = screen.queryByText('test@example.com')
    const logoutText = screen.getByText(/abmelden/i)
    const logoutButton = logoutText.closest('button')
    
    // User info should be visible
    expect(userEmail).toBeInTheDocument()
    expect(logoutButton).toBeInTheDocument()
    // Logout button should be schlicht (no blue background)
    expect(logoutButton).toHaveClass('text-gray-600')
    expect(logoutButton).not.toHaveClass('bg-primary')
  })

  it('should NOT show navigation on login page', () => {
    vi.mocked(usePathname).mockReturnValue('/login')
    const { container } = render(<Navigation />)
    
    expect(container.firstChild).toBeNull()
  })

  it('should have logo with title and subtitle', () => {
    vi.mocked(usePathname).mockReturnValue('/users')
    render(<Navigation />)
    
    const logo = screen.getByAltText(/DocuMind-AI/i)
    expect(logo).toBeInTheDocument()
    
    expect(screen.getByText(/DocuMind-AI/i)).toBeInTheDocument()
    expect(screen.getByText(/RAG-Powered QMS/i)).toBeInTheDocument()
  })
})

