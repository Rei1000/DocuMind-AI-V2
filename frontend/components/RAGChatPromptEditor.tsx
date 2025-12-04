'use client'

import { useState, useEffect } from 'react'
import { FileText, Edit2, Save, RotateCcw, ChevronDown, ChevronRight, X } from 'lucide-react'
import { getRAGChatPrompt, saveRAGChatPrompt, deleteRAGChatPrompt, RAGChatPromptResponse, SaveRAGChatPromptRequest } from '@/lib/api/rag'
import { useUser } from '@/lib/contexts/UserContext'

interface RAGChatPromptEditorProps {
  documentTypeId: number | null
  documentTypeName?: string
  className?: string
}

export default function RAGChatPromptEditor({
  documentTypeId,
  documentTypeName,
  className = ''
}: RAGChatPromptEditorProps) {
  const { userLevel } = useUser()
  const canEdit = userLevel >= 4  // Level 4+ können Prompts anpassen

  const [isExpanded, setIsExpanded] = useState(false)
  const [prompt, setPrompt] = useState<RAGChatPromptResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Edit Mode
  const [isEditing, setIsEditing] = useState(false)
  const [editedPromptText, setEditedPromptText] = useState('')
  const [editedMultiQueryPromptText, setEditedMultiQueryPromptText] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'rag' | 'multi-query'>('rag')  // Tab für RAG Chat Prompt oder Multi-Query Prompt

  // Lade Prompt wenn Document Type ausgewählt wird
  useEffect(() => {
    if (documentTypeId) {
      loadPrompt()
    } else {
      setPrompt(null)
      setIsExpanded(false)
    }
  }, [documentTypeId])

  const loadPrompt = async () => {
    if (!documentTypeId) return

    try {
      setIsLoading(true)
      setError(null)
      const response = await getRAGChatPrompt(documentTypeId)
      setPrompt(response)
      setEditedPromptText(response.prompt_text)
      setEditedMultiQueryPromptText(response.multi_query_prompt_text || '')
    } catch (err) {
      console.error('Fehler beim Laden des Prompts:', err)
      setError(err instanceof Error ? err.message : 'Fehler beim Laden des Prompts')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = () => {
    if (!prompt) return
    setEditedPromptText(prompt.prompt_text)
    setEditedMultiQueryPromptText(prompt.multi_query_prompt_text || '')
    setIsEditing(true)
  }

  const handleCancel = () => {
    if (prompt) {
      setEditedPromptText(prompt.prompt_text)
      setEditedMultiQueryPromptText(prompt.multi_query_prompt_text || '')
    }
    setIsEditing(false)
  }

  const handleSave = async () => {
    if (!documentTypeId) return

    try {
      setIsSaving(true)
      setError(null)

      const request: SaveRAGChatPromptRequest = {
        prompt_text: editedPromptText.trim(),
        multi_query_prompt_text: editedMultiQueryPromptText.trim() || null
      }

      const saved = await saveRAGChatPrompt(documentTypeId, request)
      setPrompt(saved)
      setIsEditing(false)
    } catch (err) {
      console.error('Fehler beim Speichern des Prompts:', err)
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern des Prompts')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = async () => {
    if (!documentTypeId || !prompt?.is_custom) return

    if (!confirm('Möchten Sie den Custom Prompt wirklich zurücksetzen? Der Standard-Prompt wird dann wieder verwendet.')) {
      return
    }

    try {
      setIsSaving(true)
      setError(null)
      await deleteRAGChatPrompt(documentTypeId)
      // Lade Prompt neu (wird dann Standard-Prompt sein)
      await loadPrompt()
    } catch (err) {
      console.error('Fehler beim Zurücksetzen des Prompts:', err)
      setError(err instanceof Error ? err.message : 'Fehler beim Zurücksetzen des Prompts')
    } finally {
      setIsSaving(false)
    }
  }

  // Zeige nichts wenn kein Document Type ausgewählt
  if (!documentTypeId) {
    return null
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <FileText className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">
            RAG Chat Prompt
            {documentTypeName && (
              <span className="text-gray-500 ml-1">({documentTypeName})</span>
            )}
          </span>
          {prompt?.is_custom && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
              Custom
            </span>
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 border-t border-gray-200">
          {isLoading ? (
            <div className="text-sm text-gray-500">Lade Prompt...</div>
          ) : error ? (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {error}
            </div>
          ) : prompt ? (
            <>
              {/* Tabs für RAG Chat Prompt und Multi-Query Prompt */}
              <div className="flex gap-2 mb-4 border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('rag')}
                  className={`px-3 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'rag'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  RAG Chat Prompt
                </button>
                <button
                  onClick={() => setActiveTab('multi-query')}
                  className={`px-3 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'multi-query'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Multi-Query Prompt
                </button>
              </div>

              {/* RAG Chat Prompt Tab */}
              {activeTab === 'rag' && (
                <div className="space-y-3">
                  {!isEditing && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-xs text-blue-700">
                      <strong>Hinweis:</strong> Dieser Prompt wird tatsächlich im RAG Chat verwendet. Sie können den vollständigen Prompt bearbeiten, inkl. System-Prompt-Teil oben. Verwenden Sie <code className="bg-blue-100 px-1 rounded">{'{context}'}</code> und <code className="bg-blue-100 px-1 rounded">{'{question}'}</code> als Platzhalter.
                    </div>
                  )}
                  {isEditing ? (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          RAG Chat Prompt-Text (vollständig, wie er verwendet wird)
                        </label>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-2 text-xs text-blue-700">
                          <strong>Hinweis:</strong> Sie können den vollständigen Prompt bearbeiten, inkl. System-Prompt-Teil. Verwenden Sie <code className="bg-blue-100 px-1 rounded">{'{context}'}</code> für den Dokument-Kontext und <code className="bg-blue-100 px-1 rounded">{'{question}'}</code> für die User-Frage. Diese werden beim Verwenden automatisch ersetzt.
                        </div>
                        <textarea
                          value={editedPromptText}
                          onChange={(e) => setEditedPromptText(e.target.value)}
                          rows={15}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                          placeholder="Geben Sie den vollständigen RAG Chat Prompt-Text ein (inkl. System-Prompt-Teil)..."
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          {editedPromptText.length} Zeichen
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSave}
                          disabled={isSaving || !editedPromptText.trim()}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Save className="w-4 h-4" />
                          {isSaving ? 'Speichere...' : 'Speichern'}
                        </button>
                        <button
                          onClick={handleCancel}
                          disabled={isSaving}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                        >
                          <X className="w-4 h-4" />
                          Abbrechen
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                          {prompt.prompt_text}
                        </pre>
                      </div>
                      <div className="flex gap-2">
                        {canEdit && (
                          <button
                            onClick={handleEdit}
                            className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                          >
                            <Edit2 className="w-4 h-4" />
                            Bearbeiten
                          </button>
                        )}
                        {canEdit && prompt.is_custom && (
                          <button
                            onClick={handleReset}
                            disabled={isSaving}
                            className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                          >
                            <RotateCcw className="w-4 h-4" />
                            Zurücksetzen
                          </button>
                        )}
                      </div>
                      {!canEdit && (
                        <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded p-2">
                          Nur Level 4+ (QM/QM Admin) können Prompts anpassen.
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Multi-Query Prompt Tab */}
              {activeTab === 'multi-query' && (
                <div className="space-y-3">
                  {isEditing ? (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Multi-Query Prompt-Text
                          <span className="text-gray-500 ml-1">(Verwenden Sie {'{question}'} als Platzhalter für die User-Frage)</span>
                        </label>
                        <textarea
                          value={editedMultiQueryPromptText}
                          onChange={(e) => setEditedMultiQueryPromptText(e.target.value)}
                          rows={12}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                          placeholder="Erstelle 3-5 verschiedene Suchvarianten für diese Frage, um möglichst viele relevante Dokumente zu finden:\n\nOriginal: {question}\n\n..."
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          {editedMultiQueryPromptText.length} Zeichen
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSave}
                          disabled={isSaving}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Save className="w-4 h-4" />
                          {isSaving ? 'Speichere...' : 'Speichern'}
                        </button>
                        <button
                          onClick={handleCancel}
                          disabled={isSaving}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                        >
                          <X className="w-4 h-4" />
                          Abbrechen
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      {prompt.multi_query_prompt_text ? (
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                          <div className="mb-2 text-xs font-medium text-gray-600">
                            {prompt.is_custom ? 'Custom Multi-Query Prompt:' : 'Standard Multi-Query Prompt:'}
                          </div>
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                            {prompt.multi_query_prompt_text}
                          </pre>
                        </div>
                      ) : (
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-500">
                          Kein Multi-Query Prompt vorhanden. Der Standard-Prompt wird verwendet.
                        </div>
                      )}
                      <div className="flex gap-2">
                        {canEdit && (
                          <button
                            onClick={handleEdit}
                            className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                          >
                            <Edit2 className="w-4 h-4" />
                            {prompt.multi_query_prompt_text && prompt.is_custom ? 'Bearbeiten' : 'Erstellen'}
                          </button>
                        )}
                        {canEdit && prompt.is_custom && (
                          <button
                            onClick={handleReset}
                            disabled={isSaving}
                            className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                          >
                            <RotateCcw className="w-4 h-4" />
                            Zurücksetzen
                          </button>
                        )}
                      </div>
                      {!canEdit && (
                        <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded p-2">
                          Nur Level 4+ (QM/QM Admin) können Prompts anpassen.
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-sm text-gray-500">Kein Prompt gefunden.</div>
          )}
        </div>
      )}
    </div>
  )
}

