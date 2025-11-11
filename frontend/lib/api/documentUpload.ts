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

export interface AIProcessingResult {
  id: number;
  document_page_id: number;
  prompt_template_id: number | null;
  ai_model_used: string;
  raw_response: string;
  parsed_json: any;
  tokens_sent: number;
  tokens_received: number;
  processing_time_ms: number;
  status: 'success' | 'failed' | 'pending';
  error_message: string | null;
  created_at: string;
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
  ai_processing_result?: AIProcessingResult | null;
}

export interface DocumentComment {
  id: number;
  document_id: number;
  user_id: number;
  user_name?: string;
  comment_text: string;
  comment_type: 'general' | 'review' | 'approval' | 'rejection';
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
  document_type_name?: string; // Document Type Name
  qm_chapter: string;
  version: string;
  page_count: number;
  uploaded_by_user_id: number;
  uploaded_by_user_name?: string; // User Name des Uploaders
  uploaded_at: string;
  file_path: string;
  processing_method: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  workflow_status?: 'draft' | 'reviewed' | 'approved' | 'rejected'; // Workflow-Status (für RAG Indexierung)
  is_duplicate?: boolean; // NEU: Flag ob Dokument ein Duplikat ist
  duplicate_of_document_id?: number | null; // NEU: ID des Original-Dokuments (wenn Duplikat)
}

export interface UploadedDocumentDetail extends UploadedDocument {
  pages: DocumentPage[];
  interest_groups: InterestGroupAssignment[];
  // NEU: RAG Indexierungs-Status
  is_indexed?: boolean;
  indexed_at?: string;
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

export interface ProcessPageRequest {
  prompt_template_id?: number;
}

export interface ProcessPageResponse {
  success: boolean;
  message: string;
  result: AIProcessingResult;
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

  const response = await apiClient.postForm<UploadDocumentResponse>(
    '/api/document-upload/upload',
    formData
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Upload a document (COMPLETE - Atomic)
 * 
 * Dieser Endpoint macht Upload + Preview + Interest Groups + KI-Verarbeitung in EINER Transaktion.
 * Bei Fehler wird automatisch ein Rollback durchgeführt (Dokument + Dateien gelöscht).
 * 
 * @param file - Datei zum Hochladen
 * @param request - Upload-Request mit Metadaten
 * @param interestGroupIds - Interest Group IDs (comma-separated string)
 * @param onProgress - Callback für Fortschritt (optional)
 * @returns Upload-Response mit fertig verarbeitetem Dokument
 */
export async function uploadDocumentComplete(
  file: File,
  request: UploadDocumentRequest,
  interestGroupIds: string,
  onProgress?: (progress: number, message: string) => void
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('filename', request.filename);
  formData.append('original_filename', request.original_filename);
  formData.append('document_type_id', request.document_type_id.toString());
  formData.append('qm_chapter', request.qm_chapter);
  formData.append('version', request.version);
  formData.append('processing_method', request.processing_method);
  formData.append('interest_group_ids', interestGroupIds);

  // Progress Callback
  if (onProgress) {
    onProgress(10, 'Upload wird vorbereitet...');
  }

  const response = await apiClient.postForm<UploadDocumentResponse>(
    '/api/document-upload/upload-complete',
    formData
  );

  if (response.error) {
    throw new Error(response.error);
  }

  if (onProgress) {
    onProgress(100, 'Upload erfolgreich abgeschlossen!');
  }

  return response.data!;
}

/**
 * Generate preview images for a document
 */
export async function generatePreview(
  documentId: number
): Promise<GeneratePreviewResponse> {
  const response = await apiClient.post<GeneratePreviewResponse>(
    `/api/document-upload/${documentId}/generate-preview`,
    {}
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Assign interest groups to a document
 */
export async function assignInterestGroups(
  documentId: number,
  request: AssignInterestGroupsRequest
): Promise<AssignInterestGroupsResponse> {
  const response = await apiClient.post<AssignInterestGroupsResponse>(
    `/api/document-upload/${documentId}/assign-interest-groups`,
    request
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Get upload details (with pages and interest groups)
 */
export async function getUploadDetails(
  documentId: number
): Promise<GetUploadDetailsResponse> {
  const response = await apiClient.get<GetUploadDetailsResponse>(
    `/api/document-upload/${documentId}`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
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
  
  const response = await apiClient.get<GetUploadsListResponse>(url);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Delete an upload (cascade delete: files + DB)
 */
export async function deleteUpload(
  documentId: number
): Promise<DeleteUploadResponse> {
  const response = await apiClient.delete<DeleteUploadResponse>(
    `/api/document-upload/${documentId}`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Mark document as failed
 */
export async function markDocumentAsFailed(
  documentId: number
): Promise<{ success: boolean; message: string; document_id: number; processing_status: string }> {
  const response = await apiClient.post<{ success: boolean; message: string; document_id: number; processing_status: string }>(
    `/api/document-upload/${documentId}/mark-as-failed`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
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

/**
 * Process a document page with AI
 */
export async function processDocumentPage(
  documentId: number,
  pageNumber: number,
  request?: ProcessPageRequest
): Promise<ProcessPageResponse> {
  const response = await apiClient.post<ProcessPageResponse>(
    `/api/document-upload/${documentId}/process-page/${pageNumber}`,
    request || {}
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// ============================================================================
// DOCUMENT COMMENTS API
// ============================================================================

export interface CreateCommentRequest {
  comment_text: string;
  comment_type?: 'general' | 'review' | 'approval' | 'rejection';
}

export interface CreateCommentResponse {
  success: boolean;
  message: string;
  comment?: DocumentComment;
}

export interface GetCommentsResponse {
  success: boolean;
  comments: DocumentComment[];
}

/**
 * Erstelle einen Kommentar zu einem Dokument.
 * 
 * @param documentId - Dokument ID
 * @param request - Kommentar-Daten
 * @returns Erstellter Kommentar
 */
export async function createDocumentComment(
  documentId: number,
  request: CreateCommentRequest
): Promise<CreateCommentResponse> {
  const response = await apiClient.post<CreateCommentResponse>(
    `/api/document-upload/${documentId}/comments`,
    {
      comment_text: request.comment_text,
      comment_type: request.comment_type || 'general'
    }
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

/**
 * Lade alle Kommentare eines Dokuments.
 * 
 * @param documentId - Dokument ID
 * @returns Liste der Kommentare
 */
export async function getDocumentComments(
  documentId: number
): Promise<DocumentComment[]> {
  const response = await apiClient.get<GetCommentsResponse>(
    `/api/document-upload/${documentId}/comments`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!.comments || [];
}

// ============================================================================
// RETRY PROCESSING
// ============================================================================

export interface RetryProcessingResponse {
  success: boolean;
  message: string;
  statistics: {
    total_pages: number;
    retried_pages: number;
    successful_pages: number;
    failed_pages: number;
  };
  errors: string[];
}

/**
 * Starte AI-Verarbeitung für fehlgeschlagenes Dokument neu.
 * 
 * @param documentId - Dokument ID
 * @param retryAll - Wenn true, alle Seiten neu verarbeiten (nicht nur fehlgeschlagene)
 * @returns Retry-Statistiken
 */
export async function retryDocumentProcessing(
  documentId: number,
  retryAll: boolean = false
): Promise<RetryProcessingResponse> {
  const response = await apiClient.post<RetryProcessingResponse>(
    `/api/document-upload/${documentId}/retry-processing?retry_all=${retryAll}`,
    {}
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

