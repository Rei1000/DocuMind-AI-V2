'use client'

import { useState, useEffect } from 'react'
import { Search, Filter, X, FileText, Calendar, Tag } from 'lucide-react'
import { useDashboard, SearchFilters } from '@/lib/contexts/DashboardContext'
import { getDocumentTypes, DocumentType } from '@/lib/api/documentTypes'
import { apiClient } from '@/lib/api/rag'
import { useUser } from '@/lib/contexts/UserContext'
import RAGChatPromptEditor from '@/components/RAGChatPromptEditor'

interface DocumentTypeWithCount extends DocumentType {
  count: number
}

interface FilterPanelProps {
  className?: string
}

export default function FilterPanel({ 
  className = ''
}: FilterPanelProps) {
  const { searchFilters, updateFilters, clearFilters, currentMessages } = useDashboard()
  const { userLevel, isLoading: userContextLoading } = useUser()
  
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeWithCount[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [lastUsedPromptInfo, setLastUsedPromptInfo] = useState<{
    documentType: string | null
    documentTypeEffective: string | null
    timestamp: number
  } | null>(null)

  useEffect(() => {
    // Warte auf UserContext bevor wir laden
    if (!userContextLoading) {
      loadDocumentTypes()
    }
  }, [userContextLoading, userLevel])

  // NEU: Überwache letzte Assistant-Message für Prompt-Info
  useEffect(() => {
    if (currentMessages && currentMessages.length > 0) {
      // Finde letzte Assistant-Message
      const lastAssistantMessage = [...currentMessages]
        .reverse()
        .find(msg => msg.role === 'assistant' && msg.metadata)
      
      if (lastAssistantMessage && lastAssistantMessage.metadata) {
        const metadata = lastAssistantMessage.metadata
        const documentTypeEffective = metadata.document_type_effective
        const documentTypeSelected = metadata.document_type_selected
        
        // Nur aktualisieren wenn sich etwas geändert hat
        if (documentTypeEffective || documentTypeSelected) {
          setLastUsedPromptInfo({
            documentType: documentTypeSelected || null,
            documentTypeEffective: documentTypeEffective || null,
            timestamp: Date.now()
          })
          
          // Auto-Hide nach 10 Sekunden
          setTimeout(() => {
            setLastUsedPromptInfo(null)
          }, 10000)
        }
      }
    }
  }, [currentMessages])

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
        
        // RBAC Multi-Level: Filtere DocumentTypes basierend auf User-Level
        // Level 4-5: Alle DocumentTypes anzeigen
        // Level 1-3: Nur DocumentTypes mit count > 0 (bereits durch RBAC gefiltert)
        const filteredTypes = userLevel >= 4
          ? typesWithCount  // Level 4-5: Alle anzeigen
          : typesWithCount.filter(type => type.count > 0)  // Level 1-3: Nur mit Dokumenten
        
        setDocumentTypes(filteredTypes)
      } catch (countError) {
        console.warn('Fehler beim Laden der Document Type Counts:', countError)
        // Fallback: Bei Fehler für Level 1-3 leere Liste, für Level 4-5 alle Typen
        if (userLevel >= 4) {
          const typesWithCount: DocumentTypeWithCount[] = types.map(type => ({
            ...type,
            count: 0
          }))
          setDocumentTypes(typesWithCount)
        } else {
          // Level 1-3: Keine Typen zeigen wenn Counts fehlschlagen (sicherer)
          setDocumentTypes([])
        }
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
      searchFilters.minConfidence !== 0.02 ||
      searchFilters.adaptiveMinAvgScore !== 0.15 ||
      searchFilters.adaptiveMinMaxScore !== 0.25 ||
      !searchFilters.useHybridSearch ||
      searchFilters.useMultiQuery  // NEU: MultiQuery als aktiver Filter
    )
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
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
          
          {/* NEU: Echtzeit-Anzeige des verwendeten Prompts nach Suche */}
          {lastUsedPromptInfo && lastUsedPromptInfo.documentTypeEffective && (
            <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3 text-xs">
              <div className="flex items-start gap-2">
                <div className="flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <strong className="font-semibold text-green-900">Verwendeter Prompt:</strong>
                  <p className="mt-1 text-green-800">
                    {lastUsedPromptInfo.documentTypeEffective}
                    {lastUsedPromptInfo.documentType && lastUsedPromptInfo.documentType !== lastUsedPromptInfo.documentTypeEffective && (
                      <span className="ml-2 text-green-700">
                        (Filter: {lastUsedPromptInfo.documentType})
                      </span>
                    )}
                  </p>
                  <p className="mt-1 text-green-700 text-xs">
                    Basierend auf den gefundenen Chunks wurde automatisch der dokumenttyp-spezifische Prompt verwendet.
                  </p>
                </div>
                <button
                  onClick={() => setLastUsedPromptInfo(null)}
                  className="flex-shrink-0 text-green-600 hover:text-green-800"
                  title="Schließen"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* PHASE 3: RAG Chat Prompt Editor - Zeige immer (Default-Prompt wenn kein Document Type ausgewählt) */}
          <div className="mt-3">
            <RAGChatPromptEditor
              documentTypeId={searchFilters.documentType ? parseInt(searchFilters.documentType) : null}
              documentTypeName={searchFilters.documentType ? documentTypes.find(t => t.id.toString() === searchFilters.documentType)?.name : undefined}
            />
          </div>
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
                <strong>Werte:</strong> 0.000 (alle Chunks) bis 0.050 (nur sehr relevante).
                <br />
                <strong>OpenAI Embeddings:</strong> Typische Scores liegen bei 0.02-0.03. Höhere Threshold = strengerer Filter = weniger, aber relevantere Ergebnisse.
                <br />
                <strong>Standard:</strong> 0.02 (empfohlen für OpenAI Embeddings, erhöht für bessere Filterung)
                <br />
                <strong>NEU:</strong> Adaptive Filterung - Wenn alle Chunks zu unrelevant sind, werden keine verwendet.
              </p>
            </div>

            {/* Hybrid Search Info */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
              <p className="text-xs text-green-700">
                <strong>Hybrid Search {searchFilters.useHybridSearch ? '(AKTIV)' : '(DEAKTIVIERT)'}:</strong>
                <br />
                {searchFilters.useHybridSearch ? (
                  <>
                    <strong>Was passiert:</strong> Kombiniert zwei Suchmethoden für optimale Ergebnisse:
                    <br />
                    • <strong>Vektor-Suche (70%):</strong> Semantische Suche nach Bedeutung - findet ähnliche Inhalte auch bei anderen Formulierungen
                    <br />
                    • <strong>Text-Suche (30%):</strong> Wort-Übereinstimmungen - findet exakte Begriffe und Phrasen
                    <br />
                    <strong>Formel:</strong> Finaler Score = (Vector-Score × 0.7) + (Text-Score × 0.3)
                    <br />
                    <strong>Vorteil:</strong> Findet sowohl inhaltlich ähnliche als auch exakt passende Chunks.
                  </>
                ) : (
                  <>
                    <strong>Was passiert:</strong> Nur reine Vektor-Suche (semantische Suche nach Bedeutung).
                    <br />
                    • Findet Chunks basierend auf Ähnlichkeit der Bedeutung
                    <br />
                    • Ignoriert exakte Wort-Übereinstimmungen
                    <br />
                    • Filtert direkt nach Vector-Score ≥ Threshold
                    <br />
                    <strong>Vorteil:</strong> Schneller, findet ähnliche Inhalte auch bei anderen Formulierungen.
                    <br />
                    <strong>Nachteil:</strong> Verpasst möglicherweise Chunks mit exakten Wort-Übereinstimmungen.
                  </>
                )}
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

            {/* Top K Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Top K (Anzahl Chunks): {searchFilters.topK}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={searchFilters.topK}
                onChange={(e) => updateFilter('topK', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1 (minimal)</span>
                <span>20 (maximal)</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Aktuell: {searchFilters.topK} beste Chunks werden für die Antwort verwendet
              </div>
            </div>

            {/* Adaptive Filterung - Mindest-Durchschnitts-Score */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Adaptive Filterung - Mindest-Durchschnitts-Score: {(searchFilters.adaptiveMinAvgScore * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.01"
                value={searchFilters.adaptiveMinAvgScore}
                onChange={(e) => updateFilter('adaptiveMinAvgScore', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0% (deaktiviert)</span>
                <span>50% (sehr streng)</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Wenn der durchschnittliche Hybrid-Score der Top-K Chunks &lt; {(searchFilters.adaptiveMinAvgScore * 100).toFixed(0)}% ist, werden keine Chunks verwendet.
              </div>
            </div>

            {/* Adaptive Filterung - Mindest-Maximal-Score */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Adaptive Filterung - Mindest-Maximal-Score: {(searchFilters.adaptiveMinMaxScore * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.01"
                value={searchFilters.adaptiveMinMaxScore}
                onChange={(e) => updateFilter('adaptiveMinMaxScore', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0% (deaktiviert)</span>
                <span>50% (sehr streng)</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Wenn der beste Chunk-Score &lt; {(searchFilters.adaptiveMinMaxScore * 100).toFixed(0)}% ist, werden keine Chunks verwendet.
              </div>
            </div>

            {/* Initialer Score-Filter (während der Suche) */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Initialer Score-Filter: {(searchFilters.minConfidence * 100).toFixed(1)}%
              </label>
              <input
                type="range"
                min="0"
                max="0.05"
                step="0.001"
                value={searchFilters.minConfidence}
                onChange={(e) => updateFilter('minConfidence', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.0% (alle Ergebnisse)</span>
                <span>5.0% (nur sehr relevante)</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Filtert einzelne Chunks <strong>während der Suche</strong> heraus, wenn ihr Hybrid-Score &lt; {(searchFilters.minConfidence * 100).toFixed(1)}% ist.
                <br />
                <strong>Hinweis:</strong> Wird vor den adaptiven Filtern angewendet. Niedrige Werte (z.B. 1-2%) lassen mehr Chunks durch, die dann von den adaptiven Filtern geprüft werden.
              </div>
            </div>

            {/* Filter-Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 mt-4">
              <p className="text-xs text-blue-700">
                <strong>Filter-Reihenfolge:</strong>
                <br />
                1. <strong>Initialer Score-Filter</strong> ({(searchFilters.minConfidence * 100).toFixed(1)}%): Filtert während der Suche einzelne Chunks heraus
                <br />
                2. <strong>Adaptive Filterung</strong> ({(searchFilters.adaptiveMinAvgScore * 100).toFixed(0)}% / {(searchFilters.adaptiveMinMaxScore * 100).toFixed(0)}%): Prüft nach der Suche die Gesamtrelevanz aller Chunks
                <br />
                <br />
                <strong>Empfehlung:</strong> Initialer Filter bei 1-2% (niedrig), Adaptive Filter bei 15%/25% (Standard) für beste Balance zwischen Recall und Precision.
              </p>
            </div>

            {/* Search Options */}
            <div className="space-y-3">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <input
                    type="checkbox"
                    checked={searchFilters.useHybridSearch}
                    onChange={(e) => updateFilter('useHybridSearch', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  Hybrid Search verwenden {searchFilters.useHybridSearch ? '(AKTIV)' : '(DEAKTIVIERT)'}
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  {searchFilters.useHybridSearch 
                    ? '✓ Kombiniert Vektor- (70%) + Text-Suche (30%) für beste Ergebnisse'
                    : '→ Nur Vektor-Suche (semantisch nach Bedeutung)'}
                </p>
              </div>
              
              {/* NEU: MultiQuery Option */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <input
                    type="checkbox"
                    checked={searchFilters.useMultiQuery}
                    onChange={(e) => updateFilter('useMultiQuery', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  MultiQuery verwenden {searchFilters.useMultiQuery ? '(AKTIV)' : '(DEAKTIVIERT)'}
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  {searchFilters.useMultiQuery 
                    ? '✓ Erstellt automatisch Varianten Ihrer Frage für bessere Suchergebnisse (z.B. "loctite kleber" → "Loctite 648", "Beständigkeit gegen Medien")'
                    : '→ Nur Original-Frage wird verwendet'}
                </p>
              </div>
              
              {/* NEU: ML Re-Ranking Option (Phase 4) */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <input
                    type="checkbox"
                    checked={searchFilters.useMlReranking}
                    onChange={(e) => updateFilter('useMlReranking', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  ML Re-Ranking verwenden {searchFilters.useMlReranking ? '(AKTIV)' : '(DEAKTIVIERT)'}
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  {searchFilters.useMlReranking 
                    ? '✓ Learning-to-Rank Model verbessert die Relevanz-Rankings basierend auf SHAP-Features und User-Feedback'
                    : '→ Standard Hybrid Search Ranking wird verwendet'}
                </p>
              </div>
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
              !searchFilters.useHybridSearch && 'Search-Modus',
              searchFilters.useMultiQuery && 'MultiQuery'  // NEU: MultiQuery als aktiver Filter
            ].filter(Boolean).length}
          </div>
        )}
      </div>
    </div>
  )
}
