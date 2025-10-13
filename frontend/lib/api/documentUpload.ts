/**
 * Document Upload API Client
 * 
 * Provides functions to interact with the Document Upload backend API.
 */

import { apiClient } from '../api';

// ============================================================================
// TYPES
// ============================================================================

export interface UploadDocumentRequest {
  filename: string;
  original_filename: string;
  document_type_id: number;
  qm_chapter: string;
  version: string;
  processing_method: 'ocr' | 'vision';
}

export interface DocumentPage {
  id: number;
  upload_document_id: number;
  page_number: number;
  preview_image_path: string;
  thumbnail_path: string | null;
  width: number | null;
  height: number | null;
  created_at: string;
}

export interface InterestGroupAssignment {
  id: number;
  upload_document_id: number;
  interest_group_id: number;
  assigned_by_user_id: number;
  assigned_at: string;
}

export interface UploadedDocument {
  id: number;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  file_type: string;
  document_type_id: number;
  qm_chapter: string;
  version: string;
  page_count: number;
  uploaded_by_user_id: number;
  uploaded_at: string;
  file_path: string;
  processing_method: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface UploadedDocumentDetail extends UploadedDocument {
  pages: DocumentPage[];
  interest_groups: InterestGroupAssignment[];
}

export interface UploadDocumentResponse {
  success: boolean;
  message: string;
  document: UploadedDocument;
}

export interface GeneratePreviewResponse {
  success: boolean;
  message: string;
  pages_generated: number;
  pages: DocumentPage[];
}

export interface AssignInterestGroupsRequest {
  interest_group_ids: number[];
}

export interface AssignInterestGroupsResponse {
  success: boolean;
  message: string;
  assignments: InterestGroupAssignment[];
}

export interface GetUploadDetailsResponse {
  success: boolean;
  document: UploadedDocumentDetail;
}

export interface GetUploadsListResponse {
  success: boolean;
  total: number;
  documents: UploadedDocument[];
}

export interface DeleteUploadResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Upload a document
 */
export async function uploadDocument(
  file: File,
  request: UploadDocumentRequest
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('filename', request.filename);
  formData.append('original_filename', request.original_filename);
  formData.append('document_type_id', request.document_type_id.toString());
  formData.append('qm_chapter', request.qm_chapter);
  formData.append('version', request.version);
  formData.append('processing_method', request.processing_method);

  const response = await apiClient.postForm(
    '/api/document-upload/upload',
    formData
  );

  return response;
}

/**
 * Generate preview images for a document
 */
export async function generatePreview(
  documentId: number
): Promise<GeneratePreviewResponse> {
  const response = await apiClient.post(
    `/api/document-upload/${documentId}/generate-preview`,
    {}
  );

  return response;
}

/**
 * Assign interest groups to a document
 */
export async function assignInterestGroups(
  documentId: number,
  request: AssignInterestGroupsRequest
): Promise<AssignInterestGroupsResponse> {
  const response = await apiClient.post(
    `/api/document-upload/${documentId}/assign-interest-groups`,
    request
  );

  return response;
}

/**
 * Get upload details (with pages and interest groups)
 */
export async function getUploadDetails(
  documentId: number
): Promise<GetUploadDetailsResponse> {
  const response = await apiClient.get(
    `/api/document-upload/${documentId}`
  );

  return response;
}

/**
 * Get list of uploads (with optional filters)
 */
export async function getUploadsList(params?: {
  user_id?: number;
  document_type_id?: number;
  processing_status?: string;
  limit?: number;
  offset?: number;
}): Promise<GetUploadsListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params?.user_id) queryParams.append('user_id', params.user_id.toString());
  if (params?.document_type_id) queryParams.append('document_type_id', params.document_type_id.toString());
  if (params?.processing_status) queryParams.append('processing_status', params.processing_status);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const url = `/api/document-upload/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  
  const response = await apiClient.get(url);

  return response;
}

/**
 * Delete an upload (cascade delete: files + DB)
 */
export async function deleteUpload(
  documentId: number
): Promise<DeleteUploadResponse> {
  const response = await apiClient.delete(
    `/api/document-upload/${documentId}`
  );

  return response;
}

/**
 * Get preview image URL
 */
export function getPreviewImageUrl(previewPath: string): string {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  return `${API_BASE_URL}/data/uploads/${previewPath}`;
}

/**
 * Get thumbnail image URL
 */
export function getThumbnailImageUrl(thumbnailPath: string): string {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  return `${API_BASE_URL}/data/uploads/${thumbnailPath}`;
}

