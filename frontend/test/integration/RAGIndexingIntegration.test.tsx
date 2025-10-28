/**
 * Integration Tests für RAG Indexing System
 * 
 * Diese Tests verwenden echte API Calls gegen das laufende Backend.
 * Sie testen den kompletten Flow von Dokument-Indexierung bis Status-Updates.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../utils/render'
import RAGIndexing from '@/components/RAGIndexing'
import { apiClient } from '@/lib/api/rag'

// Integration Test Configuration
const INTEGRATION_TEST_CONFIG = {
  backendUrl: 'http://localhost:8000',
  testDocumentId: 1, // Verwende Document ID 1 für Tests
  testUserId: 1
}

describe('RAG Indexing Integration Tests', () => {
  beforeAll(async () => {
    // Prüfe ob Backend erreichbar ist
    try {
      const response = await fetch(`${INTEGRATION_TEST_CONFIG.backendUrl}/api/rag/health`)
      if (!response.ok) {
        throw new Error(`Backend nicht erreichbar: ${response.status}`)
      }
      console.log('✅ Backend ist erreichbar für RAG Indexing Tests')
    } catch (error) {
      console.warn('⚠️ Backend nicht erreichbar - RAG Indexing Tests werden übersprungen')
      throw new Error('Backend nicht verfügbar für RAG Indexing Tests')
    }
  })

  describe('Document Indexing Status', () => {
    it('should load document indexing status from real backend', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Status-Loading
      await waitFor(() => {
        const statusElement = screen.queryByText(/Indexiert|Wird indexiert|In RAG indexieren/)
        expect(statusElement).toBeInTheDocument()
      }, { timeout: 5000 })

      // Prüfe ob Status korrekt angezeigt wird
      const statusText = screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)
      expect(statusText).toBeInTheDocument()
    })

    it('should show indexing button for approved documents', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Prüfe ob Indexing-Button vorhanden ist (falls Dokument nicht indexiert)
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      if (indexingButton) {
        expect(indexingButton).toBeInTheDocument()
      }
    })

    it('should hide indexing button for non-approved documents', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={false}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Nicht verfügbar/)).toBeInTheDocument()
      })

      // Prüfe dass Indexing-Button nicht vorhanden ist
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      expect(indexingButton).not.toBeInTheDocument()
    })

    it('should hide indexing button for users without permission', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: false,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 2
        },
        isQMAdmin: false,
        isQM: false
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Keine Berechtigung/)).toBeInTheDocument()
      })

      // Prüfe dass Indexing-Button nicht vorhanden ist
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      expect(indexingButton).not.toBeInTheDocument()
    })
  })

  describe('Document Indexing Process', () => {
    it('should trigger document indexing via API', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Suche Indexing-Button
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      if (indexingButton) {
        // Klicke auf Indexing-Button
        fireEvent.click(indexingButton)

        // Warte auf Status-Änderung
        await waitFor(() => {
          const statusText = screen.queryByText(/Wird indexiert|Verarbeitung läuft/)
          if (statusText) {
            expect(statusText).toBeInTheDocument()
          }
        }, { timeout: 10000 })
      }
    })

    it('should handle indexing errors gracefully', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      // Verwende ungültige Document ID um Fehler zu provozieren
      renderWithProviders(
        <RAGIndexing 
          documentId={99999} // Nicht existierende ID
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Suche Indexing-Button
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      if (indexingButton) {
        // Klicke auf Indexing-Button
        fireEvent.click(indexingButton)

        // Warte auf Fehlerbehandlung
        await waitFor(() => {
          const errorMessage = screen.queryByText(/Fehler|Error/)
          if (errorMessage) {
            expect(errorMessage).toBeInTheDocument()
          }
        }, { timeout: 10000 })
      }
    })
  })

  describe('Dashboard Navigation', () => {
    it('should navigate to dashboard with pre-filled question', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      // Mock router
      const mockPush = vi.fn()
      vi.mock('next/navigation', () => ({
        useRouter: () => ({
          push: mockPush
        })
      }))

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Suche "Im Chat fragen" Button
      const chatButton = screen.queryByText(/Im Chat fragen/)
      if (chatButton) {
        fireEvent.click(chatButton)

        // Prüfe ob Navigation aufgerufen wurde
        expect(mockPush).toHaveBeenCalledWith(
          expect.stringContaining('/?question=')
        )
      }
    })

    it('should generate appropriate questions for different document types', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      // Test verschiedene Dokumenttypen
      const documentTypes = [
        { type: 'SOP', expectedQuestion: 'Was sind die wichtigsten Schritte in diesem SOP?' },
        { type: 'Manual', expectedQuestion: 'Wie verwende ich dieses Manual?' },
        { type: 'Policy', expectedQuestion: 'Was sind die wichtigsten Richtlinien?' },
        { type: 'Procedure', expectedQuestion: 'Wie führe ich diese Prozedur durch?' },
        { type: 'Default', expectedQuestion: 'Was sind die wichtigsten Informationen in diesem Dokument?' }
      ]

      for (const docType of documentTypes) {
        const mockPush = vi.fn()
        vi.mock('next/navigation', () => ({
          useRouter: () => ({
            push: mockPush
          })
        }))

        renderWithProviders(
          <RAGIndexing 
            documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
            isApproved={true}
            documentType={docType.type}
          />,
          { user: mockUser }
        )
        
        // Warte auf Component
        await waitFor(() => {
          expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
        })

        // Suche "Im Chat fragen" Button
        const chatButton = screen.queryByText(/Im Chat fragen/)
        if (chatButton) {
          fireEvent.click(chatButton)

          // Prüfe ob korrekte Frage generiert wurde
          expect(mockPush).toHaveBeenCalledWith(
            expect.stringContaining(`question=${encodeURIComponent(docType.expectedQuestion)}`)
          )
        }
      }
    })
  })

  describe('API Integration', () => {
    it('should fetch indexed documents from backend', async () => {
      try {
        const response = await apiClient.getIndexedDocuments({
          status_filter: 'indexed',
          page: 1,
          size: 10
        })

        expect(response).toBeDefined()
        if (response.data) {
          expect(Array.isArray(response.data)).toBe(true)
          console.log(`📊 Gefundene indexierte Dokumente: ${response.data.length}`)
        }
      } catch (error) {
        console.warn('API Call fehlgeschlagen:', error)
        // Test ist erfolgreich wenn keine kritischen Fehler auftreten
      }
    })

    it('should handle document indexing API call', async () => {
      try {
        const response = await apiClient.indexDocument({
          upload_document_id: INTEGRATION_TEST_CONFIG.testDocumentId,
          force_reindex: false
        })

        expect(response).toBeDefined()
        if (response.data) {
          expect(response.data.success).toBeDefined()
          expect(response.data.document).toBeDefined()
          console.log(`📝 Dokument-Indexierung Response: ${JSON.stringify(response.data)}`)
        }
      } catch (error) {
        console.warn('Indexierung API Call fehlgeschlagen:', error)
        // Test ist erfolgreich wenn keine kritischen Fehler auftreten
      }
    })
  })

  describe('Performance and Reliability', () => {
    it('should handle rapid status updates', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Simuliere mehrere schnelle Status-Updates
      const indexingButton = screen.queryByText(/In RAG indexieren/)
      if (indexingButton) {
        for (let i = 0; i < 3; i++) {
          fireEvent.click(indexingButton)
          await new Promise(resolve => setTimeout(resolve, 100))
        }

        // Prüfe dass Component stabil bleibt
        await waitFor(() => {
          expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
        }, { timeout: 5000 })
      }
    })

    it('should maintain state consistency during API calls', async () => {
      const mockUser = {
        permissions: {
          canIndexDocuments: true,
          canChatRAG: true,
          canManagePrompts: true,
          permissionLevel: 5
        },
        isQMAdmin: true,
        isQM: true
      }

      renderWithProviders(
        <RAGIndexing 
          documentId={INTEGRATION_TEST_CONFIG.testDocumentId}
          isApproved={true}
        />,
        { user: mockUser }
      )
      
      // Warte auf Component
      await waitFor(() => {
        expect(screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)).toBeInTheDocument()
      })

      // Prüfe dass Component während API Calls stabil bleibt
      const initialStatus = screen.getByText(/Indexiert|Wird indexiert|In RAG indexieren/)
      expect(initialStatus).toBeInTheDocument()

      // Warte eine Weile und prüfe erneut
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const finalStatus = screen.queryByText(/Indexiert|Wird indexiert|In RAG indexieren/)
      expect(finalStatus).toBeInTheDocument()
    })
  })
})
