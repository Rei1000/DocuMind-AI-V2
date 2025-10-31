'use client'

import { useState, useEffect } from 'react'
import { Search, Filter, X, FileText, Calendar, Tag } from 'lucide-react'
import { useDashboard, SearchFilters } from '@/lib/contexts/DashboardContext'
import { getDocumentTypes, DocumentType } from '@/lib/api/documentTypes'
import { apiClient } from '@/lib/api/rag'

interface DocumentTypeWithCount extends DocumentType {
  count: number
}

interface FilterPanelProps {
  className?: string
}

export default function FilterPanel({ 
  className = ''
}: FilterPanelProps) {
  const { searchFilters, updateFilters, clearFilters } = useDashboard()
  
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeWithCount[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    loadDocumentTypes()
  }, [])

  const loadDocumentTypes = async () => {
    try {
      setIsLoading(true)
      
      // Lade Document Types von der API
      const types = await getDocumentTypes(true) // active_only = true
      
      // Hole Dokument-Anzahl für jeden Typ von der RAG API
      try {
        const typeIds = types.map(type => type.id)
        const countsResponse = await apiClient.getDocumentTypeCounts(typeIds)
        
        const counts = countsResponse.data || {}
        
        const typesWithCount: DocumentTypeWithCount[] = types.map(type => ({
          ...type,
          count: counts[type.id] || 0  // Verwende Count aus API oder 0 als Fallback
        }))
        
        setDocumentTypes(typesWithCount)
      } catch (countError) {
        console.warn('Fehler beim Laden der Document Type Counts:', countError)
        // Fallback: Setze count auf 0 wenn API-Call fehlschlägt
        const typesWithCount: DocumentTypeWithCount[] = types.map(type => ({
          ...type,
          count: 0
        }))
        setDocumentTypes(typesWithCount)
      }
    } catch (error) {
      console.error('Fehler beim Laden der Dokumenttypen:', error)
      // Fallback: Leere Liste bei Fehler
      setDocumentTypes([])
    } finally {
      setIsLoading(false)
    }
  }

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    updateFilters({ [key]: value })
  }

  const updateDateRange = (key: 'from' | 'to', value: string) => {
    updateFilters({
      dateRange: {
        ...searchFilters.dateRange,
        [key]: value
      }
    })
  }

  const addPageNumber = (page: number) => {
    if (!searchFilters.pageNumbers.includes(page)) {
      updateFilters({
        pageNumbers: [...searchFilters.pageNumbers, page]
      })
    }
  }

  const removePageNumber = (page: number) => {
    updateFilters({
      pageNumbers: searchFilters.pageNumbers.filter(p => p !== page)
    })
  }

  const hasActiveFilters = () => {
    return (
      searchFilters.query !== '' ||
      searchFilters.documentType !== '' ||
      searchFilters.dateRange.from !== '' ||
      searchFilters.dateRange.to !== '' ||
      searchFilters.pageNumbers.length > 0 ||
      searchFilters.minConfidence !== 0.01 ||
      !searchFilters.useHybridSearch
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
          <div className="flex items-center gap-2 mb-1">
            <Search className="text-gray-400 w-4 h-4" />
            <label className="block text-sm font-medium text-gray-700">
              Schnellsuche (Optional)
            </label>
            <div className="group relative">
              <span className="text-xs text-gray-400 cursor-help">ⓘ</span>
              <div className="hidden group-hover:block absolute z-10 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg -top-2 left-6">
                Geben Sie einen Suchbegriff ein, der als zusätzlicher Kontext zu Ihrer Frage verwendet wird. 
                Beispiel: "Sicherheitshinweise" → Alle Fragen werden dann im Kontext von Sicherheitshinweisen beantwortet.
              </div>
            </div>
          </div>
          <input
            type="text"
            value={searchFilters.query}
            onChange={(e) => updateFilter('query', e.target.value)}
            placeholder="z.B. 'Sicherheitshinweise'..."
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
              value={searchFilters.documentType}
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
              value={searchFilters.dateRange.from}
              onChange={(e) => updateDateRange('from', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="date"
              value={searchFilters.dateRange.to}
              onChange={(e) => updateDateRange('to', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <>
            {/* Confidence Threshold Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-xs text-blue-700">
                <strong>Score Threshold:</strong> Filtert Suchergebnisse nach Ähnlichkeits-Score (Vector-Similarity).
                <br />
                <strong>Werte:</strong> 0.000 (alle Chunks) bis 0.020 (nur sehr relevante).
                <br />
                <strong>OpenAI Embeddings:</strong> Typische Scores liegen bei 0.02-0.03. Höhere Threshold = strengerer Filter = weniger, aber relevantere Ergebnisse.
                <br />
                <strong>Standard:</strong> 0.01 (empfohlen für OpenAI Embeddings)
              </p>
            </div>

            {/* Hybrid Search Info */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
              <p className="text-xs text-green-700">
                <strong>Hybrid Search:</strong> Kombiniert semantische Vektor-Suche (Bedeutung) 
                mit Text-basierter Suche (exakte Begriffe) für bessere Ergebnisse.
              </p>
            </div>

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
                {searchFilters.pageNumbers.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {searchFilters.pageNumbers.map((page) => (
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
                Score Threshold: {searchFilters.minConfidence.toFixed(3)}
              </label>
              <input
                type="range"
                min="0"
                max="0.02"
                step="0.001"
                value={searchFilters.minConfidence}
                onChange={(e) => updateFilter('minConfidence', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.000 (alle Ergebnisse)</span>
                <span>0.020 (nur sehr relevante)</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Aktuell: {searchFilters.minConfidence.toFixed(3)} (nur Chunks mit Score ≥ {searchFilters.minConfidence.toFixed(3)})
              </div>
            </div>

            {/* Search Options */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={searchFilters.useHybridSearch}
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
              searchFilters.query && 'Suche',
              searchFilters.documentType && 'Typ',
              (searchFilters.dateRange.from || searchFilters.dateRange.to) && 'Datum',
              searchFilters.pageNumbers.length > 0 && 'Seiten',
              searchFilters.minConfidence !== 0.01 && 'Threshold',
              !searchFilters.useHybridSearch && 'Search-Modus'
            ].filter(Boolean).length}
          </div>
        )}
      </div>
    </div>
  )
}
