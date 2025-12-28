'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

/**
 * User Permissions Interface
 * 
 * Definiert die verschiedenen Berechtigungen basierend auf user_level (RBAC Phase 1):
 * - Level 1: Mitarbeiter (nur RAG Chat, nur eigene Interest Groups)
 * - Level 2: Teamleiter (RAG Chat + Dokumenten-Liste, nur eigene Interest Groups)
 * - Level 3: Abteilungsleiter (RAG Chat + Kanban, nur eigene Interest Groups)
 * - Level 4: QM Mitarbeiter (RAG Chat + Indexierung + Upload + alle Dokumente)
 * - Level 5: QMS Admin (alle Rechte)
 */
export interface UserPermissions {
  canIndexDocuments: boolean  // Nur QM Admin, QM (Level 4+)
  canChatRAG: boolean         // Alle authenticated users (Level 1+)
  canManagePrompts: boolean   // Nur QMS Admin (Level 5)
  canUploadDocuments: boolean // Nur QM (Level 4+)
  canAccessUserManagement: boolean // Nur QMS Admin (Level 5)
  canAccessKanban: boolean    // Abteilungsleiter+ (Level 3+)
  canAccessDocumentsList: boolean // Teamleiter+ (Level 2+)
  permissionLevel: number     // 1-5 (Legacy-Alias für userLevel)
  userLevel: number           // 1-5 (RBAC Phase 1: user_level aus JWT Token)
}

/**
 * User Context Interface
 * 
 * RBAC Phase 4: Erweitert um user_level, is_qms_admin, interest_group_ids aus JWT Token
 * RBAC Multi-Level: Erweitert um interest_groups_with_levels
 */
export interface UserContextType {
  userId: number | null
  userEmail: string | null
  permissions: UserPermissions
  isQMAdmin: boolean
  isQM: boolean
  isLoading: boolean
  error: string | null
  // RBAC Phase 4: Neue Felder aus JWT Token
  userLevel: number           // 1-5 (aus JWT Token: user_level)
  isQmsAdmin: boolean         // true wenn Level 5 (aus JWT Token: is_qms_admin)
  interestGroupIds: number[]  // Liste der Interest Group IDs (aus JWT Token: interest_group_ids)
  // RBAC Multi-Level: Interest Groups mit Levels
  interestGroupsWithLevels: Array<{
    id: number
    level: number
    name: string
  }>
  // Helper Functions
  hasPermission: (requiredLevel: number) => boolean  // Prüft ob userLevel >= requiredLevel
  canAccess: (feature: string) => boolean            // Feature-basierte Berechtigung
  getLevelForInterestGroup: (igId: number) => number  // Hole Level für spezifische IG
  canPerformActionOnDocument: (
    documentInterestGroupIds: number[],
    requiredLevel: number
  ) => boolean  // Context-specific Permission Check
}

/**
 * User Context
 */
export const UserContext = createContext<UserContextType>({
  userId: null,
  userEmail: null,
  permissions: {
    canIndexDocuments: false,
    canChatRAG: false,
    canManagePrompts: false,
    canUploadDocuments: false,
    canAccessUserManagement: false,
    canAccessKanban: false,
    canAccessDocumentsList: false,
    permissionLevel: 1,
    userLevel: 1
  },
  isQMAdmin: false,
  isQM: false,
  isLoading: true,
  error: null,
  // RBAC Phase 4
  userLevel: 1,
  isQmsAdmin: false,
  interestGroupIds: [],
  // RBAC Multi-Level
  interestGroupsWithLevels: [],
  hasPermission: () => false,
  canAccess: () => false,
  getLevelForInterestGroup: () => 0,
  canPerformActionOnDocument: () => false
})

/**
 * User Provider Props
 */
interface UserProviderProps {
  children: ReactNode
}

/**
 * User Provider Component
 * 
 * Lädt User-Daten beim Mount und berechnet Permissions
 */
export function UserProvider({ children }: UserProviderProps) {
  const [userId, setUserId] = useState<number | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [permissions, setPermissions] = useState<UserPermissions>({
    canIndexDocuments: false,
    canChatRAG: false,
    canManagePrompts: false,
    canUploadDocuments: false,
    canAccessUserManagement: false,
    canAccessKanban: false,
    canAccessDocumentsList: false,
    permissionLevel: 1,
    userLevel: 1
  })
  // RBAC Phase 4: Neue State-Variablen
  const [userLevel, setUserLevel] = useState<number>(1)
  const [isQmsAdmin, setIsQmsAdmin] = useState<boolean>(false)
  const [interestGroupIds, setInterestGroupIds] = useState<number[]>([])
  // RBAC Multi-Level: Interest Groups mit Levels
  const [interestGroupsWithLevels, setInterestGroupsWithLevels] = useState<Array<{
    id: number
    level: number
    name: string
  }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /**
   * RBAC Phase 4: Parse JWT Token und extrahiere user_level, is_qms_admin, interest_group_ids
   * RBAC Multi-Level: Erweitert um interest_groups_with_levels
   */
  const parseJWTToken = (token: string): { 
    userLevel: number
    isQmsAdmin: boolean
    interestGroupIds: number[]
    interestGroupsWithLevels: Array<{ id: number; level: number; name: string }>
  } => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      const payload = JSON.parse(jsonPayload)
      
      // RBAC Phase 4: Extrahiere neue Felder
      const level = payload.user_level || payload.permission_level || 1
      const isAdmin = payload.is_qms_admin || level === 5
      const igIds = payload.interest_group_ids || []
      
      // RBAC Multi-Level: Extrahiere Interest Groups mit Levels
      const igsWithLevels = payload.interest_groups_with_levels || []
      const normalizedIgs = Array.isArray(igsWithLevels)
        ? igsWithLevels.map((ig: any) => ({
            id: ig.interest_group_id || ig.id || 0,
            level: ig.approval_level || ig.level || 1,
            name: ig.interest_group_name || ig.name || 'Unknown'
          }))
        : []
      
      return {
        userLevel: level,
        isQmsAdmin: isAdmin,
        interestGroupIds: Array.isArray(igIds) ? igIds : [],
        interestGroupsWithLevels: normalizedIgs
      }
    } catch (e) {
      console.error('Failed to parse JWT token:', e)
      return { 
        userLevel: 1, 
        isQmsAdmin: false, 
        interestGroupIds: [],
        interestGroupsWithLevels: []
      }
    }
  }

  /**
   * Berechne Permissions basierend auf user_level (RBAC Phase 4)
   */
  const calculatePermissions = (userLevel: number): UserPermissions => {
    return {
      canIndexDocuments: userLevel >= 4,        // QM Mitarbeiter (Level 4+)
      canChatRAG: userLevel >= 1,                // Alle (Level 1+)
      canManagePrompts: userLevel === 5,        // Nur QMS Admin (Level 5)
      canUploadDocuments: userLevel >= 4,       // QM Mitarbeiter (Level 4+)
      canAccessUserManagement: userLevel === 5, // Nur QMS Admin (Level 5)
      canAccessKanban: userLevel >= 3,          // Abteilungsleiter (Level 3+)
      canAccessDocumentsList: userLevel >= 2,   // Teamleiter (Level 2+)
      permissionLevel: userLevel,               // Legacy-Alias
      userLevel                                  // RBAC Phase 4: Neues Feld
    }
  }

  /**
   * Lade User-Daten vom Backend
   */
  const loadUserData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Token-Quelle: localStorage (Tab-übergreifend) bevorzugt, sessionStorage fallback
      const token =
        localStorage.getItem('access_token') ||
        localStorage.getItem('token') ||
        sessionStorage.getItem('access_token') ||
        sessionStorage.getItem('token')
      if (!token) {
        throw new Error('No access token found')
      }

      // RBAC Phase 4: Extrahiere RBAC-Felder direkt aus JWT Token (schneller, zuverlässiger)
      let extractedLevel = 1
      let extractedIsAdmin = false
      let extractedIgIds: number[] = []
      let extractedIgsWithLevels: Array<{ id: number; level: number; name: string }> = []
      
      try {
        const tokenData = parseJWTToken(token)
        extractedLevel = tokenData.userLevel
        extractedIsAdmin = tokenData.isQmsAdmin
        extractedIgIds = tokenData.interestGroupIds
        extractedIgsWithLevels = tokenData.interestGroupsWithLevels
        console.log('UserContext: Extracted from JWT Token - Level:', extractedLevel, 'IsAdmin:', extractedIsAdmin, 'IGs:', extractedIgIds, 'IGs with Levels:', extractedIgsWithLevels)
      } catch (e) {
        console.error('UserContext: Failed to parse token, will use backend fallback:', e)
      }

      // Lade User-Daten vom Backend
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const userData = await response.json()
      console.log('UserContext: User data loaded:', userData)
      
      // Setze User-Daten
      setUserId(userData.id)
      setUserEmail(userData.email)
      
      // Fallback: Falls JWT Token keine Daten hat, versuche aus Backend-Response
      let permissionLevel = extractedLevel || userData.user_level || userData.permission_level
      if (!permissionLevel || permissionLevel === undefined) {
        // Fallback: Bestimme Level basierend auf vorhandenen permissions
        const perms = userData.permissions || []
        if (perms.includes('system_administration') || userData.capabilities?.can_manage_users) {
          permissionLevel = 5  // QMS Admin
        } else {
          permissionLevel = 1  // Standard User (kann RAG Chat nutzen)
        }
        console.log('UserContext: permission_level not found, using fallback:', permissionLevel)
      }
      
      // Setze RBAC-Felder
      setUserLevel(extractedLevel || permissionLevel)
      setIsQmsAdmin(extractedIsAdmin || permissionLevel === 5)
      setInterestGroupIds(extractedIgIds.length > 0 ? extractedIgIds : [])
      // RBAC Multi-Level: Setze Interest Groups mit Levels
      setInterestGroupsWithLevels(extractedIgsWithLevels.length > 0 ? extractedIgsWithLevels : [])
      
      // Berechne und setze Permissions
      const finalLevel = extractedLevel || permissionLevel
      const userPermissions = calculatePermissions(finalLevel)
      console.log('UserContext: Calculated permissions:', userPermissions)
      setPermissions(userPermissions)

      // Store user_id für API calls
      sessionStorage.setItem('user_id', userData.id.toString())
      localStorage.setItem('user_id', userData.id.toString())

    } catch (err) {
      console.error('Failed to load user data:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      
      // Fallback: Versuche JWT Token zu parsen (auch bei Fehler)
      const token =
        localStorage.getItem('access_token') ||
        localStorage.getItem('token') ||
        sessionStorage.getItem('access_token') ||
        sessionStorage.getItem('token')
      if (token) {
        try {
          const tokenData = parseJWTToken(token)
          setUserLevel(tokenData.userLevel)
          setIsQmsAdmin(tokenData.isQmsAdmin)
          setInterestGroupIds(tokenData.interestGroupIds)
          setInterestGroupsWithLevels(tokenData.interestGroupsWithLevels)
          setPermissions(calculatePermissions(tokenData.userLevel))
          console.log('UserContext: Fallback - Using JWT Token data:', tokenData)
        } catch (e) {
          console.error('UserContext: Failed to parse token in fallback:', e)
        }
      }
      
      // Fallback: Setze Default-Werte
      setUserId(1) // Default für Tests
      setUserEmail('test@example.com')
      if (!token) {
        setPermissions(calculatePermissions(1))
        setUserLevel(1)
        setIsQmsAdmin(false)
        setInterestGroupIds([])
        setInterestGroupsWithLevels([])
      }
      sessionStorage.setItem('user_id', '1')
      localStorage.setItem('user_id', '1')
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Effect: Lade User-Daten beim Mount
   */
  // Lade User-Daten beim Mount
  useEffect(() => {
    loadUserData()
  }, [])

  // RBAC Fix: Reagiere auf Token-Änderungen (z.B. beim Login)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      // Wenn access_token geändert wurde, lade User-Daten neu
      if (e.key === 'access_token' && e.newValue) {
        console.log('UserContext: Token changed, reloading user data...')
        loadUserData()
      }
    }

    // Höre auf Storage-Events (von anderen Tabs/Windows)
    window.addEventListener('storage', handleStorageChange)

    // Höre auch auf Custom Events (vom gleichen Tab)
    const handleCustomStorageChange = () => {
      console.log('UserContext: Custom storage event, reloading user data...')
      loadUserData()
    }
    window.addEventListener('tokenChanged', handleCustomStorageChange)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('tokenChanged', handleCustomStorageChange)
    }
  }, [])

  // Zusätzlich: Prüfe alle 2 Sekunden ob Token geändert wurde (Fallback für gleichen Tab)
  useEffect(() => {
    let lastToken =
      localStorage.getItem('access_token') ||
      localStorage.getItem('token') ||
      sessionStorage.getItem('access_token') ||
      sessionStorage.getItem('token')
    
    const checkTokenChange = () => {
      const currentToken =
        localStorage.getItem('access_token') ||
        localStorage.getItem('token') ||
        sessionStorage.getItem('access_token') ||
        sessionStorage.getItem('token')
      if (currentToken !== lastToken) {
        console.log('UserContext: Token changed (polling), reloading user data...')
        lastToken = currentToken
        loadUserData()
      }
    }

    // Prüfe alle 2 Sekunden
    const interval = setInterval(checkTokenChange, 2000)

    return () => clearInterval(interval)
  }, [])

  /**
   * Berechne abgeleitete Werte
   */
  const isQMAdmin = permissions.userLevel >= 5
  const isQM = permissions.userLevel >= 4

  /**
   * RBAC Phase 4: Helper Functions
   */
  const hasPermission = (requiredLevel: number): boolean => {
    return userLevel >= requiredLevel
  }

  const canAccess = (feature: string): boolean => {
    // Analytics: Level 4+ (QM Mitarbeiter+)
    if (feature === 'analytics') {
      return userLevel >= 4;
    }
    // Feature-basierte Berechtigungen gemäß RBAC_SPECIFICATION.md
    const featureMap: Record<string, boolean> = {
      'users': userLevel === 5,              // Nur QMS Admin
      'upload': userLevel >= 4,              // QM Mitarbeiter+
      'kanban': userLevel >= 3,              // Abteilungsleiter+
      'documents-list': userLevel >= 2,      // Teamleiter+ (normale Dokumenten-Liste)
      'archive': userLevel >= 4,             // QM Mitarbeiter+ (Archiv)
      'prompt-management': userLevel === 5,  // Nur QMS Admin
      'ai-models': userLevel === 5,          // Nur QMS Admin
      'rag-chat': userLevel >= 1             // Alle
    }
    return featureMap[feature] || false
  }

  /**
   * RBAC Multi-Level: Helper Functions
   */
  const getLevelForInterestGroup = (igId: number): number => {
    const ig = interestGroupsWithLevels.find(ig => ig.id === igId)
    return ig ? ig.level : 0
  }

  const canPerformActionOnDocument = (
    documentInterestGroupIds: number[],
    requiredLevel: number
  ): boolean => {
    // Level 4-5: Immer berechtigt
    if (userLevel >= 4) {
      return true
    }

    // Level 1-3: Prüfe ob User für mindestens eine IG des Dokuments das required_level hat
    for (const docIgId of documentInterestGroupIds) {
      const userLevelForIg = getLevelForInterestGroup(docIgId)
      if (userLevelForIg >= requiredLevel) {
        return true
      }
    }

    // User hat für keine IG des Dokuments das required_level
    return false
  }

  const contextValue: UserContextType = {
    userId,
    userEmail,
    permissions,
    isQMAdmin,
    isQM,
    isLoading,
    error,
    // RBAC Phase 4: Neue Felder
    userLevel,
    isQmsAdmin,
    interestGroupIds,
    // RBAC Multi-Level: Interest Groups mit Levels
    interestGroupsWithLevels,
    hasPermission,
    canAccess,
    // RBAC Multi-Level: Helper Functions
    getLevelForInterestGroup,
    canPerformActionOnDocument
  }

  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  )
}

/**
 * Hook: useUser
 * 
 * Gibt den aktuellen User Context zurück
 */
export function useUser(): UserContextType {
  const context = useContext(UserContext)
  
  if (!context) {
    throw new Error('useUser must be used within a UserProvider')
  }
  
  return context
}

/**
 * Hook: usePermissions
 * 
 * Gibt nur die Permissions zurück (convenience hook)
 */
export function usePermissions(): UserPermissions {
  const { permissions } = useUser()
  return permissions
}

/**
 * Hook: useCanIndexDocuments
 * 
 * Convenience hook für RAG Indexierung Permission
 */
export function useCanIndexDocuments(): boolean {
  const { permissions } = useUser()
  return permissions.canIndexDocuments
}

export default UserContext
