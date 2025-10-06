'use client'

import { useState, useEffect } from 'react'
import {
  getAvailableModels,
  testConnection,
  testModel,
  compareModels,
  AIModel,
  TestResult,
  ConnectionTest,
  ModelConfig
} from '@/lib/api/aiPlayground'

export default function AIPlaygroundPage() {
  const [models, setModels] = useState<AIModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [compareModelIds, setCompareModelIds] = useState<string[]>([])
  const [prompt, setPrompt] = useState('')
  const [config, setConfig] = useState<ModelConfig>({
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1.0
  })
  
  const [loading, setLoading] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [compareResults, setCompareResults] = useState<TestResult[]>([])
  const [connectionTests, setConnectionTests] = useState<Record<string, ConnectionTest>>({})
  const [mode, setMode] = useState<'single' | 'compare'>('single')
  
  // Load models on mount
  useEffect(() => {
    loadModels()
  }, [])
  
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
      setModels([]) // Ensure models is always an array
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
  
  const handleTestModel = async () => {
    if (!selectedModel || !prompt.trim()) {
      alert('Bitte Modell und Prompt auswählen')
      return
    }
    
    setLoading(true)
    setTestResult(null)
    
    try {
      const result = await testModel({
        model_id: selectedModel,
        prompt: prompt,
        config: config
      })
      setTestResult(result)
    } catch (error: any) {
      console.error('Test failed:', error)
      alert(`Test fehlgeschlagen: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  const handleCompareModels = async () => {
    if (compareModelIds.length < 2 || !prompt.trim()) {
      alert('Bitte mindestens 2 Modelle und einen Prompt auswählen')
      return
    }
    
    setLoading(true)
    setCompareResults([])
    
    try {
      const results = await compareModels({
        model_ids: compareModelIds,
        prompt: prompt,
        config: config
      })
      setCompareResults(results)
    } catch (error: any) {
      console.error('Comparison failed:', error)
      alert(`Vergleich fehlgeschlagen: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  const toggleCompareModel = (modelId: string) => {
    setCompareModelIds(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId)
      } else {
        if (prev.length >= 5) {
          alert('Maximal 5 Modelle können verglichen werden')
          return prev
        }
        return [...prev, modelId]
      }
    })
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">AI Playground</h1>
        <p className="text-muted-foreground">
          Teste AI-Modelle, prüfe Verbindungen und vergleiche Responses
        </p>
      </div>
      
      {/* Mode Selection */}
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
        {/* Left Panel: Models */}
        <div className="lg:col-span-1">
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">Available Models</h2>
            
            <div className="space-y-3">
              {models && models.length > 0 ? models.map((model) => (
                <div
                  key={model.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    mode === 'single' && selectedModel === model.id
                      ? 'border-blue-500 bg-blue-50'
                      : mode === 'compare' && compareModelIds.includes(model.id)
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${!model.is_configured ? 'opacity-50' : ''}`}
                  onClick={() => {
                    if (!model.is_configured) return
                    if (mode === 'single') {
                      setSelectedModel(model.id)
                    } else {
                      toggleCompareModel(model.id)
                    }
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-sm">{model.name}</h3>
                    {mode === 'compare' && compareModelIds.includes(model.id) && (
                      <span className="text-green-600 text-xs">✓</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{model.provider}</p>
                  
                  <div className="flex items-center justify-between">
                    <span className={`text-xs px-2 py-1 rounded ${
                      model.is_configured
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {model.is_configured ? 'Configured' : 'Not Configured'}
                    </span>
                    
                    {model.is_configured && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTestConnection(model.id)
                        }}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Test Connection
                      </button>
                    )}
                  </div>
                  
                  {connectionTests[model.id] && (
                    <div className="mt-2 text-xs">
                      {connectionTests[model.id].success ? (
                        <span className="text-green-600">
                          ✓ Connected ({connectionTests[model.id].latency_ms?.toFixed(0)}ms)
                        </span>
                      ) : (
                        <span className="text-red-600">
                          ✗ {connectionTests[model.id].error_message}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )) : (
                <div className="text-center py-4 text-gray-500">
                  {loading ? 'Loading models...' : 'No models available'}
                </div>
              )}
            </div>
          </div>
          
          {/* Configuration Panel */}
          <div className="border rounded-lg p-6 bg-white mt-6">
            <h3 className="text-lg font-semibold mb-4">Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Temperature: {config.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  0 = deterministisch, 2 = sehr kreativ
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  Max Tokens: {config.max_tokens}
                </label>
                <input
                  type="range"
                  min="100"
                  max="4000"
                  step="100"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  Top P: {config.top_p}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.top_p}
                  onChange={(e) => setConfig({ ...config, top_p: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Chat & Results */}
        <div className="lg:col-span-2">
          {/* Prompt Input */}
          <div className="border rounded-lg p-6 bg-white mb-6">
            <h2 className="text-xl font-semibold mb-4">Prompt</h2>
            
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here..."
              className="w-full h-32 p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            
            <div className="flex justify-between items-center mt-4">
              <div className="text-sm text-gray-600">
                {mode === 'single' && selectedModel && (
                  <span>Selected: {models.find(m => m.id === selectedModel)?.name}</span>
                )}
                {mode === 'compare' && (
                  <span>{compareModelIds.length} models selected</span>
                )}
              </div>
              
              <button
                onClick={mode === 'single' ? handleTestModel : handleCompareModels}
                disabled={loading || !prompt.trim() || (mode === 'single' && !selectedModel) || (mode === 'compare' && compareModelIds.length < 2)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Testing...' : mode === 'single' ? 'Test Model' : 'Compare Models'}
              </button>
            </div>
          </div>

          {/* Results */}
          {mode === 'single' && testResult && (
            <div className="border rounded-lg p-6 bg-white">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold">Result</h2>
                <span className={`px-3 py-1 rounded text-sm ${
                  testResult.success
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {testResult.success ? 'Success' : 'Failed'}
                </span>
              </div>
              
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700 mb-2">Response:</p>
                <p className="text-sm whitespace-pre-wrap">{testResult.response || testResult.error_message}</p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-700">{testResult.tokens_sent}</div>
                  <div className="text-xs text-gray-600">Tokens Sent</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-700">{testResult.tokens_received}</div>
                  <div className="text-xs text-gray-600">Tokens Received</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-700">{testResult.total_tokens}</div>
                  <div className="text-xs text-gray-600">Total Tokens</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-700">
                    {testResult.response_time_ms.toFixed(0)}ms
                  </div>
                  <div className="text-xs text-gray-600">Response Time</div>
                </div>
              </div>
            </div>
          )}

          {mode === 'compare' && compareResults.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Comparison Results</h2>
              
              {compareResults.map((result, index) => (
                <div key={index} className="border rounded-lg p-6 bg-white">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">{result.model_name}</h3>
                      <p className="text-sm text-gray-600">{result.provider}</p>
                    </div>
                    <span className={`px-3 py-1 rounded text-sm ${
                      result.success
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {result.success ? 'Success' : 'Failed'}
                    </span>
                  </div>
                  
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">
                      {result.response || result.error_message}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="text-center p-2 bg-blue-50 rounded">
                      <div className="font-bold text-blue-700">{result.tokens_sent}</div>
                      <div className="text-gray-600">Sent</div>
                    </div>
                    <div className="text-center p-2 bg-green-50 rounded">
                      <div className="font-bold text-green-700">{result.tokens_received}</div>
                      <div className="text-gray-600">Received</div>
                    </div>
                    <div className="text-center p-2 bg-purple-50 rounded">
                      <div className="font-bold text-purple-700">{result.total_tokens}</div>
                      <div className="text-gray-600">Total</div>
                    </div>
                    <div className="text-center p-2 bg-orange-50 rounded">
                      <div className="font-bold text-orange-700">
                        {result.response_time_ms.toFixed(0)}ms
                      </div>
                      <div className="text-gray-600">Time</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
