/**
 * Integration Test Setup
 * 
 * Konfiguration und Setup für Integration Tests mit echtem Backend.
 */

import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Integration Test Configuration
export const INTEGRATION_CONFIG = {
  backendUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  testUserId: 1,
  timeout: 30000, // 30 Sekunden Timeout für Integration Tests
  retries: 3
}

// Test Data Factory
export const createTestData = {
  session: (name: string = `Test Session ${Date.now()}`) => ({
    session_name: name,
    user_id: INTEGRATION_CONFIG.testUserId
  }),
  
  message: (content: string = 'Test Message') => ({
    question: content,
    session_id: null,
    model: 'gpt-4o-mini',
    top_k: 5,
    score_threshold: 0.7,
    filters: {},
    use_hybrid_search: true
  }),
  
  document: (id: number = 1) => ({
    upload_document_id: id,
    force_reindex: false
  })
}

// Backend Health Check
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${INTEGRATION_CONFIG.backendUrl}/api/rag/health`)
    return response.ok
  } catch (error) {
    console.warn('Backend Health Check fehlgeschlagen:', error)
    return false
  }
}

// Test Session Management
export class TestSessionManager {
  private sessionIds: number[] = []

  async createSession(name?: string): Promise<number | null> {
    try {
      const { apiClient } = await import('@/lib/api/rag')
      const response = await apiClient.createChatSession(createTestData.session(name))
      
      if (response.data) {
        this.sessionIds.push(response.data.id)
        console.log(`📝 Test Session erstellt: ${response.data.id}`)
        return response.data.id
      }
      return null
    } catch (error) {
      console.error('Fehler beim Erstellen der Test-Session:', error)
      return null
    }
  }

  async cleanup(): Promise<void> {
    const { apiClient } = await import('@/lib/api/rag')
    
    for (const sessionId of this.sessionIds) {
      try {
        await apiClient.deleteChatSession(sessionId)
        console.log(`🗑️ Test Session gelöscht: ${sessionId}`)
      } catch (error) {
        console.error(`Fehler beim Löschen der Session ${sessionId}:`, error)
      }
    }
    
    this.sessionIds = []
  }

  getSessionIds(): number[] {
    return [...this.sessionIds]
  }
}

// Global Test Setup
let testSessionManager: TestSessionManager

beforeAll(async () => {
  // Prüfe Backend-Verfügbarkeit
  const isBackendHealthy = await checkBackendHealth()
  if (!isBackendHealthy) {
    console.warn('⚠️ Backend nicht verfügbar - Integration Tests werden übersprungen')
    throw new Error('Backend nicht verfügbar für Integration Tests')
  }
  
  console.log('✅ Backend ist verfügbar für Integration Tests')
  
  // Initialisiere Test Session Manager
  testSessionManager = new TestSessionManager()
})

beforeEach(async () => {
  // Erstelle Test-Session für jeden Test
  await testSessionManager.createSession()
})

afterEach(() => {
  // Cleanup nach jedem Test
  cleanup()
})

afterAll(async () => {
  // Cleanup aller Test-Sessions
  await testSessionManager.cleanup()
})

// Export für Tests
export { testSessionManager }

// Utility Functions für Tests
export const waitForBackendResponse = async <T>(
  apiCall: () => Promise<T>,
  timeout: number = INTEGRATION_CONFIG.timeout
): Promise<T> => {
  const startTime = Date.now()
  
  while (Date.now() - startTime < timeout) {
    try {
      const result = await apiCall()
      return result
    } catch (error) {
      if (Date.now() - startTime >= timeout) {
        throw error
      }
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
  
  throw new Error(`Backend Response Timeout nach ${timeout}ms`)
}

export const retryApiCall = async <T>(
  apiCall: () => Promise<T>,
  retries: number = INTEGRATION_CONFIG.retries
): Promise<T> => {
  let lastError: Error
  
  for (let i = 0; i < retries; i++) {
    try {
      return await apiCall()
    } catch (error) {
      lastError = error as Error
      console.warn(`API Call fehlgeschlagen (Versuch ${i + 1}/${retries}):`, error)
      
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
      }
    }
  }
  
  throw lastError!
}

// Mock Functions für Tests
export const createMockUser = (overrides: any = {}) => ({
  userId: 1,
  userEmail: 'test@example.com',
  permissions: {
    canIndexDocuments: true,
    canChatRAG: true,
    canManagePrompts: true,
    permissionLevel: 5
  },
  isLoading: false,
  error: null,
  isQMAdmin: true,
  isQM: true,
  ...overrides
})

export const createMockSession = (overrides: any = {}) => ({
  id: 1,
  session_name: 'Test Session',
  created_at: new Date().toISOString(),
  last_activity: new Date().toISOString(),
  message_count: 0,
  ...overrides
})

export const createMockMessage = (overrides: any = {}) => ({
  id: 1,
  role: 'user' as const,
  content: 'Test Message',
  source_references: [],
  structured_data: [],
  created_at: new Date().toISOString(),
  ...overrides
})

// Test Assertions
export const expectApiResponse = (response: any) => {
  expect(response).toBeDefined()
  expect(typeof response).toBe('object')
}

export const expectApiError = (error: any) => {
  expect(error).toBeDefined()
  expect(error).toBeInstanceOf(Error)
}

// Performance Testing Utilities
export const measurePerformance = async <T>(
  operation: () => Promise<T>,
  operationName: string = 'Operation'
): Promise<{ result: T; duration: number }> => {
  const startTime = performance.now()
  const result = await operation()
  const endTime = performance.now()
  const duration = endTime - startTime
  
  console.log(`⏱️ ${operationName} dauerte: ${duration.toFixed(2)}ms`)
  
  return { result, duration }
}

// Test Data Cleanup
export const cleanupTestData = async () => {
  try {
    const { apiClient } = await import('@/lib/api/rag')
    
    // Lösche alle Test-Sessions
    const sessions = await apiClient.getChatSessions(INTEGRATION_CONFIG.testUserId)
    if (sessions.data) {
      for (const session of sessions.data) {
        if (session.session_name.includes('Test Session')) {
          await apiClient.deleteChatSession(session.id)
        }
      }
    }
  } catch (error) {
    console.warn('Cleanup fehlgeschlagen:', error)
  }
}
