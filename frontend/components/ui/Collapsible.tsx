'use client'

import { ReactNode, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface CollapsibleProps {
  title: string
  children: ReactNode
  defaultOpen?: boolean
  className?: string
  icon?: ReactNode
}

/**
 * Collapsible Component für aufklappbare Bereiche
 * 
 * Verwendet für Details, die nicht immer sichtbar sein müssen.
 * Verbessert die UX durch reduzierte visuelle Überladung.
 */
export default function Collapsible({
  title,
  children,
  defaultOpen = false,
  className = '',
  icon
}: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className={`border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between text-left"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2">
          {icon && <span className="text-gray-600">{icon}</span>}
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>
      
      {isOpen && (
        <div className="p-4 bg-white">
          {children}
        </div>
      )}
    </div>
  )
}

