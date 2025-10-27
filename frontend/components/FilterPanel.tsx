'use client'

import { useState, useEffect } from 'react'
import { Search, Filter, X, FileText, Calendar, Tag, Users } from 'lucide-react'

interface DocumentType {
  id: string
  name: string
  count: number
}

interface FilterPanelProps {
  className?: string
  onFiltersChange?: (filters: SearchFilters) => void
}

interface SearchFilters {
  query: string
  documentType: string
  dateRange: {
    from: string
    to: string
  }
  pageNumbers: number[]
  minConfidence: number
  useHybridSearch: boolean
}

export default function FilterPanel({ 
  className = '', 
  onFiltersChange 
}: FilterPanelProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    documentType: '',
    dateRange: {
      from: '',
      to: ''
    },
    pageNumbers: [],
    minConfidence: 0.7,
    useHybridSearch: true
  })
  
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    loadDocumentTypes()
  }, [])

  useEffect(() => {
    onFiltersChange?.(filters)
  }, [filters, onFiltersChange])

  const loadDocumentTypes = async () => {
    try {
      setIsLoading(true)
      // TODO: Implementiere echten API Call
      const response = await fetch('/api/rag/documents', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })

      if (response.ok) {
        const documents = await response.json()
        // Gruppiere nach Dokumenttyp
        const typeMap = new Map<string, number>()
        documents.forEach((doc: any) => {
          const count = typeMap.get(doc.document_type) || 0
          typeMap.set(doc.document_type, count + 1)
        })
        
        const types = Array.from(typeMap.entries()).map(([name, count]) => ({
          id: name,
          name,
          count
        }))
        
        setDocumentTypes(types)
      } else {
        // Fallback: Mock data
        setDocumentTypes([
          { id: 'work_instructions', name: 'Arbeitsanweisungen', count: 15 },
          { id: 'safety_instructions', name: 'Sicherheitshinweise', count: 8 },
          { id: 'maintenance_guides', name: 'Wartungsanleitungen', count: 12 },
          { id: 'installation_guides', name: 'Installationsanleitungen', count: 6 }
        ])
      }
    } catch (error) {
      console.error('Fehler beim Laden der Dokumenttypen:', error)
      setDocumentTypes([])
    } finally {
      setIsLoading(false)
    }
  }

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const updateDateRange = (key: 'from' | 'to', value: string) => {
    setFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        [key]: value
      }
    }))
  }

  const addPageNumber = (page: number) => {
    if (!filters.pageNumbers.includes(page)) {
      setFilters(prev => ({
        ...prev,
        pageNumbers: [...prev.pageNumbers, page]
      }))
    }
  }

  const removePageNumber = (page: number) => {
    setFilters(prev => ({
      ...prev,
      pageNumbers: prev.pageNumbers.filter(p => p !== page)
    }))
  }

  const clearFilters = () => {
    setFilters({
      query: '',
      documentType: '',
      dateRange: {
        from: '',
        to: ''
      },
      pageNumbers: [],
      minConfidence: 0.7,
      useHybridSearch: true
    })
  }

  const hasActiveFilters = () => {
    return (
      filters.query !== '' ||
      filters.documentType !== '' ||
      filters.dateRange.from !== '' ||
      filters.dateRange.to !== '' ||
      filters.pageNumbers.length > 0 ||
      filters.minConfidence !== 0.7 ||
      !filters.useHybridSearch
    )
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900">Filter & Suche</h2>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <Filter className="w-4 h-4" />
          </button>
        </div>
        
        {/* Quick Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={filters.query}
            onChange={(e) => updateFilter('query', e.target.value)}
            placeholder="Schnellsuche..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Document Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <FileText className="w-4 h-4 inline mr-1" />
            Dokumenttyp
          </label>
          {isLoading ? (
            <div className="text-sm text-gray-500">Lade...</div>
          ) : (
            <select
              value={filters.documentType}
              onChange={(e) => updateFilter('documentType', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Alle Typen</option>
              {documentTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name} ({type.count})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Date Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Calendar className="w-4 h-4 inline mr-1" />
            Datumsbereich
          </label>
          <div className="space-y-2">
            <input
              type="date"
              value={filters.dateRange.from}
              onChange={(e) => updateDateRange('from', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="date"
              value={filters.dateRange.to}
              onChange={(e) => updateDateRange('to', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <>
            {/* Page Numbers Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Tag className="w-4 h-4 inline mr-1" />
                Seitenzahlen
              </label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="1"
                    placeholder="Seite hinzufügen..."
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const page = parseInt((e.target as HTMLInputElement).value)
                        if (page > 0) {
                          addPageNumber(page)
                          ;(e.target as HTMLInputElement).value = ''
                        }
                      }
                    }}
                  />
                </div>
                {filters.pageNumbers.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {filters.pageNumbers.map((page) => (
                      <span
                        key={page}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                      >
                        Seite {page}
                        <button
                          onClick={() => removePageNumber(page)}
                          className="hover:text-blue-600"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Confidence Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mindest-Vertrauen: {Math.round(filters.minConfidence * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.minConfidence}
                onChange={(e) => updateFilter('minConfidence', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Search Options */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={filters.useHybridSearch}
                  onChange={(e) => updateFilter('useHybridSearch', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Hybrid Search verwenden
              </label>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <button
            onClick={clearFilters}
            disabled={!hasActiveFilters()}
            className="flex-1 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Filter zurücksetzen
          </button>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {showAdvanced ? 'Einfach' : 'Erweitert'}
          </button>
        </div>
        
        {hasActiveFilters() && (
          <div className="mt-2 text-xs text-gray-500 text-center">
            Aktive Filter: {[
              filters.query && 'Suche',
              filters.documentType && 'Typ',
              (filters.dateRange.from || filters.dateRange.to) && 'Datum',
              filters.pageNumbers.length > 0 && 'Seiten',
              filters.minConfidence !== 0.7 && 'Vertrauen',
              !filters.useHybridSearch && 'Search-Modus'
            ].filter(Boolean).length}
          </div>
        )}
      </div>
    </div>
  )
}
