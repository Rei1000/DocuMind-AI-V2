import { vi } from 'vitest'

/**
 * Mock API Client für Tests
 * 
 * Exportiert gemockte Versionen aller API-Funktionen
 */

export const mockApiClient = {
  // RAG Chat Endpoints
  askQuestion: vi.fn(),
  createChatSession: vi.fn(),
  getChatSessions: vi.fn(),
  getChatHistory: vi.fn(),
  deleteChatSession: vi.fn(),
  
  // Document Management
  indexDocument: vi.fn(),
  reindexDocument: vi.fn(),
  getIndexedDocuments: vi.fn(),
  
  // Search
  searchDocuments: vi.fn(),
  
  // System
  getSystemInfo: vi.fn(),
  getHealthCheck: vi.fn(),
  getUsageStatistics: vi.fn()
}

/**
 * Reset all mocks
 * Call this in beforeEach() or afterEach()
 */
export const resetMocks = () => {
  Object.values(mockApiClient).forEach(mock => {
    mock.mockReset()
  })
}

/**
 * Mock successful API responses
 */
export const mockSuccessResponses = () => {
  mockApiClient.getChatSessions.mockResolvedValue({
    data: [
      {
        id: 1,
        session_name: 'Test Session',
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        message_count: 5
      }
    ]
  })

  mockApiClient.createChatSession.mockResolvedValue({
    data: {
      id: 1,
      session_name: 'New Session',
      created_at: new Date().toISOString(),
      last_activity: new Date().toISOString(),
      message_count: 0
    }
  })

  mockApiClient.askQuestion.mockResolvedValue({
    data: {
      answer: 'Test answer',
      source_references: [],
      structured_data: [],
      suggested_questions: [],
      search_results: [],
      model_used: 'gpt-4o-mini',
      processing_time_ms: 100,
      tokens_used: 50
    }
  })

  mockApiClient.getChatHistory.mockResolvedValue({
    data: {
      messages: [
        {
          id: 1,
          role: 'user',
          content: 'Test question',
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          role: 'assistant',
          content: 'Test answer',
          source_references: [],
          created_at: new Date().toISOString()
        }
      ]
    }
  })

  mockApiClient.getIndexedDocuments.mockResolvedValue({
    data: [
      {
        id: 1,
        upload_document_id: 1,
        document_title: 'Test Document',
        document_type: 'SOP',
        status: 'indexed',
        indexed_at: new Date().toISOString(),
        total_chunks: 10,
        last_updated: new Date().toISOString()
      }
    ]
  })
}

