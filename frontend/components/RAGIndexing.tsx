'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Database, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  RefreshCw, 
  Eye,
  BarChart3,
  FileText,
  Zap
} from 'lucide-react'
import { apiClient, IndexedDocument } from '@/lib/api/rag'
import { useUser } from '@/lib/contexts/UserContext'

interface RAGIndexingProps {
  documentId: number
  documentTitle: string
  documentType: string
  isApproved: boolean
  className?: string
}

interface IndexingStatus {
  status: 'not_indexed' | 'indexing' | 'indexed' | 'failed' | 'reindexing'
  indexedDocument?: IndexedDocument
  error?: string
  progress?: number
}

export default function RAGIndexing({ 
  documentId, 
  documentTitle, 
  documentType, 
  isApproved,
  className = '' 
}: RAGIndexingProps) {
  const { permissions } = useUser()
  const router = useRouter()
  const [indexingStatus, setIndexingStatus] = useState<IndexingStatus>({ status: 'not_indexed' })
  const [isLoading, setIsLoading] = useState(true)
  const [showDetails, setShowDetails] = useState(false)

  // Permission Check: Nur QM/QM Admin dürfen indexieren
  const canIndex = permissions.canIndexDocuments && isApproved

  useEffect(() => {
    checkIndexingStatus()
  }, [documentId])

  // Generiere eine intelligente Frage basierend auf Dokument-Titel und Typ
  const generateQuestion = (title: string, type: string): string => {
    const encodedTitle = encodeURIComponent(title)
    const encodedType = encodeURIComponent(type)
    
    // Generiere eine kontextuelle Frage basierend auf dem Dokumenttyp
    let questionTemplate = ''
    switch (type.toLowerCase()) {
      case 'sop':
        questionTemplate = `Was sind die wichtigsten Schritte und Verfahren in dem SOP "${title}"?`
        break
      case 'manual':
        questionTemplate = `Welche Anweisungen und Richtlinien sind in dem Handbuch "${title}" beschrieben?`
        break
      case 'policy':
        questionTemplate = `Was sind die Hauptrichtlinien und Regeln in der Policy "${title}"?`
        break
      case 'procedure':
        questionTemplate = `Wie ist das Verfahren "${title}" strukturiert und was sind die wichtigsten Punkte?`
        break
      default:
        questionTemplate = `Was ist in dem Dokument "${title}" (${type}) beschrieben?`
    }
    
    return encodeURIComponent(questionTemplate)
  }

  // Navigiere zum Dashboard mit vorausgefüllter Frage
  const navigateToDashboardWithQuestion = () => {
    const question = generateQuestion(documentTitle, documentType)
    const url = `/?question=${question}&documentType=${encodeURIComponent(documentType)}`
    router.push(url)
  }

  const checkIndexingStatus = async () => {
    try {
      setIsLoading(true)
      
      // Prüfe ob Dokument bereits indexiert ist
      const response = await apiClient.getIndexedDocuments()

      if (response.data) {
        const indexedDoc = response.data.find((doc: IndexedDocument) => 
          doc.upload_document_id === documentId
        )
        
        if (indexedDoc) {
          setIndexingStatus({
            status: indexedDoc.status === 'indexed' ? 'indexed' : 
                   indexedDoc.status === 'processing' ? 'indexing' : 'failed',
            indexedDocument: indexedDoc
          })
        } else {
          setIndexingStatus({ status: 'not_indexed' })
        }
      }
    } catch (error) {
      console.error('Fehler beim Prüfen des Indexierungsstatus:', error)
      setIndexingStatus({ 
        status: 'not_indexed',
        error: 'Fehler beim Laden des Status'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleIndexDocument = async () => {
    if (!canIndex) {
      if (!isApproved) {
        alert('Dokument muss freigegeben sein, um indexiert zu werden.')
      } else if (!permissions.canIndexDocuments) {
        alert('Sie haben keine Berechtigung, Dokumente zu indexieren. Nur QM und QM Admin dürfen diese Aktion durchführen.')
      }
      return
    }

    try {
      setIndexingStatus({ status: 'indexing', progress: 0 })
      
      // Simuliere Progress
      const progressInterval = setInterval(() => {
        setIndexingStatus(prev => ({
          ...prev,
          progress: Math.min((prev.progress || 0) + 10, 90)
        }))
      }, 500)

      const response = await apiClient.indexDocument({
        upload_document_id: documentId,
        force_reindex: false
      })

      clearInterval(progressInterval)

      if (response.data) {
        setIndexingStatus({
          status: 'indexed',
          indexedDocument: response.data.document,
          progress: 100
        })
        
        // Zeige Erfolgsmeldung
        alert(`✅ Dokument erfolgreich indexiert!\n\nChunks erstellt: ${response.data.chunks_created}\nVerarbeitungszeit: ${response.data.processing_time_ms}ms`)
      } else {
        throw new Error(response.error || 'Indexierung fehlgeschlagen')
      }
    } catch (error) {
      console.error('Fehler bei der Indexierung:', error)
      setIndexingStatus({
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unbekannter Fehler'
      })
    }
  }

  const handleReindexDocument = async () => {
    if (!indexingStatus.indexedDocument) return

    try {
      setIndexingStatus({ status: 'reindexing', progress: 0 })
      
      // Simuliere Progress
      const progressInterval = setInterval(() => {
        setIndexingStatus(prev => ({
          ...prev,
          progress: Math.min((prev.progress || 0) + 15, 90)
        }))
      }, 300)

      const response = await apiClient.reindexDocument(
        indexingStatus.indexedDocument.id,
        { force_reindex: true }
      )

      clearInterval(progressInterval)

      if (response.data) {
        setIndexingStatus({
          status: 'indexed',
          indexedDocument: response.data.document,
          progress: 100
        })
        
        // Zeige Erfolgsmeldung
        alert(`✅ Dokument erfolgreich re-indexiert!\n\nAlte Chunks gelöscht: ${response.data.old_chunks_deleted}\nNeue Chunks erstellt: ${response.data.new_chunks_created}\nVerarbeitungszeit: ${response.data.processing_time_ms}ms`)
      } else {
        throw new Error(response.error || 'Re-Indexierung fehlgeschlagen')
      }
    } catch (error) {
      console.error('Fehler bei der Re-Indexierung:', error)
      setIndexingStatus({
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unbekannter Fehler'
      })
    }
  }

  const getStatusIcon = () => {
    switch (indexingStatus.status) {
      case 'indexed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'indexing':
      case 'reindexing':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      default:
        return <Database className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusText = () => {
    switch (indexingStatus.status) {
      case 'indexed':
        return 'Indexiert'
      case 'indexing':
        return 'Wird indexiert...'
      case 'reindexing':
        return 'Wird re-indexiert...'
      case 'failed':
        return 'Fehlgeschlagen'
      default:
        return 'Nicht indexiert'
    }
  }

  const getStatusColor = () => {
    switch (indexingStatus.status) {
      case 'indexed':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'indexing':
      case 'reindexing':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-5 h-5 text-gray-400" />
          <h2 className="text-xl font-bold text-gray-800">RAG Indexierung</h2>
        </div>
        <div className="flex items-center gap-2 text-gray-500">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span className="text-sm">Lade Status...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-800">RAG Indexierung</h2>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
        >
          <Eye className="w-4 h-4" />
        </button>
      </div>

      {/* Status */}
      <div className="mb-4">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor()}`}>
          {getStatusIcon()}
          {getStatusText()}
        </div>
        
        {/* Progress Bar */}
        {(indexingStatus.status === 'indexing' || indexingStatus.status === 'reindexing') && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
              <span>Fortschritt</span>
              <span>{indexingStatus.progress || 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${indexingStatus.progress || 0}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Message */}
        {indexingStatus.status === 'failed' && indexingStatus.error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm font-medium">Fehler:</p>
            <p className="text-red-600 text-sm">{indexingStatus.error}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="space-y-2">
        {indexingStatus.status === 'not_indexed' && (
          <button
            onClick={handleIndexDocument}
            disabled={!canIndex}
            className={`w-full px-4 py-2 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
              canIndex
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
            title={
              !isApproved ? 'Dokument muss freigegeben sein' :
              !permissions.canIndexDocuments ? 'Nur QM/QM Admin dürfen indexieren' :
              'In RAG indexieren'
            }
          >
            <Zap className="w-4 h-4" />
            {!isApproved ? 'Dokument nicht freigegeben' :
             !permissions.canIndexDocuments ? 'Keine Berechtigung' :
             'In RAG indexieren'}
          </button>
        )}

        {indexingStatus.status === 'indexed' && (
          <div className="flex gap-2">
            <button
              onClick={handleReindexDocument}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Re-indexieren
            </button>
            <button
              onClick={navigateToDashboardWithQuestion}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium flex items-center justify-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Im Chat fragen
            </button>
          </div>
        )}

        {(indexingStatus.status === 'indexing' || indexingStatus.status === 'reindexing') && (
          <button
            disabled
            className="w-full px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed font-medium flex items-center justify-center gap-2"
          >
            <Clock className="w-4 h-4" />
            Verarbeitung läuft...
          </button>
        )}

        {indexingStatus.status === 'failed' && (
          <button
            onClick={handleIndexDocument}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Erneut versuchen
          </button>
        )}
      </div>

      {/* Details */}
      {showDetails && indexingStatus.indexedDocument && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Indexierungsdetails:</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">Chunks:</span>
              <span className="font-medium text-gray-900 ml-2">
                {indexingStatus.indexedDocument.total_chunks}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Typ:</span>
              <span className="font-medium text-gray-900 ml-2">
                {indexingStatus.indexedDocument.document_type}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Indexiert:</span>
              <span className="font-medium text-gray-900 ml-2">
                {formatDate(indexingStatus.indexedDocument.indexed_at)}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Aktualisiert:</span>
              <span className="font-medium text-gray-900 ml-2">
                {formatDate(indexingStatus.indexedDocument.last_updated)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-start gap-2 text-xs text-gray-500">
          <BarChart3 className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium mb-1">RAG Indexierung:</p>
            <ul className="space-y-1">
              <li>• Dokument wird in semantische Chunks aufgeteilt</li>
              <li>• Embeddings werden mit OpenAI generiert</li>
              <li>• Chunks werden in Qdrant Vector Store gespeichert</li>
              <li>• Ermöglicht intelligente Suche und Fragen</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
