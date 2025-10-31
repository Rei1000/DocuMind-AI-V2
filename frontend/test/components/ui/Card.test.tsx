import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Card from '@/components/ui/Card'

describe('Card Component', () => {
  it('should render with white background and shadow', () => {
    render(<Card>Card Content</Card>)
    const card = screen.getByText('Card Content').closest('div')
    
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('shadow-sm')
  })

  it('should apply small padding', () => {
    render(<Card padding="sm">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('p-3')
  })

  it('should apply medium padding (default)', () => {
    render(<Card>Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('p-6')
  })

  it('should apply large padding', () => {
    render(<Card padding="lg">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('p-8')
  })

  it('should apply small shadow', () => {
    render(<Card shadow="sm">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('shadow-sm')
  })

  it('should apply medium shadow (default)', () => {
    render(<Card>Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('shadow-sm')
  })

  it('should apply large shadow', () => {
    render(<Card shadow="md">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('shadow-md')
  })

  it('should have no shadow when shadow="none"', () => {
    render(<Card shadow="none">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).not.toHaveClass('shadow-sm')
    expect(card).not.toHaveClass('shadow-md')
  })

  it('should have rounded corners and border', () => {
    render(<Card>Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('rounded-lg')
    expect(card).toHaveClass('border')
    expect(card).toHaveClass('border-gray-200')
  })

  it('should apply custom className', () => {
    render(<Card className="custom-card">Content</Card>)
    const card = screen.getByText('Content').closest('div')
    
    expect(card).toHaveClass('custom-card')
  })
})

