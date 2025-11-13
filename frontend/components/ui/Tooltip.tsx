'use client'

import { ReactNode, useState, useRef, useEffect } from 'react'
import { Info } from 'lucide-react'

interface TooltipProps {
  content: ReactNode
  children?: ReactNode
  icon?: boolean
  className?: string
}

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right'

/**
 * Tooltip Component
 * 
 * Zeigt zusätzliche Informationen bei Hover/Klick.
 * Kann mit oder ohne Icon verwendet werden.
 * Automatische Positionierung basierend auf verfügbarem Platz.
 */
export default function Tooltip({ 
  content, 
  children, 
  icon = false,
  className = '' 
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState<TooltipPosition>('bottom')
  const tooltipRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const calculatePosition = () => {
        if (!tooltipRef.current || !triggerRef.current) return
        
        const triggerRect = triggerRef.current.getBoundingClientRect()
        const tooltipRect = tooltipRef.current.getBoundingClientRect()
        const viewportWidth = window.innerWidth
        const viewportHeight = window.innerHeight
        
        const spaceBelow = viewportHeight - triggerRect.bottom
        const spaceAbove = triggerRect.top
        const spaceRight = viewportWidth - triggerRect.left
        const spaceLeft = triggerRect.right
        
        // Verwende tatsächliche Tooltip-Dimensionen, falls verfügbar
        const tooltipWidth = tooltipRect.width || 320 // w-80 = 320px
        const tooltipHeight = tooltipRect.height || 200 // Schätzwert für ersten Render
        
        // Prüfe verfügbaren Platz in jeder Richtung (mit Padding)
        const padding = 10
        const canFitBelow = spaceBelow >= tooltipHeight + padding
        const canFitAbove = spaceAbove >= tooltipHeight + padding
        const canFitRight = spaceRight >= tooltipWidth + padding
        const canFitLeft = spaceLeft >= tooltipWidth + padding
        
        // Priorität: bottom > top > right > left
        if (canFitBelow) {
          setPosition('bottom')
        } else if (canFitAbove) {
          setPosition('top')
        } else if (canFitRight) {
          setPosition('right')
        } else if (canFitLeft) {
          setPosition('left')
        } else {
          // Fallback: Wähle Position mit dem meisten Platz
          const spaces = [
            { pos: 'bottom' as TooltipPosition, space: spaceBelow },
            { pos: 'top' as TooltipPosition, space: spaceAbove },
            { pos: 'right' as TooltipPosition, space: spaceRight },
            { pos: 'left' as TooltipPosition, space: spaceLeft }
          ]
          const bestPosition = spaces.reduce((best, current) => 
            current.space > best.space ? current : best
          )
          setPosition(bestPosition.pos)
        }
      }
      
      // Kurze Verzögerung, damit Tooltip gerendert wird und Dimensionen verfügbar sind
      const timeoutId = setTimeout(calculatePosition, 10)
      
      // Recalculate on scroll/resize
      window.addEventListener('scroll', calculatePosition, true)
      window.addEventListener('resize', calculatePosition)
      
      return () => {
        clearTimeout(timeoutId)
        window.removeEventListener('scroll', calculatePosition, true)
        window.removeEventListener('resize', calculatePosition)
      }
    }
  }, [isVisible])

  const getPositionClasses = (pos: TooltipPosition) => {
    switch (pos) {
      case 'top':
        return 'bottom-full left-1/2 -translate-x-1/2 mb-2'
      case 'bottom':
        return 'top-full left-1/2 -translate-x-1/2 mt-2'
      case 'left':
        return 'right-full top-1/2 -translate-y-1/2 mr-2'
      case 'right':
        return 'left-full top-1/2 -translate-y-1/2 ml-2'
      default:
        return 'top-full left-1/2 -translate-x-1/2 mt-2'
    }
  }

  const getArrowClasses = (pos: TooltipPosition) => {
    switch (pos) {
      case 'top':
        return 'absolute top-full left-1/2 -translate-x-1/2 -mt-1 w-2 h-2 bg-gray-900 transform rotate-45'
      case 'bottom':
        return 'absolute bottom-full left-1/2 -translate-x-1/2 -mb-1 w-2 h-2 bg-gray-900 transform rotate-45'
      case 'left':
        return 'absolute left-full top-1/2 -translate-y-1/2 -ml-1 w-2 h-2 bg-gray-900 transform rotate-45'
      case 'right':
        return 'absolute right-full top-1/2 -translate-y-1/2 -mr-1 w-2 h-2 bg-gray-900 transform rotate-45'
      default:
        return 'absolute bottom-full left-1/2 -translate-x-1/2 -mb-1 w-2 h-2 bg-gray-900 transform rotate-45'
    }
  }

  return (
    <div 
      ref={triggerRef}
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {icon ? (
        <button
          type="button"
          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Informationen anzeigen"
        >
          <Info className="w-3 h-3" />
        </button>
      ) : (
        children
      )}
      
      {isVisible && (
        <div 
          ref={tooltipRef}
          className={`absolute z-50 w-80 p-4 bg-gray-900 text-white text-sm rounded-lg shadow-xl ${getPositionClasses(position)}`}
        >
          <div className="space-y-2">
            {content}
          </div>
          {/* Arrow */}
          <div className={getArrowClasses(position)} />
        </div>
      )}
    </div>
  )
}

