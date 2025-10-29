'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Paperclip, Settings, RefreshCw, AlertCircle, RotateCcw } from 'lucide-react'
import SourcePreviewModal from './SourcePreviewModal'
import { useDashboard } from '@/lib/contexts/DashboardContext'
import toast from 'react-hot-toast'

interface SourceReference {
  document_id: number
  document_title: string
  page_number: number
  chunk_id: number
  preview_image_path?: string
  relevance_score: number
  text_excerpt: string
}

interface StructuredData {
  data_type: string
  content: Record<string, any>
  confidence: number
}

interface RAGChatProps {
  className?: string
}

export default function RAGChat({ 
  className = ''
}: RAGChatProps) {
  const {
    selectedSessionId,
    currentMessages,
    sendMessage,
    isLoadingMessages
  } = useDashboard()
  
  const [inputValue, setInputValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini')
  const [selectedSource, setSelectedSource] = useState<SourceReference | null>(null)
  const [showSourceModal, setShowSourceModal] = useState(false)
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null)
  const [isRetrying, setIsRetrying] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentMessages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoadingMessages) return

    const question = inputValue.trim()
    setInputValue('')
    setLastFailedMessage(null) // Clear any previous failed message

    try {
      await sendMessage(question)
      
      // Show success toast
      toast.success('Nachricht erfolgreich gesendet')
      
      // Update suggested questions based on response
      // This would be handled by the backend response in a real implementation
      if (question.includes('Sicherheit')) {
        setSuggestedQuestions([
          'Welche persönliche Schutzausrüstung ist erforderlich?',
          'Gibt es spezielle Warnhinweise zu beachten?',
          'Wie verhalte ich mich bei Notfällen?'
        ])
      }
    } catch (error) {
      console.error('Fehler beim Senden der Nachricht:', error)
      
      // Store the failed message for retry
      setLastFailedMessage(question)
      
      // Show error toast
      toast.error('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.')
    }
  }

  const handleRetryMessage = async () => {
    if (!lastFailedMessage || isRetrying) return

    setIsRetrying(true)
    try {
      await sendMessage(lastFailedMessage)
      setLastFailedMessage(null)
      toast.success('Nachricht erfolgreich gesendet')
    } catch (error) {
      console.error('Fehler beim erneuten Senden der Nachricht:', error)
      toast.error('Fehler beim erneuten Senden der Nachricht. Bitte versuchen Sie es erneut.')
    } finally {
      setIsRetrying(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSourceClick = (ref: SourceReference) => {
    // SourceReference is already in the correct format for SourcePreviewModal
    setSelectedSource(ref)
    setShowSourceModal(true)
  }


  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // TODO: Implementiere Voice Recording
  }

  const renderSourceReference = (ref: SourceReference) => (
    <div key={ref.chunk_id} className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 
            className="font-medium text-blue-900 text-sm cursor-pointer hover:text-blue-700"
            onClick={() => handleSourceClick(ref)}
          >
            {ref.document_title} (Seite {ref.page_number})
          </h4>
          <p className="text-blue-600 text-xs mt-2 italic">"{ref.text_excerpt}"</p>
        </div>
        <div className="flex items-center gap-2 ml-3">
          <span className="text-xs text-blue-500 bg-blue-100 px-2 py-1 rounded">
            {Math.round(ref.relevance_score * 100)}%
          </span>
          <button 
            onClick={() => handleSourceClick(ref)}
            className="text-blue-600 hover:text-blue-800 text-xs"
          >
            Preview
          </button>
        </div>
      </div>
    </div>
  )

  const renderStructuredData = (data: StructuredData) => (
    <div key={data.data_type} className="bg-green-50 border border-green-200 rounded-lg p-3 mb-2">
      <h4 className="font-medium text-green-900 text-sm mb-2">{data.data_type}</h4>
      <div className="text-green-700 text-xs">
        {data.data_type === 'work_instructions' && (
          <div>
            {data.content.steps && (
              <div className="mb-2">
                <strong>Schritte:</strong>
                <ol className="list-decimal list-inside ml-2">
                  {data.content.steps.map((step: string, index: number) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
            )}
            {data.content.parts && (
              <div className="mb-2">
                <strong>Benötigte Teile:</strong>
                <ul className="list-disc list-inside ml-2">
                  {data.content.parts.map((part: string, index: number) => (
                    <li key={index}>{part}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.content.safety_notes && (
              <div className="mb-2">
                <strong>Sicherheitshinweise:</strong>
                <ul className="list-disc list-inside ml-2">
                  {data.content.safety_notes.map((note: string, index: number) => (
                    <li key={index}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        {data.data_type === 'safety_instructions' && (
          <div>
            {data.content.warnings && (
              <div className="mb-2">
                <strong>Warnungen:</strong>
                <ul className="list-disc list-inside ml-2">
                  {data.content.warnings.map((warning: string, index: number) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="text-xs text-green-600 mt-2">
        Vertrauen: {Math.round(data.confidence * 100)}%
      </div>
    </div>
  )

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 text-sm font-bold">RAG</span>
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">DocuMind AI Assistant</h2>
            <p className="text-xs text-gray-500">Fragen Sie nach Ihren Dokumenten</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-5-mini">GPT-5 Mini</option>
            <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
          </select>
          <button className="p-1 text-gray-500 hover:text-gray-700">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentMessages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              
              {/* Source References */}
              {message.source_references && message.source_references.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium mb-2">Quellen:</p>
                  {message.source_references.map(renderSourceReference)}
                </div>
              )}
              
              {/* Structured Data */}
              {message.structured_data && message.structured_data.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium mb-2">Strukturierte Daten:</p>
                  {message.structured_data.map(renderStructuredData)}
                </div>
              )}
              
              <p className="text-xs opacity-70 mt-2">
                {new Date(message.created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isLoadingMessages && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-sm text-gray-500">Antwort wird generiert...</span>
              </div>
            </div>
          </div>
        )}
        
        {lastFailedMessage && (
          <div className="flex justify-end">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 max-w-[80%]">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                <span className="text-sm font-medium text-red-900">Fehler beim Senden</span>
              </div>
              <p className="text-sm text-red-700 mb-3">{lastFailedMessage}</p>
              <button
                onClick={handleRetryMessage}
                disabled={isRetrying}
                className="flex items-center gap-2 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRetrying ? (
                  <>
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Wird erneut versucht...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3 h-3" />
                    Erneut versuchen
                  </>
                )}
              </button>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Fragen Sie nach Ihren Dokumenten..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isLoadingMessages}
            />
          </div>
          <div className="flex flex-col gap-2">
            <button
              onClick={toggleRecording}
              className={`p-2 rounded-lg ${
                isRecording
                  ? 'bg-red-100 text-red-600 hover:bg-red-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              aria-label={isRecording ? 'Aufnahme stoppen' : 'Aufnahme starten'}
              title={isRecording ? 'Aufnahme stoppen' : 'Aufnahme starten'}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoadingMessages}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Nachricht senden"
              title="Nachricht senden"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        
      </div>

      {/* Source Preview Modal */}
      {selectedSource && (
        <SourcePreviewModal
          source={selectedSource}
          isOpen={showSourceModal}
          onClose={() => {
            setShowSourceModal(false)
            setSelectedSource(null)
          }}
        />
      )}
    </div>
  )
}
