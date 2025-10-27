'use client'

import { useState } from 'react'
import { X, ExternalLink, Download, ZoomIn, ZoomOut } from 'lucide-react'

interface SourceReference {
  document_id: number
  document_title: string
  page_number: number
  chunk_id: number
  preview_image_path?: string
  relevance_score: number
  text_excerpt: string
}

interface SourcePreviewModalProps {
  source: SourceReference
  isOpen: boolean
  onClose: () => void
}

export default function SourcePreviewModal({ 
  source, 
  isOpen, 
  onClose 
}: SourcePreviewModalProps) {
  const [zoomLevel, setZoomLevel] = useState(100)

  if (!isOpen) return null

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 25, 300))
  }

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 25, 50))
  }

  const handleResetZoom = () => {
    setZoomLevel(100)
  }

  const getPreviewImageUrl = (path: string) => {
    // TODO: Implementiere echte Preview URL Logik
    return `http://localhost:8000/static/uploads/previews/${path}`
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getConfidenceText = (score: number) => {
    if (score >= 0.8) return 'Sehr relevant'
    if (score >= 0.6) return 'Relevant'
    return 'Wenig relevant'
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900 mb-1">
              {source.document_title}
            </h2>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Seite {source.page_number}</span>
              <span>•</span>
              <span>Chunk ID: {source.chunk_id}</span>
              <span>•</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(source.relevance_score)}`}>
                {getConfidenceText(source.relevance_score)} ({Math.round(source.relevance_score * 100)}%)
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Zoom Controls */}
            <div className="flex items-center gap-1 border border-gray-300 rounded">
              <button
                onClick={handleZoomOut}
                className="p-2 hover:bg-gray-100 transition-colors"
                disabled={zoomLevel <= 50}
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="px-2 py-1 text-sm font-medium min-w-[3rem] text-center">
                {zoomLevel}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-2 hover:bg-gray-100 transition-colors"
                disabled={zoomLevel >= 300}
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
            
            <button
              onClick={handleResetZoom}
              className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              Reset
            </button>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-120px)]">
          {/* Left: Preview Image */}
          <div className="flex-1 p-6 bg-gray-50 overflow-auto">
            {source.preview_image_path ? (
              <div className="flex items-center justify-center min-h-full">
                <div 
                  className="bg-white shadow-lg rounded-lg overflow-hidden"
                  style={{ 
                    transform: `scale(${zoomLevel / 100})`,
                    transformOrigin: 'center'
                  }}
                >
                  <img
                    src={getPreviewImageUrl(source.preview_image_path)}
                    alt={`${source.document_title} - Seite ${source.page_number}`}
                    className="max-w-full h-auto"
                    style={{ 
                      maxHeight: 'none',
                      width: 'auto'
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4">📄</div>
                  <p className="text-gray-600 text-lg">Kein Preview verfügbar</p>
                  <p className="text-gray-500 text-sm mt-2">
                    Preview-Bild wurde noch nicht generiert
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Right: Text Excerpt & Actions */}
          <div className="w-80 border-l border-gray-200 p-6 overflow-y-auto">
            <div className="space-y-6">
              {/* Text Excerpt */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Text-Auszug
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 border">
                  <p className="text-gray-800 text-sm leading-relaxed">
                    "{source.text_excerpt}"
                  </p>
                </div>
              </div>

              {/* Relevance Info */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Relevanz
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Score:</span>
                    <span className="font-medium text-gray-900">
                      {Math.round(source.relevance_score * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        source.relevance_score >= 0.8 ? 'bg-green-500' :
                        source.relevance_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${source.relevance_score * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    {getConfidenceText(source.relevance_score)}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Aktionen
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      // TODO: Implementiere Dokument-Detail öffnen
                      window.open(`/documents/${source.document_id}`, '_blank')
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Dokument öffnen
                  </button>
                  
                  {source.preview_image_path && (
                    <button
                      onClick={() => {
                        // TODO: Implementiere Download
                        const link = document.createElement('a')
                        link.href = getPreviewImageUrl(source.preview_image_path)
                        link.download = `${source.document_title}_page_${source.page_number}.jpg`
                        link.click()
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Preview herunterladen
                    </button>
                  )}
                  
                  <button
                    onClick={() => {
                      // TODO: Implementiere RAG Chat mit dieser Quelle
                      window.open('/rag-chat', '_blank')
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Im RAG Chat fragen
                  </button>
                </div>
              </div>

              {/* Metadata */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Metadaten
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Dokument ID:</span>
                    <span className="font-medium text-gray-900">{source.document_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Chunk ID:</span>
                    <span className="font-medium text-gray-900">{source.chunk_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Seite:</span>
                    <span className="font-medium text-gray-900">{source.page_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Relevanz:</span>
                    <span className="font-medium text-gray-900">
                      {Math.round(source.relevance_score * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            Quelle: {source.document_title} • Seite {source.page_number}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Schließen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
