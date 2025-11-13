"""
Detaillierte Analyse: Warum werden Arbeitsanweisungen nicht gefunden?

Prüft:
1. Sind Arbeitsanweisungen in Qdrant?
2. Welche Scores haben sie bei "Montage"-Query?
3. Vergleich mit gefundenen Fachartikeln
4. ML-Modell Einfluss
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from backend.app.database import get_db
from sqlalchemy import text
from contexts.ragintegration.infrastructure.embedding_factory import create_embedding_service
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter
from dataclasses import dataclass
from typing import List

@dataclass
class EmbeddingVector:
    """Embedding Vector Value Object."""
    vector: List[float]
    model: str
    dimensions: int

def analyze_montage_search():
    """Analysiere die Suche nach 'Montage' in Arbeitsanweisungen."""
    
    print("=" * 80)
    print("DETAILLIERTE ANALYSE: Montage-Suche in Arbeitsanweisungen")
    print("=" * 80)
    
    # 1. Hole alle indexierten Arbeitsanweisungen
    db = next(get_db())
    result = db.execute(text('''
        SELECT 
            ud.id as upload_id,
            ud.original_filename,
            rid.id as indexed_id,
            rid.qdrant_collection_name,
            rid.total_chunks
        FROM upload_documents ud
        JOIN document_types dt ON ud.document_type_id = dt.id
        JOIN rag_indexed_documents rid ON rid.upload_document_id = ud.id
        WHERE dt.name = 'Arbeitsanweisung'
        ORDER BY ud.id
    '''))
    
    arbeitsanweisungen = list(result)
    print(f"\n1. INDEXIERTE ARBEITSANWEISUNGEN: {len(arbeitsanweisungen)}")
    print("-" * 80)
    for row in arbeitsanweisungen:
        print(f"  ID: {row[0]}, Datei: {row[1]}, Collection: {row[3]}, Chunks: {row[4]}")
    
    if not arbeitsanweisungen:
        print("  ❌ KEINE ARBEITSANWEISUNGEN INDEXIERT!")
        return
    
    # 2. Initialisiere Vector Store und Embedding Service
    # WICHTIG: Verwende OpenAI Embeddings, da alle Dokumente mit OpenAI indexiert wurden (1536 dim)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("\n❌ OPENAI_API_KEY nicht gefunden!")
        print("   Versuche Google Gemini als Fallback...")
        embedding_service = create_embedding_service()
    else:
        # Erzwinge OpenAI Embeddings
        from contexts.ragintegration.infrastructure.embedding_adapter import OpenAIEmbeddingAdapter
        embedding_service = OpenAIEmbeddingAdapter(api_key=openai_api_key)
    vector_store = QdrantVectorStoreAdapter(collection_name="documind_rag")  # Wird pro Collection überschrieben
    
    # 3. Erstelle Query-Embedding
    query = "Was sind die wichtigsten Schritte bei der Montage?"
    embedding_list = embedding_service.generate_embedding(query)
    model_name = embedding_service.get_model_name() if hasattr(embedding_service, 'get_model_name') else 'unknown'
    dimensions = embedding_service.get_dimensions() if hasattr(embedding_service, 'get_dimensions') else len(embedding_list)
    query_embedding = EmbeddingVector(vector=embedding_list, model=model_name, dimensions=dimensions)
    
    print(f"\n2. QUERY: '{query}'")
    print(f"   Embedding-Dimension: {dimensions}, Modell: {model_name}")
    
    # 4. Suche in jeder Collection der Arbeitsanweisungen
    print("\n3. SUCHE IN ARBEITSANWEISUNGEN:")
    print("-" * 80)
    
    all_aa_results = []
    for aa in arbeitsanweisungen:
        collection_name = aa[3]
        if not collection_name:
            print(f"  ⚠️  ID {aa[0]}: Keine Collection!")
            continue
        
        print(f"\n  Collection: {collection_name} (Dokument ID: {aa[0]})")
        
        try:
            # Direkte Vektor-Suche
            results = vector_store.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                filters={},
                top_k=10,
                min_score=0.0  # Kein Threshold für Analyse
            )
            
            print(f"    Gefundene Chunks: {len(results)}")
            
            for i, result in enumerate(results[:5], 1):
                chunk_id = result.get('chunk_id', 'unknown')
                score = result.get('score', 0.0)
                metadata = result.get('metadata', {})
                doc_type = metadata.get('document_type', 'unknown')
                doc_title = metadata.get('document_title', 'unknown')
                chunk_text = metadata.get('chunk_text', '')[:100]
                
                all_aa_results.append({
                    'collection': collection_name,
                    'upload_id': aa[0],
                    'chunk_id': chunk_id,
                    'score': score,
                    'document_type': doc_type,
                    'document_title': doc_title,
                    'chunk_text': chunk_text
                })
                
                print(f"    {i}. Score: {score:.4f}, Typ: {doc_type}, Chunk: {chunk_id}")
                print(f"       Text: {chunk_text}...")
        
        except Exception as e:
            print(f"    ❌ Fehler: {e}")
    
    # 5. Suche in Fachartikeln zum Vergleich
    print("\n4. SUCHE IN FACHARTIKELN (ZUM VERGLEICH):")
    print("-" * 80)
    
    result = db.execute(text('''
        SELECT DISTINCT rid.qdrant_collection_name
        FROM upload_documents ud
        JOIN document_types dt ON ud.document_type_id = dt.id
        JOIN rag_indexed_documents rid ON rid.upload_document_id = ud.id
        WHERE dt.name = 'Fachartikel'
        LIMIT 3
    '''))
    
    fachartikel_collections = [row[0] for row in result if row[0]]
    
    all_fa_results = []
    for collection_name in fachartikel_collections[:3]:
        print(f"\n  Collection: {collection_name}")
        
        try:
            results = vector_store.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                filters={},
                top_k=5,
                min_score=0.0
            )
            
            print(f"    Gefundene Chunks: {len(results)}")
            
            for i, result in enumerate(results[:3], 1):
                chunk_id = result.get('chunk_id', 'unknown')
                score = result.get('score', 0.0)
                metadata = result.get('metadata', {})
                doc_type = metadata.get('document_type', 'unknown')
                chunk_text = metadata.get('chunk_text', '')[:100]
                
                all_fa_results.append({
                    'collection': collection_name,
                    'chunk_id': chunk_id,
                    'score': score,
                    'document_type': doc_type,
                    'chunk_text': chunk_text
                })
                
                print(f"    {i}. Score: {score:.4f}, Typ: {doc_type}")
                print(f"       Text: {chunk_text}...")
        
        except Exception as e:
            print(f"    ❌ Fehler: {e}")
    
    # 6. Score-Vergleich
    print("\n5. SCORE-VERGLEICH:")
    print("-" * 80)
    
    if all_aa_results:
        aa_scores = [r['score'] for r in all_aa_results]
        print(f"  Arbeitsanweisungen:")
        print(f"    Anzahl: {len(aa_scores)}")
        print(f"    Min: {min(aa_scores):.4f}")
        print(f"    Max: {max(aa_scores):.4f}")
        print(f"    Durchschnitt: {sum(aa_scores)/len(aa_scores):.4f}")
        print(f"    Über Threshold (0.010): {sum(1 for s in aa_scores if s >= 0.010)}")
    
    if all_fa_results:
        fa_scores = [r['score'] for r in all_fa_results]
        print(f"\n  Fachartikel:")
        print(f"    Anzahl: {len(fa_scores)}")
        print(f"    Min: {min(fa_scores):.4f}")
        print(f"    Max: {max(fa_scores):.4f}")
        print(f"    Durchschnitt: {sum(fa_scores)/len(fa_scores):.4f}")
        print(f"    Über Threshold (0.010): {sum(1 for s in fa_scores if s >= 0.010)}")
    
    # 7. Keyword-Analyse
    print("\n6. KEYWORD-ANALYSE (BM25):")
    print("-" * 80)
    
    query_words = ["Montage", "Schritte", "wichtigsten"]
    
    print(f"  Query-Wörter: {query_words}")
    
    if all_aa_results:
        print(f"\n  Arbeitsanweisungen (Top 3):")
        for i, result in enumerate(all_aa_results[:3], 1):
            chunk_text = result.get('chunk_text', '').lower()
            matches = sum(1 for word in query_words if word.lower() in chunk_text)
            print(f"    {i}. Chunk {result['chunk_id']}: {matches}/{len(query_words)} Matches")
    
    if all_fa_results:
        print(f"\n  Fachartikel (Top 3):")
        for i, result in enumerate(all_fa_results[:3], 1):
            chunk_text = result.get('chunk_text', '').lower()
            matches = sum(1 for word in query_words if word.lower() in chunk_text)
            print(f"    {i}. Chunk {result['chunk_id']}: {matches}/{len(query_words)} Matches")
    
    # 8. Zusammenfassung
    print("\n7. ZUSAMMENFASSUNG:")
    print("-" * 80)
    
    if all_aa_results:
        best_aa_score = max(r['score'] for r in all_aa_results)
        print(f"  ✅ Beste Arbeitsanweisung Score: {best_aa_score:.4f}")
    else:
        print(f"  ❌ Keine Arbeitsanweisungen gefunden!")
    
    if all_fa_results:
        best_fa_score = max(r['score'] for r in all_fa_results)
        print(f"  ✅ Bester Fachartikel Score: {best_fa_score:.4f}")
    
    if all_aa_results and all_fa_results:
        if best_aa_score < best_fa_score:
            print(f"  ⚠️  Problem: Fachartikel haben höhere Scores!")
            print(f"     Differenz: {best_fa_score - best_aa_score:.4f}")
        else:
            print(f"  ✅ Arbeitsanweisungen haben höhere Scores!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_montage_search()

