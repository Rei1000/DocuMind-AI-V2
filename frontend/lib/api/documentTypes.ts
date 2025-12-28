/**
 * Document Types API Client
 * 
 * Kommuniziert mit /api/document-types Endpoints
 */

import { apiClient } from '../api'

export interface DocumentType {
  id: number
  name: string
  code: string
  description: string
  allowed_file_types: string[]
  max_file_size_mb: number
  requires_ocr: boolean
  requires_vision: boolean
  default_prompt_template_id: number | null
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface DocumentTypeCreate {
  name: string
  code: string
  description?: string
  allowed_file_types: string[]
  max_file_size_mb: number
  requires_ocr?: boolean
  requires_vision?: boolean
  sort_order?: number
}

export interface DocumentTypeUpdate {
  name?: string
  description?: string
  allowed_file_types?: string[]
  max_file_size_mb?: number
  requires_ocr?: boolean
  requires_vision?: boolean
  default_prompt_template_id?: number | null
  is_active?: boolean
  sort_order?: number
}

// API Functions
export const getDocumentTypes = async (activeOnly: boolean = true): Promise<DocumentType[]> => {
  const response = await apiClient.get<DocumentType[]>(`/api/document-types?active_only=${activeOnly}`)
  
  // 401 Unauthorized: Token abgelaufen → apiClient leitet bereits zu Login um
  // Keinen Fehler werfen, da Redirect bereits stattgefunden hat
  if (response.status === 401) {
    return []  // Leere Liste zurückgeben, Redirect läuft bereits
  }
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  return response.data || []
}

export const getDocumentType = async (id: number): Promise<DocumentType> => {
  const response = await apiClient.get<DocumentType>(`/api/document-types/${id}`)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Document type not found')
  }
  
  return response.data
}

export const createDocumentType = async (data: DocumentTypeCreate): Promise<DocumentType> => {
  const response = await apiClient.post<DocumentType>('/api/document-types', data)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to create document type')
  }
  
  return response.data
}

export const updateDocumentType = async (
  id: number,
  data: DocumentTypeUpdate
): Promise<DocumentType> => {
  const response = await apiClient.put<DocumentType>(`/api/document-types/${id}`, data)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to update document type')
  }
  
  return response.data
}

export const deleteDocumentType = async (id: number): Promise<void> => {
  const response = await apiClient.delete(`/api/document-types/${id}`)
  
  if (response.error) {
    throw new Error(response.error)
  }
}

export const setDefaultPromptTemplate = async (
  documentTypeId: number,
  promptTemplateId: number
): Promise<DocumentType> => {
  const response = await apiClient.put<DocumentType>(
    `/api/document-types/${documentTypeId}/set-default-prompt`,
    { prompt_template_id: promptTemplateId }
  )
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to set default prompt template')
  }
  
  return response.data
}

export const removeDefaultPromptTemplate = async (documentTypeId: number): Promise<DocumentType> => {
  const response = await apiClient.delete<DocumentType>(`/api/document-types/${documentTypeId}/default-prompt`)
  
  if (response.error) {
    throw new Error(response.error)
  }
  
  if (!response.data) {
    throw new Error('Failed to remove default prompt template')
  }
  
  return response.data
}

