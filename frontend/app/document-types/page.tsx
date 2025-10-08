'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  getDocumentTypes,
  createDocumentType,
  deleteDocumentType,
  DocumentType,
  DocumentTypeCreate
} from '@/lib/api/documentTypes'

export default function DocumentTypesPage() {
  const router = useRouter()
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newDocType, setNewDocType] = useState<DocumentTypeCreate>({
    name: '',
    code: '',
    description: '',
    allowed_file_types: ['.pdf'],
    max_file_size_mb: 10,
    requires_ocr: false,
    requires_vision: false,
    sort_order: 0
  })

  useEffect(() => {
    loadDocumentTypes()
  }, [])

  const loadDocumentTypes = async () => {
    try {
      const data = await getDocumentTypes()
      setDocumentTypes(data || [])
    } catch (error: any) {
      console.error('Failed to load document types:', error)
      setDocumentTypes([]) // Ensure it's always an array
      if (error.response?.status === 401) {
        router.push('/login')
      } else {
        alert(`Fehler beim Laden: ${error.response?.data?.detail || error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      await createDocumentType(newDocType)
      setShowCreateModal(false)
      setNewDocType({
        name: '',
        code: '',
        description: '',
        allowed_file_types: ['.pdf'],
        max_file_size_mb: 10,
        requires_ocr: false,
        requires_vision: false,
        sort_order: 0
      })
      loadDocumentTypes()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Dokumenttyp "${name}" wirklich löschen?`)) return
    try {
      await deleteDocumentType(id)
      loadDocumentTypes()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Lade Dokumenttypen...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Dokumenttypen
          </h1>
          <p className="text-muted-foreground">
            Verwaltung von QMS-Dokumentkategorien
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Neuer Typ
        </button>
      </div>

      {/* Document Types Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documentTypes.map((docType) => (
          <div
            key={docType.id}
            className="border rounded-lg p-6 bg-white hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold">{docType.name}</h3>
                <span className="text-xs text-gray-500">{docType.code}</span>
              </div>
              <button
                onClick={() => handleDelete(docType.id, docType.name)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">{docType.description}</p>

            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Dateitypen:</span>{' '}
                {docType.allowed_file_types.join(', ')}
              </div>
              <div>
                <span className="font-medium">Max Größe:</span>{' '}
                {docType.max_file_size_mb} MB
              </div>
              <div className="flex gap-2 mt-3">
                {docType.requires_vision && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                    🔍 Vision AI
                  </span>
                )}
                {docType.requires_ocr && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                    📄 OCR
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {documentTypes.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Keine Dokumenttypen vorhanden. Erstelle den ersten!
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Neuer Dokumenttyp</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newDocType.name}
                  onChange={(e) =>
                    setNewDocType({ ...newDocType, name: e.target.value })
                  }
                  className="w-full p-2 border rounded"
                  placeholder="z.B. Flussdiagramm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Code</label>
                <input
                  type="text"
                  value={newDocType.code}
                  onChange={(e) =>
                    setNewDocType({
                      ...newDocType,
                      code: e.target.value.toUpperCase()
                    })
                  }
                  className="w-full p-2 border rounded"
                  placeholder="z.B. FLOWCHART"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Beschreibung
                </label>
                <textarea
                  value={newDocType.description}
                  onChange={(e) =>
                    setNewDocType({ ...newDocType, description: e.target.value })
                  }
                  className="w-full p-2 border rounded"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Max Dateigröße (MB)
                </label>
                <input
                  type="number"
                  value={newDocType.max_file_size_mb}
                  onChange={(e) =>
                    setNewDocType({
                      ...newDocType,
                      max_file_size_mb: parseInt(e.target.value)
                    })
                  }
                  className="w-full p-2 border rounded"
                />
              </div>

              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newDocType.requires_vision}
                    onChange={(e) =>
                      setNewDocType({
                        ...newDocType,
                        requires_vision: e.target.checked
                      })
                    }
                  />
                  <span className="text-sm">Vision AI</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newDocType.requires_ocr}
                    onChange={(e) =>
                      setNewDocType({
                        ...newDocType,
                        requires_ocr: e.target.checked
                      })
                    }
                  />
                  <span className="text-sm">OCR</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleCreate}
                disabled={!newDocType.name || !newDocType.code}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
              >
                Erstellen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

