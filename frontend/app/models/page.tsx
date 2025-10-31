'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  getAvailableModels,
  testConnection,
  testModel,
  compareModels,
  testModelStream,
  evaluateResults,
  evaluateSingleModel,
  AIModel,
  TestResult,
  ConnectionTest,
  ModelConfig,
  StreamingChunk,
  EvaluationRequest,
  SingleEvaluationRequest,
  EvaluationResult
} from '@/lib/api/aiPlayground'
import { createPromptTemplateFromPlayground, getPromptTemplate } from '@/lib/api/promptTemplates'
import { getDocumentTypes, DocumentType } from '@/lib/api/documentTypes'

function AIPlaygroundPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [models, setModels] = useState<AIModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [compareModelIds, setCompareModelIds] = useState<string[]>([])
  const [prompt, setPrompt] = useState('')
  const [config, setConfig] = useState<ModelConfig>({
    temperature: 0.0,
    max_tokens: 16384,
    top_p: 1.0,
    detail_level: 'high'  // Default: High Detail für QMS-Qualität
  })
  
  // Save as Template State
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [saveTemplateData, setSaveTemplateData] = useState<{result: TestResult, aiModel: string} | null>(null)
  const [templateName, setTemplateName] = useState('')
  const [templateDescription, setTemplateDescription] = useState('')
  const [templateDocType, setTemplateDocType] = useState<number | null>(null)
  const [templateVersion, setTemplateVersion] = useState('v1.0.0')
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  
  // Image Upload State
  const [uploadedImage, setUploadedImage] = useState<string | null>(null) // Base64
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageFilename, setImageFilename] = useState<string | null>(null)
  const [originalFile, setOriginalFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [loading, setLoading] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [compareResults, setCompareResults] = useState<TestResult[]>([])
  const [connectionTests, setConnectionTests] = useState<Record<string, ConnectionTest>>({})
  
  // Streaming State
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingModel, setStreamingModel] = useState<string>('')
  const [streamingStartTime, setStreamingStartTime] = useState<number>(0)
  const [streamingProgress, setStreamingProgress] = useState<string>('')
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [mode, setMode] = useState<'single' | 'compare'>('single')
  
  // Evaluation State
  const [showEvaluationModal, setShowEvaluationModal] = useState(false)
  const [evaluationResults, setEvaluationResults] = useState<EvaluationResult[]>([])
  const [evaluationLoading, setEvaluationLoading] = useState(false)
  
  // Neue State für Schritt-für-Schritt Evaluation
  const [evaluationStep, setEvaluationStep] = useState<'none' | 'first' | 'second' | 'complete'>('none')
  const [firstEvaluation, setFirstEvaluation] = useState<EvaluationResult | null>(null)
  const [secondEvaluation, setSecondEvaluation] = useState<EvaluationResult | null>(null)
  const [evaluatorPrompt, setEvaluatorPrompt] = useState(`Du bist ein Senior Quality Auditor für KI-generierte Arbeitsanweisungen mit 15 Jahren Erfahrung in der technischen Dokumentation.

═══════════════════════════════════════════════════════════════
🎯 AUFGABE: DETAILLIERTE QUALITÄTSBEWERTUNG EINER JSON-ARBEITSANWEISUNG
═══════════════════════════════════════════════════════════════

Bewerte die Qualität einer JSON-Arbeitsanweisung nach 10 präzisen Kriterien mit strengen Maßstäben.

═══════════════════════════════════════════════════════════════
📊 BEWERTUNGSKRITERIEN (je 0-10 Punkte):
═══════════════════════════════════════════════════════════════

1️⃣ STRUKTURKONFORMITÄT (structure) - GEWICHT: 10%
✅ Prüfe:
   • Sind ALLE Hauptfelder vorhanden? (document_metadata, process_overview, steps, critical_rules, definitions, mini_flowchart_mermaid)
   • Korrekte JSON-Syntax und Typisierung?
   • Keine leeren Pflichtfelder?
❌ Abzüge:
   • -3 Punkte: Ein Hauptfeld fehlt komplett
   • -2 Punkte: Hauptfeld vorhanden aber leer
   • -1 Punkt: Falsche Typisierung (String statt Array, etc.)

2️⃣ VOLLSTÄNDIGKEIT DER SCHRITTE (steps_completeness) - GEWICHT: 15%
✅ Prüfe:
   • Alle Arbeitsschritte aus dem Originaldokument erfasst?
   • Korrekte Nummerierung und logische Reihenfolge?
   • Keine fehlenden Zwischenschritte?
❌ Abzüge:
   • -2 Punkte: Pro fehlendem Arbeitsschritt
   • -1 Punkt: Schritte in falscher Reihenfolge
   • -1 Punkt: Fehlende oder falsche Nummerierung

3️⃣ ARTIKEL- UND MATERIALDATEN (articles_materials) - GEWICHT: 15%
✅ Prüfe:
   • Alle Komponenten mit vollständigen Bezeichnungen?
   • Artikelnummern korrekt und vollständig?
   • Mengenangaben präzise und im Originalformat?
❌ Abzüge:
   • -2 Punkte: Fehlende Artikelnummer
   • -1 Punkt: Falsche oder ungenaue Mengenangabe
   • -1 Punkt: Fehlende Komponente

4️⃣ CHEMIKALIEN / VERBRAUCHSMATERIALIEN (consumables) - GEWICHT: 10%
✅ Prüfe:
   • Alle Klebstoffe, Reinigungsmittel, Schmierstoffe erfasst?
   • Anwendungskontext detailliert beschrieben?
   • Sicherheitsrelevante Hinweise enthalten?
❌ Abzüge:
   • -3 Punkte: Chemikalie fehlt komplett
   • -2 Punkte: Anwendungskontext nicht beschrieben
   • -1 Punkt: Unvollständige Spezifikation

5️⃣ WERKZEUGE / HILFSMITTEL (tools) - GEWICHT: 8%
✅ Prüfe:
   • Alle erkennbaren Werkzeuge und PSA-Elemente aufgelistet?
   • Logische Zuordnung zu Arbeitsschritten?
   • Spezifische Werkzeugbezeichnungen (nicht nur "Werkzeug")?
❌ Abzüge:
   • -2 Punkte: Erkennbares Werkzeug fehlt
   • -1 Punkt: Nur generische Bezeichnung ("Werkzeug" statt "Drehmomentschlüssel")
   • -1 Punkt: Falsche Zuordnung zu Arbeitsschritt

6️⃣ SICHERHEITSANGABEN (safety) - GEWICHT: 12%
✅ Prüfe:
   • Alle Sicherheitshinweise und Warnungen enthalten?
   • Präzise Formulierungen (z.B. "Handschuhe" vs "PSA tragen")?
   • Korrekte Zuordnung zu gefährlichen Schritten?
❌ Abzüge:
   • -3 Punkte: Kritischer Sicherheitshinweis fehlt
   • -2 Punkte: Ungenaue Formulierung
   • -1 Punkt: Falsche Zuordnung zu Schritt

7️⃣ VISUELLE BESCHREIBUNG (visuals) - GEWICHT: 10%
✅ Prüfe:
   • Alle Bilder, Markierungen (a, b, c) und Farben beschrieben?
   • Räumliche Orientierung klar (links, rechts, oben, unten)?
   • Details wie Pfeile, Zahlen, Kreise erklärt?
❌ Abzüge:
   • -2 Punkte: Bild fehlt oder keine Beschreibung
   • -1 Punkt: Markierungen nicht erklärt
   • -1 Punkt: Räumliche Orientierung fehlt

8️⃣ QUALITÄTS- UND PRÜFVORGABEN (quality_rules) - GEWICHT: 12%
✅ Prüfe:
   • Alle Prüfschritte und Montagekontrollen als critical_rules abgebildet?
   • Verknüpfung mit korrektem Arbeitsschritt (linked_step)?
   • Begründung (reason) für jede Regel vorhanden?
❌ Abzüge:
   • -3 Punkte: critical_rules-Feld komplett leer
   • -2 Punkte: Prüfschritt fehlt
   • -1 Punkt: Fehlende Begründung oder Verknüpfung

9️⃣ TEXTGENAUIGKEIT UND KONTEXTREUE (text_accuracy) - GEWICHT: 10%
✅ Prüfe:
   • Formulierungen entsprechen Originaldokument?
   • Keine erfundenen oder fehlinterpretierten Inhalte?
   • Fachbegriffe korrekt übernommen?
❌ Abzüge:
   • -3 Punkte: Erfundene Inhalte
   • -2 Punkte: Fehlinterpretation von Anweisungen
   • -1 Punkt: Ungenaue Formulierungen

🔟 RAG-TAUGLICHKEIT / TECHNISCHE KONSISTENZ (rag_ready) - GEWICHT: 8%
✅ Prüfe:
   • Eindeutige Schlüssel ohne Duplikate?
   • Konsistente Struktur über alle Schritte?
   • Maschinell lesbar und ohne syntaktische Fehler?
❌ Abzüge:
   • -2 Punkte: Inkonsistente Struktur
   • -1 Punkt: Ungünstige Schlüsselbenennungen
   • -1 Punkt: Fehlende Verknüpfungen (next_step_number, etc.)

═══════════════════════════════════════════════════════════════
🎯 BEWERTUNGSSKALA:
═══════════════════════════════════════════════════════════════
0-3 = Schwach/Fehlerhaft (nicht verwendbar)
4-5 = Unzureichend (erhebliche Mängel)
6-7 = Akzeptabel (nutzbar mit Überarbeitung)
8-9 = Gut (produktionsreif mit kleinen Anpassungen)
10  = Exzellent (perfekte Qualität, sofort verwendbar)

═══════════════════════════════════════════════════════════════
📤 AUSGABEFORMAT (NUR JSON, KEINE ZUSÄTZLICHEN TEXTE):
═══════════════════════════════════════════════════════════════

{
  "overall_score": 7.8,
  "category_scores": {
    "structure": 9,
    "steps_completeness": 8,
    "articles_materials": 9,
    "consumables": 7,
    "tools": 6,
    "safety": 9,
    "visuals": 8,
    "quality_rules": 5,
    "text_accuracy": 9,
    "rag_ready": 8
  },
  "strengths": [
    "✅ Strukturkonformität: Alle Hauptfelder vorhanden, perfekte JSON-Syntax",
    "✅ Materialdaten: Artikelnummern vollständig (z.B. 26-10-204), Mengen präzise (4x, 1x)",
    "✅ Sicherheitsangaben: Alle Warnungen erfasst (Aceton: Fenster, Abzug, Handschuhe)",
    "✅ Textgenauigkeit: Formulierungen exakt aus Dokument übernommen"
  ],
  "weaknesses": [
    "❌ critical_rules: Feld komplett leer! Keine Prüfschritte definiert (-5 Punkte)",
    "❌ definitions: Feld leer! Keine Fachbegriffe erklärt (-2 Punkte)",
    "⚠️ Werkzeuge: Nur generische Bezeichnungen ('Werkzeug') statt spezifischer Namen",
    "⚠️ Consumables: Anwendungskontext bei Loctite 648 unvollständig beschrieben"
  ],
  "summary": "Solide Basis mit guter Strukturkonformität und präzisen Materialdaten. KRITISCH: Fehlende critical_rules und definitions reduzieren Produktionsreife erheblich. Werkzeugbeschreibungen zu unspezifisch. Nach Ergänzung der fehlenden Felder und Detaillierung der Werkzeuge 8.5-9.0 Punkte erreichbar."
}

═══════════════════════════════════════════════════════════════
⚠️ WICHTIGE REGELN:
═══════════════════════════════════════════════════════════════
1. Bewerte NUR auf Basis der vorliegenden JSON-Daten
2. Erfinde KEINE Informationen
3. Gib KONKRETE Beispiele in strengths/weaknesses (z.B. Artikelnummer, Feldname)
4. overall_score = gewichteter Durchschnitt aller category_scores
5. Mindestens 3 strengths und 3 weaknesses
6. summary: Max. 2-3 Sätze mit klarer Handlungsempfehlung
7. Nutze Emojis (✅❌⚠️) für bessere Lesbarkeit

═══════════════════════════════════════════════════════════════
🚀 QUALITÄTSSTUFEN FÜR GESAMTBEWERTUNG:
═══════════════════════════════════════════════════════════════
9.0-10.0 = 🏆 Excellence - Sofort produktionsreif
8.0-8.9  = ⭐ Professional - Kleine Anpassungen empfohlen
7.0-7.9  = ✅ Good - Nutzbar, aber Überarbeitung nötig
6.0-6.9  = ⚠️ Acceptable - Erhebliche Mängel, nicht produktionsreif
0.0-5.9  = ❌ Poor - Nicht verwendbar, Neuerstellung empfohlen`)
  const [selectedEvaluatorModel, setSelectedEvaluatorModel] = useState<string | null>(null)
  
  // Get selected model object
  const selectedModelObj = models.find(m => m.id === selectedModel)
  
  // Dynamic max tokens based on selected model(s)
  const maxTokensLimit = mode === 'single'
    ? selectedModelObj?.max_tokens_supported || 4000
    : compareModelIds.length > 0
      ? Math.min(...compareModelIds.map(id => models.find(m => m.id === id)?.max_tokens_supported || 4000))
      : 4000
  
  // Load models and document types on mount
  useEffect(() => {
    loadModels()
    loadDocumentTypes()
  }, [])
  
  // Load template if template_id is in query params
  useEffect(() => {
    const templateId = searchParams.get('template_id')
    if (templateId) {
      loadTemplate(parseInt(templateId))
    }
  }, [searchParams])
  
  const loadDocumentTypes = async () => {
    try {
      const types = await getDocumentTypes()
      setDocumentTypes(types)
    } catch (error) {
      console.error('Failed to load document types:', error)
    }
  }
  
  const loadTemplate = async (templateId: number) => {
    try {
      const template = await getPromptTemplate(templateId)
      
      // Set all form fields from template
      setPrompt(template.prompt_text)
      setSelectedModel(template.ai_model)
      setConfig({
        temperature: template.temperature,
        max_tokens: template.max_tokens,
        top_p: template.top_p,
        detail_level: template.detail_level
      })
      setTemplateDocType(template.document_type_id)
      
      console.log('✅ Template geladen:', template.name)
    } catch (error: any) {
      console.error('Failed to load template:', error)
      alert(`Fehler beim Laden des Templates: ${error.response?.data?.detail || error.message}`)
    }
  }
  
  // Update max_tokens when model changes (set to model's max) or when switching modes
  useEffect(() => {
    setConfig(prev => ({ ...prev, max_tokens: Math.min(prev.max_tokens || 1000, maxTokensLimit) }))
  }, [maxTokensLimit, mode])
  
  const loadModels = async () => {
    try {
      const data = await getAvailableModels()
      setModels(data || [])
      
      // Auto-select first configured model
      const firstConfigured = data?.find(m => m.is_configured)
      if (firstConfigured) {
        setSelectedModel(firstConfigured.id)
      }
    } catch (error: any) {
      console.error('Failed to load models:', error)
      setModels([])
      if (error.response?.status === 403) {
        alert('Zugriff verweigert. Nur QMS Admin hat Zugang zum AI Playground.')
      } else {
        alert('Fehler beim Laden der Modelle. Bitte später erneut versuchen.')
      }
    }
  }
  
  const handleTestConnection = async (modelId: string) => {
    try {
      const result = await testConnection(modelId)
      setConnectionTests(prev => ({ ...prev, [modelId]: result }))
    } catch (error) {
      console.error('Connection test failed:', error)
    }
  }
  
  const processFile = async (file: File) => {
    setUploadLoading(true)
    
    try {
      // Validiere Dateiformat
      const fileExtension = file.name.toLowerCase().split('.').pop()
      const validImageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
      const validPdfTypes = ['application/pdf', 'application/x-pdf']
      const validExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf']
      
      // Prüfe nach MIME-Type ODER Dateierweiterung
      const isImage = validImageTypes.includes(file.type)
      const isPdfByMime = validPdfTypes.includes(file.type) || file.type?.includes('pdf')
      const isPdfByExtension = fileExtension === 'pdf'
      const isValidExtension = validExtensions.includes(fileExtension || '')
      
      // Akzeptiere wenn: gültiges Bild ODER PDF (per MIME oder Extension) ODER gültige Extension
      const isValidFile = isImage || isPdfByMime || isPdfByExtension || isValidExtension
      
      if (!isValidFile) {
        console.error('File validation failed:', { 
          fileName: file.name, 
          fileType: file.type, 
          fileExtension,
          isImage,
          isPdfByMime,
          isPdfByExtension,
          isValidExtension
        })
        alert(`Ungültiger Dateityp: ${file.type || 'unbekannt'}. Erlaubt: JPG, PNG, GIF, WEBP, PDF`)
        setUploadLoading(false)
        return
      }
      
      // Validiere Dateigröße (max 10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        alert(`Datei zu groß: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maximum: 10MB`)
        setUploadLoading(false)
        return
      }
      
      // Store original file for API calls
      setOriginalFile(file)
      
      // Convert file to base64 and create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        const base64 = e.target?.result as string
        
        // Für PDF: Kein Bild-Preview, aber trotzdem Base64 für API
        const fileExtension = file.name.toLowerCase().split('.').pop()
        const isPdf = file.type.includes('pdf') || fileExtension === 'pdf'
        
        if (isPdf) {
          setUploadedImage(base64.split(',')[1]) // Remove data:application/pdf;base64, prefix
          setImagePreview(null) // Kein Preview für PDF
          setImageFilename(file.name)
          console.log('PDF-Datei erkannt:', file.name, 'Type:', file.type)
        } else {
          // Für Bilder: Normaler Preview
          setUploadedImage(base64.split(',')[1]) // Remove data:image/jpeg;base64, prefix
          setImagePreview(base64) // Use full base64 for preview
          setImageFilename(file.name)
          console.log('Bild-Datei erkannt:', file.name, 'Type:', file.type)
        }
      }
      reader.readAsDataURL(file)
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(`Upload fehlgeschlagen: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploadLoading(false)
    }
  }
  
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    await processFile(file)
  }
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }
  
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }
  
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }
  
  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const file = files[0]
      await processFile(file)
    }
  }
  
  const handleRemoveImage = () => {
    setUploadedImage(null)
    setImagePreview(null)
    setImageFilename(null)
    setOriginalFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }
  
  const handleTestModel = async () => {
    if (!selectedModel || !prompt.trim()) {
      alert('Bitte Modell und Prompt auswählen')
      return
    }
    
    setLoading(true)
    setTestResult(null)
    setStreamingProgress('🔄 Verbinde mit Model...')
    
    try {
      // Show progress for slower models
      const currentModel = selectedModel.toLowerCase()
      const isSlowModel = currentModel.includes('gpt-5') || currentModel.includes('gemini')
      
      let progressInterval: NodeJS.Timeout | null = null
      if (isSlowModel) {
        let dots = 0
        progressInterval = setInterval(() => {
          dots = (dots + 1) % 4
          const dotString = '.'.repeat(dots)
          setStreamingProgress(`⏳ Model verarbeitet Anfrage${dotString}`)
        }, 500)
      }
      
      const result = await testModel(
        selectedModel,
        prompt,
        config,
        originalFile || undefined
      )
      
      if (progressInterval) clearInterval(progressInterval)
      setStreamingProgress('')
      setTestResult(result)
      
      console.log('✅ Test Result:', result) // Debug: Full result object
      console.log('✅ verified_model_id:', result.verified_model_id) // Debug
    } catch (error: any) {
      console.error('Test failed:', error)
      const errorMsg = error.response?.data?.detail 
        || error.message 
        || JSON.stringify(error)
        || 'Unbekannter Fehler'
      alert(`Test fehlgeschlagen: ${errorMsg}`)
    } finally {
      setLoading(false)
      setStreamingProgress('')
    }
  }
  
  const handleTestModelStream = async () => {
    if (!selectedModel || !prompt.trim()) {
      alert('Bitte Modell und Prompt auswählen')
      return
    }
    
    // Reset state BEFORE starting
    setTestResult(null)
    setCompareResults([])
    setIsStreaming(true)
    setStreamingContent('')
    setStreamingProgress('🔄 Verbinde mit Model...')
    
    // Create AbortController for cancellation
    const controller = new AbortController()
    setAbortController(controller)
    
    // Capture current values to avoid stale closure
    const currentModel = selectedModel
    const currentPrompt = prompt
    const currentModelObj = models.find(m => m.id === currentModel)
    const startTime = Date.now()
    
    let accumulatedContent = ''
    let chunkCount = 0
    
    // Progress indicator ONLY for non-streaming models (GPT-5, Gemini)
    let progressInterval: NodeJS.Timeout | null = null
    const isNonStreamingModel = currentModel.includes('gpt-5') || currentModel.includes('gemini')
    
    if (isNonStreamingModel) {
      let dots = 0
      progressInterval = setInterval(() => {
        dots = (dots + 1) % 4
        const dotString = '.'.repeat(dots)
        setStreamingProgress(`⏳ Model verarbeitet Anfrage${dotString}`)
      }, 500)
    }
    
    try {
      await testModelStream(
        currentModel,
        currentPrompt,
        config,
        originalFile || undefined,
        (chunk: StreamingChunk) => {
          chunkCount++
          accumulatedContent += chunk.content
          setStreamingContent(accumulatedContent)
          
          // Only show progress for non-streaming models
          if (isNonStreamingModel) {
            setStreamingProgress(`📥 Empfange Antwort... (${accumulatedContent.length} Zeichen)`)
          }
          // GPT-4o Mini: no progress indicator needed, live content is visible
        },
        () => {
          if (progressInterval) clearInterval(progressInterval)
          setIsStreaming(false)
          setStreamingProgress('')
          setAbortController(null)
          const endTime = Date.now()
          
          // Convert streaming result to TestResult format
          const result: TestResult = {
            model_name: currentModel,
            provider: currentModelObj?.provider || 'unknown',
            prompt: currentPrompt,
            response: accumulatedContent,
            tokens_sent: Math.ceil(currentPrompt.length / 4),
            tokens_received: Math.ceil(accumulatedContent.length / 4),
            total_tokens: Math.ceil((currentPrompt.length + accumulatedContent.length) / 4),
            response_time: (endTime - startTime) / 1000,
            response_time_ms: endTime - startTime,
            success: true
          }
          setTestResult(result)
        },
        (error: string) => {
          if (progressInterval) clearInterval(progressInterval)
          setIsStreaming(false)
          setStreamingContent('')
          setStreamingProgress('')
          setAbortController(null)
          if (!error.includes('aborted')) {
            alert(`Streaming fehlgeschlagen: ${error}`)
          }
        }
      )
    } catch (error: any) {
      if (progressInterval) clearInterval(progressInterval)
      setIsStreaming(false)
      setStreamingContent('')
      setStreamingProgress('')
      setAbortController(null)
      console.error('Streaming failed:', error)
      if (!error.message?.includes('aborted')) {
        alert(`Streaming fehlgeschlagen: ${error.message}`)
      }
    }
  }
  
  const handleAbortStreaming = () => {
    if (abortController) {
      abortController.abort()
      setIsStreaming(false)
      setStreamingContent('')
      setStreamingProgress('')
      setAbortController(null)
      alert('Streaming abgebrochen')
    }
  }
  
  const handleCompareModels = async () => {
    if (compareModelIds.length < 2 || !prompt.trim()) {
      alert('Bitte mindestens 2 Modelle und einen Prompt auswählen')
      return
    }
    
    setLoading(true)
    setCompareResults([])
    setStreamingProgress('🔄 Vergleiche Modelle...')
    
    try {
      // Show progress during comparison
      let dots = 0
      const progressInterval = setInterval(() => {
        dots = (dots + 1) % 4
        const dotString = '.'.repeat(dots)
        setStreamingProgress(`⏳ ${compareModelIds.length} Modelle werden getestet${dotString}`)
      }, 500)
      
      const results = await compareModels(
        compareModelIds,
        prompt,
        config,
        originalFile || undefined
      )
      
      clearInterval(progressInterval)
      setStreamingProgress('')
      setCompareResults(results)
      
      console.log('✅ Comparison Results (Full):', results) // Debug: Full results
      console.log('✅ Verified Models:', results.map(r => ({ model: r.model_name, verified: r.verified_model_id }))) // Debug
    } catch (error: any) {
      console.error('Comparison failed:', error)
      const errorMsg = error.response?.data?.detail 
        || error.message 
        || JSON.stringify(error)
        || 'Unbekannter Fehler'
      alert(`Vergleich fehlgeschlagen: ${errorMsg}`)
    } finally {
    setLoading(false)
      setStreamingProgress('')
    }
  }
  
  const handleSaveAsTemplate = (result: TestResult, aiModel: string) => {
    setSaveTemplateData({ result, aiModel })
    setTemplateName(`${result.model_name} - ${new Date().toLocaleDateString('de-DE')}`)
    setTemplateDescription('')
    setTemplateDocType(null)
    setTemplateVersion('v1.0.0')
    setShowSaveModal(true)
  }
  
  const handleSaveTemplate = async () => {
    if (!saveTemplateData || !templateName.trim()) {
      alert('Bitte Template-Name eingeben')
      return
    }
    
    if (!templateDocType) {
      alert('Bitte einen Dokumenttyp auswählen')
      return
    }
    
    try {
      const { result, aiModel } = saveTemplateData
      
      // Use selected version
      const version = templateVersion
      
      await createPromptTemplateFromPlayground({
        name: templateName,
        prompt_text: prompt,
        ai_model: aiModel,
        temperature: (config.temperature || 0.5) / 100, // Convert from 0-100 to 0-1
        max_tokens: config.max_tokens || 1000,
        top_p: (config.top_p || 50) / 100, // Convert from 0-100 to 0-1
        detail_level: config.detail_level || 'low',
        tokens_sent: result.tokens_sent,
        tokens_received: result.tokens_received,
        response_time_ms: result.response_time_ms,
        description: templateDescription || `Prompt Template erstellt am ${new Date().toLocaleString('de-DE')}`,
        document_type_id: templateDocType,
        example_output: result.response,
        // version: version  // Wird automatisch generiert
      })
      
      alert('✅ Template erfolgreich gespeichert!')
      setShowSaveModal(false)
      setSaveTemplateData(null)
      router.push('/prompt-management')
    } catch (error: any) {
      console.error('Failed to save template:', error)
      const errorMsg = error.response?.data?.detail 
        || error.message 
        || JSON.stringify(error)
        || 'Unbekannter Fehler'
      alert(`Fehler beim Speichern: ${errorMsg}`)
    }
  }
  
  const toggleCompareModel = (modelId: string) => {
    setCompareModelIds(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    )
  }
  
  // Format JSON response with syntax highlighting
  const formatResponse = (response: string) => {
    try {
      // Try to parse as JSON
      const parsed = JSON.parse(response)
    return (
        <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
          <code className="language-json">{JSON.stringify(parsed, null, 2)}</code>
        </pre>
      )
    } catch {
      // Not JSON, show as plain text
      return (
        <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap text-sm">
          {response}
      </div>
    )
    }
  }
  
  // Evaluation Functions
  const handleStartEvaluation = () => {
    if (compareResults.length < 2) {
      alert('Bitte erst einen Comparison Test durchführen')
      return
    }
    
    // Reset selection states
    setSelectedEvaluatorModel(null)
    
    setShowEvaluationModal(true)
  }
  
  const handleRunEvaluation = async () => {
    if (!selectedEvaluatorModel || !evaluatorPrompt.trim()) {
      return
    }
    
    // Reset für neue Evaluation
    setEvaluationStep('none')
    setFirstEvaluation(null)
    setSecondEvaluation(null)
    setEvaluationResults([])
    setShowEvaluationModal(false)
  }

  const handleEvaluateFirstModel = async () => {
    if (!selectedEvaluatorModel || compareResults.length === 0) {
      alert('Bitte Evaluator-Modell auswählen und Vergleichsergebnisse vorhanden')
      return
    }

    setEvaluationLoading(true)
    try {
      const request: SingleEvaluationRequest = {
        test_result: compareResults[0],
        evaluator_prompt: evaluatorPrompt,
        evaluator_model_id: selectedEvaluatorModel
      }

      console.log('Evaluating first model:', request.test_result.model_name)
      console.log('First model response (first 500 chars):', request.test_result.response.substring(0, 500))
      const result = await evaluateSingleModel(request)
      console.log('First evaluation result:', result)
      
      setFirstEvaluation(result)
      setEvaluationStep('first')
    } catch (error) {
      console.error('First evaluation error:', error)
      alert(`Evaluation des ersten Modells fehlgeschlagen: ${error}`)
    } finally {
      setEvaluationLoading(false)
    }
  }

  const handleEvaluateSecondModel = async () => {
    if (!selectedEvaluatorModel || compareResults.length < 2) {
      alert('Bitte Evaluator-Modell auswählen und mindestens 2 Vergleichsergebnisse vorhanden')
      return
    }

    setEvaluationLoading(true)
    try {
      const request: SingleEvaluationRequest = {
        test_result: compareResults[1],
        evaluator_prompt: evaluatorPrompt,
        evaluator_model_id: selectedEvaluatorModel
      }

      console.log('Evaluating second model:', request.test_result.model_name)
      console.log('Second model response (first 500 chars):', request.test_result.response.substring(0, 500))
      const result = await evaluateSingleModel(request)
      console.log('Second evaluation result:', result)
      
      setSecondEvaluation(result)
      setEvaluationStep('complete')
      
      // Setze auch die alten evaluationResults für Kompatibilität
      setEvaluationResults([firstEvaluation!, result])
    } catch (error) {
      console.error('Second evaluation error:', error)
      alert(`Evaluation des zweiten Modells fehlgeschlagen: ${error}`)
    } finally {
      setEvaluationLoading(false)
    }
  }
  
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50'
    if (score >= 80) return 'text-blue-600 bg-blue-50'
    if (score >= 70) return 'text-yellow-600 bg-yellow-50'
    if (score >= 60) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }
  
  const getScoreStars = (score: number) => {
    const stars = Math.floor(score / 20)
    return '⭐'.repeat(stars) + '☆'.repeat(5 - stars)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">AI Playground</h1>
        <p className="text-muted-foreground">
          Teste AI-Modelle, prüfe Verbindungen und vergleiche Responses
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setMode('single')}
          className={`px-6 py-2 rounded-lg font-medium transition-colors ${
            mode === 'single'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Single Model Test
        </button>
        <button
          onClick={() => setMode('compare')}
          className={`px-6 py-2 rounded-lg font-medium transition-colors ${
            mode === 'compare'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Model Comparison
        </button>
            </div>
            
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Models & Config */}
        <div className="lg:col-span-1">
          {/* Available Models */}
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">Available Models</h2>
            <div className="space-y-3">
              {models && models.length > 0 ? (
                models.map(model => (
                  <div
                    key={model.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      mode === 'single'
                        ? selectedModel === model.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                        : compareModelIds.includes(model.id)
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                    onClick={() =>
                      mode === 'single'
                        ? setSelectedModel(model.id)
                        : toggleCompareModel(model.id)
                    }
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-sm">{model.name}</h3>
                        <p className="text-xs text-gray-600 mt-1">{model.provider}</p>
                        {/* Model ID Badge */}
                        {model.model_id && (
                          <div className="mt-1">
                            <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded border border-blue-200 font-mono">
                              {model.model_id}
                            </span>
              </div>
                        )}
                        <p className="text-xs text-gray-500 mt-1">{model.description}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Max: {model.max_tokens_supported.toLocaleString()} tokens
                        </p>
              </div>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          model.is_configured
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {model.is_configured ? '✓' : '✗'}
                      </span>
              </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-gray-500">No models available</div>
              )}
              </div>
            </div>

          {/* Configuration */}
          <div className="border rounded-lg p-6 bg-white mt-6">
            <h3 className="text-lg font-semibold mb-4">Configuration</h3>
            <div className="space-y-4">
                <div>
                <label className="block text-sm font-medium mb-1 flex items-center gap-2">
                  Temperature: {config.temperature}
                  <div className="group relative inline-block">
                    <span className="text-gray-400 cursor-help text-sm">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs text-white bg-gray-900 rounded-lg shadow-lg -top-2 left-6">
                      Steuert die Zufälligkeit der Antworten. 0 = präzise und vorhersehbar, 2 = kreativ und variabel. Bei technischen Aufgaben niedrig (0-0.3), bei kreativen Texten höher (0.7-1.0).
                      <div className="absolute top-2 -left-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
                  </div>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={e =>
                    setConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  0 = präzise & faktisch, 2 = kreativ & variabel
                </p>
              </div>

                <div>
                <label className="block text-sm font-medium mb-1 flex items-center gap-2">
                  Max Tokens: {(config.max_tokens || 1000).toLocaleString('de-DE')}
                  <div className="group relative inline-block">
                    <span className="text-gray-400 cursor-help text-sm">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs text-white bg-gray-900 rounded-lg shadow-lg -top-2 left-6">
                      Maximale Länge der Antwort in Tokens (1 Token ≈ 0.75 Wörter). Begrenzt die Kosten und Response-Länge. Bei kurzen Antworten niedriger setzen, bei langen Dokumenten höher.
                      <div className="absolute top-2 -left-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
                  </div>
                </label>
                <input
                  type="range"
                  min="100"
                  max={maxTokensLimit}
                  step="100"
                  value={config.max_tokens}
                  onChange={e =>
                    setConfig(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Limit: {maxTokensLimit.toLocaleString('de-DE')} tokens
                  {mode === 'single' && selectedModelObj && ` (${selectedModelObj.name})`}
                  {mode === 'compare' && compareModelIds.length > 0 && ` (kleinste Limit der ausgewählten Modelle)`}
                </p>
              </div>

                <div>
                <label className="block text-sm font-medium mb-1 flex items-center gap-2">
                  Top P: {config.top_p}
                  <div className="group relative inline-block">
                    <span className="text-gray-400 cursor-help text-sm">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-80 p-2 text-xs text-white bg-gray-900 rounded-lg shadow-lg -top-2 left-6">
                      <strong>Nucleus Sampling</strong> - begrenzt die Wortauswahl auf die wahrscheinlichsten. 1.0 = alle Wörter möglich (kreativ), 0.9 = nur die Top 90% (ausgewogen), 0.5 = sehr fokussiert. 
                      <br/><br/>
                      <em>Beispiel:</em> Bei "Der Himmel ist ___" würde 0.5 nur "blau" zulassen, 1.0 auch "lila" oder "quadratisch".
                      <div className="absolute top-2 -left-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
              </div>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.top_p}
                  onChange={e => setConfig(prev => ({ ...prev, top_p: parseFloat(e.target.value) }))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Nucleus Sampling: 1.0 = kreativ, 0.9 = ausgewogen, 0.5 = fokussiert
                </p>
            </div>

              {/* Detail Level Toggle */}
              {uploadedImage && (
                <div className="pt-4 border-t">
                  <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                    🔍 Bilderkennung Detail-Level
                    <div className="group relative inline-block">
                      <span className="text-gray-400 cursor-help text-sm">ℹ️</span>
                      <div className="invisible group-hover:visible absolute z-10 w-80 p-2 text-xs text-white bg-gray-900 rounded-lg shadow-lg -top-2 left-6">
                        <strong>High Detail:</strong> Beste Qualität, mehr Tokens, langsamer. Für QMS-Dokumente empfohlen!
                        <br/><br/>
                        <strong>Low Detail:</strong> Schneller, weniger Tokens (~90% günstiger), aber Details können verloren gehen.
                        <div className="absolute top-2 -left-1 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                      </div>
                    </div>
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfig(prev => ({ ...prev, detail_level: 'high' }))}
                      className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                        config.detail_level === 'high'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      🎯 High Detail
                    </button>
                    <button
                      onClick={() => setConfig(prev => ({ ...prev, detail_level: 'low' }))}
                      className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                        config.detail_level === 'low'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      ⚡ Low Detail (Fast)
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {config.detail_level === 'high' 
                      ? '✅ Empfohlen für auditierbare QMS-Dokumente' 
                      : '⚠️ Nur für schnelle Tests - Details können fehlen'}
                  </p>
              </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Prompt & Results */}
        <div className="lg:col-span-2">
          {/* Image Upload */}
          <div className="border rounded-lg p-6 bg-white mb-6">
            <h2 className="text-xl font-semibold mb-4">📎 Image/Dokument Upload (Optional)</h2>
            <div className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,image/png,image/jpeg,image/jpg,image/gif,image/webp,application/pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!imagePreview && !imageFilename ? (
                <div
                  onClick={() => !uploadLoading && fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`w-full px-4 py-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 transition-colors cursor-pointer ${
                    uploadLoading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {uploadLoading ? (
                    <div className="text-center">
                      <span className="text-2xl mb-2 block">⏳</span>
                      <span className="text-sm text-gray-600">Uploading...</span>
                    </div>
                  ) : (
                    <div className="text-center">
                      <span className="text-4xl mb-2 block">📁</span>
                      <span className="text-sm text-gray-600 block">
                        Click to upload or drag & drop
                      </span>
                      <span className="text-xs text-gray-400 block mt-1">
                        Bilder (PNG, JPG, GIF, WEBP) oder PDF (max 10MB)
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="relative border rounded-lg p-4 bg-white">
                  {imagePreview ? (
                    <>
                      <img
                        src={imagePreview}
                        alt="Preview"
                        className="max-h-64 mx-auto rounded-lg border"
                      />
                      <p className="text-sm text-gray-600 mt-2 text-center">{imageFilename}</p>
                    </>
                  ) : imageFilename ? (
                    // PDF-Dokument: Zeige Datei-Info statt Preview
                    <div className="max-h-64 mx-auto rounded-lg border bg-gray-50 p-8 flex flex-col items-center justify-center">
                      <span className="text-6xl mb-4">📄</span>
                      <p className="text-sm font-medium text-gray-700 break-all text-center">{imageFilename}</p>
                      <p className="text-xs text-gray-500 mt-1">PDF-Dokument (kein Preview verfügbar)</p>
                    </div>
                  ) : null}
                  <button
                    onClick={handleRemoveImage}
                    className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-lg hover:bg-red-600 z-10"
                  >
                    ✕ Remove
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Prompt */}
          <div className="border rounded-lg p-6 bg-white mb-6">
            <h2 className="text-xl font-semibold mb-4">Prompt</h2>
            <textarea
              placeholder="Enter your prompt here... (e.g., 'Analyze this image and return a structured JSON response with: title, description, detected_objects, colors')"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              className="w-full h-48 p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-between items-center mt-4">
              <div className="text-sm text-gray-600">
                {prompt.length} characters
              </div>
              <div className="flex gap-2">
                <button
                  onClick={mode === 'single' ? handleTestModel : handleCompareModels}
                  disabled={loading || isStreaming || !prompt.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? '🔄 Testing...' : mode === 'single' ? 'Test Model' : 'Compare Models'}
                </button>
                
                {loading && (
                  <button
                    onClick={() => {
                      setLoading(false)
                      alert('Test abgebrochen')
                    }}
                    className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    🛑 Abbrechen
                  </button>
                )}
                
                {mode === 'single' && (
                  <>
                    <button
                      onClick={handleTestModelStream}
                      disabled={loading || isStreaming || !prompt.trim()}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {isStreaming ? '🔄 Streaming...' : '⚡ Stream Test'}
                    </button>
                    
                    {isStreaming && (
                      <button
                        onClick={handleAbortStreaming}
                        className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        🛑 Abbrechen
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Progress Indicator for Normal & Comparison Tests */}
            {(loading || streamingProgress) && !isStreaming && (
              <div className="mt-4 flex items-center gap-3 px-4 py-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm font-medium text-blue-700">
                  {streamingProgress || '🔄 Lädt...'}
                </span>
              </div>
            )}
          </div>

          {/* Streaming Display */}
          {isStreaming && (
            <div className="border rounded-lg p-6 bg-white mb-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600"></div>
                  <h3 className="text-lg font-semibold text-green-600">🔄 Streaming Response</h3>
                  <span className="text-sm text-gray-500">({streamingModel})</span>
                </div>
                {streamingProgress && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
                    <span className="text-sm font-medium text-blue-700">{streamingProgress}</span>
                  </div>
                )}
              </div>
              
           <div className="bg-gray-50 p-4 rounded-lg border">
             <pre className="whitespace-pre-wrap text-sm font-mono">
               {streamingContent}
               {isStreaming && <span className="animate-pulse">▋</span>}
             </pre>
             
             {/* JSON Preview for structured output */}
             {streamingContent && (streamingContent.includes('{') || streamingContent.includes('[')) && (
               <div className="mt-4 p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                 <h4 className="text-sm font-semibold text-blue-800 mb-2">📋 JSON Preview:</h4>
                 <pre className="text-xs text-blue-700 overflow-x-auto">
                   {(() => {
                     try {
                       // Try to find and parse JSON in the streaming content
                       const jsonMatch = streamingContent.match(/\{[\s\S]*\}/);
                       if (jsonMatch) {
                         const parsed = JSON.parse(jsonMatch[0]);
                         return JSON.stringify(parsed, null, 2);
                       }
                       return "JSON wird noch aufgebaut...";
                     } catch (e) {
                       return "JSON wird noch aufgebaut...";
                     }
                   })()}
                 </pre>
               </div>
             )}
           </div>
            </div>
          )}

          {/* Results */}
          {mode === 'single' && testResult && !isStreaming && (
            <div className="border rounded-lg p-6 bg-white">
              <h2 className="text-xl font-semibold mb-4">Response</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-start pb-3 border-b">
                <div>
                    <h3 className="font-semibold">{testResult.model_name}</h3>
                    <p className="text-sm text-gray-600">{testResult.provider}</p>
                    {/* Model Verification Badge */}
                    {testResult.verified_model_id && (
                      <div className="mt-1 flex items-center gap-1">
                        <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">
                          ✓ {testResult.verified_model_id}
                        </span>
                      </div>
                    )}
                  </div>
                  <span
                    className={`px-3 py-1 rounded-lg text-sm ${
                      testResult.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {testResult.success ? '✓ Success' : '✗ Failed'}
                  </span>
                </div>

                {testResult.success ? (
                  <>
                    {formatResponse(testResult.response)}
                    
                    <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">{testResult.tokens_sent.toLocaleString('de-DE')}</p>
                        <p className="text-xs text-gray-600">Tokens Sent</p>
                        {/* Token Breakdown */}
                        {testResult.text_tokens !== undefined && testResult.image_tokens !== undefined && (
                          <div className="mt-2 text-xs text-gray-500 space-y-1">
                            <div className="flex justify-between px-2">
                              <span>📝 Text:</span>
                              <span className="font-medium">{testResult.text_tokens.toLocaleString('de-DE')}</span>
                            </div>
                            {testResult.image_tokens > 0 && (
                              <div className="flex justify-between px-2">
                                <span>🖼️ Bild:</span>
                                <span className="font-medium">{testResult.image_tokens.toLocaleString('de-DE')}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {testResult.tokens_received.toLocaleString('de-DE')}
                        </p>
                        <p className="text-xs text-gray-600">Tokens Received</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">
                          {(testResult.response_time_ms / 1000).toFixed(2)}s
                        </p>
                        <p className="text-xs text-gray-600">Response Time</p>
                      </div>
                    </div>
                    
                    {/* Save as Template Button */}
                    <div className="flex justify-end pt-4 border-t">
                      <button
                        onClick={() => handleSaveAsTemplate(testResult, selectedModelObj?.id || '')}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        💾 Als Template speichern
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-red-700">{testResult.error_message}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {mode === 'compare' && compareResults.length > 0 && (
            <div className="space-y-4">
              {compareResults.map((result, idx) => (
                <div key={idx} className="border rounded-lg p-6 bg-white">
                  <div className="flex justify-between items-start pb-3 border-b mb-4">
                    <div>
                      <h3 className="font-semibold">{result.model_name}</h3>
                      <p className="text-sm text-gray-600">{result.provider}</p>
                      {/* Model Verification Badge */}
                      {result.verified_model_id && (
                        <div className="mt-1 flex items-center gap-1">
                          <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">
                            ✓ {result.verified_model_id}
                          </span>
                        </div>
                      )}
                    </div>
                    <span
                      className={`px-3 py-1 rounded-lg text-sm ${
                        result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {result.success ? '✓ Success' : '✗ Failed'}
                    </span>
                  </div>

                  {result.success ? (
                    <>
                      {formatResponse(result.response)}
                      
                      <div className="grid grid-cols-3 gap-4 pt-4 border-t mt-4">
                        <div className="text-center">
                          <p className="text-xl font-bold text-blue-600">{result.tokens_sent.toLocaleString('de-DE')}</p>
                          <p className="text-xs text-gray-600">Tokens Sent</p>
                          {/* Token Breakdown */}
                          {result.text_tokens !== undefined && result.image_tokens !== undefined && (
                            <div className="mt-2 text-xs text-gray-500 space-y-1">
                              <div className="flex justify-between px-2">
                                <span>📝 Text:</span>
                                <span className="font-medium">{result.text_tokens.toLocaleString('de-DE')}</span>
                              </div>
                              {result.image_tokens > 0 && (
                                <div className="flex justify-between px-2">
                                  <span>🖼️ Bild:</span>
                                  <span className="font-medium">{result.image_tokens.toLocaleString('de-DE')}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-center">
                          <p className="text-xl font-bold text-green-600">
                            {result.tokens_received.toLocaleString('de-DE')}
                          </p>
                          <p className="text-xs text-gray-600">Tokens Received</p>
                        </div>
                        <div className="text-center">
                          <p className="text-xl font-bold text-purple-600">
                            {(result.response_time_ms / 1000).toFixed(2)}s
                          </p>
                          <p className="text-xs text-gray-600">Response Time</p>
                        </div>
                      </div>
                      
                      {/* Save as Template Button for Comparison Results */}
                      <div className="flex justify-end pt-4 border-t mt-4">
                        <button
                          onClick={() => handleSaveAsTemplate(result, result.model_name)}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                        >
                          💾 Als Template speichern
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="bg-red-50 p-4 rounded-lg">
                      <p className="text-red-700">{result.error_message}</p>
                    </div>
                  )}
          </div>
        ))}
              
              {/* Evaluation Button */}
              <div className="flex justify-center pt-6">
                <button
                  onClick={handleStartEvaluation}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-lg font-medium"
                >
                  🧭 Evaluate Results
                </button>
      </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Save as Template Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">💾 Als Prompt Template speichern</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Template-Name *</label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="z.B. Flussdiagramm Analyse v1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Beschreibung</label>
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  className="w-full p-2 border rounded"
                  rows={3}
                  placeholder="Optional: Zweck und Anwendungsbereich des Templates"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Dokumenttyp *</label>
                <select
                  value={templateDocType || ''}
                  onChange={(e) => setTemplateDocType(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full p-2 border rounded"
                  required
                >
                  <option value="">Bitte wählen...</option>
                  {documentTypes.map(dt => (
                    <option key={dt.id} value={dt.id}>
                      {dt.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Version *</label>
                <div className="flex gap-2">
                  <select
                    value={templateVersion}
                    onChange={(e) => setTemplateVersion(e.target.value)}
                    className="flex-1 p-2 border rounded"
                  >
                    <option value="v1.0.0">v1.0.0 (Erste Version)</option>
                    <option value="v1.1.0">v1.1.0 (Kleine Verbesserung)</option>
                    <option value="v1.2.0">v1.2.0 (Neue Features)</option>
                    <option value="v2.0.0">v2.0.0 (Breaking Changes)</option>
                    <option value="custom">Manuell eingeben...</option>
                  </select>
                  {templateVersion === 'custom' && (
                    <input
                      type="text"
                      value={templateVersion}
                      onChange={(e) => setTemplateVersion(e.target.value)}
                      placeholder="z.B. v1.3.0"
                      className="flex-1 p-2 border rounded"
                    />
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Semantische Versionierung: vMAJOR.MINOR.PATCH
                </p>
              </div>
              
              <div className="bg-blue-50 p-3 rounded text-sm">
                <p className="font-medium text-blue-900 mb-1">Folgende Einstellungen werden gespeichert:</p>
                <ul className="text-blue-800 space-y-1">
                  <li>• Modell: {saveTemplateData?.aiModel}</li>
                  <li>• Temperature: {config.temperature}</li>
                  <li>• Max Tokens: {(config.max_tokens || 1000).toLocaleString('de-DE')}</li>
                  <li>• Prompt: {prompt.substring(0, 50)}...</li>
                </ul>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowSaveModal(false)
                  setSaveTemplateData(null)
                }}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleSaveTemplate}
                disabled={!templateName.trim() || !templateDocType}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300"
              >
                💾 Template speichern
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Evaluation Modal */}
      {showEvaluationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">🧭 Model Evaluation</h2>
            
            <div className="space-y-6">
              {/* Evaluator Prompt */}
              <div>
                <label className="block text-sm font-medium mb-2">Evaluator Prompt</label>
                <textarea
                  value={evaluatorPrompt}
                  onChange={(e) => setEvaluatorPrompt(e.target.value)}
                  className="w-full h-40 p-3 border rounded-lg font-mono text-sm"
                  placeholder="Du bist ein Evaluator für strukturierte Arbeitsanweisungen..."
                />
              </div>
              
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Evaluator Model</label>
                <select
                  value={selectedEvaluatorModel || ''}
                  onChange={(e) => setSelectedEvaluatorModel(e.target.value || null)}
                  className="w-full p-2 border rounded"
                >
                  <option value="">Bitte wählen...</option>
                  {models.filter(m => m.is_configured).map(model => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.provider})
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  Das Evaluator-Modell bewertet alle {compareResults.length} Comparison-Results nach den Kriterien.
                </p>
              </div>
              
              {/* Evaluation Results - Schritt-für-Schritt */}
              {(evaluationStep === 'first' || evaluationStep === 'complete') && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold">📊 Model Evaluation Results</h3>
                  
                  {/* Erste Evaluation */}
                  {firstEvaluation && (
                    <div className="bg-white border rounded-lg p-4">
                      <h4 className="font-semibold mb-3 text-blue-600">
                        ✅ {firstEvaluation.test_model_name} - Evaluated
                      </h4>
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            {firstEvaluation.overall_score.toFixed(1)} / 10
                          </div>
                          <div className="text-sm text-gray-500">Score</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {Math.round(firstEvaluation.overall_score * 10)}%
                          </div>
                          <div className="text-sm text-gray-500">Percentage</div>
                        </div>
                        <div className="text-center">
                          <div className="flex justify-center gap-1">
                            {[...Array(5)].map((_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < Math.round(firstEvaluation.overall_score / 2) ? 'text-yellow-400' : 'text-gray-300'
                                }`}
                              >
                                ⭐
                              </span>
                            ))}
                          </div>
                          <div className="text-sm text-gray-500">Stars</div>
                        </div>
                      </div>
                      
                      {/* DEBUG: Input JSON Preview */}
                      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <h5 className="font-bold text-yellow-800 mb-2">🔍 DEBUG: Was wurde ausgewertet?</h5>
                        <details className="text-xs">
                          <summary className="cursor-pointer font-medium text-yellow-700">Klicke um Input JSON zu sehen (erste 1000 Zeichen)</summary>
                          <pre className="mt-2 p-2 bg-white rounded overflow-auto max-h-40 text-xs">
                            {compareResults[0]?.response.substring(0, 1000) || 'Keine Daten'}...
                          </pre>
                        </details>
                      </div>

                      {/* Detailbewertung */}
                      {firstEvaluation.category_scores && Object.keys(firstEvaluation.category_scores).length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-bold mb-3 text-lg">📊 Detailbewertung (10-Punkte-System):</h5>
                          <div className="space-y-2">
                            {Object.entries(firstEvaluation.category_scores).map(([key, score]) => {
                              const scoreLabels: Record<string, string> = {
                                'structure': 'Strukturkonformität',
                                'steps_completeness': 'Vollständigkeit der Schritte',
                                'articles_materials': 'Artikel- und Materialdaten',
                                'consumables': 'Chemikalien / Verbrauchsmaterialien',
                                'tools': 'Werkzeuge / Hilfsmittel',
                                'safety': 'Sicherheitsangaben',
                                'visuals': 'Visuelle Beschreibung (Fotos, Markierungen)',
                                'quality_rules': 'Qualitäts- und Prüfvorgaben',
                                'text_accuracy': 'Textgenauigkeit und Kontexttreue',
                                'rag_ready': 'RAG-Tauglichkeit / technische Konsistenz'
                              }
                              const getScoreColor = (s: number) => {
                                if (s >= 9) return 'bg-green-100 text-green-800 border-green-300'
                                if (s >= 7) return 'bg-blue-100 text-blue-800 border-blue-300'
                                if (s >= 5) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
                                return 'bg-red-100 text-red-800 border-red-300'
                              }
                              return (
                                <div key={key} className={`flex justify-between items-center p-2 rounded border ${getScoreColor(score as number)}`}>
                                  <span className="font-medium">{scoreLabels[key] || key.replace('_', ' ')}</span>
                                  <span className="font-bold text-lg">{score}/10</span>
    </div>
  )
                            })}
                          </div>
                        </div>
                      )}
                      
                      {/* DEBUG: Komplette Evaluation Response */}
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                        <h5 className="font-bold text-blue-800 mb-2">🔍 DEBUG: Komplette Evaluation Response</h5>
                        <div className="text-xs space-y-2">
                          <div className="p-2 bg-white rounded">
                            <strong>Hat category_scores?</strong> {firstEvaluation.category_scores ? '✅ JA' : '❌ NEIN'}
                          </div>
                          <div className="p-2 bg-white rounded">
                            <strong>Hat strengths?</strong> {firstEvaluation.strengths ? '✅ JA (' + firstEvaluation.strengths.length + ' Einträge)' : '❌ NEIN'}
                          </div>
                          <div className="p-2 bg-white rounded">
                            <strong>Hat weaknesses?</strong> {firstEvaluation.weaknesses ? '✅ JA (' + firstEvaluation.weaknesses.length + ' Einträge)' : '❌ NEIN'}
                          </div>
                          <div className="p-2 bg-white rounded">
                            <strong>Hat summary?</strong> {firstEvaluation.summary ? '✅ JA' : '❌ NEIN'}
                          </div>
                        </div>
                        <details className="text-xs mt-2" open>
                          <summary className="cursor-pointer font-medium text-blue-700">Vollständige Antwort (JSON)</summary>
                          <pre className="mt-2 p-2 bg-white rounded overflow-auto max-h-60 text-xs">
                            {JSON.stringify(firstEvaluation, null, 2)}
                          </pre>
                        </details>
                      </div>
                      
                      {/* Strengths & Weaknesses */}
                      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {firstEvaluation.strengths && firstEvaluation.strengths.length > 0 && (
                <div>
                            <h5 className="font-medium text-green-700 mb-2">✅ Strengths:</h5>
                            <ul className="text-sm space-y-1">
                              {firstEvaluation.strengths.map((strength, i) => (
                                <li key={i} className="text-gray-600">• {strength}</li>
                              ))}
                            </ul>
                </div>
                        )}
                        
                        {firstEvaluation.weaknesses && firstEvaluation.weaknesses.length > 0 && (
                <div>
                            <h5 className="font-medium text-red-700 mb-2">❌ Weaknesses:</h5>
                            <ul className="text-sm space-y-1">
                              {firstEvaluation.weaknesses.map((weakness, i) => (
                                <li key={i} className="text-gray-600">• {weakness}</li>
                              ))}
                            </ul>
                </div>
                        )}
                      </div>
                      
                      {/* Summary */}
                      {firstEvaluation.summary && (
                        <div className="mt-4 p-3 bg-gray-50 rounded">
                          <h5 className="font-medium mb-2">📝 Summary:</h5>
                          <p className="text-sm text-gray-600">{firstEvaluation.summary}</p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Zweite Evaluation */}
                  {secondEvaluation && (
                    <div className="bg-white border rounded-lg p-4">
                      <h4 className="font-semibold mb-3 text-green-600">
                        ✅ {secondEvaluation.test_model_name} - Evaluated
                      </h4>
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {secondEvaluation.overall_score.toFixed(1)} / 10
                          </div>
                          <div className="text-sm text-gray-500">Score</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {Math.round(secondEvaluation.overall_score * 10)}%
                          </div>
                          <div className="text-sm text-gray-500">Percentage</div>
                        </div>
                        <div className="text-center">
                          <div className="flex justify-center gap-1">
                            {[...Array(5)].map((_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < Math.round(secondEvaluation.overall_score / 2) ? 'text-yellow-400' : 'text-gray-300'
                                }`}
                              >
                                ⭐
                              </span>
                            ))}
                          </div>
                          <div className="text-sm text-gray-500">Stars</div>
                        </div>
                      </div>
                      
                      {/* DEBUG: Input JSON Preview */}
                      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <h5 className="font-bold text-yellow-800 mb-2">🔍 DEBUG: Was wurde ausgewertet?</h5>
                        <details className="text-xs">
                          <summary className="cursor-pointer font-medium text-yellow-700">Klicke um Input JSON zu sehen (erste 1000 Zeichen)</summary>
                          <pre className="mt-2 p-2 bg-white rounded overflow-auto max-h-40 text-xs">
                            {compareResults[1]?.response.substring(0, 1000) || 'Keine Daten'}...
                          </pre>
                        </details>
                      </div>

                      {/* Detailbewertung */}
                      {secondEvaluation.category_scores && Object.keys(secondEvaluation.category_scores).length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-bold mb-3 text-lg">📊 Detailbewertung (10-Punkte-System):</h5>
                          <div className="space-y-2">
                            {Object.entries(secondEvaluation.category_scores).map(([key, score]) => {
                              const scoreLabels: Record<string, string> = {
                                'structure': 'Strukturkonformität',
                                'steps_completeness': 'Vollständigkeit der Schritte',
                                'articles_materials': 'Artikel- und Materialdaten',
                                'consumables': 'Chemikalien / Verbrauchsmaterialien',
                                'tools': 'Werkzeuge / Hilfsmittel',
                                'safety': 'Sicherheitsangaben',
                                'visuals': 'Visuelle Beschreibung (Fotos, Markierungen)',
                                'quality_rules': 'Qualitäts- und Prüfvorgaben',
                                'text_accuracy': 'Textgenauigkeit und Kontexttreue',
                                'rag_ready': 'RAG-Tauglichkeit / technische Konsistenz'
                              }
                              const getScoreColor = (s: number) => {
                                if (s >= 9) return 'bg-green-100 text-green-800 border-green-300'
                                if (s >= 7) return 'bg-blue-100 text-blue-800 border-blue-300'
                                if (s >= 5) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
                                return 'bg-red-100 text-red-800 border-red-300'
                              }
                              return (
                                <div key={key} className={`flex justify-between items-center p-2 rounded border ${getScoreColor(score as number)}`}>
                                  <span className="font-medium">{scoreLabels[key] || key.replace('_', ' ')}</span>
                                  <span className="font-bold text-lg">{score}/10</span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}
                      
                      {/* DEBUG: Komplette Evaluation Response */}
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                        <h5 className="font-bold text-blue-800 mb-2">🔍 DEBUG: Komplette Evaluation Response</h5>
                        <details className="text-xs">
                          <summary className="cursor-pointer font-medium text-blue-700">Klicke um vollständige Antwort zu sehen</summary>
                          <pre className="mt-2 p-2 bg-white rounded overflow-auto max-h-60 text-xs">
                            {JSON.stringify(secondEvaluation, null, 2)}
                          </pre>
                        </details>
                      </div>
                      
                      {/* Strengths & Weaknesses */}
                      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {secondEvaluation.strengths && secondEvaluation.strengths.length > 0 && (
                <div>
                            <h5 className="font-medium text-green-700 mb-2">✅ Strengths:</h5>
                            <ul className="text-sm space-y-1">
                              {secondEvaluation.strengths.map((strength, i) => (
                                <li key={i} className="text-gray-600">• {strength}</li>
                              ))}
                            </ul>
                </div>
                        )}
                        
                        {secondEvaluation.weaknesses && secondEvaluation.weaknesses.length > 0 && (
                          <div>
                            <h5 className="font-medium text-red-700 mb-2">❌ Weaknesses:</h5>
                            <ul className="text-sm space-y-1">
                              {secondEvaluation.weaknesses.map((weakness, i) => (
                                <li key={i} className="text-gray-600">• {weakness}</li>
                              ))}
                            </ul>
              </div>
                        )}
            </div>
                      
                      {/* Summary */}
                      {secondEvaluation.summary && (
                        <div className="mt-4 p-3 bg-gray-50 rounded">
                          <h5 className="font-medium mb-2">📝 Summary:</h5>
                          <p className="text-sm text-gray-600">{secondEvaluation.summary}</p>
          </div>
                      )}
                    </div>
                  )}
                  
                  {/* Vergleich wenn beide da sind */}
                  {evaluationStep === 'complete' && firstEvaluation && secondEvaluation && (
                    <div className="bg-gradient-to-r from-blue-50 to-green-50 border-2 border-blue-200 rounded-lg p-6">
                      <h4 className="text-xl font-bold text-center mb-4">🏆 Final Comparison</h4>
                      
                      <div className="grid grid-cols-2 gap-6">
                        <div className="text-center">
                          <h5 className="font-semibold text-blue-600 mb-2">{firstEvaluation.test_model_name}</h5>
                          <div className="text-3xl font-bold text-blue-600">
                            {firstEvaluation.overall_score.toFixed(1)} / 10
                          </div>
                          <div className="text-lg text-blue-600">
                            {Math.round(firstEvaluation.overall_score * 10)}%
                          </div>
                          <div className="flex justify-center gap-1 mt-2">
                            {[...Array(5)].map((_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < Math.round(firstEvaluation.overall_score / 2) ? 'text-yellow-400' : 'text-gray-300'
                                }`}
                              >
                                ⭐
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div className="text-center">
                          <h5 className="font-semibold text-green-600 mb-2">{secondEvaluation.test_model_name}</h5>
                          <div className="text-3xl font-bold text-green-600">
                            {secondEvaluation.overall_score.toFixed(1)} / 10
                          </div>
                          <div className="text-lg text-green-600">
                            {Math.round(secondEvaluation.overall_score * 10)}%
                          </div>
                          <div className="flex justify-center gap-1 mt-2">
                            {[...Array(5)].map((_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < Math.round(secondEvaluation.overall_score / 2) ? 'text-yellow-400' : 'text-gray-300'
                                }`}
                              >
                                ⭐
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-center mt-4">
                        <div className="text-lg font-semibold">
                          {firstEvaluation.overall_score > secondEvaluation.overall_score ? (
                            <span className="text-blue-600">🏆 {firstEvaluation.test_model_name} wins!</span>
                          ) : secondEvaluation.overall_score > firstEvaluation.overall_score ? (
                            <span className="text-green-600">🏆 {secondEvaluation.test_model_name} wins!</span>
                          ) : (
                            <span className="text-gray-600">🤝 It's a tie!</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Legacy Evaluation Results - für Kompatibilität */}
              {evaluationResults.length > 0 && evaluationStep === 'none' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold">📊 Model Comparison Results</h3>
                  
                  {/* Debug Info */}
                  <div className="bg-gray-100 p-3 rounded text-xs">
                    <strong>Debug:</strong> {evaluationResults.length} Results received
                    <br />
                    {evaluationResults.map((r, i) => (
                      <span key={i}>
                        {r.test_model_name}: {r.overall_score.toFixed(1)}/10 | 
                      </span>
                    ))}
                    <br />
                    <strong>Full Results:</strong>
                    <pre className="text-xs mt-2 overflow-auto max-h-32">
                      {JSON.stringify(evaluationResults, null, 2)}
                    </pre>
                  </div>
                  
                  {/* Einfache Tabelle wie im Bild */}
                  <div className="bg-white border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-left p-3 font-medium">Modell</th>
                          <th className="text-center p-3 font-medium">Durchschnitt (von 10)</th>
                          <th className="text-center p-3 font-medium">Prozent</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evaluationResults.map((result, idx) => {
                          const averageScore = result.overall_score;
                          const percentage = Math.round(result.overall_score * 10);
                          const stars = Math.round(averageScore / 2);
                          
                          return (
                            <tr key={idx} className="border-b">
                              <td className="p-3">
                                <div className="font-medium">{result.test_model_name}</div>
                                <div className="text-sm text-gray-500">{result.test_model_provider}</div>
                              </td>
                              <td className="p-3 text-center">
                                <div className="text-lg font-bold">{averageScore.toFixed(1)} / 10</div>
                                <div className="flex justify-center gap-1 mt-1">
                                  {[...Array(5)].map((_, i) => (
                                    <span
                                      key={i}
                                      className={`text-sm ${
                                        i < stars ? 'text-yellow-400' : 'text-gray-300'
                                      }`}
                                    >
                                      ⭐
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className="p-3 text-center">
                                <div className="text-lg font-bold text-green-600">{percentage}%</div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Detailbewertungen */}
                  {evaluationResults.map((result, idx) => {
                    const scores = result.category_scores || result.detailed_scores || {};
                    const scoreLabels = {
                      'structure': 'Strukturkonformität',
                      'steps_completeness': 'Vollständigkeit der Schritte',
                      'articles_materials': 'Artikel- und Materialdaten',
                      'consumables': 'Chemikalien / Verbrauchsmaterialien',
                      'tools': 'Werkzeuge / Hilfsmittel',
                      'safety': 'Sicherheitsangaben',
                      'visuals': 'Visuelle Beschreibung (Fotos, Markierungen)',
                      'quality_rules': 'Qualitäts- und Prüfvorgaben',
                      'text_accuracy': 'Textgenauigkeit und Kontexttreue',
                      'rag_ready': 'RAG-Tauglichkeit / technische Konsistenz'
                    };
                    
                    return (
                      <div key={idx} className="bg-white border rounded-lg p-4">
                        <h4 className="font-semibold mb-3">{result.test_model_name} - Detailbewertung</h4>
                        
                        {Object.keys(scores).length > 0 ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b">
                                  <th className="text-left py-2 font-medium">Kategorie</th>
                                  <th className="text-center py-2 font-medium">Score</th>
                                  <th className="text-left py-2 font-medium">Kommentar</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(scores).map(([key, score]) => (
                                  <tr key={key} className="border-b border-gray-100">
                                    <td className="py-2 text-gray-600">
                                      {(scoreLabels as any)[key] || key.replace('_', ' ')}
                                    </td>
                                    <td className="py-2 text-center">
                                      <span className={`font-medium px-2 py-1 rounded ${
                                        score >= 8 ? 'bg-green-100 text-green-800' : 
                                        score >= 6 ? 'bg-yellow-100 text-yellow-800' : 
                                        'bg-red-100 text-red-800'
                                      }`}>
                                        {score}/10
                                      </span>
                                    </td>
                                    <td className="py-2 text-gray-600">
                                      {score >= 8 ? 'Sehr gut' : score >= 6 ? 'Gut' : 'Verbesserungsbedarf'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="text-gray-500">Keine Detailbewertungen verfügbar</div>
                        )}
                        
                        {/* Strengths & Weaknesses */}
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                          {result.strengths && result.strengths.length > 0 && (
                            <div>
                              <h5 className="font-medium text-green-700 mb-2">✅ Strengths:</h5>
                              <ul className="text-sm space-y-1">
                                {result.strengths.map((strength, i) => (
                                  <li key={i} className="text-gray-600">• {strength}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {result.weaknesses && result.weaknesses.length > 0 && (
                            <div>
                              <h5 className="font-medium text-red-700 mb-2">❌ Weaknesses:</h5>
                              <ul className="text-sm space-y-1">
                                {result.weaknesses.map((weakness, i) => (
                                  <li key={i} className="text-gray-600">• {weakness}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                        
                        {/* Summary */}
                        {result.summary && (
                          <div className="mt-4 p-3 bg-gray-50 rounded">
                            <h5 className="font-medium mb-2">📝 Summary:</h5>
                            <p className="text-sm text-gray-600">{result.summary}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowEvaluationModal(false)
                  setEvaluationResults([])
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                ❌ Close
              </button>
              <div className="flex gap-2">
                {/* Schritt-für-Schritt Evaluation Buttons */}
                {evaluationStep === 'none' && (
                  <button
                    onClick={handleEvaluateFirstModel}
                    disabled={evaluationLoading || !selectedEvaluatorModel || !evaluatorPrompt.trim() || compareResults.length === 0}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 flex items-center gap-2"
                  >
                    {evaluationLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Evaluating First Model...
                      </>
                    ) : (
                      '📊 Evaluate First Model'
                    )}
                  </button>
                )}
                
                {evaluationStep === 'first' && (
                  <button
                    onClick={handleEvaluateSecondModel}
                    disabled={evaluationLoading || !selectedEvaluatorModel || !evaluatorPrompt.trim() || compareResults.length < 2}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300 flex items-center gap-2"
                  >
                    {evaluationLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Evaluating Second Model...
                      </>
                    ) : (
                      '📊 Evaluate Second Model'
                    )}
                  </button>
                )}
                
                {evaluationStep === 'complete' && (
                  <button
                    onClick={() => {
                      setEvaluationStep('none')
                      setFirstEvaluation(null)
                      setSecondEvaluation(null)
                      setEvaluationResults([])
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-2"
                  >
                    🔄 Neue Evaluation
                  </button>
                )}
              </div>
            </div>
          </div>
      </div>
      )}
    </div>
  )
}

export default function AIPlaygroundPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <AIPlaygroundPageContent />
    </Suspense>
  )
}
