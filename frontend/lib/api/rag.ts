/**
 * API Client für RAG Integration
 * 
 * Stellt alle notwendigen API-Funktionen für das RAG System bereit.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

class ApiClient {
  private getAuthHeaders(): HeadersInit {
    // Prüfe ob sessionStorage verfügbar ist (nicht in Node.js-Tests)
    let token: string | null = null
    try {
      if (typeof sessionStorage !== 'undefined') {
        // Prüfe beide möglichen Keys (wie in anderen Teilen der App)
        token = sessionStorage.getItem('access_token') || sessionStorage.getItem('token')
      }
      // Fallback zu localStorage falls sessionStorage leer ist
      if (!token && typeof localStorage !== 'undefined') {
        token = localStorage.getItem('access_token') || localStorage.getItem('token')
      }
    } catch (error) {
      // sessionStorage nicht verfügbar (z.B. in Node.js-Tests)
      console.warn('sessionStorage/localStorage not available, skipping auth token')
    }
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
    
    // Debug: Log token status (immer in Browser)
    if (typeof window !== 'undefined') {
      console.log('[RAG API] Token status:', token ? '✅ Found' : '❌ Missing', token ? `(${token.substring(0, 20)}...)` : '')
    }
    
    return headers
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${API_BASE_URL}${endpoint}`
      const headers = {
        ...this.getAuthHeaders(),
        ...options.headers
      }
      
      // Debug: Log request details (immer in Browser)
      if (typeof window !== 'undefined') {
        const headerObj = headers as Record<string, string>
        console.log(`[RAG API] ${options.method || 'GET'} ${url}`, {
          headers: { 
            ...headerObj, 
            Authorization: headerObj.Authorization ? 'Bearer ***' : 'None' 
          },
          body: options.body ? JSON.parse(options.body as string) : undefined
        })
      }
      
      const response = await fetch(url, {
        method: options.method || 'GET',
        ...options,
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail 
          ? (Array.isArray(errorData.detail) 
              ? errorData.detail.map((e: any) => e.msg || e).join(', ')
              : errorData.detail)
          : `HTTP ${response.status}`
        
        // Debug: Log error details
        console.error(`[RAG API] Error ${response.status} on ${endpoint}:`, errorMessage, errorData)
        
        // 401 Unauthorized: Token abgelaufen → Redirect zu Login
        if (response.status === 401 && typeof window !== 'undefined') {
          console.warn('[RAG API] Token abgelaufen (401), leite zu Login um...')
          // Token entfernen
          sessionStorage.removeItem('access_token')
          sessionStorage.removeItem('token')
          localStorage.removeItem('access_token')
          localStorage.removeItem('token')
          // Redirect zu Login
          window.location.href = '/login'
          throw new Error('Token abgelaufen. Bitte neu anmelden.')
        }
        
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      // Debug: Log successful response (immer in Browser)
      if (typeof window !== 'undefined') {
        console.log(`[RAG API] ✅ Success on ${endpoint}`, data)
      }
      
      // Backend gibt manchmal direkt Daten zurück (z.B. Listen), manchmal wrapped
      // Wenn data bereits eine Liste/Array ist und kein data-Property hat, ist es direkt das Ergebnis
      return { data: data as T }
    } catch (error) {
      console.error(`[RAG API] Request Error (${endpoint}):`, error)
      return { 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }
    }
  }

  // Convenience method for GET requests
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // Convenience method for POST requests
  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    });
  }

  // Convenience method for PUT requests
  async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    });
  }

  // Convenience method for DELETE requests
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // RAG Chat Endpoints
  async askQuestion(params: {
    question: string
    session_id?: number
    model?: string
    top_k?: number
    score_threshold?: number
    filters?: Record<string, any>
    use_hybrid_search?: boolean
    use_multi_query?: boolean,  // NEU: MultiQuery-Option
    use_ml_reranking?: boolean,  // NEU: ML Re-Ranking (Phase 4, deprecated)
    use_ml_ranking?: boolean,  // NEU: Learning-to-Rank ML-Ranking (v2.7.0)
    temperature?: number,  // NEU v2.10.3: AI Temperature
    max_tokens?: number,  // NEU v2.10.3: Max Tokens
    top_p?: number,  // NEU v2.10.3: Top P
    adaptive_min_avg_score?: number,  // NEU: Adaptive Filterung - Mindest-Durchschnitts-Score
    adaptive_min_max_score?: number  // NEU: Adaptive Filterung - Mindest-Maximal-Score
  }): Promise<ApiResponse<AskQuestionResponse>> {
    return this.request<AskQuestionResponse>('/api/rag/chat/ask', {
      method: 'POST',
      body: JSON.stringify({
        question: params.question,
        session_id: params.session_id,
        model: params.model || 'gpt-4o-mini',
        top_k: params.top_k || 5,
        score_threshold: params.score_threshold ?? 0.01,  // PHASE 0.3: Default 0.01 für OpenAI Embeddings (nicht 0.7!)
        filters: params.filters,
        use_hybrid_search: params.use_hybrid_search ?? true,
        use_multi_query: params.use_multi_query ?? false,  // NEU: MultiQuery-Option (Standard: false)
        use_ml_reranking: params.use_ml_reranking ?? false,  // NEU: ML Re-Ranking (Phase 4) - Standard: false
        use_ml_ranking: params.use_ml_ranking ?? true,  // NEU: Learning-to-Rank ML-Ranking (v2.7.0) - Default: true
        temperature: params.temperature,  // NEU v2.10.3: AI Temperature
        max_tokens: params.max_tokens,  // NEU v2.10.3: Max Tokens
        top_p: params.top_p,  // NEU v2.10.3: Top P
        adaptive_min_avg_score: params.adaptive_min_avg_score,  // NEU: Adaptive Filterung - Mindest-Durchschnitts-Score
        adaptive_min_max_score: params.adaptive_min_max_score  // NEU: Adaptive Filterung - Mindest-Maximal-Score
      })
    })
  }

  async createChatSession(params: {
    session_name: string
    user_id: number
  }): Promise<ApiResponse<ChatSession>> {
    return this.request<ChatSession>(`/api/rag/chat/sessions`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: params.user_id,
        session_name: params.session_name
      })
    })
  }

  async getChatSessions(userId: number): Promise<ApiResponse<ChatSession[]>> {
    return this.request<ChatSession[]>(`/api/rag/chat/sessions?user_id=${userId}`)
  }

  async getChatHistory(sessionId: number): Promise<ApiResponse<{ session: ChatSession; messages: ChatMessage[]; total_messages: number }>> {
    return this.request<{ session: ChatSession; messages: ChatMessage[]; total_messages: number }>(`/api/rag/chat/sessions/${sessionId}/history`)
  }

  async deleteChatSession(sessionId: number) {
    return this.request(`/api/rag/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    })
  }

  async updateChatSession(sessionId: number, sessionName: string): Promise<ApiResponse<ChatSession>> {
    return this.request<ChatSession>(`/api/rag/chat/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify({
        user_id: 0,  // Wird ignoriert im Backend
        session_name: sessionName
      })
    })
  }

  // Document Management Endpoints
  async indexDocument(params: {
    upload_document_id: number
    force_reindex?: boolean
  }): Promise<ApiResponse<IndexDocumentResponse>> {
    return this.request<IndexDocumentResponse>('/api/rag/documents/index', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async reindexDocument(documentId: number, params: {
    force_reindex?: boolean
  } = {}): Promise<ApiResponse<ReindexDocumentResponse>> {
    return this.request<ReindexDocumentResponse>(`/api/rag/documents/${documentId}/reindex`, {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  /**
   * Prüft ob ein Dokument bereits in RAG indexiert ist.
   * NEU: Für Anzeige des Indexierungs-Status in UI.
   */
  async getDocumentIndexStatus(uploadDocumentId: number): Promise<ApiResponse<{
    is_indexed: boolean
    indexed_document_id: number | null
    indexed_at: string | null
    total_chunks: number | null
    embedding_model: string | null
  }>> {
    return this.request<{
      is_indexed: boolean
      indexed_document_id: number | null
      indexed_at: string | null
      total_chunks: number | null
      embedding_model: string | null
    }>(`/api/rag/documents/${uploadDocumentId}/index-status`)
  }

  async getIndexedDocuments(params: {
    status_filter?: string
    document_type?: string
    page?: number
    size?: number
  } = {}): Promise<ApiResponse<IndexedDocument[]>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    
    const queryString = searchParams.toString()
    return this.request<IndexedDocument[]>(`/api/rag/documents${queryString ? `?${queryString}` : ''}`)
  }

  // Search Endpoints
  async searchDocuments(params: {
    query: string
    top_k?: number
    score_threshold?: number
    document_type?: string
    page_numbers?: number[]
    use_hybrid_search?: boolean
  }) {
    return this.request('/api/rag/search', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  // System Endpoints
  async getSystemInfo() {
    return this.request('/api/rag/system/info')
  }

  async getHealthCheck() {
    return this.request('/api/rag/health')
  }

  async getUsageStatistics() {
    return this.request('/api/rag/statistics')
  }

  // Document Upload Integration
  async getUploadDocuments(params: {
    status?: string
    page?: number
    size?: number
  } = {}) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    
    const queryString = searchParams.toString()
    return this.request(`/api/documentupload/documents${queryString ? `?${queryString}` : ''}`)
  }

  async getDocumentDetails(documentId: number) {
    return this.request(`/api/documentupload/documents/${documentId}`)
  }

  // AI Playground Integration
  async getAIModels() {
    return this.request('/api/aiplayground/models')
  }

  async processDocumentWithAI(params: {
    document_id: number
    model: string
    prompt_template_id?: number
  }) {
    return this.request('/api/aiplayground/process', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  /**
   * Ruft die Anzahl indexierter Dokumente pro Document Type ab.
   */
  async getDocumentTypeCounts(documentTypeIds?: number[]): Promise<ApiResponse<Record<number, number>>> {
    const params = documentTypeIds && documentTypeIds.length > 0 
      ? `?document_type_ids=${documentTypeIds.join(',')}` 
      : ''
    return this.request<Record<number, number>>(
      `/api/rag/documents/types/counts${params}`,
      { method: 'GET' }
    )
  }
}

export const apiClient = new ApiClient()

// Type definitions
export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  source_references?: SourceReference[]
  structured_data?: StructuredData[]
  created_at: string
  ai_model_used?: string
  // PHASE 3.2: Metadaten für Transparency Layer
  metadata?: {
    processing_time_ms?: number
    tokens_used?: number
    query_params?: {
      top_k?: number
      score_threshold?: number
      use_hybrid_search?: boolean
      use_multi_query?: boolean
    }
    embedding_provider?: string
    embedding_dimensions?: number
  }
}

export interface SourceReference {
  document_id: number
  document_title: string
  page_number: number
  chunk_id: number | string  // Kann String (z.B. "doc_14_page_1_text") oder int sein
  preview_image_path?: string
  relevance_score: number
  text_excerpt: string
  
  // NEU: Erweiterte Metadaten (Phase 2: RAG Transparenz)
  vector_score?: number  // Reine Vektor-Ähnlichkeit (0-1)
  text_score?: number  // Text-Matching-Score (0-1)
  hybrid_score?: number  // Kombinierter Score (0-1), entspricht relevance_score
  rank_position?: number  // Position im Ranking (1-basiert)
  total_candidates?: number  // Anzahl der gefundenen Kandidaten vor Filtering
  passed_rbac_filter?: boolean  // Wurde durch RBAC-Filter durchgelassen?
  passed_score_threshold?: boolean  // Erfüllt score_threshold?
  chunk_metadata?: {
    heading_hierarchy?: string[]
    confidence_score?: number
    chunk_type?: string
    token_count?: number
    [key: string]: any  // Weitere Metadaten
  }
  // NEU: Query-Text für Text-Highlighting (Phase 3)
  query_text?: string,  // Die ursprüngliche Query, die zu diesem Source Reference führte
  // NEU: ML Re-Ranking Score (Phase 4)
  ml_score?: number  // ML Re-Ranking Score (0-1), falls ML Re-Ranking verwendet wurde
}

export interface StructuredData {
  data_type: string
  content: Record<string, any>
  confidence: number
}

export interface ChatSession {
  id: number
  session_name: string
  created_at: string
  last_activity: string
  message_count: number
}

export interface IndexedDocument {
  id: number
  upload_document_id: number
  document_title: string
  document_type: string
  status: 'indexed' | 'processing' | 'failed'
  indexed_at: string
  total_chunks: number
  last_updated: string
}

interface IndexDocumentResponse {
  success: boolean
  document: IndexedDocument
  chunks_created: number
  processing_time_ms: number
  message: string
}

interface ReindexDocumentResponse {
  success: boolean
  document: IndexedDocument
  old_chunks_deleted: number
  new_chunks_created: number
  processing_time_ms: number
  message: string
}

export interface SearchResult {
  chunk_id: number
  score: number
  chunk_text: string
  source_reference: SourceReference
  metadata: Record<string, any>
}

export interface AskQuestionResponse {
  answer: string
  source_references: SourceReference[]
  structured_data?: StructuredData[]
  suggested_questions?: string[]
  search_results: SearchResult[]
  model_used: string
  processing_time_ms: number
  tokens_used?: number
  message_id?: number  // NEU: Message-ID für Prompt Viewer
  metadata?: {  // NEU: Metadaten für Transparency Layer (inkl. query_params mit generated_queries)
    processing_time_ms?: number
    tokens_used?: number
    query_params?: {
      top_k?: number
      score_threshold?: number
      use_hybrid_search?: boolean
      use_multi_query?: boolean
      generated_queries?: string[]  // NEU: Generierte Multi-Query Varianten
    }
    prompt_text?: string
    embedding_provider?: string
    embedding_dimensions?: number
  }
  analytics?: {  // NEU v2.7.0: Analytics-Block für Dashboard
    scores?: any[]
    background_data_stats?: any
    cache_stats?: any
    model_info?: any
  }
}

export interface SystemInfo {
  vector_store: {
    type: string
    mode: string
    collection: string
    total_chunks: number
    vector_dimension: number
  }
  embedding_service: {
    model: string
    dimension: number
    provider: string
  }
  repositories: Record<string, string>
  services: Record<string, string>
  total_documents: number
  total_chunks: number
}

export interface HealthCheck {
  overall_status: 'healthy' | 'degraded' | 'unhealthy'
  services: Record<string, string>
  errors: string[]
  timestamp: string
}

export interface UsageStatistics {
  documents: {
    total_indexed: number
    by_status: Record<string, number>
  }
  chunks: {
    total_in_vector_store: number
    average_per_document: number
  }
  vector_store: {
    collection_size: number
    vector_dimension: number
  }
  last_updated: string
}

// Utility functions
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

export const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return 'Heute'
  } else if (diffDays === 1) {
    return 'Gestern'
  } else if (diffDays < 7) {
    return `${diffDays} Tage`
  } else {
    return formatDate(dateString)
  }
}

export const getConfidenceColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600 bg-green-100'
  if (score >= 0.6) return 'text-yellow-600 bg-yellow-100'
  return 'text-red-600 bg-red-100'
}

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'indexed':
      return 'text-green-600 bg-green-100'
    case 'processing':
      return 'text-blue-600 bg-blue-100'
    case 'failed':
      return 'text-red-600 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

// ============================================================================
// CHUNK PREVIEW API (PHASE 2.1)
// ============================================================================

export interface ChunkMetadata {
  page_numbers: number[]
  heading_hierarchy: string[]
  chunk_type: string
  token_count?: number
  sentence_count?: number
  has_overlap: boolean
  overlap_sentence_count: number
}

export interface ChunkPreview {
  id: number
  chunk_id: string
  chunk_text: string
  metadata: ChunkMetadata
  indexed_document_id: number
  created_at: string
}

export interface ChunksListResponse {
  document_id: number
  indexed_document_id: number | null
  total_chunks: number
  chunks: ChunkPreview[]
}

/**
 * Hole alle Chunks für ein Dokument (Read-Only Vorschau).
 * 
 * @param uploadDocumentId - Upload Document ID
 * @returns Liste aller Chunks mit Metadaten
 */
export async function getChunksForDocument(
  uploadDocumentId: number
): Promise<ChunksListResponse> {
  const response = await apiClient.get<ChunksListResponse>(
    `/api/rag/chunks/${uploadDocumentId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// ============================================================================
// CHUNK EDITOR API (PHASE 2.2)
// ============================================================================

/**
 * Bearbeite Chunk-Text.
 * 
 * @param chunkId - Chunk ID
 * @param newText - Neuer Chunk-Text
 * @returns Aktualisierter Chunk
 */
export async function editChunk(
  chunkId: number,
  newText: string
): Promise<ChunkPreview> {
  const response = await apiClient.put<ChunkPreview>(
    `/api/rag/chunks/${chunkId}`,
    { new_text: newText }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Lösche Chunk.
 * 
 * @param chunkId - Chunk ID
 * @returns Success-Status
 */
export async function deleteChunk(chunkId: number): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/api/rag/chunks/${chunkId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Splitte Chunk in zwei Teile.
 * 
 * @param chunkId - Chunk ID
 * @param splitPosition - Split-Position (Character-Index)
 * @returns Liste der zwei neuen Chunks
 */
export async function splitChunk(
  chunkId: number,
  splitPosition: number,
  overlapSentences: number = 0
): Promise<{ success: boolean; message: string; new_chunks: Array<{ id: number; chunk_id: string; chunk_text: string }> }> {
  const response = await apiClient.post<{ success: boolean; message: string; new_chunks: Array<{ id: number; chunk_id: string; chunk_text: string }> }>(
    `/api/rag/chunks/${chunkId}/split`,
    { 
      split_position: splitPosition,
      overlap_sentences: overlapSentences
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Führe mehrere Chunks zusammen.
 * 
 * @param chunkIds - Liste von Chunk IDs (mindestens 2)
 * @returns Zusammengeführter Chunk
 */
export async function mergeChunks(
  chunkIds: number[]
): Promise<{ success: boolean; message: string; merged_chunk: { id: number; chunk_id: string; chunk_text: string } }> {
  const response = await apiClient.post<{ success: boolean; message: string; merged_chunk: { id: number; chunk_id: string; chunk_text: string } }>(
    `/api/rag/chunks/merge`,
    { chunk_ids: chunkIds }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// ============================================================================
// CHUNKING STRATEGY SELECTOR API (PHASE 2.3)
// ============================================================================

export interface ChunkingStrategyOption {
  id: string;
  name: string;
  description: string;
  embedding_provider: string;
  embedding_dimensions: number;
  recommended_for: string[];
  is_default: boolean;
}

export interface ChunkingStrategiesResponse {
  strategies: ChunkingStrategyOption[];
  default_strategy: string;
  document_type_suggestion: string | null;
}

/**
 * Hole alle verfügbaren Chunking-Strategien.
 * 
 * @param documentType - Optional: Dokumenttyp für Empfehlung
 * @returns Liste aller verfügbaren Strategien mit Empfehlungen
 */
export async function getChunkingStrategies(
  documentType?: string
): Promise<ChunkingStrategiesResponse> {
  const endpoint = documentType 
    ? `/api/rag/chunking-strategies?document_type=${encodeURIComponent(documentType)}`
    : '/api/rag/chunking-strategies';
  
  const response = await apiClient.get<ChunkingStrategiesResponse>(endpoint);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// ============================================================================
// RAG CHAT PROMPT VIEWER API (PHASE 3.1)
// ============================================================================

export interface DocumentTypeDistribution {
  document_type: string;
  chunk_count: number;
}

export interface PromptViewerResponse {
  message_id: number;
  question: string;
  prompt_text: string;
  context_chunks: Array<{
    chunk_id: string;
    chunk_text: string;
    metadata?: {
      page_numbers?: number[];
      heading_hierarchy?: string[];
      chunk_type?: string;
      document_type?: string | null;
    };
  }>;
  document_type: string | null;
  model_used: string;
  tokens_used: number | null;
  prompt_state?: string;
  prompt_type?: string;
  document_type_selected?: string;
  document_type_effective?: string;
  document_type_distribution?: DocumentTypeDistribution[];  // NEU: Dokumententyp-Verteilung
}

/**
 * Hole den verwendeten Prompt für eine Chat-Message.
 * 
 * @param messageId - Chat Message ID
 * @returns Prompt-Daten mit vollständigem Prompt-Text
 */
export async function getPromptForMessage(
  messageId: number
): Promise<PromptViewerResponse> {
  const response = await apiClient.get<PromptViewerResponse>(
    `/api/rag/chat/messages/${messageId}/prompt`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// ============================================================================
// RAG FEEDBACK API (PHASE 4.1)
// ============================================================================

export interface FeedbackResponse {
  id: number;
  chat_message_id: number;
  user_id: number;
  rating: string;
  comment: string | null;
  submitted_at: string;
}

export interface FeedbackStatisticsResponse {
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  average_rating: number;
}

export interface SubmitFeedbackRequest {
  chat_message_id: number;
  rating: 'positive' | 'negative' | 'neutral';
  comment?: string | null;
}

/**
 * Gebe Feedback zu einer RAG Chat-Antwort ab.
 * 
 * @param request - Feedback-Daten
 * @returns Gespeichertes Feedback
 */
export async function submitFeedback(
  request: SubmitFeedbackRequest
): Promise<FeedbackResponse> {
  const response = await apiClient.post<FeedbackResponse>(
    '/api/rag/chat/feedback',
    request
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Hole Feedback für eine Chat-Message.
 * 
 * @param messageId - Chat Message ID
 * @returns Feedback oder null wenn keines vorhanden
 */
export async function getFeedbackForMessage(
  messageId: number
): Promise<FeedbackResponse | null> {
  const response = await apiClient.get<FeedbackResponse>(
    `/api/rag/chat/messages/${messageId}/feedback`
  );

  if (response.error) {
    // Wenn 404 oder "Not Found", gibt es kein Feedback
    if (response.error.includes('404') || response.error.includes('Not Found')) {
      return null;
    }
    throw new Error(response.error);
  }

  return response.data || null;
}

/**
 * Hole Feedback-Statistiken.
 * 
 * @param chatMessageId - Optional: Filter nach Chat Message
 * @param userId - Optional: Filter nach User
 * @returns Feedback-Statistiken
 */
export async function getFeedbackStatistics(
  chatMessageId?: number,
  userId?: number
): Promise<FeedbackStatisticsResponse> {
  const params = new URLSearchParams();
  if (chatMessageId) params.append('chat_message_id', chatMessageId.toString());
  if (userId) params.append('user_id', userId.toString());

  const endpoint = `/api/rag/chat/feedback/statistics${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiClient.get<FeedbackStatisticsResponse>(endpoint);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// ============================================================================
// RAG CHAT PROMPT API (PHASE 1 & 2)
// ============================================================================

export interface RAGChatPromptResponse {
  id: number
  document_type_id: number
  prompt_text: string
  multi_query_prompt_text: string | null
  is_custom: boolean
  created_by_user_id: number
  created_at: string
  updated_at: string
}

export interface SaveRAGChatPromptRequest {
  prompt_text: string
  multi_query_prompt_text?: string | null
}

/**
 * Hole RAG Chat Prompt für einen Dokumenttyp.
 * 
 * @param documentTypeId - Document Type ID
 * @returns RAG Chat Prompt (Custom oder Standard)
 */
export async function getRAGChatPrompt(
  documentTypeId: number
): Promise<RAGChatPromptResponse> {
  const response = await apiClient.get<RAGChatPromptResponse>(
    `/api/rag/chat/prompts/${documentTypeId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Speichere RAG Chat Prompt für einen Dokumenttyp (Level 4+).
 * 
 * @param documentTypeId - Document Type ID (null = Default-Prompt)
 * @param request - Prompt-Daten
 * @returns Gespeicherter Prompt
 */
export async function saveRAGChatPrompt(
  documentTypeId: number | null,
  request: SaveRAGChatPromptRequest
): Promise<RAGChatPromptResponse> {
  // Verwende spezielle Route für Default-Prompts
  const endpoint = documentTypeId === null || documentTypeId === 0
    ? '/api/rag/chat/prompts/default'
    : `/api/rag/chat/prompts/${documentTypeId}`
  
  const response = await apiClient.post<RAGChatPromptResponse>(
    endpoint,
    request
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Lösche RAG Chat Prompt (zurücksetzen auf Standard, Level 4+).
 * 
 * @param documentTypeId - Document Type ID (null = Default-Prompt)
 * @returns Success-Status
 */
export async function deleteRAGChatPrompt(
  documentTypeId: number | null
): Promise<{ success: boolean; message: string }> {
  // Verwende spezielle Route für Default-Prompts
  const endpoint = documentTypeId === null || documentTypeId === 0
    ? '/api/rag/chat/prompts/default'
    : `/api/rag/chat/prompts/${documentTypeId}`
  
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    endpoint
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

/**
 * Hole Default RAG Chat Prompt (ohne document_type_id).
 * 
 * Wird verwendet wenn kein Dokumententyp ausgewählt ist.
 * @returns Default RAG Chat Prompt
 */
export async function getDefaultRAGChatPrompt(): Promise<RAGChatPromptResponse> {
  const response = await apiClient.get<RAGChatPromptResponse>(
    `/api/rag/chat/prompts/default`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// ============================================================================
// RAG ANALYTICS API (PHASE 4.2)
// ============================================================================

export interface SHAPStatisticsResponse {
  total_explanations: number;
  average_feature_count: number;
  top_features: Array<{
    feature: string;
    average_importance: number;
  }>;
}

export interface MLPerformanceResponse {
  model_accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  training_samples: number;
}

export interface OptimizationHistoryResponse {
  date: string;
  action: string;
  before_score: number;
  after_score: number;
  improvement: number;
}

export interface RAGAnalyticsResponse {
  feedback: FeedbackStatisticsResponse;
  queries: {
    total: number;
    average_duration_ms: number;
    success_rate: number;
  };
  chunking: {
    started: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  indexing: {
    started: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  messages: {
    total: number;
    assistant: number;
    user: number;
  };
  quality: {
    score: number;
    trend: string;
  };
  shap?: SHAPStatisticsResponse;  // NEU: SHAP-Statistiken (optional)
  ml_performance?: MLPerformanceResponse;  // NEU: ML-Model Performance (optional)
  optimization_history?: OptimizationHistoryResponse[];  // NEU: Optimization History (optional)
  time_range?: {
    start_date?: string | null;
    end_date?: string | null;
  };
}

/**
 * Hole umfassende RAG Analytics.
 * 
 * @param startDate - Optional: Start-Datum (ISO format)
 * @param endDate - Optional: End-Datum (ISO format)
 * @param userId - Optional: Filter nach User ID
 * @returns RAG Analytics Daten
 */
export async function getRAGAnalytics(
  startDate?: string,
  endDate?: string,
  userId?: number
): Promise<RAGAnalyticsResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (userId) params.append('user_id', userId.toString());

  const endpoint = `/api/rag/analytics${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiClient.get<RAGAnalyticsResponse>(endpoint);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Search Quality Analytics Response Types
 */
export interface DocumentTypeDistribution {
  document_type: string;
  count: number;
  average_score: number;
  found_in_top_k: number;
}

export interface ScoreDistribution {
  min: number;
  max: number;
  average: number;
  median: number;
}

export interface TopQuery {
  query: string;
  document_types_found: string[];
  missing_document_types: string[];
  average_score: number;
}

export interface SHAPInsight {
  feature: string;
  impact: number;
  explanation: string;
}

export interface SearchQualityAnalyticsResponse {
  document_type_distribution: DocumentTypeDistribution[];
  score_distribution: ScoreDistribution;
  top_queries: TopQuery[];
  shap_insights: SHAPInsight[];
}

/**
 * Hole Search Quality Analytics.
 * 
 * @param startDate - Optional: Start-Datum (ISO format)
 * @param endDate - Optional: End-Datum (ISO format)
 * @param topK - Optional: Top-K für "found_in_top_k" Berechnung (default: 5)
 * @returns Search Quality Analytics Daten
 */
export async function getSearchQualityAnalytics(
  startDate?: string,
  endDate?: string,
  topK: number = 5
): Promise<SearchQualityAnalyticsResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('top_k', topK.toString());

  const endpoint = `/api/rag/analytics/search-quality${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiClient.get<SearchQualityAnalyticsResponse>(endpoint);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

export default apiClient
