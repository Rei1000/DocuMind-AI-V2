'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  getAvailableModels,
  testConnection,
  testModel,
  compareModels,
  testModelStream,
  AIModel,
  TestResult,
  ConnectionTest,
  ModelConfig,
  StreamingChunk
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
      // Store original file for API calls
      setOriginalFile(file)
      
      // Convert file to base64 and create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        const base64 = e.target?.result as string
        setUploadedImage(base64.split(',')[1]) // Remove data:image/jpeg;base64, prefix
        setImagePreview(base64) // Use full base64 for preview
        setImageFilename(file.name)
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
        version: version
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
                accept="image/*,.pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!imagePreview ? (
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
                        Image or PDF (max 10MB)
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="relative">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-64 mx-auto rounded-lg border"
                  />
                  <button
                    onClick={handleRemoveImage}
                    className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-lg hover:bg-red-600"
                  >
                    ✕ Remove
                  </button>
                  <p className="text-sm text-gray-600 mt-2 text-center">{imageFilename}</p>
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
