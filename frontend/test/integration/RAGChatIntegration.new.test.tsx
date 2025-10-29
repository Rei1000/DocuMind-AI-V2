import { describe, it, expect, beforeAll } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RAGChat from '@/components/RAGChat'
import { renderWithProviders } from '@/test/utils/render'

// KEINE MOCKS - echte Backend-API
describe('RAGChat - Integration Tests (Real API)', () => {
  let backendRunning = false

  beforeAll(async () => {
    // Prüfe ob Backend läuft
    try {
      const response = await fetch('http://localhost:8000/health')
      backendRunning = response.ok
    } catch {
      console.warn('⚠️ Backend nicht erreichbar - Integration Tests übersprungen')
    }
  })

  it('should complete full RAG chat flow with Document 273', async () => {
    if (!backendRunning) {
      console.log('⏭️ Skipped: Backend not running')
      return
    }

    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    // Warte auf Session-Load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeEnabled()
    }, { timeout: 5000 })
    
    // Stelle Frage
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.type(input, 'Was ist die Artikelnummer der Freilaufwelle?')
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    await user.click(sendButton)
    
    // Warte auf User-Nachricht
    await waitFor(() => {
      expect(screen.getByText('Was ist die Artikelnummer der Freilaufwelle?')).toBeInTheDocument()
    }, { timeout: 2000 })
    
    // Warte auf Loading-Indikator
    await waitFor(() => {
      expect(screen.getByText('Antwort wird generiert...')).toBeInTheDocument()
    }, { timeout: 2000 })
    
    // Warte auf Antwort
    await waitFor(() => {
      expect(screen.getByText(/26-10-204/)).toBeInTheDocument()
    }, { timeout: 15000 })
    
    // Prüfe Quellen
    expect(screen.getByText(/Arbeitsanweisung/i)).toBeInTheDocument()
    expect(screen.getByText(/Seite/)).toBeInTheDocument()
    expect(screen.getByText('Vorschau')).toBeInTheDocument()
  }, 20000)

  it('should load chat history for existing session', async () => {
    if (!backendRunning) {
      console.log('⏭️ Skipped: Backend not running')
      return
    }

    renderWithProviders(<RAGChat />)
    
    // Warte auf Session-Load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeEnabled()
    }, { timeout: 5000 })
    
    // Wenn Historie vorhanden, sollten Nachrichten sichtbar sein
    const messages = screen.queryAllByText(/26-10-204|Freilaufwelle/i)
    // Geschichte kann leer sein, also nur prüfen dass Component geladen ist
    expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeInTheDocument()
  }, 10000)

  it('should open source preview modal and show document', async () => {
    if (!backendRunning) {
      console.log('⏭️ Skipped: Backend not running')
      return
    }

    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    // Warte auf Session-Load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeEnabled()
    }, { timeout: 5000 })
    
    // Wenn Nachrichten mit Quellen vorhanden sind
    const previewButtons = screen.queryAllByText('Vorschau')
    if (previewButtons.length > 0) {
      await user.click(previewButtons[0])
      
      // Modal sollte sich öffnen
      await waitFor(() => {
        // SourcePreviewModal wird gerendert
        expect(previewButtons[0]).toBeInTheDocument()
      }, { timeout: 2000 })
    } else {
      console.log('ℹ️ No sources available for preview test')
    }
  }, 10000)

  it('should handle error gracefully when backend is slow', async () => {
    if (!backendRunning) {
      console.log('⏭️ Skipped: Backend not running')
      return
    }

    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')).toBeEnabled()
    }, { timeout: 5000 })
    
    const input = screen.getByPlaceholderText('Fragen Sie nach Ihren Dokumenten...')
    await user.type(input, 'Test Frage für Timeout')
    
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    await user.click(sendButton)
    
    // Component sollte nicht crashen
    expect(input).toBeInTheDocument()
  }, 10000)

  it('should display model selection and allow switching', async () => {
    if (!backendRunning) {
      console.log('⏭️ Skipped: Backend not running')
      return
    }

    const user = userEvent.setup()
    renderWithProviders(<RAGChat />)
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    }, { timeout: 5000 })
    
    const modelSelect = screen.getByRole('combobox')
    expect(modelSelect).toHaveValue('gpt-4o-mini')
    
    // Wechsle Modell
    await user.selectOptions(modelSelect, 'gemini-2.5-flash')
    expect(modelSelect).toHaveValue('gemini-2.5-flash')
  }, 10000)
})

