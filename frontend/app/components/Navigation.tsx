'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Users, FileText, BarChart3, Settings, LogOut } from 'lucide-react'

/**
 * Unified Navigation Component - Dashboard-Style
 * 
 * Elegantes, minimales Design wie auf der Dashboard-Seite:
 * - Weißer Hintergrund, sanfter Border
 * - Schlichte Links (text-gray-600 hover:text-gray-900)
 * - KEINE blauen Buttons
 * - Aktive Route: Dunklerer Text (text-gray-900), kein Hintergrund
 */
export default function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userEmail, setUserEmail] = useState('')

  useEffect(() => {
    // Check if user is logged in
    const token = sessionStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
      const email = localStorage.getItem('user_email')
      if (email) setUserEmail(email)
    }
  }, [pathname])

  const handleLogout = () => {
    sessionStorage.removeItem('access_token')
    localStorage.removeItem('user_email')
    setIsLoggedIn(false)
    router.push('/login')
  }

  // Don't show navigation on login page
  if (pathname === '/login') {
    return null
  }
  
  // Don't show on homepage if not logged in
  if (pathname === '/' && !isLoggedIn) {
    return null
  }

  // Navigation Links - Dashboard-Style (schlicht, ohne Icons im Link selbst)
  const navLinks = [
    { href: '/users', label: 'Benutzer', icon: Users },
    { href: '/document-upload', label: 'Dokument Upload', icon: FileText },
    { href: '/documents', label: 'Dokumente', icon: FileText },
    { href: '/prompt-management', label: 'Prompt-Verwaltung', icon: Settings },
    { href: '/models', label: 'AI Models', icon: BarChart3 },
  ]

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Title - Dashboard Style */}
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-4 hover:opacity-90 transition-opacity">
              <img 
                src="/logo.png" 
                alt="DocuMind-AI" 
                className="h-8 w-auto"
              />
              <div>
                <h1 className="text-xl font-bold text-gray-900">DocuMind-AI</h1>
                <p className="text-xs text-gray-500">RAG-Powered QMS</p>
              </div>
            </Link>
          </div>

          {/* Navigation Links - Dashboard Style (schlicht, ohne blauen Hintergrund) */}
          <div className="flex items-center gap-6">
            {navLinks.map((link) => {
              const IconComponent = link.icon
              const isActive = pathname === link.href || 
                (link.href === '/documents' && pathname?.startsWith('/documents'))
              
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`
                    flex items-center gap-2 transition-colors
                    ${isActive 
                      ? 'text-gray-900'  // Aktive Route: Dunkler Text, KEIN Hintergrund
                      : 'text-gray-600 hover:text-gray-900'  // Normale Links: Schlicht
                    }
                  `}
                >
                  <IconComponent className="w-4 h-4" />
                  <span className="text-sm font-medium">{link.label}</span>
                </Link>
              )
            })}
          </div>

          {/* User Actions - Dashboard Style */}
          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{userEmail || 'Admin'}</span>
                  <span className="text-gray-400 ml-1">•</span>
                  <span className="ml-1">Online</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 text-gray-600 hover:text-red-600 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm">Abmelden</span>
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span className="text-sm font-medium">Anmelden</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
