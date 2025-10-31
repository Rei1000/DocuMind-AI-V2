import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import Spinner from '@/components/ui/Spinner'

describe('Spinner Component', () => {
  it('should render with default size (md)', () => {
    const { container } = render(<Spinner />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('h-4')
    expect(spinner).toHaveClass('w-4')
  })

  it('should render with small size', () => {
    const { container } = render(<Spinner size="sm" />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toHaveClass('h-3')
    expect(spinner).toHaveClass('w-3')
  })

  it('should render with medium size', () => {
    const { container } = render(<Spinner size="md" />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toHaveClass('h-4')
    expect(spinner).toHaveClass('w-4')
  })

  it('should render with large size', () => {
    const { container } = render(<Spinner size="lg" />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toHaveClass('h-6')
    expect(spinner).toHaveClass('w-6')
  })

  it('should apply custom className', () => {
    const { container } = render(<Spinner className="custom-spinner" />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toHaveClass('custom-spinner')
  })

  it('should have animation classes', () => {
    const { container } = render(<Spinner />)
    const spinner = container.querySelector('[data-testid="spinner"]')
    
    expect(spinner).toHaveClass('animate-spin')
    expect(spinner).toHaveClass('rounded-full')
  })
})

