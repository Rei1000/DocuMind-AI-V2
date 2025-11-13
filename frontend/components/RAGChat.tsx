'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Paperclip, Settings, RefreshCw, AlertCircle, RotateCcw, ExternalLink, FileText, Clock, Code } from 'lucide-react'
import SourcePreviewModal from './SourcePreviewModal'
import PromptViewerModal from './PromptViewerModal'  // PHASE 3.1: Prompt Viewer
import RAGTransparencyLayer from './RAGTransparencyLayer'  // PHASE 3.2: Transparency Layer
import RAGFeedbackButton from './RAGFeedbackButton'  // PHASE 4.1: Feedback System
import { useDashboard } from '@/lib/contexts/DashboardContext'
import Spinner from './ui/Spinner'
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
  const [showPromptViewer, setShowPromptViewer] = useState(false)  // PHASE 3.1: Prompt Viewer
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null)  // PHASE 3.1: Prompt Viewer
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = (immediate = false) => {
    // Verwende requestAnimationFrame um sicherzustellen dass DOM aktualisiert ist
    if (immediate) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' })
    } else {
      // Kleine Verzögerung um sicherzustellen dass Rendering abgeschlossen ist
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 50)
    }
  }

  // Scrolling: Nur scrollen wenn User eine neue Message sendet, NIE beim initial Load
  const prevMessagesLengthRef = useRef(0)
  const isInitialLoadRef = useRef(true)
  const hasUserSentMessageRef = useRef(false)
  
  // Reset wenn Session wechselt
  useEffect(() => {
    if (selectedSessionId) {
      isInitialLoadRef.current = true
      hasUserSentMessageRef.current = false
      prevMessagesLengthRef.current = 0
    }
  }, [selectedSessionId])
  
  useEffect(() => {
    // Beim ersten Render nach Session-Wechsel (initial Load): Setze Ref und scroll NICHT
    if (isInitialLoadRef.current) {
      isInitialLoadRef.current = false
      prevMessagesLengthRef.current = currentMessages.length
      return  // KEIN Scroll beim initial Load
    }
    
    // Scroll NUR wenn User explizit eine Message gesendet hat
    // (hasUserSentMessageRef wird in handleSendMessage gesetzt)
    if (hasUserSentMessageRef.current) {
      const hasNewMessages = currentMessages.length > prevMessagesLengthRef.current
      if (hasNewMessages) {
        // Scroll nach kurzer Verzögerung um sicherzustellen dass DOM aktualisiert ist
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }, 100)
        prevMessagesLengthRef.current = currentMessages.length
        hasUserSentMessageRef.current = false  // Reset nach Scroll
      }
    } else if (currentMessages.length === 0) {
      // Reset bei leerer Liste
      prevMessagesLengthRef.current = 0
    }
  }, [currentMessages, selectedSessionId])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const message = inputValue.trim()
    setInputValue('')
    
    // Markiere dass User eine Message sendet (für Scrolling)
    hasUserSentMessageRef.current = true
    
    try {
      // sendMessage creates session automatically if none exists
      // Wichtig: Übergebe selectedModel damit es pro Nachricht gespeichert wird
      await sendMessage(message, selectedModel)
      toast.success('Nachricht erfolgreich gesendet')
    } catch (error) {
      console.error('Fehler beim Senden:', error)
      setLastFailedMessage(message)
      toast.error('Fehler beim Senden der Nachricht')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleRetryMessage = async () => {
    if (!lastFailedMessage || !selectedSessionId) return
    
    setIsRetrying(true)
    try {
      await sendMessage(lastFailedMessage)
      setLastFailedMessage(null)
      toast.success('Nachricht erneut gesendet')
    } catch (error) {
      console.error('Fehler beim erneuten Senden:', error)
      toast.error('Fehler beim erneuten Senden')
    } finally {
      setIsRetrying(false)
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // TODO: Implementiere Voice Recording
  }

  const handleSourceClick = (ref: SourceReference) => {
    setSelectedSource(ref)
    setShowSourceModal(true)
  }

  /**
   * Extrahiert Suchwörter aus einer Frage (entfernt Stop-Wörter und kurze Wörter).
   */
  const extractSearchTerms = (question: string): string[] => {
    if (!question) return []
    
    // Entferne HTML-Tags falls vorhanden
    const cleanQuestion = question.replace(/<[^>]*>/g, ' ')
    
    // Stop-Wörter (deutsch)
    const stopWords = new Set([
      'der', 'die', 'das', 'ein', 'eine', 'einer', 'einem', 'einen',
      'und', 'oder', 'aber', 'dass', 'was', 'wie', 'wo', 'wann', 'warum',
      'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'wurden',
      'hat', 'haben', 'hatte', 'hatten', 'wird', 'werden',
      'zu', 'zum', 'zur', 'von', 'vom', 'für', 'mit', 'bei', 'in', 'im', 'auf', 'an',
      'als', 'wenn', 'ob', 'dass', 'weil', 'damit', 'obwohl',
      'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie',
      'mein', 'dein', 'sein', 'ihr', 'unser', 'euer',
      'mir', 'dir', 'ihm', 'ihr', 'uns', 'euch', 'ihnen',
      'mich', 'dich', 'ihn', 'sie', 'uns', 'euch',
      'dieser', 'diese', 'dieses', 'jener', 'jene', 'jenes',
      'welcher', 'welche', 'welches',
      'nicht', 'kein', 'keine', 'keinen', 'keinem', 'keiner',
      'auch', 'noch', 'schon', 'noch', 'immer', 'nie', 'nie', 'mal',
      'sehr', 'viel', 'wenig', 'mehr', 'meist', 'meiste',
      'kann', 'können', 'muss', 'müssen', 'soll', 'sollen', 'will', 'wollen'
    ])
    
    // Extrahiere Wörter (mindestens 3 Zeichen, keine Zahlen allein)
    const words = cleanQuestion
      .toLowerCase()
      .replace(/[^\wäöüß\s]/g, ' ')
      .split(/\s+/)
      .filter(word => 
        word.length >= 3 && 
        !stopWords.has(word) && 
        !/^\d+$/.test(word) // Keine reinen Zahlen
      )
    
    // Entferne Duplikate und sortiere nach Länge (längere Wörter zuerst)
    const uniqueWords = Array.from(new Set(words))
      .sort((a, b) => b.length - a.length)
      .slice(0, 10) // Maximal 10 Suchwörter
    
    return uniqueWords
  }

  /**
   * Formatiert eine Chat-Nachricht und ersetzt Referenzen durch klickbare Links.
   * Erkennt Muster wie "**Referenz**: chunk [Nummer]" und macht sie klickbar.
   * Die Referenzen stehen direkt im Text, nicht am Ende.
   * 
   * NEU: Fügt chunk_id und highlight terms zu den Links hinzu für bessere UX.
   */
  const formatMessageWithLinks = (
    content: string, 
    sourceReferences: SourceReference[],
    userQuestion?: string
  ): string => {
    if (!sourceReferences || sourceReferences.length === 0) {
      return content.replace(/\n/g, '<br />')
    }

    // Debug Log entfernt - keine Console-Ausgaben mehr

    let formatted = content

    // Erstelle eine Map für schnellen Zugriff auf Referenzen nach chunk_id
    const refMap = new Map<number, SourceReference>()
    sourceReferences.forEach((ref, index) => {
      // Mappe nach Index (Chunk 1, Chunk 2, etc.) - die AI verwendet die Nummer aus dem Kontext
      refMap.set(index + 1, ref)
      // Auch nach chunk_id falls vorhanden
      if (ref.chunk_id) {
        // chunk_id kann String oder Number sein
        const chunkIdNum = typeof ref.chunk_id === 'string' ? parseInt(ref.chunk_id) : ref.chunk_id
        if (!isNaN(chunkIdNum)) {
          refMap.set(chunkIdNum, ref)
        }
      }
    })

    // Extrahiere Suchwörter aus der User-Frage für Highlighting
    const searchTerms = userQuestion ? extractSearchTerms(userQuestion) : []
    const highlightParam = searchTerms.length > 0 
      ? `&highlight=${encodeURIComponent(searchTerms.join(','))}` 
      : ''

    // Debug-Ausgaben entfernt

    // Pattern 1: **Referenz**: chunk [Nummer] - Hauptpattern das die AI verwendet
    // Beispiel: "Die Artikelnummer ist 123.456.789. **Referenz**: chunk 1"
    formatted = formatted.replace(
      /\*\*Referenz\*\*:\s*chunk\s*(\d+)/gi,
      (match, chunkNum) => {
        const chunkId = parseInt(chunkNum)
        const ref = refMap.get(chunkId)
        if (ref) {
          // NEU: Füge page_number, chunk_id und highlight terms als Query-Parameter hinzu
          const chunkIdParam = ref.chunk_id 
            ? `&chunk=${encodeURIComponent(String(ref.chunk_id))}` 
            : ''
          const link = `/documents/${ref.document_id}?page=${ref.page_number}${chunkIdParam}${highlightParam}`
          // Escaped HTML für Sicherheit
          const title = ref.document_title.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
          // WICHTIG: target="_self" statt "_blank" um Authentifizierung zu erhalten
          // onClick Handler verhindert Standard-Navigation und nutzt Router
          const replacedText = `<strong>Referenz</strong>: chunk ${chunkNum} <a href="${link}" onclick="event.preventDefault(); window.location.href='${link}'; return false;" style="color: #2563eb; text-decoration: underline; font-weight: 500; margin-left: 4px; cursor: pointer;">📄 ${title} (Seite ${ref.page_number})</a>`
          
          // Debug-Ausgaben entfernt
          
          return replacedText
        } else {
          // Debug-Ausgaben entfernt
        }
        return match
      }
    )

    // Pattern 2: Referenz: chunk [Nummer] (ohne **)
    formatted = formatted.replace(
      /Referenz:\s*chunk\s*(\d+)/gi,
      (match, chunkNum) => {
        const chunkId = parseInt(chunkNum)
        const ref = refMap.get(chunkId)
        if (ref) {
          // NEU: Füge page_number, chunk_id und highlight terms als Query-Parameter hinzu
          const chunkIdParam = ref.chunk_id 
            ? `&chunk=${encodeURIComponent(String(ref.chunk_id))}` 
            : ''
          const link = `/documents/${ref.document_id}?page=${ref.page_number}${chunkIdParam}${highlightParam}`
          const title = ref.document_title.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
          return `Referenz: chunk ${chunkNum} <a href="${link}" onclick="event.preventDefault(); window.location.href='${link}'; return false;" style="color: #2563eb; text-decoration: underline; font-weight: 500; margin-left: 4px; cursor: pointer;">📄 ${title} (Seite ${ref.page_number})</a>`
        }
        return match
      }
    )

    // Pattern 3: [Referenz chunk 1] oder [Referenz 1]
    formatted = formatted.replace(
      /\[Referenz\s*(?:chunk\s*)?(\d+)\]/gi,
      (match, chunkNum) => {
        const chunkId = parseInt(chunkNum)
        const ref = refMap.get(chunkId)
        if (ref) {
          // NEU: Füge page_number, chunk_id und highlight terms als Query-Parameter hinzu
          const chunkIdParam = ref.chunk_id 
            ? `&chunk=${encodeURIComponent(String(ref.chunk_id))}` 
            : ''
          const link = `/documents/${ref.document_id}?page=${ref.page_number}${chunkIdParam}${highlightParam}`
          const title = ref.document_title.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
          return `<a href="${link}" onclick="event.preventDefault(); window.location.href='${link}'; return false;" style="color: #2563eb; text-decoration: underline; font-weight: 500; cursor: pointer;">[Referenz ${chunkNum}: ${title}]</a>`
        }
        return match
      }
    )
    
    // Ersetze Zeilenumbrüche (WICHTIG: NACH allen Replacements, sonst werden <br /> Tags in Links eingefügt)
    formatted = formatted.replace(/\n/g, '<br />')

    // Debug-Ausgaben entfernt

    return formatted
  }

  const renderSourceReference = (ref: SourceReference, index: number) => (
    <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200 hover:border-blue-300 transition-colors">
      <FileText className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-blue-900 truncate">
            {ref.document_title}
          </span>
          <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full font-medium">
            Seite {ref.page_number}
          </span>
          <span className="text-xs text-green-700 bg-green-100 px-2 py-1 rounded-full font-medium">
            {Math.round(ref.relevance_score * 100)}%
          </span>
        </div>
        <p className="text-xs text-blue-700 mt-2 line-clamp-3 leading-relaxed">
          {ref.text_excerpt}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2 flex-shrink-0">
        <a
          href={`/documents/${ref.document_id}?page=${ref.page_number}`}
          onClick={(e) => {
            e.preventDefault()
            window.location.href = `/documents/${ref.document_id}?page=${ref.page_number}`
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors shadow-sm"
          title="Originaldokument öffnen"
        >
          <FileText className="w-3.5 h-3.5" />
          Original
        </a>
        <button
          onClick={() => handleSourceClick(ref)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-white border border-blue-300 hover:bg-blue-50 rounded-md transition-colors"
          title="Chunk-Vorschau anzeigen"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Vorschau
        </button>
      </div>
    </div>
  )

  const renderStructuredData = (data: StructuredData, index: number) => (
    <div key={index} className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm font-medium text-green-900">
          {data.data_type === 'safety_instructions' ? 'Sicherheitshinweise' : 
           data.data_type === 'article_data' ? 'Artikel-Daten' : 
           data.data_type}
        </span>
        <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
          {Math.round(data.confidence * 100)}% Vertrauen
        </span>
      </div>
      
      {data.data_type === 'article_data' && (
        <div>
          {data.content.articles && (
            <div className="mb-2">
              <strong>Artikel:</strong>
              <ul className="list-disc list-inside ml-2">
                {data.content.articles.map((article: any, idx: number) => (
                  <li key={idx}>{article.name} (Art-Nr: {article.art_nr})</li>
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
                {data.content.warnings.map((warning: string, idx: number) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
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

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {currentMessages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] ${message.role === 'user' ? 'ml-12' : 'mr-12'}`}>
              {/* Message Bubble */}
              <div
                className={`rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-900 rounded-bl-md'
                }`}
              >
                <div 
                  className="prose prose-sm max-w-none"
                  style={{
                    // Überschreibe prose-Link-Styles
                    '--tw-prose-links': '#2563eb',
                  } as React.CSSProperties}
                >
                  <div 
                    className="whitespace-pre-wrap break-words"
                    dangerouslySetInnerHTML={{
                      __html: formatMessageWithLinks(
                        message.content, 
                        message.source_references || [],
                        // Finde die vorherige User-Message für diese Assistant-Message
                        message.role === 'assistant' 
                          ? currentMessages.find((m, idx) => 
                              idx < currentMessages.indexOf(message) && 
                              m.role === 'user'
                            )?.content
                          : undefined
                      )
                    }}
                  />
                </div>
                {/* Debug-Ausgaben entfernt - keine Debug-Info im UI mehr */}
                
                {/* Message Metadata */}
                <div className={`flex items-center justify-between mt-2 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(message.created_at).toLocaleTimeString()}</span>
                    {message.role === 'assistant' && (
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                        {message.ai_model_used || selectedModel}
                      </span>
                    )}
                  </div>
                  {/* PHASE 3.1: Prompt Viewer Button (nur für Assistant-Messages) */}
                  {message.role === 'assistant' && message.id && (
                    <button
                      onClick={() => {
                        setSelectedMessageId(message.id!);
                        setShowPromptViewer(true);
                      }}
                      className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                      title="Prompt anzeigen"
                    >
                      <Code className="w-3 h-3" />
                      Prompt
                    </button>
                  )}
                </div>
              </div>

              {/* Source References entfernt - Alle Referenzen werden jetzt inline im Text angezeigt */}
              {/* Falls Modelle keine Referenzen im Text einfügen, werden sie trotzdem nicht separat angezeigt */}
              
              {/* Structured Data (only for assistant messages) */}
              {message.role === 'assistant' && message.structured_data && message.structured_data.length > 0 && (
                <div className="mt-3">
                  {message.structured_data.map(renderStructuredData)}
                </div>
              )}

              {/* PHASE 3.2: Transparency Layer (nur für Assistant-Messages) */}
              {message.role === 'assistant' && message.id && (
                <RAGTransparencyLayer
                  messageId={message.id}
                  sourceReferences={message.source_references || []}
                  modelUsed={message.ai_model_used}
                  processingTimeMs={message.metadata?.processing_time_ms}
                  tokensUsed={message.metadata?.tokens_used}
                  queryParams={message.metadata?.query_params}
                  embeddingProvider={message.metadata?.embedding_provider}
                  embeddingDimensions={message.metadata?.embedding_dimensions}
                />
              )}

              {/* PHASE 4.1: Feedback Button (nur für Assistant-Messages) */}
              {message.role === 'assistant' && message.id && (
                <RAGFeedbackButton
                  messageId={message.id}
                  onFeedbackSubmitted={() => {
                    // Optional: Reload oder Update UI
                  }}
                />
              )}
            </div>
          </div>
        ))}
        
        {/* Loading Indicator */}
        {isLoadingMessages && (
          <div className="flex justify-start">
            <div className="max-w-[85%] mr-12">
              <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-gray-500" />
                  <span className="text-sm text-gray-500">Antwort wird generiert...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Failed Message Retry */}
        {lastFailedMessage && (
          <div className="flex justify-end">
            <div className="max-w-[85%] ml-12">
              <div className="bg-red-50 border border-red-200 rounded-2xl rounded-br-md p-4">
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
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Fragen Sie nach Ihren Dokumenten..."
              className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={toggleRecording}
              className={`p-2 rounded-lg transition-colors ${
                isRecording 
                  ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            
            <button className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
              <Paperclip className="w-4 h-4" />
            </button>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoadingMessages}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 min-w-[44px]"
            >
              {isLoadingMessages ? (
                <Spinner size="sm" className="border-white border-t-white" />
              ) : (
                <Send className="w-4 h-4" />
              )}
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

      {/* PHASE 3.1: Prompt Viewer Modal */}
      {selectedMessageId && (
        <PromptViewerModal
          isOpen={showPromptViewer}
          onClose={() => {
            setShowPromptViewer(false)
            setSelectedMessageId(null)
          }}
          messageId={selectedMessageId}
        />
      )}
    </div>
  )
}