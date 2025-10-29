'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import RAGChat from '@/components/RAGChat'
import SessionSidebar from '@/components/SessionSidebar'
import FilterPanel from '@/components/FilterPanel'
import { DashboardProvider } from '@/lib/contexts/DashboardContext'
import { UserProvider } from '@/lib/contexts/UserContext'
import { Settings, Users, FileText, BarChart3, LogOut } from 'lucide-react'

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo & Title */}
            <div className="flex items-center gap-4">
              <img 
                src="/logo.png" 
                alt="DocuMind-AI" 
                className="h-8 w-auto"
              />
              <div>
                <h1 className="text-xl font-bold text-gray-900">DocuMind-AI</h1>
                <p className="text-xs text-gray-500">RAG-Powered QMS</p>
              </div>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center gap-6">
              <Link 
                href="/users" 
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <Users className="w-4 h-4" />
                <span className="text-sm font-medium">Benutzer</span>
              </Link>
              
              <Link 
                href="/document-upload" 
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span className="text-sm font-medium">Dokumente</span>
              </Link>
              
              <Link 
                href="/models" 
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm font-medium">AI Models</span>
              </Link>
              
              <Link 
                href="/prompt-management" 
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span className="text-sm font-medium">Prompts</span>
              </Link>
            </div>

            {/* User Actions */}
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">Admin</span>
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
            </div>
          </div>
        </div>
      </nav>

      {/* Main Dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Section */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-1">
            RAG Chat Dashboard
          </h2>
          <p className="text-gray-600">
            Stellen Sie Fragen zu Ihren indexierten Dokumenten und erhalten Sie intelligente Antworten
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)]">
          {/* Session Sidebar - 15% */}
          <div className="col-span-2">
            <SessionSidebar />
          </div>

          {/* RAG Chat - 70% */}
          <div className="col-span-8">
            <RAGChat />
          </div>

          {/* Filter Panel - 15% */}
          <div className="col-span-2">
            <FilterPanel />
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