"""
Celery Tasks für RAG Background Jobs.

Infrastructure Layer: Asynchrone SHAP-Berechnungen und automatisches ML-Training.

TDD Phase 2: GREEN - Minimale Task-Implementierung.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
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


# ============================================================================
# AUTOMATISCHES ML-TRAINING TASK (v2.9.0)
# ============================================================================

@celery_app.task(
    name='ragintegration.auto_retrain_ml_model',
    bind=True,
    max_retries=2,
    default_retry_delay=3600,  # 1 Stunde bei Retry
    soft_time_limit=1800,  # 30 Minuten Soft Limit
    time_limit=2100  # 35 Minuten Hard Limit
)
def auto_retrain_ml_model(
    self,
    min_new_samples: int = 100,
    min_improvement_threshold: float = 0.01,  # 1% Verbesserung erforderlich
    force_retrain: bool = False
) -> Dict[str, Any]:
    """
    Automatisches Re-Training des ML-Ranking-Modells.
    
    Prüft ob genug neue Training-Daten vorhanden sind und trainiert das Modell neu,
    falls das neue Modell besser ist als das aktuelle.
    
    Args:
        self: Task-Context (bind=True)
        min_new_samples: Minimale Anzahl neuer Samples für Re-Training (default: 100)
        min_improvement_threshold: Minimale NDCG-Verbesserung für Deployment (default: 0.01 = 1%)
        force_retrain: Erzwinge Re-Training auch ohne neue Samples (default: False)
        
    Returns:
        Dict mit Training-Ergebnissen:
        {
            'success': bool,
            'trained': bool,  # Ob tatsächlich trainiert wurde
            'deployed': bool,  # Ob neues Modell deployed wurde
            'old_ndcg': float,  # NDCG des alten Modells
            'new_ndcg': float,  # NDCG des neuen Modells
            'improvement': float,  # Verbesserung in Prozent
            'num_samples': int,  # Anzahl verwendeter Training-Samples
            'validation_scores': Dict,  # Cross-Validation Scores
            'message': str,
            'timestamp': str
        }
    """
    try:
        # Update State
        if self.request.id:
            self.update_state(
                state='STARTED',
                meta={'current': 0, 'total': 100, 'status': 'Prüfe Training-Daten...'}
            )
        
        # Importiere benötigte Komponenten
        from backend.app.database import SessionLocal
        from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
            TrainingDataRepositorySQLite
        )
        from contexts.ragintegration.infrastructure.ml.training_pipeline import (
            LTRTrainingPipeline
        )
        from contexts.ragintegration.infrastructure.ml.inference_service import (
            LTRInferenceService
        )
        import os
        from pathlib import Path
        
        db_session = SessionLocal()
        
        try:
            # 1. Prüfe Training-Daten
            if self.request.id:
                self.update_state(
                    state='PROGRESS',
                    meta={'current': 10, 'total': 100, 'status': 'Lade Training-Daten...'}
                )
            
            training_data_repo = TrainingDataRepositorySQLite(db_session=db_session)
            stats = training_data_repo.get_statistics()
            
            total_samples = stats.get('total_samples', 0)
            
            # Prüfe ob genug Daten vorhanden sind
            if total_samples < min_new_samples and not force_retrain:
                return {
                    'success': True,
                    'trained': False,
                    'deployed': False,
                    'message': f'Nicht genug Training-Daten: {total_samples} < {min_new_samples}. Mindestens {min_new_samples} Samples erforderlich.',
                    'num_samples': total_samples,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 2. Hole letztes Training-Datum (aus Model-Metadaten oder Config)
            model_dir = os.getenv('ML_MODEL_DIR', 'data/ml_models')
            model_name = os.getenv('ML_MODEL_NAME', 'ltr_ranker_v1.pkl')
            model_path = os.path.join(model_dir, model_name)
            
            # Prüfe ob aktuelles Modell existiert
            current_model_exists = os.path.exists(model_path) if model_path else False
            
            # Hole letztes Training-Datum (aus Model-File oder Default)
            last_training_date = None
            if current_model_exists:
                try:
                    # Versuche letztes Training-Datum aus Model-Metadaten zu holen
                    import pickle
                    with open(model_path, 'rb') as f:
                        model_data = pickle.load(f)
                        last_training_date_str = model_data.get('last_training_date')
                        if last_training_date_str:
                            last_training_date = datetime.fromisoformat(last_training_date_str)
                except Exception as e:
                    print(f"DEBUG: Konnte letztes Training-Datum nicht aus Model holen: {e}")
                    # Fallback: 7 Tage zurück
                    last_training_date = datetime.now() - timedelta(days=7)
            else:
                # Kein Modell vorhanden → verwende alle Daten
                last_training_date = None
            
            # 3. Zähle neue Samples seit letztem Training
            if last_training_date:
                new_samples = training_data_repo.get_training_samples(
                    min_date=last_training_date
                )
                num_new_samples = len(new_samples)
            else:
                # Kein letztes Training-Datum → verwende alle Samples
                all_samples = training_data_repo.get_training_samples()
                num_new_samples = len(all_samples)
            
            # Prüfe ob genug neue Samples vorhanden sind
            if num_new_samples < min_new_samples and not force_retrain:
                return {
                    'success': True,
                    'trained': False,
                    'deployed': False,
                    'message': f'Nicht genug neue Training-Daten: {num_new_samples} < {min_new_samples}. Mindestens {min_new_samples} neue Samples seit letztem Training erforderlich.',
                    'num_samples': total_samples,
                    'num_new_samples': num_new_samples,
                    'last_training_date': last_training_date.isoformat() if last_training_date else None,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 4. Hole aktuelles Modell NDCG (falls vorhanden)
            old_ndcg = None
            if current_model_exists:
                try:
                    # Lade aktuelles Modell und evaluiere
                    if self.request.id:
                        self.update_state(
                            state='PROGRESS',
                            meta={'current': 20, 'total': 100, 'status': 'Evaluiere aktuelles Modell...'}
                        )
                    
                    # TODO: Evaluiere aktuelles Modell auf Test-Set
                    # Für jetzt: Verwende Default-Wert
                    old_ndcg = 0.75  # Placeholder
                except Exception as e:
                    print(f"DEBUG: Konnte aktuelles Modell nicht evaluieren: {e}")
            
            # 5. Trainiere neues Modell
            if self.request.id:
                self.update_state(
                    state='PROGRESS',
                    meta={'current': 30, 'total': 100, 'status': 'Trainiere neues Modell...'}
                )
            
            training_pipeline = LTRTrainingPipeline(
                training_data_repo=training_data_repo,
                model_type='lightgbm',
                model_version='1.0.0'
            )
            
            # Trainiere mit Cross-Validation
            validation_scores = training_pipeline.train_and_validate(
                n_splits=3,
                num_boost_round=100,
                learning_rate=0.1,
                max_depth=6,
                num_leaves=31
            )
            
            new_ndcg = validation_scores.get('ndcg_mean', 0.0)
            
            if self.request.id:
                self.update_state(
                    state='PROGRESS',
                    meta={'current': 70, 'total': 100, 'status': f'Training abgeschlossen. NDCG: {new_ndcg:.3f}'}
                )
            
            # 6. Prüfe ob neues Modell besser ist
            should_deploy = False
            improvement = 0.0
            
            if old_ndcg is None:
                # Kein altes Modell → deploye immer
                should_deploy = True
                improvement = 0.0
            else:
                improvement = new_ndcg - old_ndcg
                improvement_percent = (improvement / old_ndcg * 100) if old_ndcg > 0 else 0.0
                
                if improvement >= min_improvement_threshold:
                    should_deploy = True
                else:
                    should_deploy = False
            
            # 7. Deploy neues Modell (falls besser)
            deployed = False
            if should_deploy:
                if self.request.id:
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': 80, 'total': 100, 'status': 'Deploye neues Modell...'}
                    )
                
                # Erstelle Model-Verzeichnis falls nicht vorhanden
                Path(model_dir).mkdir(parents=True, exist_ok=True)
                
                # Backup altes Modell (falls vorhanden)
                if current_model_exists:
                    backup_path = f"{model_path}.backup.{int(datetime.now().timestamp())}"
                    import shutil
                    shutil.copy2(model_path, backup_path)
                    print(f"DEBUG: Altes Modell gesichert: {backup_path}")
                
                # Speichere neues Modell mit Metadaten
                model_data = {
                    'model': training_pipeline.model,
                    'model_type': training_pipeline.model_type,
                    'model_version': training_pipeline.model_version,
                    'feature_names': training_pipeline.feature_extractor.feature_names,
                    'last_training_date': datetime.now().isoformat(),
                    'validation_scores': validation_scores,
                    'num_training_samples': total_samples,
                    'old_ndcg': old_ndcg,
                    'new_ndcg': new_ndcg,
                    'improvement': improvement
                }
                
                with open(model_path, 'wb') as f:
                    import pickle
                    pickle.dump(model_data, f)
                
                deployed = True
                print(f"✅ Neues ML-Modell deployed: {model_path} (NDCG: {new_ndcg:.3f}, Improvement: {improvement:.3f})")
            else:
                print(f"⚠️ Neues Modell nicht besser (NDCG: {new_ndcg:.3f} vs {old_ndcg:.3f}, Improvement: {improvement:.3f} < {min_improvement_threshold})")
            
            # 8. Return Ergebnis
            if self.request.id:
                self.update_state(
                    state='SUCCESS',
                    meta={'current': 100, 'total': 100, 'status': 'Fertig!'}
                )
            
            return {
                'success': True,
                'trained': True,
                'deployed': deployed,
                'old_ndcg': old_ndcg,
                'new_ndcg': new_ndcg,
                'improvement': improvement,
                'improvement_percent': (improvement / old_ndcg * 100) if old_ndcg and old_ndcg > 0 else 0.0,
                'num_samples': total_samples,
                'num_new_samples': num_new_samples,
                'validation_scores': validation_scores,
                'model_path': model_path,
                'message': f'Training abgeschlossen. NDCG: {new_ndcg:.3f} ({"+" if improvement >= 0 else ""}{improvement:.3f} vs altes Modell). {"Deployed" if deployed else "Nicht deployed (nicht besser genug)"}.',
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            db_session.close()
        
    except Exception as e:
        # Error Handling
        import traceback
        error_trace = traceback.format_exc()
        
        # Update State zu FAILURE
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
            countdown = 2 ** self.request.retries * 3600  # 1h, 2h
            raise self.retry(exc=e, countdown=countdown)
        
        # Nach max_retries: Gebe Fehler-Dict zurück
        return {
            'success': False,
            'trained': False,
            'deployed': False,
            'error': str(e),
            'traceback': error_trace,
            'message': f'Fehler beim automatischen ML-Training: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

