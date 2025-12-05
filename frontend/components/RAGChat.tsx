'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Paperclip, Settings, RefreshCw, AlertCircle, RotateCcw, ExternalLink, FileText, Clock, Code } from 'lucide-react'
import SourcePreviewModal from './SourcePreviewModal'
import PromptViewerModal from './PromptViewerModal'  // PHASE 3.1: Prompt Viewer
import RAGTransparencyLayer from './RAGTransparencyLayer'  // PHASE 3.2: Transparency Layer
import RAGFeedbackButton from './RAGFeedbackButton'  // PHASE 4.1: Feedback System
import RAGChatSettingsModal, { AISettings, DEFAULT_SETTINGS } from './RAGChatSettingsModal'  // NEU v2.10.3: Settings Modal
import { useDashboard } from '@/lib/contexts/DashboardContext'
import Spinner from './ui/Spinner'
import toast from 'react-hot-toast'
import { SourceReference } from '@/lib/api/rag'  // NEU: Verwende erweiterte SourceReference aus API
import { highlightQueryWords } from '@/lib/utils/textHighlighting'  // NEU: Text-Highlighting (Phase 3)

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
  const [showSettingsModal, setShowSettingsModal] = useState(false)  // NEU v2.10.3: Settings Modal
  const [aiSettings, setAiSettings] = useState<AISettings>(() => {
    // Lade Settings aus localStorage oder verwende Defaults
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('rag_chat_ai_settings')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch (e) {
          console.warn('Failed to parse saved AI settings, using defaults')
        }
      }
    }
    return DEFAULT_SETTINGS
  })  // NEU v2.10.3: AI Settings State
  
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
      // Wichtig: Übergebe selectedModel und AI-Einstellungen damit sie pro Nachricht gespeichert werden
      await sendMessage(message, selectedModel, aiSettings)
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
   * Konvertiert Info-Boxes (Blockquotes mit Emoji) zu HTML-Boxes.
   * Pattern: > 🔵 **INFO:** Text oder > ⚠️ **WICHTIG:** Text
   * NEU v2.8.0: Unterstützt Info-Boxes für wichtige Informationen.
   */
  const convertInfoBoxes = (text: string): string => {
    // Pattern: > [Emoji] **TYPE:** Text
    const infoBoxRegex = /^>\s*([🔵⚠️✅❌])\s*\*\*([^*]+)\*\*:\s*(.+)$/gm;
    
    return text.replace(infoBoxRegex, (match, emoji, type, content) => {
      // Bestimme Farben basierend auf Emoji
      let bgColor = 'bg-blue-50';
      let borderColor = 'border-blue-200';
      let textColor = 'text-blue-900';
      let iconColor = 'text-blue-600';
      
      if (emoji === '⚠️') {
        bgColor = 'bg-yellow-50';
        borderColor = 'border-yellow-200';
        textColor = 'text-yellow-900';
        iconColor = 'text-yellow-600';
      } else if (emoji === '✅') {
        bgColor = 'bg-green-50';
        borderColor = 'border-green-200';
        textColor = 'text-green-900';
        iconColor = 'text-green-600';
      } else if (emoji === '❌') {
        bgColor = 'bg-red-50';
        borderColor = 'border-red-200';
        textColor = 'text-red-900';
        iconColor = 'text-red-600';
      }
      
      return `<div class="${bgColor} ${borderColor} border-l-4 ${textColor} p-4 my-3 rounded-r-md">
        <div class="flex items-start">
          <span class="${iconColor} text-xl mr-2">${emoji}</span>
          <div>
            <strong class="font-semibold">${type}:</strong>
            <span class="ml-1">${content}</span>
          </div>
        </div>
      </div>`;
    });
  };

  /**
   * Konvertiert Code-Blöcke zu HTML.
   * Pattern: ```language\ncode\n```
   * NEU v2.8.0: Unterstützt Code-Blöcke für Formeln/Parameter.
   */
  const convertCodeBlocks = (text: string): string => {
    // Pattern: ```language\ncode\n```
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    
    return text.replace(codeBlockRegex, (match, language, code) => {
      // Escape HTML in Code
      const escapedCode = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
      
      return `<div class="bg-gray-900 rounded-lg p-4 my-3 overflow-x-auto">
        ${language ? `<div class="text-gray-400 text-xs mb-2 font-mono">${language}</div>` : ''}
        <pre class="text-gray-100 font-mono text-sm"><code>${escapedCode}</code></pre>
      </div>`;
    });
  };

  /**
   * Highlightet Zahlen mit Einheiten visuell.
   * Pattern: Zahl + Einheit (z.B. 850°C, 30-40 min, 1.0 bar)
   * NEU v2.8.0: Unterstützt Zahlen-Highlighting für technische Daten.
   */
  const highlightNumbers = (text: string): string => {
    // Pattern: Zahl (optional Dezimal, optional Punkt nach Zahl) + Einheit
    // WICHTIG: Nur außerhalb von HTML-Tags (nicht in bereits formatiertem HTML)
    // Erweitert um mehr Einheiten: mm, cm, m, Minute, Minuten, etc.
    // Unterstützt auch "40. Minute" (Zahl mit Punkt + Leerzeichen + Einheit)
    const numberPattern = /(\d+(?:[.,]\d+)?\.?)\s*([°C]|min|Minute|Minuten|bar|MPa|kN|mm|cm|m|kg|g|%|h|s|€|km\/h|m\/s|Hz|kHz|MHz|GHz|V|mV|A|mA|W|kW|MW|J|kJ|MJ|Wh|kWh|MWh|lx|cd|lm|dB|ppm|psi|rpm|g\/cm³|kg\/m³|N|Nm|Pa|kPa|GPa|°|K|mol|cd|sr|rad|bit|byte|kB|MB|GB|TB|ms|µs|ns|ps|°F|K|pH|l|ml|µl|dl|cl|hl|m²|cm²|mm²|km²|ha|m³|cm³|mm³|l|ml|µl|dl|cl|hl)/g;
    
    // Teile Text in Teile außerhalb und innerhalb von HTML-Tags
    const parts: string[] = [];
    let lastIndex = 0;
    let inTag = false;
    
    for (let i = 0; i < text.length; i++) {
      if (text[i] === '<') {
        if (lastIndex < i) {
          // Text vor dem Tag
          parts.push(text.substring(lastIndex, i));
        }
        inTag = true;
        lastIndex = i;
      } else if (text[i] === '>' && inTag) {
        // Tag-Ende
        parts.push(text.substring(lastIndex, i + 1));
        lastIndex = i + 1;
        inTag = false;
      }
    }
    
    // Rest nach dem letzten Tag
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    
    // Wende Highlighting nur auf Text-Teile an (nicht auf HTML-Tags)
    return parts.map((part, index) => {
      if (part.startsWith('<')) {
        return part; // HTML-Tag, nicht ändern
      }
      // Text-Teil: Wende Highlighting an
      return part.replace(numberPattern, (match, number, unit) => {
        return `<span class="text-blue-600 font-semibold">${number}${unit}</span>`;
      });
    }).join('');
  };

  /**
   * Konvertiert Markdown-Listen zu HTML.
   * Pattern: - Item oder 1. Item oder **Bold**: Text (für strukturierte Listen)
   * NEU v2.8.0: Unterstützt Markdown-Listen.
   */
  const convertMarkdownLists = (text: string): string => {
    // Unnummerierte Listen: - Item oder * Item (auch mit **Bold** am Anfang)
    const unorderedListRegex = /^([-*])\s+(.+)$/gm;
    text = text.replace(unorderedListRegex, (match, marker, content) => {
      // Erlaube auch **Bold**: Text Format
      return `<li class="ml-4 mb-1">${content}</li>`;
    });
    
    // Nummerierte Listen: 1. Item
    const orderedListRegex = /^(\d+)\.\s+(.+)$/gm;
    text = text.replace(orderedListRegex, (match, number, content) => {
      return `<li class="ml-4 mb-1">${content}</li>`;
    });
    
    // Wrappe Listen in <ul> oder <ol>
    // Einfache Heuristik: Wenn mehrere <li> in Folge, wrappe sie
    // WICHTIG: Entferne <br /> zwischen List-Items vor dem Wrapping
    text = text.replace(/(<li[^>]*>.*?<\/li>)(\s*<br\s*\/?>\s*)(<li[^>]*>.*?<\/li>)/g, '$1$3')
    
    // Jetzt wrappe die Listen
    text = text.replace(/(<li[^>]*>.*?<\/li>(?:\s*<li[^>]*>.*?<\/li>)*)/g, (match) => {
      // Prüfe ob nummeriert (enthält Zahlen am Anfang)
      const isOrdered = /^\d+\./.test(match);
      const tag = isOrdered ? 'ol' : 'ul';
      return `<${tag} class="list-disc list-inside my-2 space-y-1">${match}</${tag}>`;
    });
    
    return text;
  };

  /**
   * Konvertiert Markdown-Überschriften zu HTML.
   * Pattern: # H1, ## H2, etc.
   * NEU v2.8.0: Unterstützt Markdown-Überschriften.
   */
  const convertMarkdownHeadings = (text: string): string => {
    // H1: #
    text = text.replace(/^#\s+(.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');
    // H2: ##
    text = text.replace(/^##\s+(.+)$/gm, '<h2 class="text-xl font-semibold mt-3 mb-2">$1</h2>');
    // H3: ###
    text = text.replace(/^###\s+(.+)$/gm, '<h3 class="text-lg font-semibold mt-2 mb-1">$1</h3>');
    // H4: ####
    text = text.replace(/^####\s+(.+)$/gm, '<h4 class="text-base font-semibold mt-2 mb-1">$1</h4>');
    
    return text;
  };

  /**
   * Konvertiert Markdown-Tabellen zu HTML-Tabellen.
   * NEU v2.8.0: Unterstützt Markdown-Tabellen für Fachartikel-Antworten.
   */
  const convertMarkdownTablesToHTML = (text: string): string => {
    // Erkenne Markdown-Tabellen (Pattern: | Spalte 1 | Spalte 2 |)
    // Tabelle beginnt mit | und hat mindestens eine Zeile mit |---| (Separator)
    const tableRegex = /(\|.+\|\n\|[-\s|]+\|\n(?:\|.+\|\n?)+)/g
    
    return text.replace(tableRegex, (match) => {
      const lines = match.trim().split('\n')
      if (lines.length < 2) return match // Keine gültige Tabelle
      
      // Erste Zeile = Header
      const headerRow = lines[0]
      const headerCells = headerRow.split('|').map(cell => cell.trim()).filter(cell => cell)
      
      // Überspringe Separator-Zeile (zweite Zeile)
      // Rest = Datenzeilen
      const dataRows = lines.slice(2).filter(line => line.trim())
      
      // Erstelle HTML-Tabelle
      let htmlTable = '<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse border border-gray-300 bg-white">'
      
      // Header
      if (headerCells.length > 0) {
        htmlTable += '<thead><tr class="bg-gray-50">'
        headerCells.forEach(cell => {
          htmlTable += `<th class="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-900">${cell}</th>`
        })
        htmlTable += '</tr></thead>'
      }
      
      // Body
      if (dataRows.length > 0) {
        htmlTable += '<tbody>'
        dataRows.forEach((row, rowIndex) => {
          const cells = row.split('|').map(cell => cell.trim()).filter(cell => cell)
          htmlTable += `<tr class="${rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`
          cells.forEach(cell => {
            htmlTable += `<td class="border border-gray-300 px-4 py-2 text-sm text-gray-700">${cell}</td>`
          })
          htmlTable += '</tr>'
        })
        htmlTable += '</tbody>'
      }
      
      htmlTable += '</table></div>'
      return htmlTable
    })
  }

  /**
   * Formatiert eine Chat-Nachricht und ersetzt Referenzen durch klickbare Links.
   * Erkennt Muster wie "**Referenz**: chunk [Nummer]" und macht sie klickbar.
   * Die Referenzen stehen direkt im Text, nicht am Ende.
   * 
   * NEU v2.8.0: Konvertiert Markdown-Tabellen zu HTML-Tabellen für bessere Darstellung.
   * NEU: Fügt chunk_id und highlight terms zu den Links hinzu für bessere UX.
   */
  const formatMessageWithLinks = (
    content: string, 
    sourceReferences: SourceReference[],
    userQuestion?: string
  ): string => {
    // NEU v2.8.0: Erweiterte Markdown-Features
    // Reihenfolge ist wichtig! Zuerst Code-Blöcke (können andere Patterns enthalten)
    let formatted = convertCodeBlocks(content)
    
    // Dann Info-Boxes (Blockquotes)
    formatted = convertInfoBoxes(formatted)
    
    // Dann Markdown-Tabellen
    formatted = convertMarkdownTablesToHTML(formatted)
    
    // Dann Listen
    formatted = convertMarkdownLists(formatted)
    
    // Dann Überschriften
    formatted = convertMarkdownHeadings(formatted)
    
    // Dann Zahlen-Highlighting (NACH anderen Formatierungen, damit HTML-Tags nicht betroffen sind)
    formatted = highlightNumbers(formatted)
    
    // WICHTIG: Entferne <br /> innerhalb von Listen (zerstört Listen-Struktur)
    formatted = formatted.replace(/(<li[^>]*>.*?)(<br\s*\/?>)(.*?<\/li>)/g, '$1$3')
    
    if (!sourceReferences || sourceReferences.length === 0) {
      // Wenn keine Referenzen, nur Zeilenumbrüche konvertieren (aber Tabellen bleiben HTML)
      // WICHTIG: Keine <br /> innerhalb von Listen, Tabellen, etc.
      formatted = formatted.replace(/\n/g, (match, offset, string) => {
        // Prüfe ob wir innerhalb einer Liste oder Tabelle sind
        const before = string.substring(0, offset)
        const after = string.substring(offset)
        
        // Wenn innerhalb von <ul>, <ol>, <table>, <thead>, <tbody>, <tr>, <td>, <th>, <li> -> kein <br />
        if (before.match(/<(ul|ol|table|thead|tbody|tr|td|th|li)[^>]*>[\s\S]*$/) && 
            after.match(/^[\s\S]*<\/(ul|ol|table|thead|tbody|tr|td|th|li)>/)) {
          return ' ' // Ersetze durch Leerzeichen statt <br />
        }
        return '<br />'
      })
      return formatted
    }

    // Debug Log entfernt - keine Console-Ausgaben mehr
    // formatted wurde bereits mit Markdown-Tabellen konvertiert

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

    // Pattern 4: Dateiname mit "Seite X" - erkenne Dateinamen aus sourceReferences und mache sie zu Links
    // Beispiel: "Loctite_Sicherheitsdatenblatt_135525_DE_DE.pdf (Seite 10)" oder "Loctite_Sicherheitsdatenblatt_135525_DE_DE (Seite 10)"
    sourceReferences.forEach((ref, index) => {
      try {
        // Escaped Titel für Regex (mit und ohne .pdf Extension)
        // WICHTIG: Escape alle Regex-Sonderzeichen, inklusive eckige Klammern
        const escapedTitle = ref.document_title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        const escapedTitleWithoutExt = escapedTitle.replace(/\.pdf$/i, '')
        
        // Pattern 4a: Dateiname mit .pdf gefolgt von "(Seite X)" oder "Seite X"
        // WICHTIG: Pattern für optionale Klammern: \\(? bedeutet optionale öffnende Klammer, \\)? bedeutet optionale schließende Klammer
        // Aber wir müssen sicherstellen, dass das Pattern korrekt ist
        const patternWithExtStr = `(${escapedTitle})\\s*(?:\\(Seite\\s*(\\d+)\\)|Seite\\s*(\\d+))`
        const patternWithExt = new RegExp(patternWithExtStr, 'gi')
        
        // Pattern 4b: Dateiname ohne .pdf gefolgt von "(Seite X)" oder "Seite X"
        const patternWithoutExtStr = `(${escapedTitleWithoutExt})\\s*(?:\\(Seite\\s*(\\d+)\\)|Seite\\s*(\\d+))`
        const patternWithoutExt = new RegExp(patternWithoutExtStr, 'gi')
        
        // WICHTIG: Prüfe zuerst ob bereits ein Link ist (wurde schon von Pattern 1-3 verarbeitet)
        const alreadyLinked = formatted.includes(`href="/documents/${ref.document_id}?page=${ref.page_number}`)
        
        if (!alreadyLinked) {
          // Pattern 4a: Mit Extension
          formatted = formatted.replace(patternWithExt, (match, title, pageNumWithParens, pageNumWithoutParens) => {
            // Prüfe ob bereits ein Link ist
            if (match.includes('<a href')) {
              return match
            }
            // Verwende pageNum aus der passenden Gruppe
            const pageNum = pageNumWithParens || pageNumWithoutParens
            if (!pageNum) return match
            
            const chunkIdParam = ref.chunk_id 
              ? `&chunk=${encodeURIComponent(String(ref.chunk_id))}` 
              : ''
            const link = `/documents/${ref.document_id}?page=${pageNum}${chunkIdParam}${highlightParam}`
            const escapedTitleForHTML = ref.document_title.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
            return `<a href="${link}" onclick="event.preventDefault(); window.location.href='${link}'; return false;" style="color: #2563eb; text-decoration: underline; font-weight: 500; cursor: pointer;">📄 ${escapedTitleForHTML} (Seite ${pageNum})</a>`
          })
          
          // Pattern 4b: Ohne Extension (nur wenn Pattern 4a nichts gefunden hat)
          formatted = formatted.replace(patternWithoutExt, (match, title, pageNumWithParens, pageNumWithoutParens) => {
            // Prüfe ob bereits ein Link ist
            if (match.includes('<a href')) {
              return match
            }
            // Verwende pageNum aus der passenden Gruppe
            const pageNum = pageNumWithParens || pageNumWithoutParens
            if (!pageNum) return match
            
            const chunkIdParam = ref.chunk_id 
              ? `&chunk=${encodeURIComponent(String(ref.chunk_id))}` 
              : ''
            const link = `/documents/${ref.document_id}?page=${pageNum}${chunkIdParam}${highlightParam}`
            const escapedTitleForHTML = ref.document_title.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
            return `<a href="${link}" onclick="event.preventDefault(); window.location.href='${link}'; return false;" style="color: #2563eb; text-decoration: underline; font-weight: 500; cursor: pointer;">📄 ${escapedTitleForHTML} (Seite ${pageNum})</a>`
          })
        }
      } catch (error) {
        // Fallback: Wenn Regex-Fehler, überspringe diese Referenz
        console.warn(`Fehler beim Erstellen des Regex-Patterns für "${ref.document_title}":`, error)
      }
    })
    
    // Ersetze Zeilenumbrüche (WICHTIG: NACH allen Replacements, sonst werden <br /> Tags in Links eingefügt)
    formatted = formatted.replace(/\n/g, '<br />')

    // Debug-Ausgaben entfernt

    return formatted
  }

  const renderSourceReference = (ref: SourceReference, index: number) => {
    // NEU: Erweiterte Metadaten für Transparenz
    const hasExtendedMetadata = ref.vector_score !== undefined || ref.text_score !== undefined
    
    return (
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
            {/* NEU: Ranking-Informationen */}
            {ref.rank_position !== undefined && ref.total_candidates !== undefined && (
              <span className="text-xs text-purple-700 bg-purple-100 px-2 py-1 rounded-full font-medium">
                Position: Rang {ref.rank_position} von {ref.total_candidates}
              </span>
            )}
          </div>
          
          {/* NEU: Score-Aufschlüsselung (Vector vs Text) */}
          {hasExtendedMetadata && (
            <div className="mt-2 flex items-center gap-3 text-xs">
              {ref.vector_score !== undefined && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-600">Vector-Score:</span>
                  <span className="font-semibold text-blue-600">
                    {Math.round(ref.vector_score * 100)}%
                  </span>
                </div>
              )}
              {ref.text_score !== undefined && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-600">Text-Score:</span>
                  <span className="font-semibold text-green-600">
                    {Math.round(ref.text_score * 100)}%
                  </span>
                </div>
              )}
              {ref.hybrid_score !== undefined && ref.hybrid_score !== ref.relevance_score && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-600">Hybrid:</span>
                  <span className="font-semibold text-purple-600">
                    {Math.round(ref.hybrid_score * 100)}%
                  </span>
                </div>
              )}
            </div>
          )}
          
          <p 
            className="text-xs text-blue-700 mt-2 line-clamp-3 leading-relaxed"
            dangerouslySetInnerHTML={{
              __html: ref.query_text 
                ? highlightQueryWords(ref.text_excerpt, ref.query_text)
                : ref.text_excerpt
            }}
          />
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
  }

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
          <button 
            onClick={() => setShowSettingsModal(true)}
            className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
            title="AI-Modell Einstellungen"
          >
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

      {/* Settings Modal - NEU v2.10.3 */}
      <RAGChatSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onSave={(settings) => {
          setAiSettings(settings)
          // Speichere in localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('rag_chat_ai_settings', JSON.stringify(settings))
          }
          toast.success('Einstellungen gespeichert')
        }}
        currentSettings={aiSettings}
      />
    </div>
  )
}