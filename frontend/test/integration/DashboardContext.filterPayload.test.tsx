import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DashboardProvider, useDashboard } from '@/lib/contexts/DashboardContext'
import { UserContext, UserContextType } from '@/lib/contexts/UserContext'

const { askQuestionMock, createChatSessionMock } = vi.hoisted(() => ({
  askQuestionMock: vi.fn(),
  createChatSessionMock: vi.fn()
}))

vi.mock('next/navigation', () => ({
  usePathname: () => '/'
}))

vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getChatSessions: vi.fn().mockResolvedValue({
      data: [
        {
          id: 101,
          session_name: 'Filter Test Session',
          created_at: '2026-02-01T10:00:00Z',
          last_activity: '2026-02-01T10:00:00Z',
          message_count: 0
        }
      ]
    }),
    getChatHistory: vi.fn().mockResolvedValue({
      data: { session: { id: 101 }, messages: [], total_messages: 0 }
    }),
    createChatSession: createChatSessionMock,
    deleteChatSession: vi.fn(),
    updateChatSession: vi.fn(),
    askQuestion: askQuestionMock
  }
}))

function FilterPayloadHarness() {
  const { selectedSessionId, updateFilters, sendMessage } = useDashboard()

  return (
    <div>
      <div data-testid="selected-session">{selectedSessionId ?? 'none'}</div>
      <button
        data-testid="profile-a"
        onClick={() =>
          updateFilters({
            documentType: '1',
            pageNumbers: [2, 7],
            minConfidence: 0.019,
            topK: 8,
            useHybridSearch: true,
            useMultiQuery: true,
            useMlRanking: true,
            adaptiveMinAvgScore: 0.11,
            adaptiveMinMaxScore: 0.21
          })
        }
      >
        Profile A
      </button>

      <button
        data-testid="profile-b"
        onClick={() =>
          updateFilters({
            documentType: '',
            pageNumbers: [],
            minConfidence: 0.005,
            topK: 3,
            useHybridSearch: false,
            useMultiQuery: false,
            useMlRanking: false,
            adaptiveMinAvgScore: 0.02,
            adaptiveMinMaxScore: 0.04
          })
        }
      >
        Profile B
      </button>

      <button
        data-testid="send"
        onClick={() => sendMessage('trägheitsmoment', 'gemini-2.5-flash')}
      >
        Send
      </button>
    </div>
  )
}

const mockUser: UserContextType = {
  userId: 1,
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
  },
  isLoading: false,
  error: null,
  isQMAdmin: true,
  isQM: true,
  userLevel: 5,
  isQmsAdmin: true,
  interestGroupIds: [],
  interestGroupsWithLevels: [],
  hasPermission: () => true,
  canAccess: () => true,
  getLevelForInterestGroup: () => 5,
  canPerformActionOnDocument: () => true
}

describe('DashboardContext Filter Payload', () => {
  beforeEach(() => {
    askQuestionMock.mockReset()
    createChatSessionMock.mockReset()
    askQuestionMock.mockResolvedValue({
      data: {
        answer: 'ok',
        source_references: [],
        model_used: 'gemini-2.5-flash',
        processing_time_ms: 12
      }
    })
    createChatSessionMock.mockResolvedValue({
      data: {
        id: 202,
        session_name: 'Created Session',
        created_at: '2026-02-01T10:00:00Z',
        last_activity: '2026-02-01T10:00:00Z',
        message_count: 0
      }
    })
  })

  it('sendet MultiQuery + ML + adaptive Filter dynamisch', async () => {
    render(
      <UserContext.Provider value={mockUser}>
        <DashboardProvider>
          <FilterPayloadHarness />
        </DashboardProvider>
      </UserContext.Provider>
    )

    fireEvent.click(screen.getByTestId('profile-a'))
    await waitFor(() => expect(screen.getByTestId('selected-session').textContent).not.toBe('none'))
    fireEvent.click(screen.getByTestId('send'))

    await waitFor(() => expect(askQuestionMock).toHaveBeenCalled())
    const payload = askQuestionMock.mock.calls.at(-1)?.[0]

    expect(payload.model).toBe('gemini-2.5-flash')
    expect(payload.top_k).toBe(8)
    expect(payload.score_threshold).toBe(0.019)
    expect(payload.use_hybrid_search).toBe(true)
    expect(payload.use_multi_query).toBe(true)
    expect(payload.use_ml_ranking).toBe(true)
    expect(payload.adaptive_min_avg_score).toBe(0.11)
    expect(payload.adaptive_min_max_score).toBe(0.21)
    expect(payload.filters.document_type).toBe('1')
    expect(payload.filters.page_numbers).toEqual([2, 7])
  })

  it('ändert Parameter pro Profil ohne Hardcoding', async () => {
    render(
      <UserContext.Provider value={mockUser}>
        <DashboardProvider>
          <FilterPayloadHarness />
        </DashboardProvider>
      </UserContext.Provider>
    )

    fireEvent.click(screen.getByTestId('profile-a'))
    await waitFor(() => expect(screen.getByTestId('selected-session').textContent).not.toBe('none'))
    fireEvent.click(screen.getByTestId('send'))

    await waitFor(() => expect(askQuestionMock).toHaveBeenCalledTimes(1))
    const firstPayload = askQuestionMock.mock.calls[0][0]

    fireEvent.click(screen.getByTestId('profile-b'))
    fireEvent.click(screen.getByTestId('send'))

    await waitFor(() => expect(askQuestionMock).toHaveBeenCalledTimes(2))
    const secondPayload = askQuestionMock.mock.calls[1][0]

    expect(firstPayload.top_k).toBe(8)
    expect(secondPayload.top_k).toBe(3)
    expect(firstPayload.use_multi_query).toBe(true)
    expect(secondPayload.use_multi_query).toBe(false)
    expect(firstPayload.use_ml_ranking).toBe(true)
    expect(secondPayload.use_ml_ranking).toBe(false)
    expect(firstPayload.adaptive_min_avg_score).toBe(0.11)
    expect(secondPayload.adaptive_min_avg_score).toBe(0.02)
    expect(firstPayload.adaptive_min_max_score).toBe(0.21)
    expect(secondPayload.adaptive_min_max_score).toBe(0.04)
    expect(firstPayload.use_hybrid_search).toBe(true)
    expect(secondPayload.use_hybrid_search).toBe(false)
  })
})
