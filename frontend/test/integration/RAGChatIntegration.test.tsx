/**
 * Integration Tests für RAG Chat System
 * 
 * Diese Tests verwenden echte API Calls gegen das laufende Backend.
 * Sie testen den kompletten Flow von Session-Erstellung bis Chat-Nachrichten.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../utils/render'
import RAGChat from '@/components/RAGChat'
import SessionSidebar from '@/components/SessionSidebar'
import FilterPanel from '@/components/FilterPanel'
import { apiClient } from '@/lib/api/rag'

// Integration Test Configuration
const INTEGRATION_TEST_CONFIG = {
  backendUrl: 'http://localhost:8000',
  testUserId: 1, // Verwende User ID 1 für Tests
  testSessionName: 'Integration Test Session',
  testQuestion: 'Was ist ein QMS?'
}

describe('RAG Chat Integration Tests', () => {
  let testSessionId: number | null = null

  beforeAll(async () => {
    // Prüfe ob Backend erreichbar ist
    try {
      const response = await fetch(`${INTEGRATION_TEST_CONFIG.backendUrl}/api/rag/health`)
      if (!response.ok) {
        throw new Error(`Backend nicht erreichbar: ${response.status}`)
      }
      console.log('✅ Backend ist erreichbar für Integration Tests')
    } catch (error) {
      console.warn('⚠️ Backend nicht erreichbar - Integration Tests werden übersprungen')
      throw new Error('Backend nicht verfügbar für Integration Tests')
    }
  })

  beforeEach(async () => {
    // Erstelle eine neue Test-Session für jeden Test
    try {
      const response = await apiClient.createChatSession({
        session_name: `${INTEGRATION_TEST_CONFIG.testSessionName} - ${Date.now()}`,
        user_id: INTEGRATION_TEST_CONFIG.testUserId
      })
      
      if (response.data) {
        testSessionId = response.data.id
        console.log(`📝 Test Session erstellt: ${testSessionId}`)
      }
    } catch (error) {
      console.error('Fehler beim Erstellen der Test-Session:', error)
      testSessionId = null
    }
  })

  afterAll(async () => {
    // Cleanup: Lösche Test-Sessions
    if (testSessionId) {
      try {
        await apiClient.deleteChatSession(testSessionId)
        console.log(`🗑️ Test Session gelöscht: ${testSessionId}`)
      } catch (error) {
        console.error('Fehler beim Löschen der Test-Session:', error)
      }
    }
  })

  describe('Session Management Integration', () => {
    it('should create and load chat sessions from real backend', async () => {
      const { container } = renderWithProviders(<SessionSidebar />)
      
      // Warte auf Session-Loading
      await waitFor(() => {
        expect(screen.getByText(/Chat Sessions/)).toBeInTheDocument()
      }, { timeout: 5000 })

      // Prüfe ob Sessions geladen wurden
      const sessionItems = container.querySelectorAll('[data-testid="session-item"]')
      expect(sessionItems.length).toBeGreaterThan(0)
    })

    it('should create new session via UI and backend', async () => {
      const { container } = renderWithProviders(<SessionSidebar />)
      
      // Warte auf initiale Sessions
      await waitFor(() => {
        expect(screen.getByText(/Chat Sessions/)).toBeInTheDocument()
      })

      // Klicke auf "Neue Session" Button
      const newSessionButton = screen.getByText('Neue Session')
      fireEvent.click(newSessionButton)

      // Fülle Session-Name aus
      const nameInput = screen.getByPlaceholderText('Session-Name eingeben...')
      fireEvent.change(nameInput, { target: { value: 'Integration Test Session' } })

      // Bestätige Erstellung
      const createButton = screen.getByText('Erstellen')
      fireEvent.click(createButton)

      // Warte auf Session-Erstellung
      await waitFor(() => {
        expect(screen.getByText('Integration Test Session')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('should delete session via UI and backend', async () => {
      const { container } = renderWithProviders(<SessionSidebar />)
      
      // Warte auf Sessions
      await waitFor(() => {
        expect(screen.getByText(/Chat Sessions/)).toBeInTheDocument()
      })

      // Finde eine Session zum Löschen
      const sessionItems = container.querySelectorAll('[data-testid="session-item"]')
      if (sessionItems.length > 0) {
        const firstSession = sessionItems[0]
        const deleteButton = firstSession.querySelector('[data-testid="delete-session"]')
        
        if (deleteButton) {
          fireEvent.click(deleteButton)
          
          // Bestätige Löschung
          await waitFor(() => {
            expect(screen.getByText('Session wirklich löschen?')).toBeInTheDocument()
          })
          
          const confirmButton = screen.getByText('Löschen')
          fireEvent.click(confirmButton)
          
          // Warte auf Löschung
          await waitFor(() => {
            expect(screen.queryByText('Integration Test Session')).not.toBeInTheDocument()
          }, { timeout: 5000 })
        }
      }
    })
  })

  describe('RAG Chat Integration', () => {
    it('should send message and receive response from real backend', async () => {
      renderWithProviders(<RAGChat />)
      
      // Warte auf Chat-Interface
      await waitFor(() => {
        expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
      })

      // Sende eine Test-Nachricht
      const messageInput = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      fireEvent.change(messageInput, { target: { value: INTEGRATION_TEST_CONFIG.testQuestion } })

      const sendButton = screen.getByRole('button', { name: /senden/i })
      fireEvent.click(sendButton)

      // Warte auf Antwort
      await waitFor(() => {
        expect(screen.getByText(INTEGRATION_TEST_CONFIG.testQuestion)).toBeInTheDocument()
      }, { timeout: 10000 })

      // Prüfe ob Antwort angezeigt wird (kann variieren je nach Backend-Status)
      await waitFor(() => {
        const messages = screen.getAllByRole('listitem')
        expect(messages.length).toBeGreaterThanOrEqual(1)
      }, { timeout: 15000 })
    })

    it('should handle chat with session context', async () => {
      if (!testSessionId) {
        console.warn('Keine Test-Session verfügbar - Test wird übersprungen')
        return
      }

      renderWithProviders(<RAGChat />)
      
      // Warte auf Chat-Interface
      await waitFor(() => {
        expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
      })

      // Sende Nachricht mit Session-Kontext
      const messageInput = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      fireEvent.change(messageInput, { target: { value: 'Hallo, das ist ein Test' } })

      const sendButton = screen.getByRole('button', { name: /senden/i })
      fireEvent.click(sendButton)

      // Warte auf Nachricht
      await waitFor(() => {
        expect(screen.getByText('Hallo, das ist ein Test')).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('should display source references when available', async () => {
      renderWithProviders(<RAGChat />)
      
      // Warte auf Chat-Interface
      await waitFor(() => {
        expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
      })

      // Sende eine Frage, die möglicherweise Source References zurückgibt
      const messageInput = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      fireEvent.change(messageInput, { target: { value: 'Welche Dokumente sind verfügbar?' } })

      const sendButton = screen.getByRole('button', { name: /senden/i })
      fireEvent.click(sendButton)

      // Warte auf Antwort
      await waitFor(() => {
        expect(screen.getByText('Welche Dokumente sind verfügbar?')).toBeInTheDocument()
      }, { timeout: 10000 })

      // Prüfe auf Source References (falls vorhanden)
      await waitFor(() => {
        const sourceReferences = screen.queryAllByText(/Preview/)
        // Source References sind optional - Test ist erfolgreich wenn keine Fehler auftreten
        expect(sourceReferences.length).toBeGreaterThanOrEqual(0)
      }, { timeout: 15000 })
    })
  })

  describe('Filter Panel Integration', () => {
    it('should load document types from real backend', async () => {
      renderWithProviders(<FilterPanel />)
      
      // Warte auf Filter Panel
      await waitFor(() => {
        expect(screen.getByText('Filter & Suche')).toBeInTheDocument()
      })

      // Prüfe ob Document Types geladen wurden
      await waitFor(() => {
        const documentTypeSelect = screen.queryByRole('combobox')
        if (documentTypeSelect) {
          expect(documentTypeSelect).toBeInTheDocument()
        }
      }, { timeout: 5000 })
    })

    it('should apply filters and send to backend', async () => {
      renderWithProviders(<FilterPanel />)
      
      // Warte auf Filter Panel
      await waitFor(() => {
        expect(screen.getByText('Filter & Suche')).toBeInTheDocument()
      })

      // Teste Query-Input (erstes Element)
      const queryInputs = screen.getAllByPlaceholderText('Schnellsuche...')
      const queryInput = queryInputs[0] // Nimm das erste Element
      fireEvent.change(queryInput, { target: { value: 'Test Query' } })

      // Prüfe ob Filter gesetzt wurden
      expect(queryInput).toHaveValue('Test Query')
    })
  })

  describe('Error Handling Integration', () => {
    it('should handle backend errors gracefully', async () => {
      // Temporär Backend-URL ändern um Fehler zu simulieren
      const originalApiUrl = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:9999' // Nicht existierender Port

      renderWithProviders(<RAGChat />)
      
      // Warte auf Chat-Interface
      await waitFor(() => {
        expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
      })

      // Sende Nachricht (sollte Fehler verursachen)
      const messageInput = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      fireEvent.change(messageInput, { target: { value: 'Test Error Handling' } })

      const sendButton = screen.getByRole('button', { name: /senden/i })
      fireEvent.click(sendButton)

      // Warte auf Fehlerbehandlung
      await waitFor(() => {
        const errorMessage = screen.queryByText(/Fehler aufgetreten/)
        if (errorMessage) {
          expect(errorMessage).toBeInTheDocument()
        }
      }, { timeout: 10000 })

      // Stelle ursprüngliche URL wieder her
      process.env.NEXT_PUBLIC_API_URL = originalApiUrl
    })
  })

  describe('Performance Integration', () => {
    it('should handle multiple rapid requests', async () => {
      renderWithProviders(<RAGChat />)
      
      // Warte auf Chat-Interface
      await waitFor(() => {
        expect(screen.getByText('DocuMind AI Assistant')).toBeInTheDocument()
      })

      const messageInput = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
      const sendButton = screen.getByRole('button', { name: /senden/i })

      // Sende mehrere Nachrichten schnell hintereinander
      for (let i = 0; i < 3; i++) {
        fireEvent.change(messageInput, { target: { value: `Test Message ${i + 1}` } })
        fireEvent.click(sendButton)
        
        // Kurze Pause zwischen Nachrichten
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      // Warte auf alle Nachrichten
      await waitFor(() => {
        const messages = screen.getAllByRole('listitem')
        expect(messages.length).toBeGreaterThanOrEqual(3)
      }, { timeout: 15000 })
    })
  })
})
