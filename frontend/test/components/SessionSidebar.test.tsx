import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/utils/render'
import SessionSidebar from '@/components/SessionSidebar'
import { apiClient } from '@/lib/api/rag'

vi.mock('@/lib/api/rag', () => ({
  apiClient: {
    getChatSessions: vi.fn(),
    createChatSession: vi.fn(),
    deleteChatSession: vi.fn(),
    getChatHistory: vi.fn(),
    askQuestion: vi.fn(),
  },
}))

describe('SessionSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
    sessionStorage.setItem('access_token', 'test-token')

    vi.mocked(apiClient.getChatSessions).mockResolvedValue({ success: true, data: [] })
    vi.mocked(apiClient.createChatSession).mockResolvedValue({
      success: true,
      data: {
        id: 1,
        session_name: 'Test Session',
        created_at: '2024-01-01T00:00:00Z',
        last_activity: '2024-01-01T00:00:00Z',
        message_count: 0,
      },
    })
    vi.mocked(apiClient.deleteChatSession).mockResolvedValue({ success: true, data: {} })
    vi.mocked(apiClient.getChatHistory).mockResolvedValue({
      success: true,
      data: {
        session: {
          id: 1,
          session_name: 'Test Session',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-01T00:00:00Z',
          message_count: 0,
        },
        messages: [],
        total_messages: 0,
      },
    })

    Object.defineProperty(window, 'confirm', {
      value: vi.fn(() => true),
      writable: true,
    })
  })

  it('erstellt automatisch eine Default-Session wenn keine vorhanden ist', async () => {
    renderWithProviders(<SessionSidebar />)
    expect(await screen.findByText('Test Session')).toBeInTheDocument()
    expect(screen.getByText('1 Session')).toBeInTheDocument()
  })

  it('rendert vorhandene Sessions mit Message Count', async () => {
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [
        {
          id: 1,
          session_name: 'Test Session 1',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-01T12:00:00Z',
          message_count: 5,
        },
        {
          id: 2,
          session_name: 'Test Session 2',
          created_at: '2024-01-02T00:00:00Z',
          last_activity: '2024-01-02T12:00:00Z',
          message_count: 3,
        },
      ],
    })

    renderWithProviders(<SessionSidebar />)

    expect(await screen.findByText('Test Session 1')).toBeInTheDocument()
    expect(screen.getByText('Test Session 2')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('2 Sessions')).toBeInTheDocument()
  })

  it('zeigt Ladezustand bei langsamer Session-Abfrage', async () => {
    vi.mocked(apiClient.getChatSessions).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true, data: [] }), 100))
    )

    renderWithProviders(<SessionSidebar />)
    expect(screen.getByText('Lade...')).toBeInTheDocument()
  })

  it('erstellt neue Session mit eingegebenem Namen', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SessionSidebar />)

    await user.click(await screen.findByLabelText('Neue Session erstellen'))
    const input = screen.getByPlaceholderText('Name...')
    await user.type(input, 'Neue Session')
    await user.click(screen.getByText('OK'))

    await waitFor(() => {
      expect(apiClient.createChatSession).toHaveBeenCalledWith({
        session_name: 'Neue Session',
        user_id: 1,
      })
    })
  })

  it('bricht Session-Erstellung per Escape ab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SessionSidebar />)

    await user.click(await screen.findByLabelText('Neue Session erstellen'))
    expect(screen.getByPlaceholderText('Name...')).toBeInTheDocument()
    await user.keyboard('{Escape}')
    expect(screen.queryByPlaceholderText('Name...')).not.toBeInTheDocument()
  })

  it('selektiert Session und lädt History', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [
        {
          id: 11,
          session_name: 'Wartung',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-01T12:00:00Z',
          message_count: 2,
        },
      ],
    })

    renderWithProviders(<SessionSidebar />)

    const sessionName = await screen.findByText('Wartung')
    await user.click(sessionName)
    await waitFor(() => {
      expect(apiClient.getChatHistory).toHaveBeenCalledWith(11)
    })
  })

  it('löscht Session nach Bestätigung', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [
        {
          id: 17,
          session_name: 'Zu löschen',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-01T12:00:00Z',
          message_count: 1,
        },
      ],
    })

    renderWithProviders(<SessionSidebar />)
    await screen.findByText('Zu löschen')
    await user.click(screen.getByTitle('Löschen'))

    await waitFor(() => {
      expect(apiClient.deleteChatSession).toHaveBeenCalledWith(17)
    })
  })

  it('formatiert Datum labels (Heute/Gestern)', async () => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)

    vi.mocked(apiClient.getChatSessions).mockResolvedValue({
      success: true,
      data: [
        {
          id: 1,
          session_name: 'Heute Session',
          created_at: today.toISOString(),
          last_activity: today.toISOString(),
          message_count: 1,
        },
        {
          id: 2,
          session_name: 'Gestern Session',
          created_at: yesterday.toISOString(),
          last_activity: yesterday.toISOString(),
          message_count: 2,
        },
      ],
    })

    renderWithProviders(<SessionSidebar />)
    await screen.findByText('Heute Session')
    expect(screen.getByText('Heute')).toBeInTheDocument()
    expect(screen.getByText('Gestern')).toBeInTheDocument()
  })
})