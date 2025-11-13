#!/usr/bin/env python3
"""
RAG Search Quality Analysis Script

Analysiert die aktuelle Suche-Qualität und identifiziert Probleme.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'contexts'))

from backend.app.database import SessionLocal
from contexts.ragintegration.infrastructure.adapters import RAGInfrastructureAdapter
from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
from backend.app.models import UploadDocument, DocumentTypeModel
from contexts.ragintegration.infrastructure.models import IndexedDocumentModel

def analyze_search_quality(
    question: str = "Was sind die wichtigsten Schritte bei der Montage?",
    session_id: int = 3,
    user_id: int = 1,
    score_threshold: float = 0.01,
    top_k: int = 10
):
    """Analysiere Suche-Qualität für eine gegebene Frage."""
    
    print("=" * 80)
    print("RAG SEARCH QUALITY ANALYSIS")
    print("=" * 80)
    print(f"\nQuery: {question}")
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print(f"Score Threshold: {score_threshold}")
    print(f"Top-K: {top_k}")
    print("\n" + "=" * 80 + "\n")
    
    db = SessionLocal()
    try:
        # 1. Hole alle indexierten Dokumente
        print("1. INDEXIERTE DOKUMENTE")
        print("-" * 80)
        indexed_docs = db.query(IndexedDocumentModel).all()
        print(f"Anzahl indexierter Dokumente: {len(indexed_docs)}")
        
        doc_type_counts = {}
        for doc_model in indexed_docs:
            upload_doc = db.query(UploadDocument).filter(UploadDocument.id == doc_model.upload_document_id).first()
            if upload_doc and upload_doc.document_type:
                doc_type = upload_doc.document_type.name
                doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
        
        print("\nDokumenttypen-Verteilung:")
        for doc_type, count in sorted(doc_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {doc_type}: {count}")
        
        # 2. Hole User-Level und Interest Groups
        print("\n2. USER-BERECHTIGUNGEN")
        print("-" * 80)
        permission_service = SQLAlchemyWorkflowPermissionService(db)
        user_level = permission_service.get_user_level(user_id)
        user_interest_groups = permission_service.get_user_interest_groups(user_id)
        print(f"User Level: {user_level}")
        print(f"Interest Groups: {user_interest_groups}")
        
        # 3. Initialisiere RAG Adapter
        print("\n3. RAG ADAPTER INITIALISIERUNG")
        print("-" * 80)
        import os
        openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_GPT5_MINI_API_KEY")
        rag_adapter = RAGInfrastructureAdapter(
            db_session=db,
            openai_api_key=openai_api_key,
            collection_name="rag_documents"
        )
        print("✅ RAG Adapter initialisiert")
        
        # 4. Führe direkte Suche durch
        print("\n4. DIREKTE VEKTOR-SUCHE ANALYSE")
        print("-" * 80)
        
        # Hole alle indexierten Dokumente
        indexed_docs = rag_adapter.indexed_document_repo.get_all()
        print(f"Gefunden {len(indexed_docs)} indexierte Dokumente")
        
        # Führe direkte Suche für jedes Dokument durch
        all_results = []
        print("\nGeneriere Query-Embedding...")
        query_embedding = rag_adapter.embedding_service.generate_embedding(question)
        print(f"✅ Embedding generiert ({len(query_embedding.vector)} Dimensionen)")
        
        for doc in indexed_docs:
            upload_doc = db.query(UploadDocument).filter(UploadDocument.id == doc.upload_document_id).first()
            doc_type_name = upload_doc.document_type.name if upload_doc and upload_doc.document_type else "Unbekannt"
            
            # Suche in Collection
            results = rag_adapter.vector_store.search_similar(
                collection_name=doc.collection_name,
                query_embedding=query_embedding,
                filters={},
                top_k=top_k * 2,  # Mehr Ergebnisse für Analyse
                min_score=0.0  # Kein Threshold für vollständige Analyse
            )
            
            # Erweitere Ergebnisse mit Metadaten
            for result in results:
                result['document_id'] = doc.upload_document_id
                result['document_type'] = doc_type_name
                result['document_title'] = upload_doc.filename if upload_doc else "Unbekannt"
                result['collection_name'] = doc.collection_name
            
            all_results.extend(results)
            print(f"  {doc_type_name} ({doc.collection_name}): {len(results)} Ergebnisse")
        
        print(f"\nGesamt: {len(all_results)} Ergebnisse gefunden")
        
        # 6. ANALYSE DER ERGEBNISSE
        print("\n6. ERGEBNISSE-ANALYSE")
        print("-" * 80)
        
        # Sortiere nach Score
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Score-Verteilung
        print("\nScore-Verteilung:")
        score_ranges = {
            "0.9-1.0": 0,
            "0.8-0.9": 0,
            "0.7-0.8": 0,
            "0.6-0.7": 0,
            "0.5-0.6": 0,
            "0.4-0.5": 0,
            "0.3-0.4": 0,
            "0.2-0.3": 0,
            "0.1-0.2": 0,
            "0.0-0.1": 0
        }
        
        for result in all_results:
            score = result.get('score', 0)
            if score >= 0.9:
                score_ranges["0.9-1.0"] += 1
            elif score >= 0.8:
                score_ranges["0.8-0.9"] += 1
            elif score >= 0.7:
                score_ranges["0.7-0.8"] += 1
            elif score >= 0.6:
                score_ranges["0.6-0.7"] += 1
            elif score >= 0.5:
                score_ranges["0.5-0.6"] += 1
            elif score >= 0.4:
                score_ranges["0.4-0.5"] += 1
            elif score >= 0.3:
                score_ranges["0.3-0.4"] += 1
            elif score >= 0.2:
                score_ranges["0.2-0.3"] += 1
            elif score >= 0.1:
                score_ranges["0.1-0.2"] += 1
            else:
                score_ranges["0.0-0.1"] += 1
        
        for range_name, count in score_ranges.items():
            if count > 0:
                print(f"  {range_name}: {count} Ergebnisse")
        
        # Top 20 Ergebnisse
        print("\nTop 20 Ergebnisse:")
        print("-" * 80)
        for i, result in enumerate(all_results[:20], 1):
            score = result.get('score', 0)
            doc_type = result.get('document_type', 'Unbekannt')
            doc_title = result.get('document_title', 'Unbekannt')
            chunk_id = result.get('chunk_id', 'N/A')
            metadata = result.get('metadata', {})
            chunk_text = metadata.get('chunk_text', '')[:100] if metadata else 'N/A'
            
            print(f"\n{i}. Score: {score:.4f} | Typ: {doc_type}")
            print(f"   Dokument: {doc_title}")
            print(f"   Chunk ID: {chunk_id}")
            print(f"   Text: {chunk_text}...")
        
        # Dokumenttypen-Verteilung in Top-K
        print("\n7. DOKUMENTTYPEN-VERTEILUNG (Top-K)")
        print("-" * 80)
        top_k_results = all_results[:top_k]
        doc_type_in_top_k = {}
        for result in top_k_results:
            doc_type = result.get('document_type', 'Unbekannt')
            doc_type_in_top_k[doc_type] = doc_type_in_top_k.get(doc_type, 0) + 1
        
        print(f"Top {top_k} Ergebnisse nach Dokumenttyp:")
        for doc_type, count in sorted(doc_type_in_top_k.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {doc_type}: {count}")
        
        # 8. THRESHOLD-ANALYSE
        print("\n8. THRESHOLD-ANALYSE")
        print("-" * 80)
        print(f"Aktueller Threshold: {score_threshold}")
        
        results_above_threshold = [r for r in all_results if r.get('score', 0) >= score_threshold]
        results_below_threshold = [r for r in all_results if r.get('score', 0) < score_threshold]
        
        print(f"Ergebnisse >= Threshold: {len(results_above_threshold)}")
        print(f"Ergebnisse < Threshold: {len(results_below_threshold)}")
        
        if results_above_threshold:
            avg_score_above = sum(r.get('score', 0) for r in results_above_threshold) / len(results_above_threshold)
            print(f"Durchschnittlicher Score (>= Threshold): {avg_score_above:.4f}")
        
        # 9. RELEVANZ-ANALYSE (basierend auf Keywords)
        print("\n9. RELEVANZ-ANALYSE")
        print("-" * 80)
        query_keywords = set(question.lower().split())
        relevant_keywords = {'montage', 'schritte', 'wichtigsten', 'wichtigste'}
        
        print(f"Query Keywords: {query_keywords}")
        print(f"Relevante Keywords: {relevant_keywords}")
        
        # Prüfe Top-K Ergebnisse auf Relevanz
        relevant_results = []
        for result in top_k_results:
            metadata = result.get('metadata', {})
            chunk_text = metadata.get('chunk_text', '').lower() if metadata else ''
            
            # Zähle relevante Keywords im Chunk
            found_keywords = [kw for kw in relevant_keywords if kw in chunk_text]
            result['found_keywords'] = found_keywords
            result['relevance_score'] = len(found_keywords) / len(relevant_keywords) if relevant_keywords else 0
            
            if found_keywords:
                relevant_results.append(result)
        
        print(f"\nTop {top_k} Ergebnisse mit relevanten Keywords:")
        for i, result in enumerate(relevant_results[:10], 1):
            found_kw = result.get('found_keywords', [])
            rel_score = result.get('relevance_score', 0)
            doc_type = result.get('document_type', 'Unbekannt')
            doc_title = result.get('document_title', 'Unbekannt')
            vector_score = result.get('score', 0)
            
            print(f"{i}. {doc_type} | {doc_title}")
            print(f"   Vector-Score: {vector_score:.4f} | Relevanz: {rel_score:.2%} | Keywords: {', '.join(found_kw)}")
        
        # 10. ZUSAMMENFASSUNG
        print("\n" + "=" * 80)
        print("10. ZUSAMMENFASSUNG")
        print("=" * 80)
        
        print(f"\nGesamt-Ergebnisse: {len(all_results)}")
        print(f"Ergebnisse >= Threshold ({score_threshold}): {len(results_above_threshold)}")
        print(f"Top-K Ergebnisse: {len(top_k_results)}")
        print(f"Relevante Ergebnisse (Keywords): {len(relevant_results)}")
        
        # Probleme identifizieren
        print("\n🔍 IDENTIFIZIERTE PROBLEME:")
        problems = []
        
        if len(results_above_threshold) < top_k:
            problems.append(f"⚠️  Zu wenige Ergebnisse >= Threshold ({len(results_above_threshold)} < {top_k})")
        
        if len(relevant_results) < len(top_k_results) * 0.5:
            problems.append(f"⚠️  Weniger als 50% der Top-K Ergebnisse enthalten relevante Keywords")
        
        # Prüfe ob relevante Dokumenttypen fehlen
        expected_doc_types = ['Arbeitsanweisung']  # Für Montage-Frage
        found_doc_types = set(doc_type_in_top_k.keys())
        missing_doc_types = set(expected_doc_types) - found_doc_types
        if missing_doc_types:
            problems.append(f"⚠️  Erwartete Dokumenttypen fehlen in Top-K: {missing_doc_types}")
        
        if not problems:
            print("✅ Keine offensichtlichen Probleme gefunden")
        else:
            for problem in problems:
                print(f"  {problem}")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    # Standard-Parameter
    question = sys.argv[1] if len(sys.argv) > 1 else "Was sind die wichtigsten Schritte bei der Montage?"
    session_id = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    user_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    score_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
    top_k = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    
    analyze_search_quality(question, session_id, user_id, score_threshold, top_k)

