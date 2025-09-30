'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userEmail, setUserEmail] = useState('')

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
      // You could fetch user info here if needed
      const email = localStorage.getItem('user_email')
      if (email) setUserEmail(email)
    }
  }, [pathname])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_email')
    setIsLoggedIn(false)
    router.push('/login')
  }

  // Don't show navigation on login page
  if (pathname === '/login') {
    return null
  }

  const navLinks = [
    { href: '/', label: 'Dashboard', icon: '🏠' },
    { href: '/users', label: 'Benutzer', icon: '👥' },
    { href: '/interest-groups', label: 'Interest Groups', icon: '🏢' },
    { href: '/models', label: 'AI Models', icon: '🤖' },
  ]

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
            <img 
              src="/logo.png" 
              alt="DocuMind-AI Logo" 
              className="h-10 w-auto"
            />
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  pathname === link.href
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{link.icon}</span>
                {link.label}
              </Link>
            ))}
          </div>

          {/* User Actions */}
          <div className="flex items-center gap-4">
            {isLoggedIn ? (
              <>
                {userEmail && (
                  <div className="hidden sm:block text-sm font-medium text-gray-600">
                    {userEmail}
                  </div>
                )}
                <button
                  onClick={handleLogout}
                  className="px-5 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="px-5 py-2.5 text-sm font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 shadow-sm hover:shadow transition-all"
              >
                Login
              </Link>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden flex gap-1 overflow-x-auto pb-2 -mx-4 px-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`flex-shrink-0 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pathname === link.href
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`}
            >
              <span className="mr-1.5">{link.icon}</span>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
