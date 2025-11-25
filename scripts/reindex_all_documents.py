#!/usr/bin/env python3
"""
Script: Re-Indexiere alle Dokumente mit einheitlichem Embedding-Modell

Dieses Script re-indexiert alle bereits indexierten Dokumente mit dem
einheitlichen Embedding-Modell text-embedding-3-small.

Verwendung:
    python scripts/reindex_all_documents.py
"""

import os
import sys
import time

# Füge Projekt-Root und Backend-Pfad hinzu
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

# Lade .env Datei
try:
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ .env Datei geladen: {env_path}")
    else:
        print(f"⚠️ .env Datei nicht gefunden: {env_path}")
except ImportError:
    # Fallback: Lade .env manuell
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        print(f"✅ .env Datei geladen (manuell): {env_path}")

from backend.app.database import SessionLocal
from sqlalchemy import text
from contexts.ragintegration.infrastructure.adapters import RAGInfrastructureAdapter
from contexts.ragintegration.application.use_cases import IndexApprovedDocumentUseCase
from contexts.ragintegration.infrastructure.embedding_factory import create_embedding_service, DEFAULT_EMBEDDING_MODEL

def reindex_all_documents():
    """Re-indexiere alle Dokumente mit einheitlichem Embedding-Modell."""
    
    print("=" * 80)
    print("RE-INDEXIERUNG ALLER DOKUMENTE")
    print("=" * 80)
    print()
    print(f"Verwendetes Embedding-Modell: {DEFAULT_EMBEDDING_MODEL}")
    print()
    
    db = SessionLocal()
    
    try:
        # Hole alle indexierten Dokumente
        result = db.execute(text("""
            SELECT 
                rid.id,
                rid.upload_document_id,
                rid.embedding_model,
                ud.original_filename,
                dt.name as document_type,
                ud.workflow_status
            FROM rag_indexed_documents rid
            JOIN upload_documents ud ON rid.upload_document_id = ud.id
            JOIN document_types dt ON ud.document_type_id = dt.id
            WHERE ud.workflow_status = 'approved'  -- Nur freigegebene Dokumente
            ORDER BY rid.indexed_at DESC
        """))
        
        docs = result.fetchall()
        
        print(f"Gefundene Dokumente: {len(docs)}")
        print()
        
        if len(docs) == 0:
            print("Keine Dokumente zum Re-Indexieren gefunden.")
            return
        
        # Erstelle RAG Adapter
        openai_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ FEHLER: OPENAI_GPT5_MINI_API_KEY oder OPENAI_API_KEY nicht gesetzt!")
            print("   Bitte setze den API Key in .env")
            return
        
        rag_adapter = RAGInfrastructureAdapter(
            db_session=db,
            openai_api_key=openai_key,
            collection_name="rag_documents"
        )
        
        # Erstelle Embedding Service mit einheitlichem Modell
        embedding_service = create_embedding_service(
            provider="openai",
            model_name=DEFAULT_EMBEDDING_MODEL,
            openai_api_key=openai_key
        )
        
        print(f"✅ Embedding Service erstellt: {DEFAULT_EMBEDDING_MODEL}")
        print()
        
        # Erstelle Use Case
        use_case = IndexApprovedDocumentUseCase(
            indexed_document_repo=rag_adapter.indexed_document_repo,
            chunk_repo=rag_adapter.document_chunk_repo,
            vision_extractor=rag_adapter.vision_extractor,
            chunking_service=rag_adapter.chunking_service,
            embedding_service=embedding_service,
            vector_store=rag_adapter.vector_store,
            event_publisher=None
        )
        
        # Re-indexiere jedes Dokument
        success_count = 0
        error_count = 0
        
        for i, doc in enumerate(docs, 1):
            indexed_doc_id = doc[0]
            upload_doc_id = doc[1]
            current_model = doc[2]
            filename = doc[3]
            doc_type = doc[4]
            
            print(f"{i}/{len(docs)}. Re-Indexiere: {filename}")
            print(f"   Upload ID: {upload_doc_id}, Typ: {doc_type}")
            print(f"   Aktuelles Modell: {current_model}")
            
            # Prüfe ob bereits text-embedding-3-small
            # WICHTIG: Auch wenn Modell text-embedding-3-small ist, könnten die Vektoren Mock Embeddings sein
            # Prüfe daher die Embedding-Qualität in Qdrant
            should_skip = False
            if current_model == DEFAULT_EMBEDDING_MODEL:
                # Hole Collection-Name
                collection_result = db.execute(text("""
                    SELECT qdrant_collection_name
                    FROM rag_indexed_documents
                    WHERE id = :id
                """), {"id": indexed_doc_id})
                collection_row = collection_result.fetchone()
                if collection_row:
                    collection_name = collection_row[0]
                    
                    # Prüfe ob Vektoren echte Embeddings sind
                    try:
                        from qdrant_client import QdrantClient
                        qdrant_client = QdrantClient(host="localhost", port=6333)
                        scroll_result = qdrant_client.scroll(
                            collection_name=collection_name,
                            limit=3,
                            with_vectors=True
                        )
                        points = scroll_result[0]
                        
                        if points:
                            sample_point = points[0]
                            if hasattr(sample_point, 'vector') and sample_point.vector:
                                vector = sample_point.vector
                                vector_values = vector[:100]
                                has_negative = any(v < 0 for v in vector_values)
                                variation = max(vector_values) - min(vector_values)
                                
                                # Echte Embeddings haben negative Werte und hohe Variation
                                if has_negative and variation > 0.3:
                                    should_skip = True
                                    print(f"   ✅ Überspringe (bereits {DEFAULT_EMBEDDING_MODEL} mit ECHTEN Embeddings)")
                                else:
                                    print(f"   ⚠️ Modell ist {DEFAULT_EMBEDDING_MODEL}, aber Vektoren sind MOCK - RE-INDEXIERE!")
                    except Exception as e:
                        print(f"   ⚠️ Konnte Embedding-Qualität nicht prüfen: {e}")
                        print(f"   → RE-INDEXIERE zur Sicherheit")
            
            if should_skip:
                print()
                continue
            
            try:
                start_time = time.time()
                
                # Re-Indexierung (IndexApprovedDocumentUseCase löscht automatisch alte Indexierung)
                result = use_case.execute(
                    upload_document_id=upload_doc_id,
                    document_type=doc_type
                )
                
                elapsed = time.time() - start_time
                
                if result.get("success"):
                    chunks = result.get("total_chunks", 0)
                    print(f"   ✅ Erfolgreich re-indexiert: {chunks} Chunks in {elapsed:.2f}s")
                    success_count += 1
                else:
                    error_msg = result.get("error", "Unbekannter Fehler")
                    print(f"   ❌ Fehler: {error_msg}")
                    error_count += 1
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                error_count += 1
                import traceback
                traceback.print_exc()
            
            print()
        
        # Zusammenfassung
        print("=" * 80)
        print("ZUSAMMENFASSUNG:")
        print("-" * 80)
        print(f"Erfolgreich: {success_count}")
        print(f"Fehler: {error_count}")
        print(f"Übersprungen (bereits {DEFAULT_EMBEDDING_MODEL}): {len(docs) - success_count - error_count}")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    reindex_all_documents()

