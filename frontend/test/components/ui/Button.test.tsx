import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'

// Mock Spinner Component
vi.mock('@/components/ui/Spinner', () => ({
  default: ({ className }: { className?: string }) => (
    <div data-testid="spinner" className={className}>Loading...</div>
  )
}))

describe('Button Component', () => {
  it('should render primary button with gray background (not blue)', () => {
    render(<Button variant="primary">Click me</Button>)
    const button = screen.getByRole('button', { name: /click me/i })
    
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('bg-gray-200')
    expect(button).toHaveClass('text-gray-700')
    expect(button).not.toHaveClass('bg-primary')
    expect(button).not.toHaveClass('bg-blue-600')
  })

  it('should render secondary button with text style', () => {
    render(<Button variant="secondary">Cancel</Button>)
    const button = screen.getByRole('button', { name: /cancel/i })
    
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('text-gray-600')
  })

  it('should render text button variant', () => {
    render(<Button variant="text">Link Button</Button>)
    const button = screen.getByRole('button', { name: /link button/i })
    
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('text-gray-600')
    expect(button).toHaveClass('hover:text-gray-900')
  })

  it('should show spinner when loading=true', () => {
    render(<Button variant="primary" loading>Submit</Button>)
    const button = screen.getByRole('button')
    const spinner = screen.getByTestId('spinner')
    
    expect(button).toBeInTheDocument()
    expect(spinner).toBeInTheDocument()
    expect(button).toHaveTextContent('Submit')
    // Spinner should be inline with text, not replace it
  })

  it('should be disabled when disabled=true', () => {
    render(<Button variant="primary" disabled>Disabled</Button>)
    const button = screen.getByRole('button', { name: /disabled/i })
    
    expect(button).toBeDisabled()
    expect(button).toHaveClass('cursor-not-allowed')
  })

  it('should be disabled when loading=true', () => {
    render(<Button variant="primary" loading>Loading</Button>)
    const button = screen.getByRole('button', { name: /loading/i })
    
    expect(button).toBeDisabled()
  })

  it('should call onClick handler when clicked', async () => {
    const handleClick = vi.fn()
    render(<Button variant="primary" onClick={handleClick}>Click</Button>)
    
    const button = screen.getByRole('button', { name: /click/i })
    await userEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should NOT call onClick when disabled', async () => {
    const handleClick = vi.fn()
    render(<Button variant="primary" disabled onClick={handleClick}>Disabled</Button>)
    
    const button = screen.getByRole('button', { name: /disabled/i })
    await userEvent.click(button)
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('should apply correct hover styles for primary variant', () => {
    render(<Button variant="primary">Hover Test</Button>)
    const button = screen.getByRole('button', { name: /hover test/i })
    
    expect(button).toHaveClass('hover:bg-gray-300')
  })

  it('should apply custom className', () => {
    render(<Button variant="primary" className="custom-class">Test</Button>)
    const button = screen.getByRole('button', { name: /test/i })
    
    expect(button).toHaveClass('custom-class')
  })

  it('should support type attribute', () => {
    render(<Button variant="primary" type="submit">Submit</Button>)
    const button = screen.getByRole('button', { name: /submit/i })
    
    expect(button).toHaveAttribute('type', 'submit')
  })
})

