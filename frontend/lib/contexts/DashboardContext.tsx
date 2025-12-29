'use client'

import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { useUser } from '@/lib/contexts/UserContext'
import { apiClient } from '@/lib/api/rag'

export interface ChatSession {
  id: number
  session_name: string
  created_at: string
  last_activity: string
  message_count: number
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  source_references?: any[]
  structured_data?: any[]
  ai_model_used?: string  // AI Model das für diese Nachricht verwendet wurde
  metadata?: {
    processing_time_ms?: number
    tokens_used?: number
    query_params?: {
      top_k?: number
      score_threshold?: number
      use_hybrid_search?: boolean
      use_multi_query?: boolean
      generated_queries?: string[]  // NEU: Generierte Multi-Query Varianten
    }
    embedding_provider?: string
    embedding_dimensions?: number
    document_type_effective?: string  // NEU: Dokumenttyp der tatsächlich verwendet wurde (aus Chunks)
    document_type_selected?: string  // NEU: Dokumenttyp der vom User ausgewählt wurde (Filter)
  }
  created_at: string
}

export interface SearchFilters {
  query: string
  documentType: string
  dateRange: {
    from: string
    to: string
  }
  pageNumbers: number[]
  minConfidence: number
  topK: number  // NEU: Anzahl der besten Chunks für die Antwort
  useHybridSearch: boolean
  useMultiQuery: boolean  // NEU: MultiQuery-Option für Query-Expansion
  useMlRanking: boolean  // NEU: ML Re-Ranking (Phase 4) - Learning-to-Rank ML-Ranking (v2.7.0)
  adaptiveMinAvgScore: number  // NEU v2.9.2: Adaptive Filterung - Mindest-Durchschnitts-Score (0-0.5)
  adaptiveMinMaxScore: number  // NEU v2.9.2: Adaptive Filterung - Mindest-Maximal-Score (0-0.5)
}

export interface DashboardState {
  // Session Management
  sessions: ChatSession[]
  selectedSessionId: number | null
  currentMessages: ChatMessage[]
  
  // Filter Management
  searchFilters: SearchFilters
  
  // Loading States
  isLoadingSessions: boolean
  isLoadingMessages: boolean
  isLoadingFilters: boolean
  
  // Error States
  error: string | null
}

export interface DashboardContextType extends DashboardState {
  // Session Actions
  createSession: (sessionName: string) => Promise<void>
  selectSession: (sessionId: number) => Promise<void>
  deleteSession: (sessionId: number) => Promise<void>
  updateSessionName: (sessionId: number, newName: string) => Promise<void>
  loadSessions: () => Promise<void>
  
  // Message Actions
  sendMessage: (
    content: string,
    model?: string,
    aiSettings?: {
      temperature: number
      max_tokens: number
      top_p: number
    }
  ) => Promise<void>
  loadSessionHistory: (sessionId: number) => Promise<void>
  
  // Filter Actions
  updateFilters: (filters: Partial<SearchFilters>) => void
  clearFilters: () => void
  
  // Utility Actions
  clearError: () => void
}

const defaultFilters: SearchFilters = {
  query: '',
  documentType: '',
  dateRange: {
    from: '',
    to: ''
  },
  pageNumbers: [],
  minConfidence: 0.01,  // 1% - Standard für OpenAI Embeddings (Scores liegen bei 0.02-0.03)
  topK: 5,  // Standard: 5 beste Chunks
  useHybridSearch: true,
  useMultiQuery: false,  // NEU: Standard deaktiviert (User kann aktivieren)
  useMlRanking: false,  // NEU: ML Re-Ranking (Phase 4) - Learning-to-Rank ML-Ranking (v2.7.0) - Standard deaktiviert
  adaptiveMinAvgScore: 0.15,  // NEU v2.9.2: 15% - Standard für adaptive Filterung (Durchschnitts-Score)
  adaptiveMinMaxScore: 0.25  // NEU v2.9.2: 25% - Standard für adaptive Filterung (Maximal-Score)
}

const defaultState: DashboardState = {
  sessions: [],
  selectedSessionId: null,
  currentMessages: [],
  searchFilters: defaultFilters,
  isLoadingSessions: false,
  isLoadingMessages: false,
  isLoadingFilters: false,
  error: null
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const { userId, permissions } = useUser()
  const pathname = usePathname()
  const [state, setState] = useState<DashboardState>(defaultState)
  
  // Ref für Race Condition Prevention
  const isLoadingSessionsRef = useRef(false)
  // Ref um vorherigen pathname zu tracken
  const previousPathnameRef = useRef<string | null>(null)

  // Load sessions on mount und beim Zurückkehren zur Dashboard-Seite
  useEffect(() => {
    const isOnDashboard = pathname === '/'
    const shouldLoad = userId && permissions.canChatRAG && !isLoadingSessionsRef.current
    const previousPathname = previousPathnameRef.current
    
    // Prüfe ob pathname sich geändert hat
    const pathnameChanged = previousPathname !== null && previousPathname !== pathname
    
    // Wir kehren zur Dashboard-Seite zurück, wenn:
    // - Wir jetzt auf Dashboard sind
    // - Pathname sich geändert hat
    // - Vorher waren wir NICHT auf Dashboard (also auf einer anderen Seite)
    const isReturningToDashboard = isOnDashboard && pathnameChanged && previousPathname !== '/' && previousPathname !== null
    
    // Erste Ladung: previousPathname ist null und wir sind auf Dashboard
    const isFirstLoad = previousPathname === null && isOnDashboard
    
    // FIX: Prüfe ob Sessions noch nicht geladen wurden (leere Liste)
    const hasNoSessions = state.sessions.length === 0
    
    console.log('DashboardContext: useEffect triggered', { 
      userId, 
      canChatRAG: permissions.canChatRAG, 
      isLoading: isLoadingSessionsRef.current,
      pathname,
      previousPathname,
      pathnameChanged,
      isOnDashboard,
      isReturningToDashboard,
      isFirstLoad,
      hasNoSessions,
      sessionsCount: state.sessions.length
    })
    
    // Wenn wir auf der Dashboard-Seite sind und die Bedingungen erfüllt sind
    // Lade Sessions wenn:
    // 1. Erste Ladung (isFirstLoad === true)
    // 2. Zurückkehren von einer anderen Seite (isReturningToDashboard === true)
    // 3. FIX: ODER wenn noch keine Sessions geladen wurden (hasNoSessions === true)
    if (isOnDashboard && shouldLoad && (isFirstLoad || isReturningToDashboard || hasNoSessions)) {
      console.log('DashboardContext: On dashboard page, calling loadSessions', {
        reason: isFirstLoad ? 'first load' : (isReturningToDashboard ? 'returning from other page' : 'no sessions loaded')
      })
      loadSessions()
    } else {
      console.log('DashboardContext: NOT calling loadSessions', { 
        userId, 
        canChatRAG: permissions.canChatRAG, 
        isLoading: isLoadingSessionsRef.current,
        isOnDashboard,
        previousPathname,
        pathnameChanged,
        isReturningToDashboard,
        isFirstLoad,
        hasNoSessions,
        sessionsCount: state.sessions.length
      })
    }
    
    // Update previous pathname NACH der Prüfung
    previousPathnameRef.current = pathname
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, permissions.canChatRAG, pathname, state.sessions.length]) // FIX: state.sessions.length hinzugefügt, um auf leere Sessions zu reagieren

  // Session Management - VEREINFACHT
  const loadSessions = async () => {
    if (!userId || isLoadingSessionsRef.current) return
    
    isLoadingSessionsRef.current = true
    
    try {
      setState(prev => ({ ...prev, isLoadingSessions: true, error: null }))

      const response = await apiClient.getChatSessions(userId)
      console.log('DashboardContext: API response:', response)

      if (response.data && response.data.length > 0) {
        console.log('DashboardContext: Loaded', response.data.length, 'sessions')
        // Bestimme Session: localStorage > State > erste Session
        let sessionToUse: number | null = null
        if (typeof window !== 'undefined') {
          const saved = localStorage.getItem('rag_selected_session_id')
          if (saved) {
            const parsed = parseInt(saved, 10)
            if (!isNaN(parsed) && response.data.some(s => s.id === parsed)) {
              sessionToUse = parsed
              console.log('DashboardContext: Using saved session from localStorage:', sessionToUse)
            }
          }
        }
        
        if (!sessionToUse && state.selectedSessionId && response.data.some(s => s.id === state.selectedSessionId)) {
          sessionToUse = state.selectedSessionId
          console.log('DashboardContext: Using current session from state:', sessionToUse)
        }
        
        if (!sessionToUse) {
          sessionToUse = response.data[0].id
          console.log('DashboardContext: Using first available session:', sessionToUse)
        }
        
        if (typeof window !== 'undefined') {
          localStorage.setItem('rag_selected_session_id', String(sessionToUse))
        }

        console.log('DashboardContext: Setting sessions in state:', response.data.length)
        setState(prev => ({
          ...prev,
          sessions: response.data!,
          selectedSessionId: sessionToUse,
          isLoadingSessions: false
        }))
        
        // WICHTIG: Setze isLoadingSessionsRef NACH setState, damit Race Conditions vermieden werden
        isLoadingSessionsRef.current = false
        
        if (sessionToUse) {
          loadSessionHistory(sessionToUse).catch(console.error)
        }
      } else {
        console.log('DashboardContext: No sessions found, creating default session')
        // Auto-create default session if none exist
        const defaultSessionName = `Chat - ${new Date().toLocaleDateString('de-DE')}`
        const response = await apiClient.createChatSession({
          user_id: userId,
          session_name: defaultSessionName
        })

        if (response.data) {
          console.log('DashboardContext: Default session created:', response.data.id)
          // Persist to localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('rag_selected_session_id', String(response.data!.id))
          }
          setState(prev => ({
            ...prev,
            sessions: [response.data!],
            isLoadingSessions: false,
            selectedSessionId: response.data!.id
          }))
        }
      }
    } catch (error) {
      console.error('DashboardContext: Fehler beim Laden der Sessions:', error)

      // Try to create default session even on error
      try {
        const defaultSessionName = `Chat - ${new Date().toLocaleDateString('de-DE')}`
        const response = await apiClient.createChatSession({
          user_id: userId,
          session_name: defaultSessionName
        })

        if (response.data) {
          // Persist to localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('rag_selected_session_id', String(response.data!.id))
          }
          setState(prev => ({
            ...prev,
            sessions: [response.data!],
            isLoadingSessions: false,
            selectedSessionId: response.data!.id,
            error: null
          }))
          isLoadingSessionsRef.current = false
        } else {
          setState(prev => ({
            ...prev,
            isLoadingSessions: false,
            error: 'Fehler beim Laden der Sessions'
          }))
          isLoadingSessionsRef.current = false
        }
      } catch (createError) {
        console.error('DashboardContext: Fehler beim Erstellen der Default-Session:', createError)
        setState(prev => ({
          ...prev,
          isLoadingSessions: false,
          error: 'Fehler beim Laden der Sessions'
        }))
        isLoadingSessionsRef.current = false
      }
    } finally {
      // WICHTIG: Stelle sicher, dass isLoadingSessionsRef immer zurückgesetzt wird
      if (isLoadingSessionsRef.current) {
        console.warn('DashboardContext: isLoadingSessionsRef wurde nicht korrekt zurückgesetzt, setze jetzt...')
        isLoadingSessionsRef.current = false
        setState(prev => ({ ...prev, isLoadingSessions: false }))
      }
    }
  }

  const createSession = async (sessionName: string) => {
    if (!userId) return

    try {
      console.log('DashboardContext: Creating new session:', sessionName)
      
      const response = await apiClient.createChatSession({
        user_id: userId,
        session_name: sessionName
      })

      if (response.data) {
        console.log('DashboardContext: Session created successfully:', response.data.id)
        
        // Persist to localStorage IMMEDIATELY
        if (typeof window !== 'undefined') {
          localStorage.setItem('rag_selected_session_id', String(response.data!.id))
          console.log('DashboardContext: New session persisted to localStorage:', response.data.id)
        }
        
        // Lade Sessions neu um sicherzustellen dass alles synchron ist
        console.log('DashboardContext: Reloading sessions after creation')
        await loadSessions()
      } else {
        throw new Error('Fehler beim Erstellen der Session')
      }
    } catch (error) {
      console.error('Fehler beim Erstellen der Session:', error)
      setState(prev => ({
        ...prev,
        error: 'Fehler beim Erstellen der Session'
      }))
      throw error  // Re-throw damit Frontend den Fehler sehen kann
    }
  }

  const selectSession = async (sessionId: number) => {
    try {
      console.log('DashboardContext: Selecting session:', sessionId)
      
      // Persist selected session to localStorage IMMEDIATELY
      if (typeof window !== 'undefined') {
        localStorage.setItem('rag_selected_session_id', String(sessionId))
        console.log('DashboardContext: Session persisted to localStorage:', sessionId)
      }

      setState(prev => ({
        ...prev,
        selectedSessionId: sessionId,
        currentMessages: []  // Clear messages when switching sessions
      }))

      // Load session history
      console.log('DashboardContext: Loading history for selected session:', sessionId)
      await loadSessionHistory(sessionId)
    } catch (error) {
      console.error('Fehler beim Auswählen der Session:', error)
      setState(prev => ({
        ...prev,
        error: 'Fehler beim Auswählen der Session'
      }))
    }
  }

  const updateSessionName = async (sessionId: number, newName: string) => {
    if (!newName.trim()) return

    try {
      console.log('DashboardContext: Updating session name:', sessionId, newName)
      const response = await apiClient.updateChatSession(sessionId, newName.trim())

      if (response.data) {
        console.log('DashboardContext: Session updated:', response.data)
        // Lade Sessions neu um sicherzustellen dass alles synchron ist
        console.log('DashboardContext: Reloading sessions after update')
        await loadSessions()
      } else {
        throw new Error('Fehler beim Aktualisieren der Session')
      }
    } catch (error) {
      console.error('Fehler beim Aktualisieren der Session:', error)
      setState(prev => ({
        ...prev,
        error: 'Fehler beim Aktualisieren der Session'
      }))
      throw error
    }
  }

  const deleteSession = async (sessionId: number) => {
    try {
      const response = await apiClient.deleteChatSession(sessionId)

      if (!response.error) {
        setState(prev => {
          const newSessions = prev.sessions.filter(session => session.id !== sessionId)
          
          // If deleted session was selected, select another one
          let newSelectedSessionId = prev.selectedSessionId
          if (prev.selectedSessionId === sessionId) {
            newSelectedSessionId = newSessions.length > 0 ? newSessions[0].id : null
            if (newSelectedSessionId) {
              // Persist new selection
              if (typeof window !== 'undefined') {
                localStorage.setItem('rag_selected_session_id', String(newSelectedSessionId))
              }
              selectSession(newSelectedSessionId)
            } else {
              // No sessions left, clear localStorage
              if (typeof window !== 'undefined') {
                localStorage.removeItem('rag_selected_session_id')
              }
            }
          }

          return {
            ...prev,
            sessions: newSessions,
            selectedSessionId: newSelectedSessionId,
            currentMessages: prev.selectedSessionId === sessionId ? [] : prev.currentMessages
          }
        })
      } else {
        throw new Error('Fehler beim Löschen der Session')
      }
    } catch (error) {
      console.error('Fehler beim Löschen der Session:', error)
      setState(prev => ({
        ...prev,
        error: 'Fehler beim Löschen der Session'
      }))
    }
  }

  // Message Management
  const loadSessionHistory = async (sessionId: number) => {
    try {
      setState(prev => ({ ...prev, isLoadingMessages: true, error: null }))

      const response = await apiClient.getChatHistory(sessionId)
      
      if (response.data?.messages) {
        console.log(`DashboardContext: Loaded ${response.data.messages.length} messages for session ${sessionId}`)
        setState(prev => ({
          ...prev,
          currentMessages: response.data!.messages,
          isLoadingMessages: false
        }))
      } else {
        console.log(`DashboardContext: No messages found for session ${sessionId}`)
        setState(prev => ({
          ...prev,
          currentMessages: [],
          isLoadingMessages: false
        }))
      }
    } catch (error) {
      console.error('Fehler beim Laden der Chat History:', error)
      setState(prev => ({
        ...prev,
        currentMessages: [],
        isLoadingMessages: false,
        error: 'Fehler beim Laden der Chat History'
      }))
    }
  }

  const sendMessage = async (
    content: string,
    model: string = 'gpt-4o-mini',
    aiSettings?: {
      temperature: number
      max_tokens: number
      top_p: number
    }
  ) => {
    // Ensure we have a session - create one if needed
    let sessionId = state.selectedSessionId
    
    // Prüfe ob Session existiert, falls nicht erstelle eine
    if (!sessionId && userId) {
      console.log('DashboardContext: No session selected, creating new session')
      try {
        const defaultSessionName = `Chat - ${new Date().toLocaleDateString('de-DE')}`
        const createResponse = await apiClient.createChatSession({
          user_id: userId,
          session_name: defaultSessionName
        })
        
        if (createResponse.data) {
          console.log('DashboardContext: Created new session for message:', createResponse.data.id)
          // Persist to localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('rag_selected_session_id', String(createResponse.data!.id))
          }
          setState(prev => ({
            ...prev,
            sessions: [createResponse.data!, ...prev.sessions],
            selectedSessionId: createResponse.data!.id
          }))
          sessionId = createResponse.data!.id
        } else {
          console.error('DashboardContext: Failed to create session, response:', createResponse)
          throw new Error('Fehler beim Erstellen der Session: Keine Daten erhalten')
        }
      } catch (error) {
        console.error('DashboardContext: Fehler beim Erstellen der Session:', error)
        throw error
      }
    }
    
    if (!sessionId) {
      console.error('DashboardContext: No session ID available and could not create one')
      throw new Error('Keine Session verfügbar und konnte keine erstellen')
    }
    
    console.log('DashboardContext: Sending message to session:', sessionId)

    try {
      // Set loading state IMMEDIATELY
      setState(prev => ({ ...prev, isLoadingMessages: true, error: null }))
      
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: Date.now(),
        role: 'user',
        content,
        created_at: new Date().toISOString()
      }

      setState(prev => ({
        ...prev,
        currentMessages: [...prev.currentMessages, userMessage]
      }))

      // Kombiniere Frage mit Schnellsuche-Query (falls gesetzt)
      let finalQuestion = content
      if (state.searchFilters.query && state.searchFilters.query.trim()) {
        // Wenn Schnellsuche gesetzt ist, verwende sie als zusätzlichen Kontext
        finalQuestion = `${state.searchFilters.query}. ${content}`
      }

      // Send to API with selected model
      const response = await apiClient.askQuestion({
        question: finalQuestion,
        session_id: sessionId,
        model: model,  // Verwende übergebenes Model statt hardcodiert
        top_k: state.searchFilters.topK,
        score_threshold: state.searchFilters.minConfidence,
        filters: {
          document_type: state.searchFilters.documentType || undefined,
          page_numbers: state.searchFilters.pageNumbers.length > 0 ? state.searchFilters.pageNumbers : undefined,
          date_from: state.searchFilters.dateRange.from || undefined,
          date_to: state.searchFilters.dateRange.to || undefined,
          query: state.searchFilters.query && state.searchFilters.query.trim() ? state.searchFilters.query.trim() : undefined  // Schnellsuche als Filter
        },
        use_hybrid_search: state.searchFilters.useHybridSearch,
        use_multi_query: state.searchFilters.useMultiQuery,  // NEU: MultiQuery-Option
        // Backward-compat: use_ml_reranking ist deprecated, aber Backend kennt es noch
        use_ml_reranking: false,
        // NEU: Learning-to-Rank ML-Ranking (v2.7.0)
        use_ml_ranking: state.searchFilters.useMlRanking,
        // NEU v2.10.3: AI Settings (pro Nachricht)
        temperature: aiSettings?.temperature,
        max_tokens: aiSettings?.max_tokens,
        top_p: aiSettings?.top_p
      })

      if (response.data) {
        console.log('DashboardContext: Received response from backend:', {
          answerLength: response.data.answer?.length || 0,
          sourcesCount: response.data.source_references?.length || 0,
          modelUsed: response.data.model_used || model,
          hasAnalytics: !!response.data.analytics  // NEU v2.7.0
        })
        
        // NEU v2.7.0: Speichere Analytics-Daten in localStorage für Analytics-Dashboard
        if (response.data.analytics) {
          try {
            localStorage.setItem('lastAnalytics', JSON.stringify(response.data.analytics))
            console.log('✅ Analytics-Daten gespeichert:', {
              scores: response.data.analytics.scores?.length || 0,
              background_stats: !!response.data.analytics.background_data_stats,
              cache_stats: !!response.data.analytics.cache_stats,
              model_info: !!response.data.analytics.model_info
            })
          } catch (error) {
            console.error('Fehler beim Speichern der Analytics-Daten:', error)
          }
        }
        
        const assistantMessage: ChatMessage = {
          id: response.data.message_id || Date.now() + 1,  // WICHTIG: Verwende echte Message-ID aus Backend
          role: 'assistant',
          content: response.data.answer || 'Keine Antwort erhalten',
          source_references: response.data.source_references || [],
          structured_data: response.data.structured_data,
          ai_model_used: response.data.model_used || model,  // Verwende Model aus Response oder übergebenes Model
          created_at: new Date().toISOString(),
          // PHASE 3.2: Verwende Metadaten aus Response (inkl. query_params mit generated_queries)
          // Falls keine Metadaten in Response, erstelle sie manuell (Fallback)
          metadata: response.data.metadata || {
            processing_time_ms: response.data.processing_time_ms,
            tokens_used: response.data.tokens_used,
            query_params: {
              top_k: state.searchFilters.topK,
              score_threshold: state.searchFilters.minConfidence,
              use_hybrid_search: state.searchFilters.useHybridSearch,
              use_multi_query: state.searchFilters.useMultiQuery
            }
            // embedding_provider und embedding_dimensions werden später aus Audit-Log geholt
          }
        }
        
        // Debug: Log source_references
        if (typeof window !== 'undefined' && assistantMessage.source_references && assistantMessage.source_references.length > 0) {
          console.log('DashboardContext: Assistant message with references:', {
            messageLength: assistantMessage.content.length,
            referencesCount: assistantMessage.source_references.length,
            references: assistantMessage.source_references,
            hasPattern: /\*\*Referenz\*\*:\s*chunk\s*\d+/gi.test(assistantMessage.content)
          })
        }

        setState(prev => ({
          ...prev,
          currentMessages: [...prev.currentMessages, assistantMessage],
          isLoadingMessages: false  // Reset loading state after success
        }))
      } else {
        console.error('DashboardContext: No data in response:', response)
        throw new Error(response.error || 'Unbekannter Fehler: Keine Daten erhalten')
      }
    } catch (error) {
      console.error('Fehler beim Senden der Nachricht:', error)
      
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Entschuldigung, es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.',
        created_at: new Date().toISOString()
      }

      setState(prev => ({
        ...prev,
        currentMessages: [...prev.currentMessages, errorMessage],
        isLoadingMessages: false,  // Reset loading state on error
        error: 'Fehler beim Senden der Nachricht'
      }))
      
      // Re-throw error so component can handle it (e.g., show toast)
      throw error
    }
  }

  // Filter Management
  const updateFilters = (filters: Partial<SearchFilters>) => {
    setState(prev => ({
      ...prev,
      searchFilters: { ...prev.searchFilters, ...filters }
    }))
  }

  const clearFilters = () => {
    setState(prev => ({
      ...prev,
      searchFilters: defaultFilters
    }))
  }

  // Utility Actions
  const clearError = () => {
    setState(prev => ({ ...prev, error: null }))
  }

  const contextValue: DashboardContextType = {
    ...state,
    createSession,
    selectSession,
    updateSessionName,
    deleteSession,
    loadSessions,
    sendMessage,
    loadSessionHistory,
    updateFilters,
    clearFilters,
    clearError
  }

  return (
    <DashboardContext.Provider value={contextValue}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const context = useContext(DashboardContext)
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider')
  }
  return context
}
