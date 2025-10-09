// DocuMind-AI V2 TypeScript Types

// ===== Interest Groups =====

export interface InterestGroup {
  id: number
  name: string
  code: string
  description: string
  group_permissions?: string
  ai_functionality?: string
  typical_tasks?: string
  is_external: boolean
  is_active: boolean
  created_at: string
}

export interface InterestGroupCreate {
  name: string
  code: string
  description?: string
  group_permissions?: string
  ai_functionality?: string
  typical_tasks?: string
  is_external?: boolean
}

export interface InterestGroupUpdate {
  name?: string
  code?: string
  description?: string
  group_permissions?: string
  ai_functionality?: string
  typical_tasks?: string
  is_external?: boolean
  is_active?: boolean
}

// ===== Users =====

export interface User {
  id: number
  email: string
  full_name: string
  employee_id?: string
  organizational_unit?: string
  individual_permissions?: string[]
  is_department_head: boolean
  approval_level: number
  is_active: boolean
  is_qms_admin?: boolean  // Level 5 - QMS Admin
  cannot_be_deleted?: boolean  // Protection flag
  created_at: string
  updated_at?: string
  
  // Legacy compatibility
  department?: {
    interest_group: {
      id: number
      name: string
      code: string
    }
    level: number
  }
  permissions?: string[]
  memberships?: UserGroupMembership[]
}

export interface UserCreate {
  email: string
  full_name: string
  password: string
  employee_id?: string
  organizational_unit?: string
  individual_permissions?: string[]
  is_department_head?: boolean
  approval_level?: number
}

export interface UserUpdate {
  email?: string
  full_name?: string
  employee_id?: string
  organizational_unit?: string
  individual_permissions?: string[]
  is_department_head?: boolean
  approval_level?: number
  is_active?: boolean
}

// ===== User Group Memberships =====

export interface UserGroupMembership {
  id: number
  user_id: number
  interest_group_id: number
  approval_level: number
  role_in_group?: string
  is_department_head: boolean
  is_active: boolean
  joined_at: string
  notes?: string
  
  // Relationships
  user?: User
  interest_group?: InterestGroup
}

export interface UserGroupMembershipCreate {
  user_id: number
  interest_group_id: number
  approval_level?: number
  role_in_group?: string
  is_department_head?: boolean
  notes?: string
}

// ===== Authentication =====

export interface LoginRequest {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  email: string
  full_name: string
  organizational_unit?: string
  is_department_head: boolean
  approval_level: number
  is_active: boolean
  groups: string[]
  permissions: string[]
}

// ===== Generic =====

export interface GenericResponse {
  message: string
  success: boolean
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}
