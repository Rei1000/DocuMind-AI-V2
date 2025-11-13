"""
Celery Tasks für RAG Background Jobs.

Infrastructure Layer: Asynchrone SHAP-Berechnungen.

TDD Phase 2: GREEN - Minimale Task-Implementierung.
"""

from typing import Dict, Any
from datetime import datetime
from .celery_app import celery_app


@celery_app.task(
    name='ragintegration.compute_shap_explanation',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=100,
    time_limit=120
)
def compute_shap_explanation(
    self,
    query: str,
    chunk: Dict[str, Any],
    vector_score: float,
    text_score: float,
    hybrid_score: float,
    document_type: str,
    user_level: int,
    keyword_matches: int,
    chunk_length: int,
    heading_hierarchy_depth: int,
    confidence_score: float
) -> Dict[str, Any]:
    """
    Compute SHAP Explanation asynchron im Background.
    
    Args:
        self: Task-Context (bind=True)
        query: Query-String
        chunk: Chunk-Dict (JSON-serialisiert)
        vector_score: Vektor-Score (0-1)
        text_score: Text-Score (0-1)
        hybrid_score: Hybrid-Score (0-1)
        document_type: Dokumenttyp
        user_level: User-Level (1-5)
        keyword_matches: Anzahl Keyword-Matches
        chunk_length: Chunk-Länge
        heading_hierarchy_depth: Heading-Hierarchie-Tiefe
        confidence_score: Confidence-Score (0-1)
        
    Returns:
        Dict mit SHAP-Explanation (JSON-serialisierbar)
    """
    try:
        # Update State zu STARTED (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='STARTED',
                meta={'current': 0, 'total': 100, 'status': 'Initialisiere SHAP-Berechnung...'}
            )
        
        # Importiere SHAP Service
        from contexts.ragintegration.infrastructure.shap_real_attribution import (
            SHAPExplainerService,
            FeatureExtractor,
            RankingModelWrapper
        )
        from contexts.ragintegration.infrastructure.shap_background_data_service import (
            SHAPBackgroundDataService
        )
        
        # Update State (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Erstelle SHAP-Service...'}
            )
        
        # Erstelle SHAP-Service
        feature_extractor = FeatureExtractor()
        ranking_model = RankingModelWrapper()
        background_data_service = SHAPBackgroundDataService(
            max_records=1000,
            feature_extractor=feature_extractor
        )
        background_data = background_data_service.get_background_data(n_samples=50)
        
        shap_service = SHAPExplainerService(
            model=ranking_model,
            feature_extractor=feature_extractor,
            background_data=background_data,
            n_background_samples=50,
            enable_cache=False  # Disable Cache für Background Jobs (jede Berechnung ist neu)
        )
        
        # Update State (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 40, 'total': 100, 'status': 'Berechne SHAP-Werte...'}
            )
        
        # Berechne SHAP-Erklärung
        explanation = shap_service.explain_search_result(
            query=query,
            chunk=chunk,
            vector_score=vector_score,
            text_score=text_score,
            hybrid_score=hybrid_score,
            document_type=document_type,
            user_level=user_level,
            keyword_matches=keyword_matches,
            chunk_length=chunk_length,
            heading_hierarchy_depth=heading_hierarchy_depth,
            confidence_score=confidence_score
        )
        
        # Update State (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Serialisiere Ergebnis...'}
            )
        
        # Konvertiere zu JSON-serialisierbarem Dict
        result = {
            'feature_importance': explanation.feature_importance,
            'base_value': explanation.base_value,
            'shap_values': explanation.shap_values,  # Sollte bereits Liste sein
            'expected_value': explanation.expected_value,
            'prediction': explanation.prediction,
            'query': explanation.query,
            'chunk_id': explanation.chunk_id,
            'timestamp': explanation.timestamp.isoformat(),  # datetime → ISO-String
            'features': explanation.features
        }
        
        # Update State zu SUCCESS (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='SUCCESS',
                meta={'current': 100, 'total': 100, 'status': 'Fertig!'}
            )
        
        return result
        
    except Exception as e:
        # Error Handling
        import traceback
        error_trace = traceback.format_exc()
        
        # Update State zu FAILURE (nur wenn task_id vorhanden)
        if self.request.id:
            self.update_state(
                state='FAILURE',
                meta={
                    'error': str(e),
                    'traceback': error_trace,
                    'status': f'Fehler: {str(e)}'
                }
            )
        
        # Retry bei temporären Fehlern
        if self.request.retries < self.max_retries:
            # Exponential Backoff
            countdown = 2 ** self.request.retries * 60  # 60s, 120s, 240s
            raise self.retry(exc=e, countdown=countdown)
        
        # Nach max_retries: Gebe Fehler-Dict zurück
        return {
            'error': str(e),
            'traceback': error_trace,
            'status': 'failed',
            'timestamp': datetime.now().isoformat()
        }

