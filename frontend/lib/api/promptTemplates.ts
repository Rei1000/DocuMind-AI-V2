/**
 * Prompt Templates API Client
 * 
 * Kommuniziert mit /api/prompt-templates Endpoints
 */

import { apiClient } from '../api'

export enum PromptStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DEPRECATED = 'deprecated'
}

export interface PromptTemplate {
  id: number
  name: string
  description: string
  prompt_text: string
  system_instructions: string | null
  document_type_id: number | null
  ai_model: string
  temperature: number
  max_tokens: number
  top_p: number
  detail_level: string
  status: string
  version: string
  tested_successfully: boolean
  success_count: number
  last_used_at: string | null
  tags: string[]
  example_input: string | null
  example_output: string | null
  created_at: string
  updated_at: string
}

export interface PromptTemplateCreate {
  name: string
  prompt_text: string
  description?: string
  document_type_id?: number | null
  ai_model?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  detail_level?: string
  system_instructions?: string | null
  tags?: string[]
}

export interface PromptTemplateUpdate {
  name?: string
  prompt_text?: string
  description?: string
  document_type_id?: number | null
  ai_model?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  detail_level?: string
  system_instructions?: string | null
  tags?: string[]
}

export interface PromptTemplateFromPlayground {
  name: string
  prompt_text: string
  ai_model: string
  temperature: number
  max_tokens: number
  top_p: number
  detail_level: string
  tokens_sent: number
  tokens_received: number
  response_time_ms: number
  description?: string
  document_type_id?: number | null
  example_output?: string | null
}

// API Functions
export const getPromptTemplates = async (
  status?: string,
  documentTypeId?: number,
  activeOnly: boolean = false
): Promise<PromptTemplate[]> => {
  let url = `/api/prompt-templates?active_only=${activeOnly}`
  if (status) url += `&status=${status}`
  if (documentTypeId) url += `&document_type_id=${documentTypeId}`
  
  const response = await apiClient.get<PromptTemplate[]>(url)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  return response.data || []
}

export const getPromptTemplate = async (id: number): Promise<PromptTemplate> => {
  const response = await apiClient.get<PromptTemplate>(`/api/prompt-templates/${id}`)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Template not found')
  }
  
  return response.data
}

export const createPromptTemplate = async (data: PromptTemplateCreate): Promise<PromptTemplate> => {
  const response = await apiClient.post<PromptTemplate>('/api/prompt-templates', data)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to create template')
  }
  
  return response.data
}

export const createPromptTemplateFromPlayground = async (
  data: PromptTemplateFromPlayground
): Promise<PromptTemplate> => {
  const response = await apiClient.post<PromptTemplate>('/api/prompt-templates/from-playground', data)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to create template from playground')
  }
  
  return response.data
}

export const updatePromptTemplate = async (
  id: number,
  data: PromptTemplateUpdate
): Promise<PromptTemplate> => {
  const response = await apiClient.put<PromptTemplate>(`/api/prompt-templates/${id}`, data)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to update template')
  }
  
  return response.data
}

export const activatePromptTemplate = async (id: number): Promise<PromptTemplate> => {
  const response = await apiClient.post<PromptTemplate>(`/api/prompt-templates/${id}/activate`, null)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to activate template')
  }
  
  return response.data
}

export const archivePromptTemplate = async (id: number): Promise<PromptTemplate> => {
  const response = await apiClient.post<PromptTemplate>(`/api/prompt-templates/${id}/archive`, null)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to archive template')
  }
  
  return response.data
}

export const deletePromptTemplate = async (id: number): Promise<void> => {
  const response = await apiClient.delete(`/api/prompt-templates/${id}`)
  
  if (response.error) {
    throw new Error(response.error)
  }
}

