"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import {
  getUploadDetails,
  getPreviewImageUrl,
  getThumbnailImageUrl,
  processDocumentPage,
  UploadedDocumentDetail,
  DocumentPage,
  InterestGroupAssignment,
  AIProcessingResult,
  DocumentComment,
  getDocumentComments,
  createDocumentComment,
} from '@/lib/api/documentUpload';
import {
  getDocumentType,
  DocumentType as DocumentTypeDetail,
} from '@/lib/api/documentTypes';
import {
  getPromptTemplate,
  PromptTemplate,
} from '@/lib/api/promptTemplates';
import { Card } from '@/components/ui';
import Spinner from '@/components/ui/Spinner';
import { useUser } from '@/lib/contexts/UserContext';
import { toast } from 'react-hot-toast';
import ChunkPreviewPanel from '@/components/ChunkPreviewPanel';
import ChunkingStrategyWizard from '@/components/ChunkingStrategyWizard';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
}

interface InterestGroup {
  id: number;
  name: string;
  code: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DocumentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const documentId = parseInt(params.id as string);
  const { userLevel } = useUser();
  
  // RBAC: Berechtigungen für Dokumenten-Detail-Seite
  const canComment = userLevel >= 1; // Kommentare für alle Level (Level 1+)
  const canViewAIProcessing = userLevel >= 4; // AI-Verarbeitung nur für Level 4+
  const canViewRAGIndexing = userLevel >= 4; // RAG Indexierung nur für Level 4+
  const canProcessAI = userLevel >= 4; // AI-Verarbeitung starten nur für Level 4+
  
  // NEU: Lese page-Parameter aus URL (für Links aus RAG Chat)
  const pageParam = searchParams.get('page');
  const initialPageIndex = pageParam ? parseInt(pageParam) - 1 : 0; // page_number ist 1-basiert, Index ist 0-basiert
  
  // NEU: Lese chunk und highlight Parameter aus URL (für Auto-Öffnen und Highlighting)
  const chunkParam = searchParams.get('chunk');
  const highlightParam = searchParams.get('highlight');
  const highlightTerms = highlightParam 
    ? highlightParam.split(',').map(term => decodeURIComponent(term.trim())).filter(term => term.length > 0)
    : [];
  
  // State
  const [document, setDocument] = useState<UploadedDocumentDetail | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [interestGroups, setInterestGroups] = useState<InterestGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPageIndex, setSelectedPageIndex] = useState(initialPageIndex);
  const [processingPage, setProcessingPage] = useState(false);
  const [processingError, setProcessingError] = useState<string | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [showStrategyWizard, setShowStrategyWizard] = useState(false);
  const [selectedChunkingStrategy, setSelectedChunkingStrategy] = useState<string | null>(null);
  
  // Prompt Template State
  const [defaultPromptTemplate, setDefaultPromptTemplate] = useState<PromptTemplate | null>(null);
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  
  // Modal State
  const [showImageModal, setShowImageModal] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [showJsonModal, setShowJsonModal] = useState(false);
  
  // RBAC Phase 9: Comment State
  const [comments, setComments] = useState<DocumentComment[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  
  // Refs für Höhen-Synchronisation
  const documentInfoRef = useRef<HTMLDivElement>(null);
  const previewCardRef = useRef<HTMLDivElement>(null);
  const [previewCardHeight, setPreviewCardHeight] = useState<number | null>(null);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadDocumentTypes();
    loadInterestGroups();
    loadDocumentDetails();
    // RBAC Phase 9: Lade Kommentare
    if (documentId) {
      loadComments();
    }
  }, [documentId]);

  // Auto-Refresh: Reagiere auf Status-Änderungen von der Dokumenten-Liste
  useEffect(() => {
    const handleDocumentStatusChanged = (event: CustomEvent) => {
      // Wenn das Event für dieses Dokument ist, lade Details neu
      if (event.detail && event.detail.documentId === documentId) {
        console.log('Document status changed, reloading details...');
        loadDocumentDetails();
      }
    };

    window.addEventListener('documentStatusChanged', handleDocumentStatusChanged as EventListener);

    return () => {
      window.removeEventListener('documentStatusChanged', handleDocumentStatusChanged as EventListener);
    };
  }, [documentId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-Refresh: Prüfe beim Mount, ob wir von einer Status-Änderung kommen
  useEffect(() => {
    // Prüfe sessionStorage für "justChangedStatus" Flag
    const justChangedStatus = sessionStorage.getItem(`document_${documentId}_status_changed`);
    if (justChangedStatus === 'true') {
      // Lade Details neu
      loadDocumentDetails();
      // Entferne Flag
      sessionStorage.removeItem(`document_${documentId}_status_changed`);
    }
  }, [documentId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-Scroll zur ausgewählten Seite beim Laden oder Änderung
  useEffect(() => {
    if (document && document.pages.length > 0) {
      // NEU: Wenn page-Parameter in URL vorhanden, setze die entsprechende Seite
      const pageParam = searchParams.get('page');
      if (pageParam) {
        const pageNumber = parseInt(pageParam);
        // Finde Index basierend auf page_number (1-basiert)
        const pageIndex = document.pages.findIndex(page => page.page_number === pageNumber);
        if (pageIndex !== -1 && pageIndex !== selectedPageIndex) {
          setSelectedPageIndex(pageIndex);
          // Scroll zu dieser Seite nach kurzer Verzögerung (damit DOM bereit ist)
          setTimeout(() => {
            scrollToPage(pageIndex);
          }, 100);
        } else if (pageIndex !== -1) {
          // Seite bereits ausgewählt, nur scrollen
          setTimeout(() => {
            scrollToPage(pageIndex);
          }, 100);
        }
      } else {
        // Kein page-Parameter: Scroll zu ausgewählter Seite
        setTimeout(() => {
          scrollToPage(selectedPageIndex);
        }, 100);
      }
    }
  }, [document, searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load default prompt template when document changes
  useEffect(() => {
    if (document) {
      loadDefaultPromptTemplate();
    }
  }, [document?.document_type_id]);

  // Synchronisiere Höhe der Preview-Card mit Document Information Card
  useEffect(() => {
    const syncHeights = () => {
      if (documentInfoRef.current && previewCardRef.current) {
        const docInfoHeight = documentInfoRef.current.offsetHeight;
        setPreviewCardHeight(docInfoHeight);
      }
    };
    
    // Initial sync after a short delay to ensure DOM is ready
    const timeoutId = setTimeout(syncHeights, 100);
    
    // Sync on resize
    window.addEventListener('resize', syncHeights);
    
    // Sync when document changes
    if (document) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(syncHeights, 200);
    }
    
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', syncHeights);
    };
  }, [document]);

  // ============================================================================
  // API CALLS
  // ============================================================================

  const loadDocumentTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/document-types/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setDocumentTypes(data.document_types);
    } catch (error) {
      console.error('Failed to load document types:', error);
    }
  };

  const loadInterestGroups = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/interest-groups/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setInterestGroups(data);
    } catch (error) {
      console.error('Failed to load interest groups:', error);
    }
  };

  const loadDocumentDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUploadDetails(documentId);
      
      if (response.success) {
        const doc = response.document;
        
        // NEU: Lade Indexierungs-Status
        try {
          const { apiClient } = await import('@/lib/api/rag');
          const indexStatusResponse = await apiClient.getDocumentIndexStatus(documentId);
          if (indexStatusResponse.data) {
            doc.is_indexed = indexStatusResponse.data.is_indexed;
            doc.indexed_at = indexStatusResponse.data.indexed_at || undefined;
          }
        } catch (error) {
          console.warn('Failed to load index status:', error);
          // Fehler ignorieren, Indexierungs-Status bleibt undefined
        }
        
        setDocument(doc);
      } else {
        setError('Failed to load document details');
      }
    } catch (error: any) {
      console.error('Failed to load document details:', error);
      setError(error.message || 'Failed to load document details');
    } finally {
      setLoading(false);
    }
  };

  const handleIndexDocument = async (strategyId: string) => {
    if (isIndexing) return;
    
    setIsIndexing(true);
    try {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      if (!token) {
        toast.error('Bitte loggen Sie sich ein');
        return;
      }

      const response = await fetch('http://localhost:8000/api/rag/documents/index', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          upload_document_id: documentId,
          force_reindex: document?.is_indexed || false,
          chunking_strategy: strategyId  // PHASE 2.3: Übergebe ausgewählte Strategie
        })
      });

      const result = await response.json();
      
      if (result.success) {
        toast.success(`✅ Dokument erfolgreich ${document?.is_indexed ? 'neu ' : ''}indexiert!\n\nChunks erstellt: ${result.chunks_created}\nVerarbeitungszeit: ${result.processing_time_ms}ms`);
        await loadDocumentDetails();
      } else {
        toast.error(`❌ Indexierung fehlgeschlagen: ${result.message}`);
      }
    } catch (error) {
      console.error('Indexierung Fehler:', error);
      toast.error('❌ Fehler bei der Indexierung. Bitte versuchen Sie es erneut.');
    } finally {
      setIsIndexing(false);
      setShowStrategyWizard(false);
      setSelectedChunkingStrategy(null);
    }
  };

  const loadDefaultPromptTemplate = async () => {
    if (!document) return;
    
    setLoadingPrompt(true);
    try {
      // First, get the document type to find default_prompt_template_id
      const docType = await getDocumentType(document.document_type_id);
      
      if (docType.default_prompt_template_id) {
        // Load the prompt template
        const template = await getPromptTemplate(docType.default_prompt_template_id);
        setDefaultPromptTemplate(template);
      } else {
        setDefaultPromptTemplate(null);
      }
    } catch (error) {
      console.error('Failed to load default prompt template:', error);
      setDefaultPromptTemplate(null);
    } finally {
      setLoadingPrompt(false);
    }
  };

  // RBAC Phase 9: Kommentar-Funktionen
  const loadComments = async () => {
    if (!documentId) return;
    
    setLoadingComments(true);
    try {
      const commentsData = await getDocumentComments(documentId);
      setComments(commentsData);
    } catch (error) {
      console.error('Failed to load comments:', error);
      toast.error('Fehler beim Laden der Kommentare');
    } finally {
      setLoadingComments(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!newComment.trim() || !canComment) return;
    
    setSubmittingComment(true);
    try {
      await createDocumentComment(documentId, {
        comment_text: newComment.trim(),
        comment_type: 'general'
      });
      
      toast.success('Kommentar erfolgreich erstellt');
      setNewComment('');
      await loadComments(); // Reload comments
    } catch (error: any) {
      console.error('Failed to create comment:', error);
      toast.error(error.message || 'Fehler beim Erstellen des Kommentars');
    } finally {
      setSubmittingComment(false);
    }
  };





  const handleProcessPage = async () => {
    console.log('[handleProcessPage] Starting...');
    if (!document || !document.pages[selectedPageIndex]) {
      console.log('[handleProcessPage] No document or page found');
      return;
    }
    
    setProcessingPage(true);
    setProcessingError(null);
    
    try {
      const currentPage = document.pages[selectedPageIndex];
      console.log('[handleProcessPage] Processing page:', currentPage.page_number);
      console.log('[handleProcessPage] Document ID:', documentId);
      
      const response = await processDocumentPage(
        documentId,
        currentPage.page_number
      );
      
      console.log('[handleProcessPage] Response received:', response);
      
      if (response.success) {
        // Reload document details to get the AI processing result
        console.log('[handleProcessPage] Success! Reloading document details...');
        await loadDocumentDetails();
        
        // Success message
        alert(`✅ Seite ${currentPage.page_number} erfolgreich verarbeitet!\n\nModell: ${response.result.ai_model_used}\nTokens: ${String(response.result.tokens_sent)} → ${String(response.result.tokens_received)}\nZeit: ${response.result.processing_time_ms}ms`);
      } else {
        console.log('[handleProcessPage] Processing failed');
        setProcessingError('Verarbeitung fehlgeschlagen');
      }
    } catch (error: any) {
      console.error('[handleProcessPage] Error:', error);
      setProcessingError(error.message || 'Verarbeitung fehlgeschlagen');
    } finally {
      console.log('[handleProcessPage] Finished');
      setProcessingPage(false);
    }
  };

  const handleNextPage = () => {
    if (!document) return;
    
    if (selectedPageIndex < document.pages.length - 1) {
      const nextIndex = selectedPageIndex + 1;
      setSelectedPageIndex(nextIndex);
      scrollToPage(nextIndex);
    }
  };

  const scrollToPage = (index: number) => {
    // Scroll zur ausgewählten Seite im horizontalen Container
    const container = typeof window !== 'undefined' ? window.document.getElementById('pages-scroll-container') : null;
    if (container) {
      const pageWidth = 96 + 12; // w-24 (96px) + gap-3 (12px)
      const padding = 48; // pl-12 (48px) - Padding wird bereits im Container berücksichtigt
      // Berechne Scroll-Position: index * pageWidth (Padding ist bereits im Container vorhanden)
      const scrollPosition = index * pageWidth;
      container.scrollTo({
        left: scrollPosition,
        behavior: 'smooth'
      });
    }
  };

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const getDocumentTypeName = (typeId: number) => {
    if (!documentTypes || documentTypes.length === 0) return 'Loading...';
    const type = documentTypes.find(dt => dt.id === typeId);
    return type ? type.name : 'Unknown';
  };

  const getInterestGroupName = (groupId: number) => {
    if (!interestGroups || interestGroups.length === 0) return 'Loading...';
    const group = interestGroups.find(ig => ig.id === groupId);
    return group ? group.name : 'Unknown';
  };

  const getInterestGroupCode = (groupId: number) => {
    if (!interestGroups || interestGroups.length === 0) return '';
    const group = interestGroups.find(ig => ig.id === groupId);
    return group ? group.code : '';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatProcessingTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getCurrentPage = () => {
    return document?.pages[selectedPageIndex];
  };

  const getCurrentAIResult = () => {
    return getCurrentPage()?.ai_processing_result;
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card padding="lg" className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <p className="text-gray-600 text-lg">Loading document details...</p>
        </Card>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card padding="lg" className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <p className="text-red-600 text-lg mb-4">{error || 'Document not found'}</p>
          <button
            onClick={() => router.push('/documents')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition cursor-pointer"
          >
            Back to Documents
          </button>
        </Card>
      </div>
    );
  }

  const currentPage = getCurrentPage();
  const aiResult = getCurrentAIResult();

  return (
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.back()}
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 cursor-pointer"
            >
              ← Zurück
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={() => router.push('/documents')}
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center cursor-pointer"
            >
              Alle Dokumente
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={() => router.push('/')}
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center cursor-pointer"
            >
              🏠 RAG Chat
            </button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{document.original_filename}</h1>
        </div>

        {/* Pages Section - Direkt unter Dokumentennamen (mit Thumbnails) */}
        {document.pages.length > 0 && (
          <Card padding="md" className="mb-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-800">📄 Seiten ({document.pages.length})</h2>
              <div className="text-sm text-gray-500">
                Seite {selectedPageIndex + 1} von {document.pages.length}
              </div>
            </div>
            
            <div className="relative overflow-visible">
              {/* Navigation Buttons */}
              <button
                onClick={() => {
                  if (selectedPageIndex > 0) {
                    setSelectedPageIndex(selectedPageIndex - 1);
                    scrollToPage(selectedPageIndex - 1);
                  }
                }}
                disabled={selectedPageIndex === 0}
                className={`absolute left-0 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full shadow-lg transition ${
                  selectedPageIndex === 0
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-blue-600 hover:bg-blue-50 border border-gray-300'
                }`}
                aria-label="Vorherige Seite"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button
                onClick={() => {
                  if (selectedPageIndex < document.pages.length - 1) {
                    setSelectedPageIndex(selectedPageIndex + 1);
                    scrollToPage(selectedPageIndex + 1);
                  }
                }}
                disabled={selectedPageIndex === document.pages.length - 1}
                className={`absolute right-0 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full shadow-lg transition ${
                  selectedPageIndex === document.pages.length - 1
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-blue-600 hover:bg-blue-50 border border-gray-300'
                }`}
                aria-label="Nächste Seite"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>

              {/* Horizontal Scroll Container */}
              <div
                id="pages-scroll-container"
                className="flex gap-3 overflow-x-auto overflow-y-visible pt-2 pb-2 scroll-smooth scrollbar-hide pl-12 pr-12"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'rgba(156, 163, 175, 0.5) transparent'
                }}
              >
                {document.pages.map((page, index) => (
                  <button
                    key={page.id}
                    onClick={() => {
                      setSelectedPageIndex(index);
                      scrollToPage(index);
                    }}
                    className={`flex-shrink-0 w-24 h-32 rounded-lg border-2 transition relative ${
                      selectedPageIndex === index
                        ? 'border-blue-500 bg-blue-50 shadow-md scale-105'
                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }`}
                  >
                    {/* Thumbnail oder Page Number */}
                    {page.thumbnail_path ? (
                      <img
                        src={getThumbnailImageUrl(page.thumbnail_path)}
                        alt={`Page ${page.page_number}`}
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg">
                        <p className="text-sm font-medium text-gray-600">
                          {page.page_number}
                        </p>
                      </div>
                    )}
                    
                    {/* Page Number Badge */}
                    <div className="absolute bottom-1 left-1 right-1">
                      <div className={`text-center text-xs font-semibold px-2 py-1 rounded ${
                        selectedPageIndex === index
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-700 bg-opacity-90'
                      }`}>
                        {page.page_number}
                      </div>
                    </div>
                    
                    {/* AI Processing Status Indicator */}
                    {page.ai_processing_result && (
                      <div className="absolute top-1 right-1">
                        <span className={`inline-block w-3 h-3 rounded-full ${
                          page.ai_processing_result.status === 'success'
                            ? 'bg-green-500'
                            : page.ai_processing_result.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-yellow-500'
                        }`} title={page.ai_processing_result.status} />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* NEU: Duplikat-Warning Banner (Option 3) - Zeigt ganz oben - Nur wenn wirklich Duplikat */}
        {document.is_duplicate === true && document.duplicate_of_document_id && (
          <div className="mb-6 bg-orange-50 border-l-4 border-orange-400 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-orange-500 text-2xl">⚠️</span>
                <div>
                  <h3 className="text-orange-800 font-semibold">Duplikat</h3>
                  <p className="text-orange-700 text-sm">
                    Dieses Dokument ist eine Kopie von Dokument #{document.duplicate_of_document_id}
                  </p>
                </div>
              </div>
              <a
                href={`/documents/${document.duplicate_of_document_id}`}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium"
              >
                Zum Original →
              </a>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT: Document Info */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Metadata */}
            <Card padding="md" ref={documentInfoRef}>
              <h2 className="text-xl font-bold text-gray-800 mb-4">📋 Document Information</h2>
              
              <div className="space-y-3">
                {/* Document Type */}
                <div>
                  <p className="text-sm text-gray-500">Dokumenttyp</p>
                  <p className="font-medium text-gray-900">
                    {document.document_type_name || getDocumentTypeName(document.document_type_id)}
                  </p>
                </div>

                {/* Workflow Status */}
                <div>
                  <p className="text-sm text-gray-500">Workflow-Status</p>
                  <p className="font-medium text-gray-900">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                      document.workflow_status === 'approved' 
                        ? 'bg-green-100 text-green-800' 
                        : document.workflow_status === 'rejected'
                        ? 'bg-red-100 text-red-800'
                        : document.workflow_status === 'reviewed'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {document.workflow_status === 'approved' ? '✅' : document.workflow_status === 'rejected' ? '❌' : document.workflow_status === 'reviewed' ? '👀' : '📝'}
                      {document.workflow_status === 'approved' ? 'Freigegeben' : 
                       document.workflow_status === 'rejected' ? 'Zurückgewiesen' :
                       document.workflow_status === 'reviewed' ? 'Geprüft' :
                       document.workflow_status === 'draft' ? 'Entwurf' : document.workflow_status || 'Unbekannt'}
                    </span>
                  </p>
                </div>

                {/* NEU: RAG Indexierungs-Status */}
                <div>
                  <p className="text-sm text-gray-500">RAG Indexierung</p>
                  <p className="font-medium text-gray-900">
                    {document.is_indexed ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        ✅ Indexiert
                        {document.indexed_at && (
                          <span className="text-xs opacity-75 ml-1">
                            ({new Date(document.indexed_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })})
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                        ⏳ Nicht indexiert
                      </span>
                    )}
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-3"></div>

                {/* QM Chapter */}
                <div>
                  <p className="text-sm text-gray-500">QM-Kapitel</p>
                  <p className="font-medium text-gray-900">{document.qm_chapter}</p>
                </div>

                {/* Version */}
                <div>
                  <p className="text-sm text-gray-500">Version</p>
                  <p className="font-medium text-gray-900">{document.version}</p>
                </div>

                <div className="border-t border-gray-200 pt-3"></div>

                {/* Original Filename */}
                <div>
                  <p className="text-sm text-gray-500">Original-Dateiname</p>
                  <p className="font-medium text-gray-900 break-words">{document.original_filename}</p>
                </div>

                {/* File Size */}
                <div>
                  <p className="text-sm text-gray-500">Dateigröße</p>
                  <p className="font-medium text-gray-900">
                    {formatFileSize(document.file_size_bytes)}
                  </p>
                </div>

                {/* File Type */}
                <div>
                  <p className="text-sm text-gray-500">Dateityp</p>
                  <p className="font-medium text-gray-900">{document.file_type.toUpperCase()}</p>
                </div>

                {/* Pages */}
                <div>
                  <p className="text-sm text-gray-500">Seiten</p>
                  <p className="font-medium text-gray-900">{document.page_count}</p>
                </div>

                {/* Processing Method */}
                <div>
                  <p className="text-sm text-gray-500">Verarbeitungs-Methode</p>
                  <p className="font-medium text-gray-900">
                    {document.processing_method.toUpperCase()}
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-3"></div>

                {/* Uploaded By */}
                <div>
                  <p className="text-sm text-gray-500">Hochgeladen von</p>
                  <p className="font-medium text-gray-900">
                    {document.uploaded_by_user_name || `User ${document.uploaded_by_user_id}`}
                  </p>
                </div>

                {/* Uploaded At */}
                <div>
                  <p className="text-sm text-gray-500">Hochgeladen am</p>
                  <p className="font-medium text-gray-900">{formatDate(document.uploaded_at)}</p>
                </div>
              </div>
            </Card>

            {/* Interest Groups */}
            <Card padding="md">
              <h2 className="text-xl font-bold text-gray-800 mb-4">🏢 Interest Groups</h2>
              
              {document.interest_groups.length === 0 ? (
                <p className="text-gray-500 text-sm">No interest groups assigned</p>
              ) : (
                <div className="space-y-2">
                  {document.interest_groups.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                    >
                      <p className="font-medium text-gray-900">
                        {getInterestGroupName(assignment.interest_group_id)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {getInterestGroupCode(assignment.interest_group_id)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Card>


            {/* RAG Indexierung - Nur für Level 4+ */}
            {canViewRAGIndexing && (
            <Card padding="md">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-5 h-5 text-blue-600">🗄️</div>
                <h2 className="text-xl font-bold text-gray-800">RAG Indexierung</h2>
              </div>

              {/* Indexierungs-Status Badge */}
              {document.is_indexed && (
                <div className="mb-4">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border bg-green-100 text-green-800 border-green-200">
                    <span className="w-2 h-2 rounded-full bg-green-600"></span>
                    ✅ Indexiert
                    {document.indexed_at && (
                      <span className="text-xs opacity-75 ml-1">
                        ({new Date(document.indexed_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })})
                      </span>
                    )}
                  </span>
                </div>
              )}

              {/* Status Badge - Nur wenn nicht indexiert */}
              {!document.is_indexed && (
                <div className="mb-4">
                  <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${
                    document.workflow_status === 'approved' 
                      ? 'bg-green-100 text-green-800 border-green-200' 
                      : 'bg-gray-100 text-gray-800 border-gray-200'
                  }`}>
                    <span className="w-2 h-2 rounded-full bg-current"></span>
                    {document.workflow_status === 'approved' ? 'Freigegeben' : `Workflow-Status: ${document.workflow_status || 'draft'}`}
                  </span>
                </div>
              )}

              {/* NEU: Warnung wenn Duplikat - Indexierung nicht möglich - Nur wenn wirklich Duplikat */}
              {document.is_duplicate === true && document.duplicate_of_document_id && (
                <div className="mb-4 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                  <p className="text-yellow-800 text-sm font-medium mb-1">⚠️ Indexierung nicht möglich</p>
                  <p className="text-yellow-700 text-xs">
                    Duplikate können nicht indexiert werden. Bitte indexieren Sie das Original-Dokument #{document.duplicate_of_document_id}.
                  </p>
                  <a
                    href={`/documents/${document.duplicate_of_document_id}`}
                    className="text-yellow-800 underline text-xs hover:text-yellow-900 mt-1 inline-block"
                  >
                    Zum Original springen →
                  </a>
                </div>
              )}

              {/* Indexierung Button - Nur wenn Dokument freigegeben ist UND KEIN Duplikat */}
              {document.workflow_status === 'approved' && document.is_duplicate !== true && (
                <button
                  onClick={() => {
                    // Öffne Wizard für Strategie-Auswahl
                    setShowStrategyWizard(true);
                  }}
                  disabled={isIndexing}
                  className={`w-full px-4 py-2 rounded-lg hover:opacity-90 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2 ${
                    document.is_indexed 
                      ? 'bg-orange-600 text-white hover:bg-orange-700' 
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isIndexing ? (
                    <>
                      <Spinner size="sm" className="border-white border-t-white" />
                      <span>Indexiere...</span>
                    </>
                  ) : (
                    <>
                      <span>{document.is_indexed ? '🔄' : '⚡'}</span>
                      <span>{document.is_indexed ? 'Re-Indexieren' : 'In RAG indexieren'}</span>
                    </>
                  )}
                </button>
              )}

              {/* Info */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-start gap-2 text-xs text-gray-500">
                  <span className="w-3 h-3 mt-0.5 flex-shrink-0">📊</span>
                  <div>
                    <p className="font-medium mb-1">RAG Indexierung:</p>
                    <ul className="space-y-1">
                      <li>• Dokument wird in semantische Chunks aufgeteilt</li>
                      <li>• Embeddings werden mit OpenAI generiert</li>
                      <li>• Chunks werden in Qdrant Vector Store gespeichert</li>
                      <li>• Ermöglicht intelligente Suche und Fragen</li>
                    </ul>
                  </div>
                </div>
              </div>
            </Card>
            )}

          </div>

          {/* RIGHT: Preview & AI Results (oben) & Chunk Preview (darunter, auf gleicher Höhe wie RAG Indexierung) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Preview & AI Results - OBEN für besseren Vergleich - Gleiche Höhe wie Document Information */}
            <Card 
              padding="md" 
              ref={previewCardRef}
              className={previewCardHeight ? `h-[${previewCardHeight}px] overflow-y-auto` : ''}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-800">
                  🔍 Preview
                  {currentPage && (
                    <span className="text-gray-500 font-normal ml-2">
                      (Page {currentPage.page_number} of {document.page_count})
                    </span>
                  )}
                </h2>
                
                {currentPage && canProcessAI && (
                  <button
                    onClick={handleProcessPage}
                    disabled={processingPage}
                    className={`px-4 py-2 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
                      processingPage
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {processingPage ? (
                      <>
                        <Spinner size="sm" />
                        <span>Verarbeite...</span>
                      </>
                    ) : (
                      <>
                        <span>🚀</span>
                        <span>Mit AI Verarbeiten</span>
                      </>
                    )}
                  </button>
                )}
              </div>
              
              {processingError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                  <p className="text-red-700 text-sm">❌ {processingError}</p>
                </div>
              )}
              
              {!currentPage ? (
                <div className="bg-gray-50 rounded-lg p-12 text-center">
                  <div className="text-6xl mb-4">📭</div>
                  <p className="text-gray-600">No preview available</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Preview generation may still be in progress
                  </p>
                </div>
              ) : (
                <div className={canViewAIProcessing ? "grid grid-cols-1 lg:grid-cols-2 gap-4" : ""}>
                  {/* Original Preview */}
                  <div className={canViewAIProcessing ? "" : "w-full"}>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">📄 Original</h3>
                    <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center min-h-[500px]">
                      <button
                        onClick={() => setShowImageModal(true)}
                        className="bg-white shadow-lg rounded hover:shadow-xl transition cursor-pointer"
                      >
                        <img
                          src={getPreviewImageUrl(currentPage.preview_image_path)}
                          alt={`Page ${currentPage.page_number}`}
                          className="rounded max-w-full h-auto"
                          style={{ maxHeight: '500px' }}
                        />
                      </button>
                    </div>
                  </div>

                  {/* AI Result - Nur für Level 4+ */}
                  {canViewAIProcessing && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">🤖 AI Analyse</h3>
                    {!aiResult ? (
                      // Show Prompt Template BEFORE processing
                      loadingPrompt ? (
                        <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-8 text-center min-h-[500px] flex flex-col items-center justify-center">
                          <div className="text-4xl mb-3">⏳</div>
                          <p className="text-gray-600 font-medium">Lade Prompt...</p>
                        </div>
                      ) : !defaultPromptTemplate ? (
                        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center min-h-[500px] flex flex-col items-center justify-center">
                          <div className="text-4xl mb-3">⚠️</div>
                          <p className="text-gray-600 font-medium mb-2">Kein Standard-Prompt definiert</p>
                          <p className="text-sm text-gray-500">
                            Bitte in der Prompt-Verwaltung einen Standard-Prompt für diesen Dokumenttyp zuweisen
                          </p>
                        </div>
                      ) : (
                        <button
                          onClick={() => setShowPromptModal(true)}
                          className="bg-white border-2 border-blue-200 rounded-lg overflow-hidden min-h-[500px] w-full text-left hover:border-blue-300 hover:shadow-md transition cursor-pointer"
                        >
                          {/* Prompt Header */}
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 border-b border-blue-200">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="text-lg font-semibold text-gray-800">{defaultPromptTemplate.name}</h4>
                                <p className="text-xs text-gray-500 font-mono">ID: {defaultPromptTemplate.id}</p>
                              </div>
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                {defaultPromptTemplate.version}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">{defaultPromptTemplate.description}</p>
                          </div>

                          {/* Prompt Config */}
                          <div className="p-4 bg-gray-50 border-b border-gray-200">
                            <div className="grid grid-cols-2 gap-3 text-sm">
                              <div>
                                <span className="text-gray-500">Modell:</span>
                                <span className="font-medium text-gray-900 ml-2">{defaultPromptTemplate.ai_model}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Temperature:</span>
                                <span className="font-medium text-gray-900 ml-2">{defaultPromptTemplate.temperature}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Max Tokens:</span>
                                <span className="font-medium text-gray-900 ml-2">{defaultPromptTemplate.max_tokens.toLocaleString('de-DE')}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Detail Level:</span>
                                <span className="font-medium text-gray-900 ml-2">{defaultPromptTemplate.detail_level}</span>
                              </div>
                            </div>
                          </div>

                          {/* Prompt Content - Scrollable */}
                          <div className="p-4 space-y-4 overflow-y-auto max-h-[600px]">
                            {/* System Instructions */}
                            {defaultPromptTemplate.system_instructions && (
                              <div>
                                <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                                  System Instructions:
                                </label>
                                <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
{defaultPromptTemplate.system_instructions}
                                </pre>
                              </div>
                            )}

                            {/* User Prompt */}
                            <div>
                              <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                                User Prompt:
                              </label>
                              <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
{defaultPromptTemplate.prompt_text}
                              </pre>
                            </div>

                            {/* Example Output */}
                            {defaultPromptTemplate.example_output && (
                              <div>
                                <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                                  Beispiel Output:
                                </label>
                                <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border max-h-60">
{defaultPromptTemplate.example_output}
                                </pre>
                              </div>
                            )}
                          </div>

                          {/* Call to Action */}
                          <div className="p-4 bg-blue-50 border-t border-blue-200">
                            <p className="text-sm text-gray-600">
                              ⬆️ Dieser Prompt wird für die AI-Verarbeitung verwendet
                            </p>
                          </div>
                        </button>
                      )
                    ) : (
                      <div className="space-y-3 min-h-[500px]">
                        {/* Metrics */}
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <p className="text-gray-500">Model</p>
                              <p className="font-medium text-gray-900">{aiResult.ai_model_used}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">Zeit</p>
                              <p className="font-medium text-gray-900">
                                {formatProcessingTime(aiResult.processing_time_ms)}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-500">Tokens Gesendet</p>
                              <p className="font-medium text-gray-900">{aiResult.tokens_sent}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">Tokens Empfangen</p>
                              <p className="font-medium text-gray-900">{aiResult.tokens_received}</p>
                            </div>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className="flex items-center justify-center">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            aiResult.status === 'success'
                              ? 'bg-green-100 text-green-800'
                              : aiResult.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {aiResult.status.toUpperCase()}
                          </span>
                        </div>

                        {/* Error Message - Nur anzeigen wenn Status wirklich 'failed' ist */}
                        {aiResult.status === 'failed' && aiResult.error_message && (
                          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <p className="text-red-700 text-sm font-medium mb-1">Error:</p>
                            <p className="text-red-600 text-sm">{aiResult.error_message}</p>
                          </div>
                        )}

                        {/* JSON Result */}
                        {aiResult.parsed_json && (
                          <button
                            onClick={() => setShowJsonModal(true)}
                            className="w-full text-left hover:bg-gray-50 transition rounded-lg border-2 border-transparent hover:border-gray-300 p-2"
                          >
                            <div className="mb-2">
                              <h4 className="text-sm font-medium text-gray-700">JSON Result:</h4>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-4 border overflow-auto max-h-[400px]">
                              <pre className="text-gray-800 text-sm font-mono">
                                {JSON.stringify(aiResult.parsed_json, null, 2)}
                              </pre>
                            </div>
                          </button>
                        )}

                        {/* Raw Response (fallback) */}
                        {!aiResult.parsed_json && aiResult.raw_response && (
                          <button
                            onClick={() => setShowJsonModal(true)}
                            className="w-full text-left hover:bg-gray-50 transition rounded-lg border-2 border-transparent hover:border-gray-300 p-2"
                          >
                            <div className="mb-2">
                              <h4 className="text-sm font-medium text-gray-700">Raw Response:</h4>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-4 border overflow-auto max-h-[400px]">
                              <pre className="text-gray-800 text-sm font-mono">
                                {aiResult.raw_response}
                              </pre>
                            </div>
                          </button>
                        )}

                        {/* Created At */}
                        <div className="text-xs text-gray-500 text-right">
                          Verarbeitet: {formatDate(aiResult.created_at)}
                        </div>
                      </div>
                    )}
                  </div>
                  )}
                </div>
              )}
            </Card>

            {/* Chunk Preview Panel - DARUNTER, auf gleicher Höhe wie RAG Indexierung (nutzt 2/3 Breite) */}
            {canViewRAGIndexing && document && document.is_indexed && (
              <ChunkPreviewPanel
                documentId={documentId}
                initialChunkId={chunkParam || undefined}
                highlightTerms={highlightTerms}
                onChunksLoaded={(count) => {
                  console.log(`✅ ${count} Chunks geladen für Dokument ${documentId}`);
                }}
              />
            )}
          </div>
        </div>

        {/* Kommentar-Sektion - VOLLBREITE - Direkt nach Grid */}
        {canComment && (
          <Card padding="md" className="mt-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">💬 Kommentare</h2>
                
                {/* Kommentar-Formular */}
                <div className="mb-6">
                  <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
                    Neuen Kommentar hinzufügen
                  </label>
                  <textarea
                    id="comment"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Schreiben Sie hier Ihren Kommentar..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={4}
                    disabled={submittingComment}
                  />
                  <div className="mt-2 flex justify-end">
                    <button
                      onClick={handleSubmitComment}
                      disabled={!newComment.trim() || submittingComment}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
                    >
                      {submittingComment ? 'Wird gesendet...' : 'Kommentar hinzufügen'}
                    </button>
                  </div>
                </div>

                {/* Kommentar-Liste */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Kommentare ({comments.length})
                  </h3>
                  {loadingComments ? (
                    <div className="text-center py-4">
                      <Spinner />
                    </div>
                  ) : comments.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>Noch keine Kommentare vorhanden.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {comments.map((comment) => (
                        <div
                          key={comment.id}
                          className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900">
                                {comment.user_name || `User ${comment.user_id}`}
                              </span>
                              <span className="text-xs text-gray-500">
                                {new Date(comment.created_at).toLocaleDateString('de-DE', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {comment.comment_type}
                            </span>
                          </div>
                          <p className="text-gray-700 whitespace-pre-wrap">{comment.comment_text}</p>
                        </div>
                      ))}
                    </div>
              )}
            </div>
          </Card>
        )}

        {/* Image Preview Modal */}
        {showImageModal && currentPage && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold">
                  Document Preview - Page {currentPage.page_number}
                </h2>
                <button
                  onClick={() => setShowImageModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>
              <div className="flex justify-center">
                <img
                  src={getPreviewImageUrl(currentPage.preview_image_path)}
                  alt={`Page ${currentPage.page_number}`}
                  className="max-w-full h-auto"
                />
              </div>
              <div className="flex justify-end pt-4 border-t mt-4">
                <button
                  onClick={() => setShowImageModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Schließen
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Prompt Preview Modal */}
        {showPromptModal && defaultPromptTemplate && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold">{defaultPromptTemplate.name}</h2>
                <button
                  onClick={() => setShowPromptModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* Config Grid */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded">
                  <div>
                    <span className="font-medium">Modell:</span> {defaultPromptTemplate.ai_model}
                  </div>
                  <div>
                    <span className="font-medium">Version:</span> {defaultPromptTemplate.version}
                  </div>
                  <div>
                    <span className="font-medium">Temperature:</span> {defaultPromptTemplate.temperature}
                  </div>
                  <div>
                    <span className="font-medium">Max Tokens:</span> {defaultPromptTemplate.max_tokens}
                  </div>
                </div>

                {/* System Instructions */}
                {defaultPromptTemplate.system_instructions && (
                  <div>
                    <label className="block font-medium mb-2">System Instructions:</label>
                    <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
                      {defaultPromptTemplate.system_instructions}
                    </pre>
                  </div>
                )}

                {/* User Prompt */}
                <div>
                  <label className="block font-medium mb-2">User Prompt:</label>
                  <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
                    {defaultPromptTemplate.prompt_text}
                  </pre>
                </div>

                {/* Example Output */}
                {defaultPromptTemplate.example_output && (
                  <div>
                    <label className="block font-medium mb-2">Beispiel Output:</label>
                    <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border max-h-60">
                      {defaultPromptTemplate.example_output}
                    </pre>
                  </div>
                )}

                <div className="flex justify-end pt-4 border-t">
                  <button
                    onClick={() => setShowPromptModal(false)}
                    className="px-4 py-2 border rounded hover:bg-gray-50"
                  >
                    Schließen
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* JSON Response Modal */}
        {showJsonModal && aiResult && aiResult.parsed_json && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold">AI Processing Result</h2>
                <button
                  onClick={() => setShowJsonModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded mb-4">
                <div>
                  <span className="font-medium">Modell:</span> {aiResult.ai_model_used}
                </div>
                <div>
                  <span className="font-medium">Tokens:</span> {aiResult.tokens_sent} / {aiResult.tokens_received}
                </div>
                <div>
                  <span className="font-medium">Zeit:</span> {aiResult.processing_time_ms}ms
                </div>
              </div>

              {/* JSON Content */}
              <div>
                <label className="block font-medium mb-2">JSON Response:</label>
                <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap border">
                  {JSON.stringify(aiResult.parsed_json, null, 2)}
                </pre>
              </div>

              <div className="flex justify-end pt-4 border-t mt-4">
                <button
                  onClick={() => setShowJsonModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Schließen
                </button>
              </div>
            </div>
          </div>
        )}

      {/* Chunking Strategy Wizard (PHASE 2.3) */}
      {showStrategyWizard && document && (
        <ChunkingStrategyWizard
          isOpen={showStrategyWizard}
          onClose={() => {
            setShowStrategyWizard(false);
            setSelectedChunkingStrategy(null);
          }}
          onSelect={handleIndexDocument}
          documentType={document.document_type_id?.toString()}
          documentTypeName={documentTypes?.find(dt => dt.id === document.document_type_id)?.name || 'Unbekannt'}
        />
      )}
    </div>
  );
}
