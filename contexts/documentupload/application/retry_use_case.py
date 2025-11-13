"""
Retry Use Case für fehlgeschlagene Dokumente

Ermöglicht das erneute Starten der AI-Verarbeitung für Dokumente,
bei denen die initiale Verarbeitung fehlgeschlagen ist.
"""
from typing import List
from datetime import datetime

from ..domain.entities import UploadedDocument, AIProcessingResult
from ..domain.repositories import UploadRepository, DocumentPageRepository, AIResponseRepository
from ..domain.value_objects import ProcessingStatus
from contexts.prompttemplates.domain.repositories import PromptTemplateRepository
from .ports import AIProcessingService


class RetryDocumentProcessingUseCase:
    """
    Use Case: Starte AI-Verarbeitung für fehlgeschlagenes Dokument neu
    
    Dieser Use Case ermöglicht es, die AI-Verarbeitung für Dokumente zu wiederholen,
    bei denen die initiale Verarbeitung fehlgeschlagen ist (z.B. wegen Safety Filter,
    Network-Fehler, Rate Limit).
    """
    
    def __init__(
        self,
        upload_repo: UploadRepository,
        page_repo: DocumentPageRepository,
        ai_response_repo: AIResponseRepository,
        prompt_template_repo: PromptTemplateRepository,
        ai_processing_service: AIProcessingService
    ):
        self.upload_repo = upload_repo
        self.page_repo = page_repo
        self.ai_response_repo = ai_response_repo
        self.prompt_template_repo = prompt_template_repo
        self.ai_processing_service = ai_processing_service
    
    async def execute(
        self,
        document_id: int,
        retry_all_pages: bool = True
    ) -> dict:
        """
        Starte AI-Verarbeitung für Dokument neu.
        
        Args:
            document_id: ID des Dokuments
            retry_all_pages: Wenn True, alle Seiten neu verarbeiten.
                            Wenn False, nur fehlgeschlagene Seiten.
        
        Returns:
            Dict mit Retry-Statistiken:
                - total_pages: Anzahl Seiten gesamt
                - retried_pages: Anzahl neu verarbeiteter Seiten
                - successful_pages: Anzahl erfolgreicher Verarbeitungen
                - failed_pages: Anzahl fehlgeschlagener Verarbeitungen
                - errors: Liste von Fehler-Messages
        
        Raises:
            ValueError: Wenn Dokument nicht gefunden
        """
        # 1. Lade Dokument
        document = await self.upload_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # 2. Lade Seiten
        pages = await self.page_repo.get_by_document_id(document_id)
        if not pages:
            raise ValueError(f"No pages found for document {document_id}")
        
        # 3. Hole Standard-Prompt-Template
        prompt_template = await self.prompt_template_repo.get_standard_for_document_type(
            document_type_id=document.document_type_id
        )
        if not prompt_template:
            raise ValueError(
                f"No standard prompt template found for document type {document.document_type_id}"
            )
        
        # 4. Bestimme welche Seiten verarbeitet werden sollen
        pages_to_retry = []
        
        if retry_all_pages:
            # Alle Seiten
            pages_to_retry = pages
        else:
            # Nur fehlgeschlagene Seiten
            for page in pages:
                # Prüfe ob letzte Verarbeitung fehlgeschlagen
                responses = await self.ai_response_repo.get_by_page_id(page.id)
                if responses:
                    latest_response = responses[-1]  # Letzte Response
                    if latest_response.processing_status == "failed":
                        pages_to_retry.append(page)
                else:
                    # Keine Response vorhanden → noch nicht verarbeitet
                    pages_to_retry.append(page)
        
        # 5. Verarbeite Seiten
        results = []
        errors = []
        
        for page in pages_to_retry:
            try:
                print(f"[RetryUseCase] Retrying page {page.page_number} of document {document_id}")
                
                # Verwende AIProcessingService
                ai_result = await self.ai_processing_service.process_page(
                    page_image_path=str(page.preview_image_path),
                    prompt_text=prompt_template.prompt_text,
                    ai_model_id=prompt_template.ai_model,
                    temperature=prompt_template.temperature,
                    max_tokens=prompt_template.max_tokens,
                    top_p=prompt_template.top_p,
                    detail_level=prompt_template.detail_level
                )
                
                # Erstelle AIProcessingResult Entity
                processing_result = AIProcessingResult(
                    id=None,
                    upload_document_id=document_id,
                    upload_document_page_id=page.id,
                    prompt_template_id=prompt_template.id,
                    ai_model_id=prompt_template.ai_model,
                    model_name=ai_result["model_name"],
                    json_response=ai_result["json_response"],
                    processing_status="completed",
                    tokens_sent=ai_result["tokens_sent"],
                    tokens_received=ai_result["tokens_received"],
                    total_tokens=ai_result["total_tokens"],
                    response_time_ms=ai_result["response_time_ms"],
                    error_message=None,
                    processed_at=datetime.utcnow()
                )
                
                # Speichere Result
                saved_result = await self.ai_response_repo.save(processing_result)
                results.append({"page": page.page_number, "status": "success", "result": saved_result})
                
                print(f"[RetryUseCase] Successfully retried page {page.page_number}")
                
            except Exception as e:
                # Fehler bei Verarbeitung
                error_msg = str(e)
                errors.append(f"Page {page.page_number}: {error_msg}")
                
                # Erstelle Failed Result
                failed_result = AIProcessingResult(
                    id=None,
                    upload_document_id=document_id,
                    upload_document_page_id=page.id,
                    prompt_template_id=prompt_template.id,
                    ai_model_id=prompt_template.ai_model,
                    model_name="unknown",
                    json_response="{}",
                    processing_status="failed",
                    tokens_sent=0,
                    tokens_received=0,
                    total_tokens=0,
                    response_time_ms=0,
                    error_message=error_msg,
                    processed_at=datetime.utcnow()
                )
                
                # Speichere Failed Result
                await self.ai_response_repo.save(failed_result)
                results.append({"page": page.page_number, "status": "failed", "error": error_msg})
                
                print(f"[RetryUseCase] Failed to retry page {page.page_number}: {error_msg}")
        
        # 6. Update Document Processing Status
        successful_count = len([r for r in results if r["status"] == "success"])
        failed_count = len([r for r in results if r["status"] == "failed"])
        
        if failed_count == 0 and successful_count > 0:
            # Alle erfolgreich
            document.processing_status = ProcessingStatus.COMPLETED
        elif successful_count > 0:
            # Teilweise erfolgreich
            document.processing_status = ProcessingStatus.COMPLETED  # Oder PARTIAL?
        else:
            # Alle fehlgeschlagen
            document.processing_status = ProcessingStatus.FAILED
        
        await self.upload_repo.save(document)
        
        # 7. Return Statistiken
        return {
            "total_pages": len(pages),
            "retried_pages": len(pages_to_retry),
            "successful_pages": successful_count,
            "failed_pages": failed_count,
            "errors": errors,
            "results": results
        }

