#!/usr/bin/env python3
"""
RAG Search Quality Measurement Script

Misst die tatsächliche Suche-Qualität über die echte API.
"""

import sys
import os
import json
import requests
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'contexts'))

from backend.app.database import SessionLocal
from backend.app.models import User
from contexts.ragintegration.infrastructure.models import IndexedDocumentModel
from backend.app.models import UploadDocument

def login_and_get_token(email: str = "qms.admin@company.com", password: str = "123") -> str:
    """Login und hole JWT Token."""
    response = requests.post(
        "http://localhost:8000/api/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

def measure_search_quality(
    question: str = "Was sind die wichtigsten Schritte bei der Montage?",
    session_id: int = 3,
    score_threshold: float = 0.01,
    top_k: int = 10
):
    """Messe Suche-Qualität über echte API."""
    
    print("=" * 80)
    print("RAG SEARCH QUALITY MEASUREMENT")
    print("=" * 80)
    print(f"\nQuery: {question}")
    print(f"Session ID: {session_id}")
    print(f"Score Threshold: {score_threshold}")
    print(f"Top-K: {top_k}")
    print("\n" + "=" * 80 + "\n")
    
    # 1. Login
    print("1. LOGIN")
    print("-" * 80)
    try:
        token = login_and_get_token()
        print(f"✅ Login erfolgreich")
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Hole System-Info (indexierte Dokumente)
    print("\n2. SYSTEM-INFO")
    print("-" * 80)
    try:
        response = requests.get("http://localhost:8000/api/rag/system/info", headers=headers)
        if response.status_code == 200:
            system_info = response.json()
            print(f"Indexierte Dokumente: {system_info.get('total_indexed_documents', 0)}")
            print(f"Gesamt Chunks: {system_info.get('total_chunks', 0)}")
        else:
            print(f"⚠️  System-Info nicht verfügbar: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Fehler bei System-Info: {e}")
    
    # 3. Führe echte Suche durch
    print("\n3. ECHTE SUCHE DURCHFÜHREN")
    print("-" * 80)
    
    request_data = {
        "question": question,
        "session_id": session_id,
        "model": "gpt-4o-mini",
        "use_hybrid_search": True,
        "use_multi_query": False,
        "score_threshold": score_threshold,
        "top_k": top_k,
        "filters": {}
    }
    
    print(f"Sende Request an /api/rag/chat/ask...")
    try:
        response = requests.post(
            "http://localhost:8000/api/rag/chat/ask",
            json=request_data,
            headers=headers,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API-Fehler: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return
        
        result = response.json()
        print(f"✅ Suche erfolgreich")
        
        # 4. Analysiere Ergebnisse
        print("\n4. ERGEBNISSE-ANALYSE")
        print("-" * 80)
        
        source_references = result.get("source_references", [])
        print(f"Anzahl Source References: {len(source_references)}")
        
        if not source_references:
            print("⚠️  Keine Source References gefunden!")
            return
        
        # Score-Verteilung
        print("\nScore-Verteilung:")
        scores = [ref.get("relevance_score", 0) for ref in source_references]
        if scores:
            print(f"  Min: {min(scores):.4f}")
            print(f"  Max: {max(scores):.4f}")
            print(f"  Avg: {sum(scores)/len(scores):.4f}")
            print(f"  Median: {sorted(scores)[len(scores)//2]:.4f}")
        
        # Dokumenttypen-Verteilung
        print("\nDokumenttypen-Verteilung:")
        doc_types = {}
        for ref in source_references:
            # Extrahiere Dokumenttyp aus Titel oder hole aus DB
            doc_title = ref.get("document_title", "")
            # Versuche Typ aus DB zu holen
            doc_id = ref.get("document_id")
            if doc_id:
                db = SessionLocal()
                try:
                    upload_doc = db.query(UploadDocument).filter(UploadDocument.id == doc_id).first()
                    if upload_doc and upload_doc.document_type:
                        doc_type = upload_doc.document_type.name
                        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                finally:
                    db.close()
        
        for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {doc_type}: {count}")
        
        # Erweiterte Metadaten
        print("\nErweiterte Metadaten:")
        has_extended_metadata = False
        for ref in source_references:
            if ref.get("vector_score") is not None or ref.get("text_score") is not None:
                has_extended_metadata = True
                break
        
        if has_extended_metadata:
            print("  ✅ Erweiterte Metadaten vorhanden")
            vector_scores = [ref.get("vector_score") for ref in source_references if ref.get("vector_score") is not None]
            text_scores = [ref.get("text_score") for ref in source_references if ref.get("text_score") is not None]
            hybrid_scores = [ref.get("hybrid_score") for ref in source_references if ref.get("hybrid_score") is not None]
            
            if vector_scores:
                print(f"  Vector-Score: Min={min(vector_scores):.4f}, Max={max(vector_scores):.4f}, Avg={sum(vector_scores)/len(vector_scores):.4f}")
            if text_scores:
                print(f"  Text-Score: Min={min(text_scores):.4f}, Max={max(text_scores):.4f}, Avg={sum(text_scores)/len(text_scores):.4f}")
            if hybrid_scores:
                print(f"  Hybrid-Score: Min={min(hybrid_scores):.4f}, Max={max(hybrid_scores):.4f}, Avg={sum(hybrid_scores)/len(hybrid_scores):.4f}")
        else:
            print("  ⚠️  Keine erweiterten Metadaten vorhanden")
        
        # Filter-Status
        print("\nFilter-Status:")
        rbac_passed = [ref.get("passed_rbac_filter") for ref in source_references if ref.get("passed_rbac_filter") is not None]
        threshold_passed = [ref.get("passed_score_threshold") for ref in source_references if ref.get("passed_score_threshold") is not None]
        
        if rbac_passed:
            rbac_true = sum(1 for x in rbac_passed if x is True)
            print(f"  RBAC-Filter: {rbac_true}/{len(rbac_passed)} bestanden")
        else:
            print(f"  RBAC-Filter: ⚠️  Keine Daten (None)")
        
        if threshold_passed:
            threshold_true = sum(1 for x in threshold_passed if x is True)
            print(f"  Score-Threshold: {threshold_true}/{len(threshold_passed)} bestanden")
        else:
            print(f"  Score-Threshold: ⚠️  Keine Daten (None)")
        
        # Top 10 Ergebnisse im Detail
        print("\n5. TOP 10 ERGEBNISSE (DETAIL)")
        print("-" * 80)
        for i, ref in enumerate(source_references[:10], 1):
            doc_id = ref.get("document_id")
            doc_title = ref.get("document_title", "Unbekannt")
            score = ref.get("relevance_score", 0)
            page = ref.get("page_number", 0)
            text_excerpt = ref.get("text_excerpt", "")[:100]
            
            # Hole Dokumenttyp
            doc_type = "Unbekannt"
            if doc_id:
                db = SessionLocal()
                try:
                    upload_doc = db.query(UploadDocument).filter(UploadDocument.id == doc_id).first()
                    if upload_doc and upload_doc.document_type:
                        doc_type = upload_doc.document_type.name
                finally:
                    db.close()
            
            print(f"\n{i}. Score: {score:.4f} | Typ: {doc_type} | Seite: {page}")
            print(f"   Dokument: {doc_title}")
            print(f"   Text: {text_excerpt}...")
            
            # Erweiterte Metadaten
            if ref.get("vector_score") is not None:
                print(f"   Vector: {ref.get('vector_score'):.4f}, Text: {ref.get('text_score', 0):.4f}, Hybrid: {ref.get('hybrid_score', score):.4f}")
            if ref.get("rank_position"):
                print(f"   Rang: {ref.get('rank_position')}/{ref.get('total_candidates', '?')}")
        
        # Relevanz-Analyse
        print("\n6. RELEVANZ-ANALYSE")
        print("-" * 80)
        query_keywords = set(question.lower().split())
        relevant_keywords = {'montage', 'schritte', 'wichtigsten', 'wichtigste', 'schritt'}
        
        print(f"Query Keywords: {query_keywords}")
        print(f"Relevante Keywords: {relevant_keywords}")
        
        relevant_results = []
        for ref in source_references:
            text_excerpt = ref.get("text_excerpt", "").lower()
            found_keywords = [kw for kw in relevant_keywords if kw in text_excerpt]
            if found_keywords:
                relevant_results.append({
                    "ref": ref,
                    "found_keywords": found_keywords,
                    "relevance": len(found_keywords) / len(relevant_keywords) if relevant_keywords else 0
                })
        
        print(f"\nErgebnisse mit relevanten Keywords: {len(relevant_results)}/{len(source_references)}")
        if relevant_results:
            print("\nRelevante Ergebnisse:")
            for i, rel_result in enumerate(relevant_results[:5], 1):
                ref = rel_result["ref"]
                found_kw = rel_result["found_keywords"]
                relevance = rel_result["relevance"]
                doc_title = ref.get("document_title", "Unbekannt")
                score = ref.get("relevance_score", 0)
                
                # Hole Dokumenttyp
                doc_type = "Unbekannt"
                doc_id = ref.get("document_id")
                if doc_id:
                    db = SessionLocal()
                    try:
                        upload_doc = db.query(UploadDocument).filter(UploadDocument.id == doc_id).first()
                        if upload_doc and upload_doc.document_type:
                            doc_type = upload_doc.document_type.name
                    finally:
                        db.close()
                
                print(f"  {i}. {doc_type} | {doc_title}")
                print(f"     Score: {score:.4f} | Relevanz: {relevance:.2%} | Keywords: {', '.join(found_kw)}")
        
        # 7. Zusammenfassung
        print("\n" + "=" * 80)
        print("7. ZUSAMMENFASSUNG")
        print("=" * 80)
        
        print(f"\nGesamt-Ergebnisse: {len(source_references)}")
        if scores:
            print(f"Durchschnittlicher Score: {sum(scores)/len(scores):.4f}")
        else:
            print(f"Durchschnittlicher Score: 0.0000")
        print(f"Relevante Ergebnisse (Keywords): {len(relevant_results)}/{len(source_references)} ({len(relevant_results)/len(source_references)*100 if source_references else 0:.1f}%)")
        
        # Erwartete vs. gefundene Dokumenttypen
        expected_doc_types = ['Arbeitsanweisung']  # Für Montage-Frage
        found_doc_types = set(doc_types.keys())
        missing_doc_types = set(expected_doc_types) - found_doc_types
        
        print(f"\nDokumenttypen in Top-K:")
        for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {doc_type}: {count}")
        
        if missing_doc_types:
            print(f"\n⚠️  Erwartete Dokumenttypen fehlen: {missing_doc_types}")
        else:
            print(f"\n✅ Alle erwarteten Dokumenttypen gefunden")
        
        # Probleme identifizieren
        print("\n🔍 IDENTIFIZIERTE PROBLEME:")
        problems = []
        
        if len(source_references) < top_k:
            problems.append(f"⚠️  Zu wenige Ergebnisse ({len(source_references)} < {top_k})")
        
        if len(relevant_results) < len(source_references) * 0.5:
            problems.append(f"⚠️  Weniger als 50% der Ergebnisse enthalten relevante Keywords ({len(relevant_results)}/{len(source_references)})")
        
        if missing_doc_types:
            problems.append(f"⚠️  Erwartete Dokumenttypen fehlen: {missing_doc_types}")
        
        if not has_extended_metadata:
            problems.append("⚠️  Keine erweiterten Metadaten (vector_score, text_score) vorhanden")
        
        if not rbac_passed or all(x is None for x in rbac_passed):
            problems.append("⚠️  RBAC-Filter-Status nicht gesetzt (alle None)")
        
        if not threshold_passed or all(x is None for x in threshold_passed):
            problems.append("⚠️  Score-Threshold-Status nicht gesetzt (alle None)")
        
        if not problems:
            print("✅ Keine offensichtlichen Probleme gefunden")
        else:
            for problem in problems:
                print(f"  {problem}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Was sind die wichtigsten Schritte bei der Montage?"
    session_id = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    score_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
    top_k = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    measure_search_quality(question, session_id, score_threshold, top_k)

