'use client'

import { X, AlertTriangle, ExternalLink } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface DuplicateWarningModalProps {
  isOpen: boolean
  onClose: () => void
  onKeepDuplicate: () => void
  duplicateOfDocumentId: number
  originalFilename?: string
  currentDocumentId: number
}

export default function DuplicateWarningModal({
  isOpen,
  onClose,
  onKeepDuplicate,
  duplicateOfDocumentId,
  originalFilename,
  currentDocumentId
}: DuplicateWarningModalProps) {
  const router = useRouter()

  if (!isOpen) return null

  const handleGoToOriginal = () => {
    router.push(`/documents/${duplicateOfDocumentId}`)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-full">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Duplikat erkannt</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-gray-700">
            Dieses Dokument ist bereits im System vorhanden!
          </p>

          {/* Original Document Info */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-2">Original-Dokument:</p>
            <p className="font-medium text-gray-900">
              📄 {originalFilename || `Dokument #${duplicateOfDocumentId}`}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ID: #{duplicateOfDocumentId}
            </p>
          </div>

          {/* Warning Info */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
            <p className="text-sm text-yellow-800">
              <strong>Hinweis:</strong> Das Duplikat wurde gespeichert, zeigt aber auf das Original-Dokument.
              Duplikate können nicht indexiert werden.
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3 pt-4">
            <button
              onClick={handleGoToOriginal}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Zum Original springen
            </button>
            <button
              onClick={() => {
                onKeepDuplicate()
                onClose()
              }}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Als Duplikat behalten
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

