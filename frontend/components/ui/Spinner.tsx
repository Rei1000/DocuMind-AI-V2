'use client'

import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/**
 * Spinner Component - Zeigt einen animierten Loading-Spinner an.
 * 
 * Verwendet für alle Loading-States in der Anwendung.
 * Minimalistisches Design im Dashboard-Style.
 */
export default function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-6 w-6'
  }

  return (
    <div
      data-testid="spinner"
      className={cn(
        'animate-spin rounded-full border-2 border-gray-300 border-t-gray-600',
        sizeClasses[size],
        className
      )}
      aria-label="Lädt..."
      role="status"
    >
      <span className="sr-only">Lädt...</span>
    </div>
  )
}

