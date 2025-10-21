'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  getDocumentTypes,
  createDocumentType,
  updateDocumentType,
  deleteDocumentType,
  setDefaultPromptTemplate,
  DocumentType,
  DocumentTypeCreate,
  DocumentTypeUpdate
} from '@/lib/api/documentTypes'
import {
  getPromptTemplates,
  updatePromptTemplate,
  activatePromptTemplate,
  archivePromptTemplate,
  deletePromptTemplate,
  PromptTemplate
} from '@/lib/api/promptTemplates'

export default function PromptManagementPage() {
  const router = useRouter()
  
  // Data State
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [loading, setLoading] = useState(true)
  
  // Selection & Filter State
  const [selectedTypeId, setSelectedTypeId] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterOCR, setFilterOCR] = useState(false)
  const [filterVision, setFilterVision] = useState(false)
  
  // Drag & Drop State
  const [draggedTemplate, setDraggedTemplate] = useState<PromptTemplate | null>(null)
  const [dragOverTypeId, setDragOverTypeId] = useState<number | null>(null)
  
  // Modal State
  const [showTypeModal, setShowTypeModal] = useState(false)
  const [editingType, setEditingType] = useState<DocumentType | null>(null)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [previewTemplate, setPreviewTemplate] = useState<PromptTemplate | null>(null)
  
  // Form State for Document Type Modal
  const [typeName, setTypeName] = useState('')
  const [typeCode, setTypeCode] = useState('')
  const [typeDescription, setTypeDescription] = useState('')
  const [typeFileTypes, setTypeFileTypes] = useState<string[]>(['.pdf'])
  const [typeMaxSize, setTypeMaxSize] = useState(10)
  const [typeRequiresOCR, setTypeRequiresOCR] = useState(false)
  const [typeRequiresVision, setTypeRequiresVision] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [typesData, templatesData] = await Promise.all([
        getDocumentTypes(false), // Include inactive
        getPromptTemplates()
      ])
      setDocumentTypes(typesData)
      setTemplates(templatesData)
    } catch (error: any) {
      console.error('Failed to load data:', error)
      if (error.response?.status === 401) {
        router.push('/login')
      }
    } finally {
      setLoading(false)
    }
  }

  // Filter document types based on search and filters
  const filteredDocTypes = documentTypes.filter(type => {
    if (searchTerm && !type.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !type.description.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    if (filterOCR && !type.requires_ocr) return false
    if (filterVision && !type.requires_vision) return false
    return true
  })

  // Get templates for selected type (grouped by version/name base)
  const getTemplatesForType = (typeId: number | null) => {
    return templates.filter(t => t.document_type_id === typeId)
  }

  const selectedTemplates = selectedTypeId !== null 
    ? getTemplatesForType(selectedTypeId) 
    : []

  const getActiveTemplateForType = (typeId: number) => {
    return templates.find(t => t.document_type_id === typeId && t.status === 'active')
  }

  // Drag & Drop Handlers
  const handleDragStart = (e: React.DragEvent, template: PromptTemplate) => {
    setDraggedTemplate(template)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragEnd = () => {
    setDraggedTemplate(null)
    setDragOverTypeId(null)
  }

  const handleDragOver = (e: React.DragEvent, typeId: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverTypeId(typeId)
  }

  const handleDragLeave = () => {
    setDragOverTypeId(null)
  }

  const handleDrop = async (e: React.DragEvent, typeId: number) => {
    e.preventDefault()
    setDragOverTypeId(null)
    
    if (!draggedTemplate) return
    
    // Check if template is already assigned to this type
    if (draggedTemplate.document_type_id !== typeId) {
      alert('⚠️ Dieser Prompt gehört zu einem anderen Dokumenttyp! Drag & Drop funktioniert nur innerhalb des gleichen Typs zum Setzen als Standard.')
      return
    }
    
    try {
      // Set as default: Archive current active and activate this one
      const currentActive = getActiveTemplateForType(typeId)
      if (currentActive && currentActive.id !== draggedTemplate.id) {
        await archivePromptTemplate(currentActive.id)
      }
      
      if (draggedTemplate.status !== 'active') {
        await activatePromptTemplate(draggedTemplate.id)
      }
      
      // WICHTIG: Setze als default_prompt_template_id für Dokumenttyp
      await setDefaultPromptTemplate(typeId, draggedTemplate.id)
      
      await loadData()
      alert(`✅ "${draggedTemplate.name}" ist jetzt der Standard-Prompt!`)
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  // Document Type CRUD
  const handleCreateType = () => {
    setEditingType(null)
    setTypeName('')
    setTypeCode('')
    setTypeDescription('')
    setTypeFileTypes(['.pdf'])
    setTypeMaxSize(10)
    setTypeRequiresOCR(false)
    setTypeRequiresVision(false)
    setShowTypeModal(true)
  }

  const handleEditType = (type: DocumentType) => {
    setEditingType(type)
    setTypeName(type.name)
    setTypeCode(type.code)
    setTypeDescription(type.description)
    setTypeFileTypes(type.allowed_file_types)
    setTypeMaxSize(type.max_file_size_mb)
    setTypeRequiresOCR(type.requires_ocr)
    setTypeRequiresVision(type.requires_vision)
    setShowTypeModal(true)
  }

  const handleSaveType = async () => {
    if (!typeName.trim() || !typeCode.trim()) {
      alert('Name und Code sind erforderlich!')
      return
    }

    try {
      if (editingType) {
        await updateDocumentType(editingType.id, {
          name: typeName,
          description: typeDescription,
          allowed_file_types: typeFileTypes,
          max_file_size_mb: typeMaxSize,
          requires_ocr: typeRequiresOCR,
          requires_vision: typeRequiresVision
        })
      } else {
        await createDocumentType({
          name: typeName,
          code: typeCode,
          description: typeDescription,
          allowed_file_types: typeFileTypes,
          max_file_size_mb: typeMaxSize,
          requires_ocr: typeRequiresOCR,
          requires_vision: typeRequiresVision
        })
      }
      setShowTypeModal(false)
      await loadData()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleToggleTypeActive = async (id: number, name: string, currentStatus: boolean) => {
    const action = currentStatus ? 'deaktivieren' : 'aktivieren'
    if (!confirm(`Dokumenttyp "${name}" wirklich ${action}?`)) return
    try {
      await updateDocumentType(id, { is_active: !currentStatus })
      await loadData()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  // Template Actions
  const handleSetAsDefault = async (template: PromptTemplate, typeId: number) => {
    try {
      // 1. First, archive the current active template for this type
      const currentActive = getActiveTemplateForType(typeId)
      if (currentActive && currentActive.id !== template.id) {
        await archivePromptTemplate(currentActive.id)
      }
      
      // 2. Activate the new template (wichtig: muss aktiv sein für default_prompt_template_id)
      await activatePromptTemplate(template.id)
      
      // 3. Set as default prompt template for document type
      await setDefaultPromptTemplate(typeId, template.id)
      
      await loadData()
      alert(`✅ "${template.name}" ist jetzt der Standard-Prompt!`)
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDeactivateTemplate = async (id: number, name: string) => {
    if (!confirm(`Prompt "${name}" wirklich archivieren?`)) return
    try {
      await archivePromptTemplate(id)
      await loadData()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDeleteTemplate = async (id: number, name: string) => {
    if (!confirm(`Prompt "${name}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden!`)) return
    try {
      await deletePromptTemplate(id)
      await loadData()
    } catch (error: any) {
      alert(`Fehler: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handlePreview = (template: PromptTemplate) => {
    setPreviewTemplate(template)
    setShowPreviewModal(true)
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        Lade Prompt-Verwaltung...
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              🎯 Prompt-Verwaltung
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Dokumenttypen verwalten und Prompt-Templates zuordnen
            </p>
          </div>
          <button
            onClick={() => router.push('/models')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow"
          >
            ➕ Neuer Prompt im Playground
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Document Types */}
        <div className="w-1/2 overflow-y-auto p-6">
          {/* Search & Filter Bar */}
          <div className="mb-6 space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="🔍 Dokumenttyp suchen..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleCreateType}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap"
              >
                + Neuer Typ
              </button>
            </div>
            
            <div className="flex gap-2">
              <label className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 bg-white">
                <input
                  type="checkbox"
                  checked={filterOCR}
                  onChange={(e) => setFilterOCR(e.target.checked)}
                />
                <span className="text-sm">📄 OCR</span>
              </label>
              <label className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 bg-white">
                <input
                  type="checkbox"
                  checked={filterVision}
                  onChange={(e) => setFilterVision(e.target.checked)}
                />
                <span className="text-sm">🔍 Vision AI</span>
              </label>
            </div>
          </div>

          {/* Document Types Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredDocTypes.map((type) => {
              const activeTemplate = getActiveTemplateForType(type.id)
              const templateCount = getTemplatesForType(type.id).length
              const isSelected = selectedTypeId === type.id
              const isDragOver = dragOverTypeId === type.id

              return (
                <div
                  key={type.id}
                  onClick={() => setSelectedTypeId(type.id)}
                  onDragOver={(e) => handleDragOver(e, type.id)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, type.id)}
                  className={`
                    p-4 rounded-lg cursor-pointer transition-all shadow-sm border-2
                    ${isSelected ? 'bg-blue-50 border-blue-500' : 'bg-white border-gray-200'}
                    ${isDragOver ? 'ring-4 ring-green-300 border-green-500' : ''}
                    ${!type.is_active ? 'opacity-60' : ''}
                    hover:shadow-md
                  `}
                >
                  {/* Header */}
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg flex items-center gap-2">
                        📄 {type.name}
                        {type.requires_vision && <span className="text-sm">🔍</span>}
                        {type.requires_ocr && <span className="text-sm">📄</span>}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">{type.code}</p>
                    </div>
                    {!type.is_active && (
                      <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                        Inaktiv
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {type.description}
                  </p>

                  {/* Meta Info */}
                  <div className="text-xs text-gray-500 space-y-1 mb-3">
                    <div>Dateitypen: {type.allowed_file_types.join(', ')}</div>
                    <div>Max Größe: {type.max_file_size_mb} MB</div>
                  </div>

                  {/* Prompt Status */}
                  <div className="mb-3 p-2 bg-gray-50 rounded">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">
                        {templateCount > 0 ? `🟢 ${templateCount} Prompt(s)` : '⚪ Keine Prompts'}
                      </span>
                      {activeTemplate && (
                        <span className="text-green-600 font-medium">⭐ Standard</span>
                      )}
                    </div>
                    {activeTemplate && (
                      <div className="text-xs text-gray-600 mt-1 truncate">
                        {activeTemplate.name}
                      </div>
                    )}
                  </div>

                  {/* Drop Zone Indicator */}
                  {isDragOver && (
                    <div className="mb-3 p-2 bg-green-50 border-2 border-dashed border-green-400 rounded text-center text-sm text-green-700">
                      ⭐ Als Standard setzen
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditType(type)
                      }}
                      className="flex-1 text-xs px-3 py-2 border border-gray-300 rounded hover:bg-gray-50"
                    >
                      ✏️ Bearbeiten
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleToggleTypeActive(type.id, type.name, type.is_active)
                      }}
                      className={`flex-1 text-xs px-3 py-2 border rounded ${
                        type.is_active
                          ? 'border-red-300 text-red-600 hover:bg-red-50'
                          : 'border-green-300 text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {type.is_active ? '🔴 Deaktivieren' : '🟢 Aktivieren'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {filteredDocTypes.length === 0 && (
            <div className="text-center py-12 border-2 border-dashed rounded-lg bg-white">
              <p className="text-gray-600 mb-2">Keine Dokumenttypen gefunden.</p>
              <button
                onClick={handleCreateType}
                className="text-blue-600 hover:text-blue-800"
              >
                + Ersten Dokumenttyp erstellen
              </button>
            </div>
          )}
        </div>

        {/* Right Panel: Stacked Prompt Cards */}
        <div className="w-1/2 bg-white border-l overflow-y-auto p-6">
          {selectedTypeId ? (
            <>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">
                  Prompt-Versionen für: {documentTypes.find(t => t.id === selectedTypeId)?.name}
                </h2>
                <p className="text-sm text-gray-600">
                  {selectedTemplates.length} Version(en) • Ziehen Sie Karten zum Zuordnen
                </p>
              </div>

              {selectedTemplates.length > 0 ? (
                <div className="relative min-h-[400px]">
                  {/* Stacked Cards Container */}
                  <div className="space-y-4">
                    {selectedTemplates.map((template, index) => {
                      const isActive = template.status === 'active'
                      const zIndex = selectedTemplates.length - index
                      
                      return (
                        <div
                          key={template.id}
                          draggable
                          onDragStart={(e) => handleDragStart(e, template)}
                          onDragEnd={handleDragEnd}
                          style={{
                            zIndex,
                            transform: `translateY(${index * 10}px) rotate(${index * 0.5}deg)`,
                            cursor: 'grab'
                          }}
                          className={`
                            relative p-6 rounded-lg shadow-lg transition-all hover:shadow-xl
                            ${isActive ? 'bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-500' : 'bg-white border-2 border-gray-200'}
                          `}
                        >
                          {/* Active Badge */}
                          {isActive && (
                            <div className="absolute -top-3 -right-3 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-md">
                              ⭐ AKTIV
                            </div>
                          )}

                          {/* Header */}
                          <div className="mb-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h3 className="text-lg font-semibold">{template.name}</h3>
                                <p className="text-xs text-gray-500 font-mono">ID: {template.id}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-gray-500 font-medium">{template.version}</div>
                                <div className="text-xs text-gray-400">
                                  {new Date(template.created_at).toLocaleDateString('de-DE')} {new Date(template.created_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                                </div>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600">{template.description}</p>
                          </div>

                          {/* Model Info */}
                          <div className="grid grid-cols-2 gap-3 text-sm mb-4 p-3 bg-white bg-opacity-50 rounded">
                            <div>
                              <span className="font-medium">Modell:</span> {template.ai_model}
                            </div>
                            <div>
                              <span className="font-medium">Temp:</span> {template.temperature}
                            </div>
                            <div>
                              <span className="font-medium">Tokens:</span> {template.max_tokens.toLocaleString('de-DE')}
                            </div>
                            <div>
                              <span className="font-medium">Verwendet:</span> {template.success_count}x
                            </div>
                          </div>

                          {/* Status Badges */}
                          <div className="flex gap-2 mb-4">
                            <span className={`px-2 py-1 rounded text-xs ${
                              template.status === 'active' ? 'bg-green-100 text-green-700' :
                              template.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {template.status}
                            </span>
                            {template.tested_successfully && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                ✓ Getestet
                              </span>
                            )}
                          </div>

                          {/* Actions */}
                          <div className="flex gap-2 flex-wrap">
                            {!isActive && selectedTypeId && (
                              <button
                                onClick={() => handleSetAsDefault(template, selectedTypeId)}
                                className="flex-1 text-sm px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                              >
                                ⭐ Als Standard setzen
                              </button>
                            )}
                            <button
                              onClick={() => handlePreview(template)}
                              className="flex-1 text-sm px-3 py-2 border border-blue-600 text-blue-600 rounded hover:bg-blue-50"
                            >
                              👁️ Vorschau
                            </button>
                            <button
                              onClick={() => router.push(`/models?template_id=${template.id}`)}
                              className="flex-1 text-sm px-3 py-2 border border-gray-300 rounded hover:bg-gray-50"
                            >
                              ✏️ Bearbeiten
                            </button>
                            {isActive ? (
                              <button
                                onClick={() => handleDeactivateTemplate(template.id, template.name)}
                                className="flex-1 text-sm px-3 py-2 border border-yellow-600 text-yellow-600 rounded hover:bg-yellow-50"
                              >
                                📦 Archivieren
                              </button>
                            ) : (
                              <button
                                onClick={() => handleDeleteTemplate(template.id, template.name)}
                                className="flex-1 text-sm px-3 py-2 border border-red-600 text-red-600 rounded hover:bg-red-50"
                              >
                                🗑️ Löschen
                              </button>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 border-2 border-dashed rounded-lg bg-gray-50">
                  <p className="text-gray-600 mb-2">Keine Prompts für diesen Dokumenttyp.</p>
                  <button
                    onClick={() => router.push('/models')}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    → Prompt im AI Playground erstellen
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-center text-gray-500">
              <div>
                <div className="text-6xl mb-4">📋</div>
                <p className="text-lg">Wählen Sie einen Dokumenttyp links aus,</p>
                <p>um die zugeordneten Prompts anzuzeigen.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Document Type Modal */}
      {showTypeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              {editingType ? 'Dokumenttyp bearbeiten' : 'Neuer Dokumenttyp'}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={typeName}
                  onChange={(e) => setTypeName(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="z.B. Flussdiagramm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Code * (nur beim Erstellen)</label>
                <input
                  type="text"
                  value={typeCode}
                  onChange={(e) => setTypeCode(e.target.value.toUpperCase())}
                  disabled={!!editingType}
                  className="w-full px-3 py-2 border rounded uppercase disabled:bg-gray-100"
                  placeholder="z.B. FLOWCHART"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Beschreibung</label>
                <textarea
                  value={typeDescription}
                  onChange={(e) => setTypeDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Erlaubte Dateitypen (durch Komma trennen)
                </label>
                <input
                  type="text"
                  value={typeFileTypes.join(', ')}
                  onChange={(e) => setTypeFileTypes(e.target.value.split(',').map(t => t.trim()))}
                  className="w-full px-3 py-2 border rounded"
                  placeholder=".pdf, .png, .jpg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Max. Dateigröße (MB)</label>
                <input
                  type="number"
                  value={typeMaxSize}
                  onChange={(e) => setTypeMaxSize(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded"
                  min="1"
                  max="100"
                />
              </div>

              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={typeRequiresOCR}
                    onChange={(e) => setTypeRequiresOCR(e.target.checked)}
                  />
                  <span>📄 Benötigt OCR</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={typeRequiresVision}
                    onChange={(e) => setTypeRequiresVision(e.target.checked)}
                  />
                  <span>🔍 Benötigt Vision AI</span>
                </label>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowTypeModal(false)}
                className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleSaveType}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {editingType ? 'Speichern' : 'Erstellen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreviewModal && previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-2xl font-bold">{previewTemplate.name}</h2>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded">
                <div>
                  <span className="font-medium">Modell:</span> {previewTemplate.ai_model}
                </div>
                <div>
                  <span className="font-medium">Version:</span> {previewTemplate.version}
                </div>
                <div>
                  <span className="font-medium">Status:</span> {previewTemplate.status}
                </div>
                <div>
                  <span className="font-medium">Verwendet:</span> {previewTemplate.success_count}x
                </div>
              </div>

              <div>
                <label className="block font-medium mb-2">Prompt Text:</label>
                <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
                  {previewTemplate.prompt_text}
                </pre>
              </div>

              {previewTemplate.system_instructions && (
                <div>
                  <label className="block font-medium mb-2">System Instructions:</label>
                  <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
                    {previewTemplate.system_instructions}
                  </pre>
                </div>
              )}

              {previewTemplate.example_output && (
                <div>
                  <label className="block font-medium mb-2">Beispiel Output:</label>
                  <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border max-h-60">
                    {previewTemplate.example_output}
                  </pre>
                </div>
              )}

              <div className="flex justify-end pt-4 border-t">
                <button
                  onClick={() => setShowPreviewModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Schließen
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

