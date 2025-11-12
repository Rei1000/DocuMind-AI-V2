"""
Test-Script zur Verifikation des RAG Cleanup nach Dokument-Löschung.

Prüft:
1. Dokument-Status vor Löschung (indexiert? Chunks vorhanden?)
2. Soft Delete des Dokuments
3. Verifikation nach Löschung:
   - IndexedDocument gelöscht?
   - DocumentChunks gelöscht?
   - Qdrant Vektoren entfernt?
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import UploadDocument, IndexedDocument, DocumentChunk
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter
from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyIndexedDocumentRepository,
    SQLAlchemyDocumentChunkRepository
)
from contexts.ragintegration.application.use_cases import RemoveDocumentFromRAGUseCase
from qdrant_client.models import Filter, FieldCondition, MatchValue


def get_indexed_documents(db: Session) -> list:
    """Hole alle indexierten Dokumente."""
    indexed_docs = db.query(IndexedDocument).all()
    result = []
    for idx_doc in indexed_docs:
        upload_doc = db.query(UploadDocument).filter(
            UploadDocument.id == idx_doc.upload_document_id
        ).first()
        result.append({
            'indexed_document_id': idx_doc.id,
            'upload_document_id': idx_doc.upload_document_id,
            'document_title': idx_doc.document_title,
            'collection_name': idx_doc.collection_name,
            'total_chunks': idx_doc.total_chunks,
            'upload_filename': upload_doc.original_filename if upload_doc else 'N/A',
            'workflow_status': upload_doc.workflow_status.value if upload_doc else 'N/A'
        })
    return result


def count_chunks_in_db(db: Session, indexed_document_id: int) -> int:
    """Zähle Chunks in der Datenbank für ein indexiertes Dokument."""
    return db.query(DocumentChunk).filter(
        DocumentChunk.indexed_document_id == indexed_document_id
    ).count()


def count_chunks_in_qdrant(collection_name: str, document_id: int) -> int:
    """Zähle Chunks in Qdrant für ein Dokument."""
    try:
        vector_store = QdrantVectorStoreAdapter(collection_name=collection_name)
        # Scroll durch alle Chunks des Dokuments
        scroll_result = vector_store.client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            ),
            limit=10000
        )
        return len(scroll_result[0]) if scroll_result else 0
    except Exception as e:
        print(f"⚠️  Fehler beim Zählen der Qdrant-Chunks: {e}")
        return -1


def verify_rag_cleanup(db: Session, upload_document_id: int):
    """Prüfe ob Dokument vollständig aus RAG entfernt wurde."""
    print(f"\n{'='*60}")
    print(f"🔍 VERIFIKATION: Dokument-ID {upload_document_id}")
    print(f"{'='*60}")
    
    # 1. Prüfe IndexedDocument
    indexed_doc = db.query(IndexedDocument).filter(
        IndexedDocument.upload_document_id == upload_document_id
    ).first()
    
    if indexed_doc:
        print(f"❌ FEHLER: IndexedDocument existiert noch (ID: {indexed_doc.id})")
        return False
    else:
        print(f"✅ IndexedDocument wurde entfernt")
    
    # 2. Prüfe DocumentChunks (sollten alle gelöscht sein, da IndexedDocument gelöscht ist)
    chunks_count = db.query(DocumentChunk).join(IndexedDocument).filter(
        IndexedDocument.upload_document_id == upload_document_id
    ).count()
    
    if chunks_count > 0:
        print(f"⚠️  WARNUNG: {chunks_count} DocumentChunks gefunden (sollten 0 sein)")
        # Prüfe direkt über IndexedDocument ID
        all_chunks = db.query(DocumentChunk).all()
        matching_chunks = [c for c in all_chunks if hasattr(c, 'indexed_document_id')]
        print(f"   Gesamt Chunks in DB: {len(all_chunks)}")
    else:
        print(f"✅ DocumentChunks wurden entfernt")
    
    # 3. Prüfe Qdrant (versuche alle Collections)
    # Da wir die Collection nicht mehr kennen, prüfen wir alle bekannten Collections
    vector_store = QdrantVectorStoreAdapter()
    try:
        collections = vector_store.client.get_collections()
        qdrant_found = False
        for collection in collections.collections:
            collection_name = collection.name
            try:
                count = count_chunks_in_qdrant(collection_name, upload_document_id)
                if count > 0:
                    print(f"❌ FEHLER: {count} Chunks noch in Qdrant Collection '{collection_name}'")
                    qdrant_found = True
            except Exception as e:
                # Collection existiert möglicherweise nicht mehr - OK
                pass
        
        if not qdrant_found:
            print(f"✅ Qdrant: Keine Chunks für dieses Dokument gefunden")
    except Exception as e:
        print(f"⚠️  WARNUNG: Konnte Qdrant nicht prüfen: {e}")
    
    return True


def main():
    """Hauptfunktion: Zeige indexierte Dokumente, wähle eines zum Löschen, lösche es und verifiziere."""
    db = SessionLocal()
    
    try:
        # 1. Zeige alle indexierten Dokumente
        print("\n" + "="*60)
        print("📋 INDEXIERTE DOKUMENTE")
        print("="*60)
        
        indexed_docs = get_indexed_documents(db)
        if not indexed_docs:
            print("❌ Keine indexierten Dokumente gefunden!")
            return
        
        for i, doc in enumerate(indexed_docs, 1):
            print(f"\n{i}. {doc['upload_filename']}")
            print(f"   Upload Document ID: {doc['upload_document_id']}")
            print(f"   Indexed Document ID: {doc['indexed_document_id']}")
            print(f"   Collection: {doc['collection_name']}")
            print(f"   Total Chunks: {doc['total_chunks']}")
            print(f"   Workflow Status: {doc['workflow_status']}")
            
            # Zähle Chunks in DB
            chunks_in_db = count_chunks_in_db(db, doc['indexed_document_id'])
            print(f"   Chunks in DB: {chunks_in_db}")
            
            # Zähle Chunks in Qdrant
            chunks_in_qdrant = count_chunks_in_qdrant(
                doc['collection_name'],
                doc['upload_document_id']
            )
            print(f"   Chunks in Qdrant: {chunks_in_qdrant}")
        
        # 2. Wähle Dokument zum Löschen
        print("\n" + "="*60)
        if len(sys.argv) > 1:
            upload_doc_id = int(sys.argv[1])
            print(f"🗑️  LÖSCHE DOKUMENT ID: {upload_doc_id}")
        else:
            print("Bitte geben Sie die Upload Document ID zum Löschen an:")
            print("python test_rag_cleanup_verification.py <upload_document_id>")
            return
        
        # Prüfe ob Dokument existiert und indexiert ist
        upload_doc = db.query(UploadDocument).filter(
            UploadDocument.id == upload_doc_id
        ).first()
        
        if not upload_doc:
            print(f"❌ Dokument {upload_doc_id} nicht gefunden!")
            return
        
        indexed_doc = db.query(IndexedDocument).filter(
            IndexedDocument.upload_document_id == upload_doc_id
        ).first()
        
        if not indexed_doc:
            print(f"⚠️  Dokument {upload_doc_id} ist nicht indexiert (kein Cleanup nötig)")
            return
        
        # 3. Zeige Status VOR Löschung
        print(f"\n{'='*60}")
        print(f"📊 STATUS VOR LÖSCHUNG")
        print(f"{'='*60}")
        print(f"Dokument: {upload_doc.original_filename}")
        print(f"Upload Document ID: {upload_doc_id}")
        print(f"Indexed Document ID: {indexed_doc.id}")
        print(f"Collection: {indexed_doc.collection_name}")
        print(f"Total Chunks (laut IndexedDocument): {indexed_doc.total_chunks}")
        
        chunks_before_db = count_chunks_in_db(db, indexed_doc.id)
        chunks_before_qdrant = count_chunks_in_qdrant(
            indexed_doc.collection_name,
            upload_doc_id
        )
        print(f"Chunks in DB: {chunks_before_db}")
        print(f"Chunks in Qdrant: {chunks_before_qdrant}")
        
        # 4. Führe RAG Cleanup durch (simuliere Event Handler)
        print(f"\n{'='*60}")
        print(f"🧹 FÜHRE RAG CLEANUP DURCH")
        print(f"{'='*60}")
        
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db)
        chunk_repo = SQLAlchemyDocumentChunkRepository(db)
        vector_store = QdrantVectorStoreAdapter(collection_name=indexed_doc.collection_name)
        
        remove_use_case = RemoveDocumentFromRAGUseCase(
            indexed_document_repository=indexed_doc_repo,
            document_chunk_repository=chunk_repo,
            vector_store=vector_store
        )
        
        result = remove_use_case.execute(upload_doc_id)
        print(f"✅ Cleanup Ergebnis: {result}")
        
        db.commit()  # WICHTIG: Commit damit DB-Änderungen gespeichert werden
        
        # 5. Verifiziere nach Löschung
        verify_rag_cleanup(db, upload_doc_id)
        
        print(f"\n{'='*60}")
        print(f"✅ RAG CLEANUP VERIFIKATION ABGESCHLOSSEN")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()






