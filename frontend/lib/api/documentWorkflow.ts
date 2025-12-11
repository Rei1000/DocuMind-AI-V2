/**
 * Document Workflow API Functions
 * 
 * API-Funktionen für den Dokumenten-Workflow (Status-Änderungen, Historie, etc.)
 */

export type WorkflowStatus = 'draft' | 'reviewed' | 'approved' | 'rejected';

export interface WorkflowDocument {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  version: string;
  workflow_status: WorkflowStatus;
  uploaded_at: string;
  interest_group_ids: number[];
  document_type?: number;
  document_type_name?: string;
  qm_chapter?: string;
  page_count?: number;
  preview_url?: string;
  
  // Verantwortlicher User & Betroffene Abteilungen
  responsible_user_id?: number;
  responsible_user_name?: string;
  affected_departments: string[];
  
  // NEU: RAG Indexierungs-Status
  is_indexed?: boolean;
  indexed_at?: string;
  
  // NEU: Duplikat-Felder (Phase 1.1)
  is_duplicate?: boolean;
  duplicate_of_document_id?: number | null;
}

export interface WorkflowStatusChange {
  id: number;
  document_id: number;
  from_status: WorkflowStatus | null;
  to_status: WorkflowStatus;
  changed_by_user_id: number;
  changed_by_user_name?: string;  // Neues Feld für Username
  created_at: string;
  reason: string;
}

export interface StatusChangeRequest {
  new_status: WorkflowStatus;
  reason: string;
}

export interface ChangeStatusRequest {
  document_id: number;
  new_status: WorkflowStatus;
  user_id: number;
  reason: string;
  comment?: string;
}

export interface ChangeStatusResponse {
  success: boolean;
  message: string;
  document_id: number;
  new_status: WorkflowStatus;
  error?: string;
}

export interface WorkflowInfoResponse {
  success: boolean;
  message: string;
  document_id: number;
  workflow: {
    current_status: WorkflowStatus;
    allowed_transitions: WorkflowStatus[];
  };
}

export type CommentType = 'general' | 'review' | 'approval' | 'rejection';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Zentrale 401-Fehlerbehandlung: Token abgelaufen → Redirect zu Login
 */
function handle401Error() {
  console.warn('[API] Token abgelaufen (401), leite zu Login um...');
  // Token entfernen
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('token');
  localStorage.removeItem('access_token');
  localStorage.removeItem('token');
  // Redirect zu Login
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

/**
 * Hole Dokumente nach Workflow-Status
 */
export async function getDocumentsByStatus(
  status: WorkflowStatus,
  interestGroupIds?: number[],
  documentTypeId?: number,
  excludeRagIndexed: boolean = true  // NEU: Standardmäßig True (für Kanban), False für Tabelle
): Promise<{success: boolean, data: {documents: WorkflowDocument[]}}> {
  const params = new URLSearchParams();
  
  // Get user_id from token
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.user_id) {
        params.append('user_id', payload.user_id.toString());
      } else {
        console.error('No user_id found in token payload');
      }
    } catch (e) {
      console.error('Failed to parse token:', e);
    }
  }
  
  // FastAPI erwartet für List[int] Query-Parameter mehrere Parameter mit demselben Namen
  // Format: ?interest_group_ids=1&interest_group_ids=2 (nicht komma-separiert)
  if (interestGroupIds && interestGroupIds.length > 0) {
    interestGroupIds.forEach(id => {
      params.append('interest_group_ids', id.toString());
    });
  }
  
  if (documentTypeId) {
    params.append('document_type_id', documentTypeId.toString());
  }
  
  // NEU: exclude_rag_indexed Parameter (True für Kanban, False für Tabelle)
  params.append('exclude_rag_indexed', excludeRagIndexed.toString());

  const url = `${API_BASE}/api/document-workflow/status/${status}?${params.toString()}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token') || sessionStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    // 401 Unauthorized: Token abgelaufen
    if (response.status === 401) {
      handle401Error();
      throw new Error('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
    }
    // Versuche Fehler-Details aus Response zu extrahieren
    let errorMessage = `Failed to fetch documents: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (e) {
      // Ignoriere JSON-Parse-Fehler
    }
    const error = new Error(errorMessage);
    (error as any).status = response.status;
    throw error;
  }

  return response.json();
}

/**
 * Hole alle Workflow-Dokumente (alle Status)
 */
export async function getAllWorkflowDocuments(
  interestGroupIds?: number[]
): Promise<Record<WorkflowStatus, WorkflowDocument[]>> {
  const statuses: WorkflowStatus[] = ['draft', 'reviewed', 'approved', 'rejected'];
  
  const promises = statuses.map(async (status) => {
    try {
      const response = await getDocumentsByStatus(status, interestGroupIds);
      return response.success ? response.data.documents : [];
    } catch (error) {
      console.error(`Failed to fetch documents for status ${status}:`, error);
      return []; // Return empty array for failed requests
    }
  });
  
  const results = await Promise.all(promises);
  
  return {
    draft: results[0],
    reviewed: results[1],
    approved: results[2],
    rejected: results[3],
  };
}

/**
 * Ändere Dokument-Status
 */
export async function changeDocumentStatus(
  documentId: number,
  request: { new_status: WorkflowStatus; reason: string }
): Promise<ChangeStatusResponse> {
  const response = await fetch(`${API_BASE}/api/document-workflow/change-status`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token') || sessionStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      new_status: request.new_status,
      reason: request.reason
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      handle401Error();
      throw new Error('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
    }
    throw new Error(`Failed to change status: ${response.status}`);
  }

  return response.json();
}

/**
 * Einzelnes Dokument abrufen
 */
export async function getDocumentWorkflow(documentId: number): Promise<WorkflowInfoResponse> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/document-workflow/${documentId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      handle401Error();
      throw new Error('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
    }
    throw new Error(`Failed to fetch document: ${response.status}`);
  }

  return response.json();
}

/**
 * Kommentar zu einem Dokument hinzufügen
 */
export async function addDocumentComment(
  documentId: number, 
  comment: { comment_text: string; comment_type: string; page_number: number }
): Promise<{ success: boolean; error?: string }> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/document-workflow/${documentId}/comments`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(comment),
  });

  if (!response.ok) {
    if (response.status === 401) {
      handle401Error();
      throw new Error('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
    }
    return { success: false, error: `Failed to add comment: ${response.status}` };
  }
  
  return { success: true };
}

/**
 * Hole erlaubte Status-Transitions für ein Dokument
 */
/**
 * Soft Delete eines Dokuments (für indexierte Dokumente)
 * NEU: Soft Delete für indexierte Dokumente, normales Löschen für nicht-indexierte
 */
export async function softDeleteDocument(
  documentId: number,
  reason: string
): Promise<{success: boolean, message: string, document_id: number, error?: string}> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE}/api/document-workflow/soft-delete`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      deletion_reason: reason
    })
  });

  const responseData = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    // WICHTIG: Prüfe ob Response trotzdem success=true hat (z.B. wenn Dokument bereits gelöscht)
    if (responseData.success === true) {
      return responseData;
    }
    const errorMessage = responseData.detail || responseData.error || `HTTP ${response.status}`;
    throw new Error(errorMessage);
  }

  return responseData;
}

export async function getAllowedTransitions(documentId: number): Promise<WorkflowStatus[] | { allowed_transitions: WorkflowStatus[], current_status: string, user_level: number }> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/document-workflow/${documentId}/allowed-transitions`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch allowed transitions: ${response.status}`);
  }

  const data = await response.json();
  console.log(`[getAllowedTransitions] Response for document ${documentId}:`, data);
  // API gibt { allowed_transitions: [...], current_status: "...", user_level: ... } zurück
  // Für Rückwärtskompatibilität: Gebe auch das vollständige Objekt zurück
  return data;
}

/**
 * Audit-Trail für ein Dokument abrufen
 */
export async function getDocumentAuditTrail(documentId: number): Promise<WorkflowStatusChange[]> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/document-workflow/history/${documentId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch audit trail: ${response.status}`);
  }

  return response.json();
}

/**
 * Status-Name für UI anzeigen
 */
export function getWorkflowStatusName(status: WorkflowStatus): string {
  switch (status) {
    case 'draft': return 'Entwurf';
    case 'reviewed': return 'Geprüft';
    case 'approved': return 'Freigegeben';
    case 'rejected': return 'Abgelehnt';
    default: return status;
  }
}

/**
 * Utility-Funktionen für Workflow-Status
 */
export const WorkflowUtils = {
  /**
   * Status-Labels für die UI
   */
  getStatusLabel: (status: WorkflowStatus): string => {
    switch (status) {
      case 'draft': return 'Entwurf';
      case 'reviewed': return 'Geprüft';
      case 'approved': return 'Freigegeben';
      case 'rejected': return 'Zurückgewiesen';
      default: return status;
    }
  },

  /**
   * Status-Farben für die UI
   */
  getStatusColor: (status: WorkflowStatus): string => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'reviewed': return 'bg-blue-100 text-blue-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  },

  /**
   * Status-Icons für die UI
   */
  getStatusIcon: (status: WorkflowStatus): string => {
    switch (status) {
      case 'draft': return '📝';
      case 'reviewed': return '👀';
      case 'approved': return '✅';
      case 'rejected': return '❌';
      default: return '📄';
    }
  },

  /**
   * Prüfe ob ein Status-Übergang erlaubt ist
   */
  isTransitionAllowed: (from: WorkflowStatus, to: WorkflowStatus, userLevel: number): boolean => {
    if (from === to) return false;
    
    // Level 2: Nur lesen
    if (userLevel === 2) return false;
    
    // Level 3: draft → reviewed
    if (userLevel === 3) {
      return from === 'draft' && to === 'reviewed';
    }
    
    // Level 4: reviewed → approved, any → rejected
    if (userLevel === 4) {
      return (from === 'reviewed' && to === 'approved') || to === 'rejected';
    }
    
    // Level 5: Alle Transitions erlaubt
    if (userLevel === 5) {
      return true;
    }
    
    return false;
  }
};

// Legacy exports for compatibility
export const getWorkflowStatusBadge = WorkflowUtils.getStatusColor;
export const getWorkflowStatusIcon = WorkflowUtils.getStatusIcon;

/**
 * NEU Archiv-System: Hole archivierte Dokumente
 */
export interface GetArchivedDocumentsParams {
  limit?: number;
  offset?: number;
  document_type_id?: number;
  deleted_before?: string;
  deleted_after?: string;
}

export interface HardDeleteDocumentResponse {
  success: boolean;
  message: string;
  files_deleted: string[];
}

/**
 * Hole alle gelöschten Dokumente (Archiv)
 */
export async function getArchivedDocuments(
  params?: GetArchivedDocumentsParams
): Promise<WorkflowDocument[]> {
  // Konsistente Token-Extraktion wie in anderen API-Funktionen
  const token = sessionStorage.getItem('access_token') || sessionStorage.getItem('token') || localStorage.getItem('access_token') || localStorage.getItem('token');
  if (!token) {
    console.error('[getArchivedDocuments] Kein Token gefunden');
    throw new Error('Nicht authentifiziert. Bitte melden Sie sich erneut an.');
  }

  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());
  if (params?.document_type_id) queryParams.append('document_type_id', params.document_type_id.toString());
  if (params?.deleted_before) queryParams.append('deleted_before', params.deleted_before);
  if (params?.deleted_after) queryParams.append('deleted_after', params.deleted_after);

  const url = `${API_BASE}/api/document-workflow/archive${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  console.log('[getArchivedDocuments] Request URL:', url);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // 401 Unauthorized: Token abgelaufen
      if (response.status === 401) {
        handle401Error();
        throw new Error('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
      }
      
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        // WICHTIG: Stelle sicher, dass detail ein String ist
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic Validation Errors sind Arrays
            errorMessage = errorData.detail.map((err: any) => 
              `${err.loc?.join('.')}: ${err.msg}`
            ).join('; ');
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
      } catch (e) {
        // Wenn JSON-Parsing fehlschlägt, nutze Status-Text
        errorMessage = response.statusText || `HTTP ${response.status}`;
      }
      console.error('[getArchivedDocuments] API Error:', response.status, errorMessage);
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Prüfe ob Response ein Array ist
    if (!Array.isArray(data)) {
      console.error('[getArchivedDocuments] Response ist kein Array:', data);
      throw new Error('Ungültige Antwort vom Server. Erwartetes Format: Array von Dokumenten.');
    }
    
    return data;
  } catch (err) {
    if (err instanceof Error) {
      throw err;
    }
    console.error('[getArchivedDocuments] Unbekannter Fehler:', err);
    throw new Error('Fehler beim Laden der archivierten Dokumente');
  }
}

/**
 * Endgültige Löschung (nur Level 5)
 */
export async function hardDeleteDocument(
  documentId: number,
  confirmation: string
): Promise<HardDeleteDocumentResponse> {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || localStorage.getItem('token') || sessionStorage.getItem('token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(
    `${API_BASE}/api/document-workflow/hard-delete/${documentId}?confirmation=${encodeURIComponent(confirmation)}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}