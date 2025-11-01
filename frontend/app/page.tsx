'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import RAGChat from '@/components/RAGChat'
import SessionSidebar from '@/components/SessionSidebar'
import FilterPanel from '@/components/FilterPanel'
import { DashboardProvider } from '@/lib/contexts/DashboardContext'
import { UserProvider } from '@/lib/contexts/UserContext'
// Navigation wird jetzt von layout.tsx übernommen (unified Navigation)

function DashboardContent() {
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

  const handleLogout = () => {
    sessionStorage.removeItem('access_token')
    router.push('/login')
  }

  // Show loading/redirect screen for non-logged in users
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50 flex flex-col items-center justify-center px-6">
        {/* Large Logo - Zentriert */}
        <div className="mb-12 text-center flex flex-col items-center justify-center">
          <img 
            src="/logo.png" 
            alt="DocuMind-AI" 
            className="max-w-md w-full mx-auto animate-pulse"
            style={{ maxHeight: '50vh' }}
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
  // Navigation wird jetzt von layout.tsx übernommen (unified Navigation)
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      {/* Main Dashboard */}
      <main className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            RAG Chat Dashboard
          </h1>
          <p className="text-gray-600">
            Stellen Sie Fragen zu Ihren indexierten Dokumenten und erhalten Sie intelligente Antworten
          </p>
        </div>

        {/* Main Content Grid - Flexible Layout mit schmaler Session Sidebar */}
        <div className="flex gap-6 h-[calc(100vh-200px)]">
          {/* LEFT: Filter Panel - AI Playground Style */}
          <div className="w-[320px] flex-shrink-0">
            <FilterPanel />
          </div>

          {/* MIDDLE: RAG Chat - flex-grow für restlichen Platz */}
          <div className="flex-1 min-w-0">
            <RAGChat />
          </div>

          {/* RIGHT: Session Sidebar - schmaler (halb so breit) */}
          <div className="w-[160px] flex-shrink-0">
            <SessionSidebar />
          </div>
        </div>
      </main>
    </div>
  )
}

export default function Home() {
  return (
    <UserProvider>
      <DashboardProvider>
        <DashboardContent />
      </DashboardProvider>
    </UserProvider>
  )
}