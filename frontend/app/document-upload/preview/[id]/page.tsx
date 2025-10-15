"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  getUploadDetails,
  processDocumentPage,
  getPreviewImageUrl,
  UploadedDocumentDetail,
  DocumentPage,
  AIProcessingResult,
} from '@/lib/api/documentUpload';

// ============================================================================
// TYPES
// ============================================================================

interface DocumentType {
  id: number;
  name: string;
}

interface PromptTemplate {
  id: number;
  name: string;
  prompt_text: string;
  ai_model: string;
  temperature: number;
  max_tokens: number;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function UploadPreviewPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = parseInt(params.id as string);
  
  // State
  const [document, setDocument] = useState<UploadedDocumentDetail | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [promptTemplate, setPromptTemplate] = useState<PromptTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [processingPages, setProcessingPages] = useState<Set<number>>(new Set());
  const [processingErrors, setProcessingErrors] = useState<Record<number, string>>({});
  const [allPagesProcessed, setAllPagesProcessed] = useState(false);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    if (documentId) {
      loadDocument();
      loadDocumentTypes();
    }
  }, [documentId]);

  useEffect(() => {
    if (document && documentTypes.length > 0) {
      loadPromptTemplate();
    }
  }, [document, documentTypes]);

  useEffect(() => {
    checkAllPagesProcessed();
  }, [document]);

  // ============================================================================
  // API CALLS
  // ============================================================================

  const loadDocument = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/document-upload/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      
      const data = await response.json();
      
      if (response.ok && data.success && data.document) {
        setDocument(data.document);
      } else {
        setError(data.detail || 'Dokument nicht gefunden');
      }
    } catch (error: any) {
      setError(error.message || 'Fehler beim Laden des Dokuments');
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/document-types/', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      setDocumentTypes(data.document_types || []);
    } catch (error) {
      console.error('Failed to load document types:', error);
    }
  };

  const loadPromptTemplate = async () => {
    if (!document) return;
    
    try {
      // Hole Standard-Prompt für Dokumenttyp
      const response = await fetch(`http://localhost:8000/api/prompt-templates/?document_type_id=${document.document_type_id}&active_only=true`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      
      if (data.templates && data.templates.length > 0) {
        // Nehme das erste aktive Template
        const template = data.templates[0];
        setPromptTemplate({
          id: template.id,
          name: template.name,
          prompt_text: template.prompt_text,
          ai_model: template.ai_model,
          temperature: template.temperature / 100, // Convert from int to float
          max_tokens: template.max_tokens
        });
      }
    } catch (error) {
      console.error('Failed to load prompt template:', error);
    }
  };

  const handleProcessPage = async (pageIndex: number) => {
    if (!document || pageIndex >= document.pages.length) return;

    const pageNumber = pageIndex + 1;
    setProcessingPages(prev => new Set(prev).add(pageIndex));
    setProcessingErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[pageIndex];
      return newErrors;
    });

    try {
      const response = await processDocumentPage(documentId, pageNumber);
      
      if (response.success && response.data) {
        // Update the page with AI processing result
        const updatedPages = [...document.pages];
        updatedPages[pageIndex] = {
          ...updatedPages[pageIndex],
          ai_processing_result: response.data
        };
        
        setDocument({
          ...document,
          pages: updatedPages
        });
      } else {
        setProcessingErrors(prev => ({
          ...prev,
          [pageIndex]: response.error || 'Processing failed'
        }));
      }
    } catch (error: any) {
      console.error('Processing error:', error);
      setProcessingErrors(prev => ({
        ...prev,
        [pageIndex]: error.message || 'Processing failed'
      }));
    } finally {
      setProcessingPages(prev => {
        const newSet = new Set(prev);
        newSet.delete(pageIndex);
        return newSet;
      });
    }
  };

  const handleProcessAllPages = async () => {
    if (!document) return;

    for (let i = 0; i < document.pages.length; i++) {
      if (!document.pages[i].ai_processing_result) {
        await handleProcessPage(i);
        // Kleine Pause zwischen den Requests
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  };

  const handleFinishUpload = () => {
    router.push('/documents');
  };

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const checkAllPagesProcessed = () => {
    if (!document) return;
    
    const processedCount = document.pages.filter(page => 
      page.ai_processing_result && page.ai_processing_result.status === 'success'
    ).length;
    
    setAllPagesProcessed(processedCount === document.pages.length && document.pages.length > 0);
  };

  const getDocumentTypeName = (typeId: number) => {
    const type = documentTypes.find(dt => dt.id === typeId);
    return type ? type.name : 'Unbekannt';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatProcessingTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Dokument wird geladen...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-red-600 mb-4">{error || 'Dokument nicht gefunden'}</p>
          <button
            onClick={() => router.push('/document-upload')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Zurück zum Upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => router.push('/document-upload')}
                className="text-blue-600 hover:text-blue-700 font-medium mb-2 flex items-center"
              >
                ← Zurück zum Upload
              </button>
              <h1 className="text-3xl font-bold text-gray-900">📤 Upload-Vorschau</h1>
              <p className="text-gray-600">Überprüfen Sie das Dokument und starten Sie die AI-Verarbeitung</p>
            </div>
            
            {/* Finish Button */}
            <div className="text-right">
              <div className="mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  allPagesProcessed 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {allPagesProcessed ? '✅ Alle Seiten verarbeitet' : '⏳ Verarbeitung ausstehend'}
                </span>
              </div>
              <button
                onClick={handleFinishUpload}
                className={`px-6 py-3 rounded-lg font-medium transition ${
                  allPagesProcessed
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
                disabled={!allPagesProcessed}
              >
                🚀 Upload abschließen
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT: Document Info & Prompt */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Document Metadata */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Dokument-Information</h2>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Dateiname</p>
                  <p className="font-medium text-gray-900">{document.original_filename}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Dokumenttyp</p>
                  <p className="font-medium text-gray-900">{getDocumentTypeName(document.document_type_id)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">QM-Kapitel</p>
                  <p className="font-medium text-gray-900">{document.qm_chapter || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Version</p>
                  <p className="font-medium text-gray-900">{document.version}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Dateigröße</p>
                  <p className="font-medium text-gray-900">{formatFileSize(document.file_size_bytes)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Seiten</p>
                  <p className="font-medium text-gray-900">{document.pages.length}</p>
                </div>
              </div>
            </div>

            {/* Prompt Template Preview */}
            {promptTemplate && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">🎯 AI-Prompt Vorschau</h2>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500">Template</p>
                    <p className="font-medium text-gray-900">{promptTemplate.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">AI-Modell</p>
                    <p className="font-medium text-gray-900">{promptTemplate.ai_model}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Temperature</p>
                      <p className="font-medium text-gray-900">{promptTemplate.temperature}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Max Tokens</p>
                      <p className="font-medium text-gray-900">{promptTemplate.max_tokens}</p>
                    </div>
                  </div>
                  
                  {/* Prompt Text Preview */}
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Prompt-Text (Vorschau)</p>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-xs text-gray-700 font-mono leading-relaxed">
                        {promptTemplate.prompt_text.substring(0, 300)}
                        {promptTemplate.prompt_text.length > 300 && '...'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Processing Actions */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">🚀 AI-Verarbeitung</h2>
              
              <div className="space-y-3">
                <button
                  onClick={handleProcessAllPages}
                  disabled={processingPages.size > 0 || allPagesProcessed}
                  className={`w-full px-4 py-3 rounded-lg font-medium transition ${
                    allPagesProcessed
                      ? 'bg-green-100 text-green-800 cursor-not-allowed'
                      : processingPages.size > 0
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {allPagesProcessed 
                    ? '✅ Alle Seiten verarbeitet'
                    : processingPages.size > 0
                    ? '⏳ Verarbeitung läuft...'
                    : '🚀 Alle Seiten verarbeiten'
                  }
                </button>

                <div className="text-xs text-gray-500 text-center">
                  oder einzelne Seiten rechts auswählen
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT: Page Preview & Processing */}
          <div className="lg:col-span-2">
            
            {/* Page Navigation */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">📄 Seiten-Vorschau</h2>
                <p className="text-sm text-gray-600">
                  Seite {selectedPageIndex + 1} von {document.pages.length}
                </p>
              </div>

              {/* Page Thumbnails */}
              <div className="grid grid-cols-8 gap-2 mb-6">
                {document.pages.map((page, index) => {
                  const isProcessed = page.ai_processing_result?.status === 'success';
                  const isProcessing = processingPages.has(index);
                  const hasError = processingErrors[index];

                  return (
                    <button
                      key={page.id}
                      onClick={() => setSelectedPageIndex(index)}
                      className={`aspect-[3/4] rounded-lg border-2 transition relative ${
                        selectedPageIndex === index
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {/* Status Indicator */}
                      <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white">
                        {isProcessing ? (
                          <div className="w-full h-full bg-yellow-400 rounded-full animate-pulse"></div>
                        ) : isProcessed ? (
                          <div className="w-full h-full bg-green-500 rounded-full"></div>
                        ) : hasError ? (
                          <div className="w-full h-full bg-red-500 rounded-full"></div>
                        ) : (
                          <div className="w-full h-full bg-gray-300 rounded-full"></div>
                        )}
                      </div>

                      <div className="flex items-center justify-center h-full text-xs font-medium text-gray-600">
                        {index + 1}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Current Page Preview */}
              {document.pages[selectedPageIndex] && (
                <div className="space-y-4">
                  {/* Preview Image */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                    <img
                      src={getPreviewImageUrl(document.pages[selectedPageIndex].preview_path)}
                      alt={`Seite ${selectedPageIndex + 1}`}
                      className="max-w-full max-h-96 mx-auto rounded-lg shadow-sm"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI4MCIgdmlld0JveD0iMCAwIDIwMCAyODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjgwIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTQwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2QjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk5vIFByZXZpZXc8L3RleHQ+Cjwvc3ZnPg==';
                      }}
                    />
                  </div>

                  {/* Page Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {/* Previous Page */}
                      <button
                        onClick={() => setSelectedPageIndex(Math.max(0, selectedPageIndex - 1))}
                        disabled={selectedPageIndex === 0}
                        className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ← Vorherige
                      </button>

                      {/* Next Page */}
                      <button
                        onClick={() => setSelectedPageIndex(Math.min(document.pages.length - 1, selectedPageIndex + 1))}
                        disabled={selectedPageIndex === document.pages.length - 1}
                        className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Nächste →
                      </button>
                    </div>

                    {/* Process This Page */}
                    <button
                      onClick={() => handleProcessPage(selectedPageIndex)}
                      disabled={
                        processingPages.has(selectedPageIndex) || 
                        document.pages[selectedPageIndex].ai_processing_result?.status === 'success'
                      }
                      className={`px-4 py-2 rounded-lg font-medium transition ${
                        document.pages[selectedPageIndex].ai_processing_result?.status === 'success'
                          ? 'bg-green-100 text-green-800 cursor-not-allowed'
                          : processingPages.has(selectedPageIndex)
                          ? 'bg-yellow-100 text-yellow-800 cursor-not-allowed'
                          : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600'
                      }`}
                    >
                      {document.pages[selectedPageIndex].ai_processing_result?.status === 'success'
                        ? '✅ Verarbeitet'
                        : processingPages.has(selectedPageIndex)
                        ? '⏳ Verarbeitung...'
                        : '🚀 Diese Seite verarbeiten'
                      }
                    </button>
                  </div>

                  {/* Processing Error */}
                  {processingErrors[selectedPageIndex] && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                      <strong>Fehler:</strong> {processingErrors[selectedPageIndex]}
                    </div>
                  )}

                  {/* AI Result Preview */}
                  {document.pages[selectedPageIndex].ai_processing_result && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h3 className="font-bold text-gray-900 mb-2">🤖 AI-Analyse Ergebnis</h3>
                      
                      {/* Metrics */}
                      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <p className="text-gray-500">Modell</p>
                          <p className="font-medium">{document.pages[selectedPageIndex].ai_processing_result?.ai_model_used}</p>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <p className="text-gray-500">Zeit</p>
                          <p className="font-medium">{formatProcessingTime(document.pages[selectedPageIndex].ai_processing_result?.processing_time_ms || 0)}</p>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <p className="text-gray-500">Tokens</p>
                          <p className="font-medium">
                            {document.pages[selectedPageIndex].ai_processing_result?.tokens_sent || 0} / {document.pages[selectedPageIndex].ai_processing_result?.tokens_received || 0}
                          </p>
                        </div>
                      </div>

                      {/* JSON Preview */}
                      <div className="bg-gray-900 text-green-400 p-3 rounded-lg text-xs font-mono max-h-40 overflow-y-auto">
                        <pre>{JSON.stringify(
                          JSON.parse(document.pages[selectedPageIndex].ai_processing_result?.json_response || '{}'), 
                          null, 
                          2
                        )}</pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
