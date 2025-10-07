'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Home() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if already logged in
    const token = sessionStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
      setIsLoading(false)
    } else {
      // Not logged in, redirect to login after short delay
      const timer = setTimeout(() => {
        router.push('/login')
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [router])

  // Show loading/redirect screen for non-logged in users
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
        {/* Large Logo */}
        <div className="mb-12 text-center">
          <img 
            src="/logo.png" 
            alt="DocuMind-AI" 
            className="w-full max-w-2xl mx-auto animate-pulse"
            style={{ maxHeight: '70vh' }}
          />
        </div>

        {/* Loading Message */}
        <div className="text-center">
          <p className="text-gray-600 text-lg mb-4">
            Willkommen bei DocuMind-AI
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span>Weiterleitung zur Anmeldung...</span>
          </div>
          <Link 
            href="/login"
            className="mt-6 inline-block px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-primary hover:text-white transition-all duration-300 shadow-sm hover:shadow-md"
          >
            Jetzt anmelden
          </Link>
        </div>

        {/* Footer */}
        <footer className="absolute bottom-6 left-0 right-0">
          <div className="text-center text-sm text-gray-400">
            <p>© {new Date().getFullYear()} DocuMind-AI | Medical Knowledge Management</p>
          </div>
        </footer>
      </div>
    )
  }

  // Dashboard for logged in users
  return (
    <main className="bg-gradient-to-b from-gray-50 to-white min-h-screen">
      <div className="container mx-auto px-6 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Dashboard
          </h1>
          <p className="text-gray-600">
            Willkommen zurück bei DocuMind-AI
          </p>
        </div>

        {/* Quick Access Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link 
            href="/users" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">👥</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Benutzerverwaltung</h2>
            <p className="text-gray-600 text-sm">
              Verwaltung von Rollen & Berechtigungen
            </p>
          </Link>
          
          <Link 
            href="/interest-groups" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🏢</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Interest Groups</h2>
            <p className="text-gray-600 text-sm">
              13 Stakeholder-Gruppen Management
            </p>
          </Link>
          
          <Link 
            href="/models" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🤖</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">AI Models</h2>
            <p className="text-gray-600 text-sm">
              OCR & Vision AI Integration
            </p>
          </Link>
        </div>

        {/* Stats Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">System Status</div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-lg font-semibold text-gray-900">Online</span>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Version</div>
            <span className="text-lg font-semibold text-gray-900">V2.0.0</span>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Architektur</div>
            <span className="text-lg font-semibold text-gray-900">DDD Clean</span>
          </div>
        </div>
      </div>
    </main>
  )
}