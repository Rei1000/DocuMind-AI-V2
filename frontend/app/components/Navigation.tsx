'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Users, FileText, BarChart3, Settings, LogOut, Archive } from 'lucide-react'
import { useUser } from '@/lib/contexts/UserContext'

/**
 * Unified Navigation Component - Dashboard-Style
 * 
 * Elegantes, minimales Design wie auf der Dashboard-Seite:
 * - Weißer Hintergrund, sanfter Border
 * - Schlichte Links (text-gray-600 hover:text-gray-900)
 * - KEINE blauen Buttons
 * - Aktive Route: Dunklerer Text (text-gray-900), kein Hintergrund
 * - RBAC Phase 5: Links werden basierend auf User-Level gefiltert
 */
export default function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const { userLevel, canAccess, isLoading, interestGroupsWithLevels } = useUser()
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
  // RBAC Phase 5: Links werden basierend auf User-Level gefiltert
  const allNavLinks = [
    { href: '/analytics', label: 'Analytics', icon: BarChart3, requiredLevel: 1, feature: 'analytics' },
    { href: '/users', label: 'Benutzer', icon: Users, requiredLevel: 5, feature: 'users' },
    { href: '/document-upload', label: 'Dokument Upload', icon: FileText, requiredLevel: 4, feature: 'upload' },
    { href: '/documents', label: 'Dokumente', icon: FileText, requiredLevel: 2, feature: 'documents-list' },
    { href: '/documents/archive', label: 'Archiv', icon: Archive, requiredLevel: 4, feature: 'documents-list' }, // NEU: Archiv (Level 4+)
    { href: '/prompt-management', label: 'Prompt-Verwaltung', icon: Settings, requiredLevel: 5, feature: 'prompt-management' },
    { href: '/models', label: 'AI Models', icon: BarChart3, requiredLevel: 5, feature: 'ai-models' },
  ]

  // Filtere Links basierend auf User-Level (nur wenn nicht loading)
  const navLinks = isLoading 
    ? [] // Während Loading: Keine Links anzeigen
    : allNavLinks.filter(link => {
        // Verwende canAccess() für Feature-basierte Prüfung (besser als requiredLevel)
        return canAccess(link.feature)
      })

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
                (link.href === '/documents' && pathname?.startsWith('/documents') && !pathname?.startsWith('/documents/archive')) ||
                (link.href === '/documents/archive' && pathname?.startsWith('/documents/archive'))
              
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
                  {/* RBAC Phase 5: Level Badge */}
                  {/* RBAC Multi-Level: Level mit IG + Levels */}
                  {!isLoading && userLevel > 0 && (
                    <>
                      {interestGroupsWithLevels.length > 0 ? (
                        <span 
                          className="ml-1 text-gray-500"
                          title={`Interest Groups: ${interestGroupsWithLevels
                            .sort((a, b) => b.level - a.level)
                            .map(ig => `${ig.name} (Level ${ig.level})`)
                            .join(', ')}`}
                        >
                          Level {userLevel} ({interestGroupsWithLevels
                            .sort((a, b) => b.level - a.level) // Höchstes Level zuerst
                            .map(ig => `${ig.name}: ${ig.level}`)
                            .join(', ')})
                        </span>
                      ) : (
                        <span className="ml-1 text-gray-500">Level {userLevel}</span>
                      )}
                      <span className="text-gray-400 ml-1">•</span>
                    </>
                  )}
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
