"""
Training Data Repository SQLite Implementation.

Infrastructure Layer: SQLite-basierte Persistenz für Training-Daten.
Ersetzt FileBasedTrainingDataRepository für bessere Persistenz.

Features:
- SQLite-Persistenz (training_samples Tabelle)
- JSON-Serialisierung für Features
- Datum-Filter
- Statistiken
- Kompatibel mit FileBasedTrainingDataRepository Interface

Version: 2.7.0
Stand: 2025-11-14
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json

from backend.app.models import TrainingSampleModel


class TrainingDataRepositorySQLite:
    """
    SQLite-basiertes Repository für Training-Daten.
    
    Speichert Training-Samples in SQLite-DB (training_samples Tabelle).
    Kompatibel mit FileBasedTrainingDataRepository Interface.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialisiere Repository.
        
        Args:
            db_session: SQLAlchemy Session
        """
        self.db = db_session
    
    def save_training_sample(self, sample: Dict[str, Any]) -> bool:
        """
        Speichere Training-Sample in SQLite.
        
        Args:
            sample: Training-Sample Dict mit:
                - query: str
                - chunk_id: str
                - features: dict (wird als JSON gespeichert)
                - relevance_score: float
                - source: str ('feedback', 'system', 'auto')
                - user_id: Optional[int]
                - feedback_id: Optional[int]
                - timestamp: Optional[str] (ISO-8601, wird auto-generiert wenn nicht vorhanden)
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # Extrahiere Felder
            query = sample.get('query')
            chunk_id = sample.get('chunk_id')
            features = sample.get('features', {})
            relevance_score = sample.get('relevance_score', 0.5)
            source = sample.get('source', 'system')
            user_id = sample.get('user_id')
            feedback_id = sample.get('feedback_id')
            
            # Timestamp
            if 'timestamp' in sample:
                if isinstance(sample['timestamp'], datetime):
                    created_at = sample['timestamp'].isoformat()
                else:
                    created_at = sample['timestamp']
            else:
                created_at = datetime.now().isoformat()
            
            # Erstelle Model
            model = TrainingSampleModel(
                query=query,
                chunk_id=chunk_id,
                features_json=json.dumps(features),
                relevance_score=float(relevance_score),
                source=source,
                user_id=user_id,
                feedback_id=feedback_id,
                created_at=created_at
            )
            
            # Speichere
            self.db.add(model)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern von Training-Sample: {e}")
            self.db.rollback()
            return False
    
    def get_training_samples(
        self,
        min_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lade Training-Samples aus SQLite.
        
        Args:
            min_date: Optional - Nur Samples nach diesem Datum
            limit: Optional - Maximale Anzahl Samples
            
        Returns:
            Liste von Training-Samples (Dict Format)
        """
        try:
            # Base Query
            query = self.db.query(TrainingSampleModel)
            
            # Datum-Filter
            if min_date:
                min_date_str = min_date.isoformat()
                query = query.filter(TrainingSampleModel.created_at >= min_date_str)
            
            # Sortierung (älteste zuerst, wie FileBasedRepository)
            query = query.order_by(TrainingSampleModel.created_at.asc())
            
            # Limit
            if limit:
                query = query.limit(limit)
            
            # Execute
            models = query.all()
            
            # Konvertiere zu Dict Format
            samples = []
            for model in models:
                features = json.loads(model.features_json)
                
                # Erstelle Sample im Format für LTRTrainingPipeline
                sample = {
                    'query': model.query,
                    'chunk_id': model.chunk_id,
                    'features': features,  # Behalte für Kompatibilität
                    'relevance_score': model.relevance_score,
                    'source': model.source,
                    'timestamp': model.created_at,
                    # Flache Felder für LTRTrainingPipeline (aus features Dict)
                    'vector_score': features.get('vector_score', 0.0),
                    'text_score': features.get('text_score', 0.0),
                    'bm25_score': features.get('bm25_score', 0.0),
                    'jaccard_score': features.get('jaccard_score', 0.0),
                    'keyword_matches': features.get('keyword_matches', 0),
                    'user_level': features.get('user_level', 1),
                    'hybrid_score': features.get('hybrid_score', 0.0),
                    # Chunk-Dict für LTRTrainingPipeline (minimal, da chunk_id vorhanden)
                    'chunk': {
                        'chunk_id': model.chunk_id,
                        'metadata': {
                            'chunk_text': '',  # Wird nicht benötigt für Feature-Extraktion
                            'document_type': features.get('document_type_encoded', 0.0),
                            'chunk_length': features.get('chunk_length', 0),
                            'heading_hierarchy_depth': features.get('heading_hierarchy_depth', 0),
                            'confidence_score': features.get('confidence_score', 0.5)
                        }
                    }
                }
                
                # Optionale Felder
                if model.user_id is not None:
                    sample['user_id'] = model.user_id
                if model.feedback_id is not None:
                    sample['feedback_id'] = model.feedback_id
                
                samples.append(sample)
            
            return samples
            
        except Exception as e:
            print(f"Fehler beim Laden von Training-Samples: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Hole Statistiken über Training-Daten.
        
        Returns:
            Dict mit:
                - total_samples: int
                - oldest_sample: Optional[str] (ISO-8601)
                - newest_sample: Optional[str] (ISO-8601)
                - unique_queries: int
        """
        try:
            # Total Count
            total_count = self.db.query(TrainingSampleModel).count()
            
            if total_count == 0:
                return {
                    'total_samples': 0,
                    'oldest_sample': None,
                    'newest_sample': None,
                    'unique_queries': 0
                }
            
            # Oldest/Newest
            oldest = self.db.query(TrainingSampleModel).order_by(
                TrainingSampleModel.created_at.asc()
            ).first()
            
            newest = self.db.query(TrainingSampleModel).order_by(
                TrainingSampleModel.created_at.desc()
            ).first()
            
            # Unique Queries
            unique_queries = self.db.query(TrainingSampleModel.query).distinct().count()
            
            return {
                'total_samples': total_count,
                'oldest_sample': oldest.created_at if oldest else None,
                'newest_sample': newest.created_at if newest else None,
                'unique_queries': unique_queries
            }
            
        except Exception as e:
            print(f"Fehler beim Laden von Statistiken: {e}")
            return {
                'total_samples': 0,
                'oldest_sample': None,
                'newest_sample': None,
                'unique_queries': 0
            }

