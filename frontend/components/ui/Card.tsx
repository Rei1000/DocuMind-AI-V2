'use client'

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: ReactNode
  padding?: 'sm' | 'md' | 'lg'
  shadow?: 'sm' | 'md' | 'none'
  className?: string
}

/**
 * Card Component - Container für Inhalte mit einheitlichem Design.
 * 
 * Verwendet auf allen Seiten für konsistentes Layout.
 * Dashboard-Style: Weißer Hintergrund, sanfter Shadow, Border.
 */
export default function Card({ 
  children, 
  padding = 'md', 
  shadow = 'sm',
  className 
}: CardProps) {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8'
  }

  const shadowClasses = {
    sm: 'shadow-sm',
    md: 'shadow-md',
    none: ''
  }

  return (
    <div
      className={cn(
        'bg-white rounded-lg border border-gray-200',
        paddingClasses[padding],
        shadowClasses[shadow],
        className
      )}
    >
      {children}
    </div>
  )
}

