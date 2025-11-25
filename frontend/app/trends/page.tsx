/**
 * Trend Analysis Page
 * 
 * Zeigt Trend-Analyse der Search Quality Metrics über Zeit.
 * Best Practice UX mit interaktiven Charts, Vorher/Nachher Vergleich.
 * 
 * Version: 2.9.0
 */

'use client'

import { useState } from 'react'
import { Calendar, Filter } from 'lucide-react'
import TrendAnalysisPanel from '@/components/TrendAnalysisPanel'

export default function TrendsPage() {
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [documentType, setDocumentType] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)

  // Default: Letzte 7 Tage
  const getDefaultStartDate = () => {
    const date = new Date()
    date.setDate(date.getDate() - 7)
    return date.toISOString().split('T')[0]
  }

  const getDefaultEndDate = () => {
    return new Date().toISOString().split('T')[0]
  }

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center gap-3">
          <Calendar className="w-10 h-10 text-blue-600" />
          Trend-Analyse
          <span className="text-xl font-normal text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
            v2.9.0
          </span>
        </h1>
        <p className="text-gray-600 text-lg">
          Analysiere die Entwicklung der Search Quality Metrics über Zeit
        </p>
      </div>

      {/* Filter */}
      <div className="mb-6 bg-white rounded-lg border border-gray-200 p-4">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
        >
          <Filter className="w-5 h-5" />
          <span className="font-medium">Filter</span>
        </button>

        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start-Datum
              </label>
              <input
                type="date"
                value={startDate || getDefaultStartDate()}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End-Datum
              </label>
              <input
                type="date"
                value={endDate || getDefaultEndDate()}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document Type (optional)
              </label>
              <input
                type="text"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                placeholder="z.B. Fachartikel"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Trend Analysis Panel */}
      <TrendAnalysisPanel
        startDate={startDate || getDefaultStartDate()}
        endDate={endDate || getDefaultEndDate()}
        documentType={documentType || undefined}
      />
    </div>
  )
}

