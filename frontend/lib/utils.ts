/**
 * Utility Functions für DocuMind-AI Frontend
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * cn - ClassName Merger (combines clsx + tailwind-merge)
 * 
 * Kombiniert mehrere className-Strings intelligent und löst Tailwind-Konflikte.
 * - clsx: Verarbeitet Conditional Classes
 * - tailwind-merge: Löst Tailwind-Konflikte intelligent (z.B. p-2 + p-4 = p-4)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

