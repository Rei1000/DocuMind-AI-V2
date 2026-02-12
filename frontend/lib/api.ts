// API Client utilities for DocuMind-AI Frontend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    // Wichtig: localStorage für neue Tabs / Deep-Links, sessionStorage als Fallback
    return (
      localStorage.getItem('access_token') ||
      localStorage.getItem('token') ||
      sessionStorage.getItem('access_token') ||
      sessionStorage.getItem('token')
    )
  }

  private getAuthHeaders(): HeadersInit {
    const token = this.getAuthToken()
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    }
  }

  private getAuthHeadersWithoutContentType(): HeadersInit {
    const token = this.getAuthToken()
    return {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    }
  }

  private shouldForceLogoutOnUnauthorized(endpoint: string): boolean {
    // Harte Logout-Entscheidung nur auf Auth-Selbsttest.
    // Ein 401 auf Nebenendpunkten (z.B. temporäre Backend-Probleme) soll
    // nicht sofort die ganze Session zerstören.
    return endpoint.startsWith('/api/auth/me')
  }

  private handleUnauthorized(endpoint: string): ApiResponse<never> {
    if (typeof window !== 'undefined' && this.shouldForceLogoutOnUnauthorized(endpoint)) {
      console.warn('[API] Auth-Check 401, leite zu Login um...')
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('token')
      window.location.href = '/login'
      return {
        error: 'Token abgelaufen. Bitte neu anmelden.',
        status: 401,
      }
    }

    return {
      error: 'Unauthorized',
      status: 401,
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      })

      if (response.status === 401) {
        return this.handleUnauthorized(endpoint)
      }

      const data = await response.json()
      
      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      }
    } catch (error) {
      return {
        error: 'Network error',
        status: 0,
      }
    }
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(body),
      })

      if (response.status === 401) {
        return this.handleUnauthorized(endpoint)
      }

      const data = await response.json()
      
      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      }
    } catch (error) {
      return {
        error: 'Network error',
        status: 0,
      }
    }
  }

  async postForm<T>(endpoint: string, formData: FormData, timeout: number = 1800000): Promise<ApiResponse<T>> {
    try {
      // Timeout Controller (default: 30 Minuten für lange KI-Verarbeitung)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getAuthHeadersWithoutContentType(),
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      const data = await response.json()
      
      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        return {
          error: 'Request timeout - Upload dauert zu lange (> 30 Min)',
          status: 408,
        }
      }
      return {
        error: 'Network error',
        status: 0,
      }
    }
  }

  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(body),
      })

      if (response.status === 401) {
        return this.handleUnauthorized(endpoint)
      }

      const data = await response.json()
      
      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      }
    } catch (error) {
      return {
        error: 'Network error',
        status: 0,
      }
    }
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      })

      if (response.status === 401) {
        return this.handleUnauthorized(endpoint)
      }

      // HTTP 204 No Content hat keinen Body!
      if (response.status === 204) {
        return {
          data: {} as T,  // Empty object als Success indicator
          status: 204,
        }
      }

      const data = await response.json()
      
      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      }
    } catch (error) {
      return {
        error: 'Network error',
        status: 0,
      }
    }
  }
}

export const apiClient = new ApiClient()

// Import types
import type { 
  User, 
  UserCreate, 
  UserUpdate,
  InterestGroup,
  InterestGroupCreate,
  InterestGroupUpdate,
  UserGroupMembership,
  UserGroupMembershipCreate,
  Token,
  UserInfo,
  GenericResponse
} from '@/types'

// Specific API functions
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<Token>('/api/auth/login', { email, password }),
  
  me: () =>
    apiClient.get<UserInfo>('/api/auth/me'),
}

export const interestGroupsApi = {
  list: () =>
    apiClient.get<InterestGroup[]>('/api/interest-groups'),
  
  get: (id: number) =>
    apiClient.get<InterestGroup>(`/api/interest-groups/${id}`),
  
  create: (data: InterestGroupCreate) =>
    apiClient.post<InterestGroup>('/api/interest-groups', data),
  
  update: (id: number, data: InterestGroupUpdate) =>
    apiClient.put<InterestGroup>(`/api/interest-groups/${id}`, data),
  
  delete: (id: number) =>
    apiClient.delete<GenericResponse>(`/api/interest-groups/${id}`),
}

export const usersApi = {
  list: () =>
    apiClient.get<User[]>('/api/users'),
  
  get: (id: number) =>
    apiClient.get<User>(`/api/users/${id}`),
  
  create: (data: UserCreate) =>
    apiClient.post<User>('/api/users', data),
  
  update: (id: number, data: UserUpdate) =>
    apiClient.put<User>(`/api/users/${id}`, data),
  
  deactivate: (id: number) =>
    apiClient.post<GenericResponse>(`/api/users/${id}/deactivate`, {}),
  
  reactivate: (id: number) =>
    apiClient.post<GenericResponse>(`/api/users/${id}/reactivate`, {}),
  
  getMemberships: (id: number) =>
    apiClient.get<UserGroupMembership[]>(`/api/users/${id}/memberships`),
  
  addMembership: (userId: number, data: UserGroupMembershipCreate) =>
    apiClient.post<UserGroupMembership>(`/api/users/${userId}/memberships`, data),
  
  removeMembership: (userId: number, groupId: number) =>
    apiClient.delete<GenericResponse>(`/api/users/${userId}/memberships/${groupId}`),
}
