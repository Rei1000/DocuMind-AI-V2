/**
 * AI Playground API Client
 * 
 * API-Client für AI Playground Context
 */

import { apiClient } from '../api'

// ===== TYPES =====

export interface ModelConfig {
  temperature?: number
  max_tokens?: number
  top_p?: number
  top_k?: number | null
  detail_level?: string  // "high" oder "low" für Bilderkennung
}

export interface AIModel {
  id: string
  name: string
  provider: string
  model_id: string
  description: string
  max_tokens_supported: number
  is_configured: boolean
}

export interface TestResult {
  model_name: string
  provider: string
  prompt: string
  response: string
  tokens_sent: number
  tokens_received: number
  total_tokens: number
  response_time: number
  response_time_ms: number
  success: boolean
  error_message?: string
  timestamp?: string
  text_tokens?: number  // Token-Breakdown für Transparenz
  image_tokens?: number
  verified_model_id?: string  // Tatsächlich verwendetes Modell (von API verifiziert)
}

export interface ConnectionTest {
  provider: string
  model_name: string
  success: boolean
  latency?: number
  latency_ms?: number
  error_message?: string
  timestamp?: string
}

export interface StreamingChunk {
  content: string
  is_final: boolean
  model_name: string
  provider: string
  chunk_index: number
  timestamp: string
}

export interface EvaluationRequest {
  evaluator_prompt: string
  test_results: TestResult[]
  evaluator_model_id: string
}

export interface SingleEvaluationRequest {
  test_result: TestResult
  evaluator_prompt: string
  evaluator_model_id: string
}

export interface EvaluationResult {
  test_model_name: string
  test_model_provider: string
  evaluator_model_name: string
  evaluation_success: boolean
  overall_score: number
  detailed_scores?: Record<string, number>  // Legacy support
  category_scores?: Record<string, number>  // New format
  explanations?: string[]  // Legacy support
  recommendations?: string[]  // Legacy support
  strengths?: string[]  // New format
  weaknesses?: string[]  // New format
  summary?: string  // New format
  error?: string
}

export interface TestModelRequest {
  model_id: string
  prompt: string
  config?: ModelConfig
  image?: File
}

export interface CompareModelsRequest {
  model_ids: string[]
  prompt: string
  config?: ModelConfig
  image?: File
}

// ===== API FUNCTIONS =====

/**
 * Get available AI models
 */
export const getAvailableModels = async (): Promise<AIModel[]> => {
  const response = await apiClient.get<AIModel[]>('/api/ai-playground/models')
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('No models data received')
  }
  
  return response.data
}

/**
 * Test connection to a specific model
 */
export const testConnection = async (modelId: string): Promise<ConnectionTest> => {
  const response = await apiClient.post<ConnectionTest>('/api/ai-playground/test-connection', {
    model_id: modelId
  })
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('No connection test data received')
  }
  
  return response.data
}

/**
 * Test a single model with prompt
 */
export const testModel = async (
  modelId: string,
  prompt: string,
  config: ModelConfig = {},
  imageFile?: File
): Promise<TestResult> => {
  const formData = new FormData()
  formData.append('model_id', modelId)
  formData.append('prompt', prompt)
  formData.append('config', JSON.stringify(config))
  
  if (imageFile) {
    formData.append('image', imageFile)
  }
  
  // Get token from sessionStorage (same as apiClient)
  const token = sessionStorage.getItem('access_token')
  
  // Prepare headers
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  // Use fetch directly for FormData
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const response = await fetch(`${API_BASE_URL}/api/ai-playground/test`, {
    method: 'POST',
    body: formData,
    headers: headers
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data
}

/**
 * Compare multiple models with the same prompt
 */
export const compareModels = async (
  modelIds: string[],
  prompt: string,
  config: ModelConfig = {},
  imageFile?: File
): Promise<TestResult[]> => {
  const formData = new FormData()
  formData.append('model_ids', JSON.stringify(modelIds))
  formData.append('prompt', prompt)
  formData.append('config', JSON.stringify(config))
  
  if (imageFile) {
    formData.append('image', imageFile)
  }
  
  // Get token from sessionStorage (same as apiClient)
  const token = sessionStorage.getItem('access_token')
  
  // Prepare headers
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  // Use fetch directly for FormData
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const response = await fetch(`${API_BASE_URL}/api/ai-playground/compare`, {
    method: 'POST',
    body: formData,
    headers: headers
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data
}

/**
 * Health check
 */
export const healthCheck = async (): Promise<{ status: string; service: string; version: string }> => {
  const response = await apiClient.get<{ status: string; service: string; version: string }>('/api/ai-playground/health')
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('No data received')
  }
  
  return response.data
}

/**
 * Test model with streaming response
 */
export const testModelStream = async (
  modelId: string,
  prompt: string,
  config: ModelConfig,
  imageFile?: File,
  onChunk?: (chunk: StreamingChunk) => void,
  onComplete?: () => void,
  onError?: (error: string) => void
): Promise<void> => {
  try {
    // Prepare form data
    const formData = new FormData()
    formData.append('model_id', modelId)
    formData.append('prompt', prompt)
    formData.append('config', JSON.stringify(config))
    
    if (imageFile) {
      formData.append('image', imageFile)
    }
    
    // Get token from sessionStorage (same as apiClient)
    const token = sessionStorage.getItem('access_token')
    
    // Prepare headers
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    // Create EventSource for Server-Sent Events
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    console.log('Starting streaming request to:', `${API_BASE_URL}/api/ai-playground/test-model-stream`)
    
    const response = await fetch(`${API_BASE_URL}/api/ai-playground/test-model-stream`, {
      method: 'POST',
      body: formData,
      headers: headers
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    console.log('Streaming response received, content-type:', response.headers.get('content-type'))
    
    // Read streaming response
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body reader available')
    }
    
    console.log('Starting to read streaming chunks...')
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        onComplete?.()
        break
      }
      
      // Decode chunk and add to buffer
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      console.log('Received chunk:', chunk)
      
      // Process complete lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer
      
      for (const line of lines) {
        console.log('Processing line:', line)
        if (line.startsWith('data: ')) {
          try {
            const chunkData = JSON.parse(line.slice(6)) as StreamingChunk
            console.log('Parsed chunk data:', chunkData)
            onChunk?.(chunkData)
            
            if (chunkData.is_final) {
              console.log('Stream completed')
              onComplete?.()
              return
            }
          } catch (e) {
            console.warn('Failed to parse chunk:', line, e)
          }
        }
      }
    }
    
  } catch (error) {
    onError?.(error instanceof Error ? error.message : 'Unknown streaming error')
  }
}

/**
 * Evaluate comparison results
 */
export const evaluateResults = async (
  request: EvaluationRequest
): Promise<EvaluationResult[]> => {
  const token = sessionStorage.getItem('access_token')
  if (!token) {
    throw new Error('No authentication token found')
  }

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const response = await fetch(`${API_BASE_URL}/api/ai-playground/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

export const evaluateSingleModel = async (
  request: SingleEvaluationRequest
): Promise<EvaluationResult> => {
  const token = sessionStorage.getItem('access_token')
  if (!token) {
    throw new Error('No authentication token found')
  }

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const response = await fetch(`${API_BASE_URL}/api/ai-playground/evaluate-single`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}