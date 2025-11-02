import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { UserContext, UserContextType, UserPermissions } from '@/lib/contexts/UserContext'
import { DashboardProvider } from '@/lib/contexts/DashboardContext'

// Default mock user for tests
const defaultMockUser: UserContextType = {
  userId: 1, // Verwende echten User aus der DB
  userEmail: 'qms.admin@company.com',
  permissions: {
    canIndexDocuments: true,
    canChatRAG: true,
    canManagePrompts: true,
    canUploadDocuments: true,
    canAccessUserManagement: true,
    canAccessKanban: true,
    canAccessDocumentsList: true,
    permissionLevel: 5,
    userLevel: 5
  } as UserPermissions,
  isLoading: false,
  error: null,
  isQMAdmin: true,
  isQM: true,
  // RBAC Phase 4
  userLevel: 5,
  isQmsAdmin: true,
  interestGroupIds: [],
  // RBAC Multi-Level
  interestGroupsWithLevels: [],
  hasPermission: (requiredLevel: number) => 5 >= requiredLevel,
  canAccess: (feature: string) => {
    const featureMap: Record<string, boolean> = {
      'users': true,
      'upload': true,
      'kanban': true,
      'documents-list': true,
      'prompt-management': true,
      'ai-models': true,
      'rag-chat': true
    }
    return featureMap[feature] || false
  },
  getLevelForInterestGroup: () => 5,
  canPerformActionOnDocument: () => true
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  user?: Partial<typeof defaultMockUser>
}

/**
 * Custom render function with UserContext Provider
 * 
 * Usage:
 * ```
 * renderWithUser(<MyComponent />, {
 *   user: { permissions: { canIndexDocuments: false } }
 * })
 * ```
 */
export function renderWithUser(
  ui: ReactElement,
  { user = {}, ...renderOptions }: CustomRenderOptions = {}
) {
  const mockUser = { ...defaultMockUser, ...user }

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <UserContext.Provider value={mockUser}>
        {children}
      </UserContext.Provider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

/**
 * Custom render function with both UserContext and DashboardContext Providers
 * 
 * Usage:
 * ```
 * renderWithProviders(<MyComponent />, {
 *   user: { permissions: { canIndexDocuments: false } }
 * })
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  { user = {}, ...renderOptions }: CustomRenderOptions = {}
) {
  const mockUser = { ...defaultMockUser, ...user }

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <UserContext.Provider value={mockUser}>
        <DashboardProvider>
          {children}
        </DashboardProvider>
      </UserContext.Provider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react'
export { renderWithUser as render }

