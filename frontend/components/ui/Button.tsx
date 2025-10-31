'use client'

import { ButtonHTMLAttributes, ReactNode } from 'react'
import Spinner from './Spinner'
import { cn } from '@/lib/utils'

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'> {
  variant?: 'primary' | 'secondary' | 'text'
  loading?: boolean
  children: ReactNode
  className?: string
}

/**
 * Button Component - Einheitliche Buttons im Dashboard-Style.
 * 
 * Design-Prinzipien:
 * - KEINE blauen Buttons (nur graue, schlichte Styles)
 * - Loading State mit inline Spinner
 * - Konsistente Hover-Effekte
 * - Disabled State klar erkennbar
 * 
 * Variants:
 * - primary: Grauer Hintergrund (bg-gray-200), für Hauptaktionen
 * - secondary: Text-Button mit Hover, für sekundäre Aktionen
 * - text: Minimal, nur Text, für Links
 */
export default function Button({
  variant = 'primary',
  loading = false,
  disabled,
  children,
  className,
  onClick,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  const variantStyles = {
    primary: 'bg-gray-200 text-gray-700 hover:bg-gray-300 font-medium',
    secondary: 'text-gray-600 hover:text-gray-900 font-medium',
    text: 'text-gray-600 hover:text-gray-900 transition-colors'
  }

  const baseStyles = 'px-4 py-2 rounded-lg transition-all duration-200 flex items-center justify-center gap-2'

  const disabledStyles = isDisabled 
    ? 'opacity-50 cursor-not-allowed' 
    : 'cursor-pointer'

  return (
    <button
      type={props.type || 'button'}
      disabled={isDisabled}
      onClick={isDisabled ? undefined : onClick}
      className={cn(
        baseStyles,
        variantStyles[variant],
        disabledStyles,
        className
      )}
      {...props}
    >
      {loading && (
        <Spinner size="sm" className="mr-0" />
      )}
      {children}
    </button>
  )
}

