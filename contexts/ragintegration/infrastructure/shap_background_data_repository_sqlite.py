"""
SHAP Background Data Repository SQLite Implementation.

Infrastructure Layer: SQLite-basierte Persistenz für SHAP Background Data.
Ersetzt In-Memory Storage in SHAPBackgroundDataService.

Features:
- SQLite-Persistenz (shap_background_data Tabelle)
- Rolling Window (max 1000 Records)
- Feature-Extraktion (mit FeatureExtractor oder manuell)
- numpy array Output für SHAP

Version: 2.7.0
Stand: 2025-11-14
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np

from backend.app.models import SHAPBackgroundDataModel


class SHAPBackgroundDataRepositorySQLite:
    """
    SQLite-basiertes Repository für SHAP Background Data.
    
    Speichert historische Search-Records in SQLite-DB (shap_background_data Tabelle).
    Ersetzt In-Memory Storage für bessere Persistenz.
    """
    
    def __init__(
        self,
        db_session: Session,
        max_records: int = 1000,
        feature_extractor=None
    ):
        """
        Initialisiere Repository.
        
        Args:
            db_session: SQLAlchemy Session
            max_records: Max Anzahl Records (Rolling Window)
            feature_extractor: Optional FeatureExtractor für Feature-Extraktion
        """
        self.db = db_session
        self.max_records = max_records
        self.feature_extractor = feature_extractor
        self._background_data: Optional[np.ndarray] = None
        self._last_update: Optional[datetime] = None
    
    def add_record(
        self,
        query: str,
        vector_score: Optional[float] = None,
        text_score: Optional[float] = None,
        user_level: Optional[int] = None,
        keyword_matches: Optional[int] = None,
        chunk_length: Optional[int] = None,
        heading_hierarchy_depth: Optional[int] = None,
        confidence_score: Optional[float] = None
    ) -> bool:
        """
        Füge einen neuen Search-Record hinzu.
        
        Implementiert Rolling Window: Wenn > max_records, werden älteste gelöscht.
        
        Args:
            query: Search-Query
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            user_level: User-Level (1-5)
            keyword_matches: Anzahl Keyword-Matches
            chunk_length: Chunk-Länge
            heading_hierarchy_depth: Heading-Hierarchie-Tiefe
            confidence_score: Confidence-Score (0-1)
        
        Returns:
            True wenn erfolgreich
        """
        try:
            # Erstelle Model
            model = SHAPBackgroundDataModel(
                query=query,
                vector_score=vector_score,
                text_score=text_score,
                user_level=user_level,
                keyword_matches=keyword_matches,
                chunk_length=chunk_length,
                heading_hierarchy_depth=heading_hierarchy_depth,
                confidence_score=confidence_score,
                created_at=datetime.now().isoformat()
            )
            
            # Speichere
            self.db.add(model)
            self.db.commit()
            
            # Rolling Window: Lösche älteste Records wenn > max_records
            total_count = self.db.query(SHAPBackgroundDataModel).count()
            
            if total_count > self.max_records:
                # Hole IDs der neuesten max_records Records
                newest_ids = self.db.query(SHAPBackgroundDataModel.id).order_by(
                    SHAPBackgroundDataModel.created_at.desc()
                ).limit(self.max_records).all()
                newest_ids = [row[0] for row in newest_ids]
                
                # Lösche alle Records die NICHT in neuesten max_records sind
                self.db.query(SHAPBackgroundDataModel).filter(
                    ~SHAPBackgroundDataModel.id.in_(newest_ids)
                ).delete(synchronize_session=False)
                self.db.commit()
            
            # Invalidiere Background-Daten (müssen neu berechnet werden)
            self._background_data = None
            self._last_update = None
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern von Background-Record: {e}")
            self.db.rollback()
            return False
    
    def get_background_data(
        self,
        n_samples: Optional[int] = None,
        force_update: bool = False
    ) -> np.ndarray:
        """
        Hole Background-Daten für SHAP.
        
        Args:
            n_samples: Anzahl Samples (None = alle verfügbaren)
            force_update: Erzwinge Neu-Berechnung (auch wenn gecacht)
        
        Returns:
            numpy array (n_samples, 7) mit historischen Features
        """
        # Prüfe ob Background-Daten aktualisiert werden müssen
        needs_update = (
            force_update or 
            self._background_data is None or 
            self._last_update is None
        )
        
        if needs_update:
            self._update_background_data()
        
        # Wenn keine Records vorhanden, generiere zufällige Daten
        if self._background_data is None or len(self._background_data) == 0:
            print("⚠️ Keine historischen Search-Daten vorhanden, generiere zufällige Background-Daten")
            return self._generate_random_background_data(n_samples or 50)
        
        # Limitiere auf n_samples falls angegeben
        if n_samples is not None and n_samples < len(self._background_data):
            # Zufällige Auswahl (nicht nur die ersten n_samples)
            indices = np.random.choice(len(self._background_data), n_samples, replace=False)
            return self._background_data[indices]
        
        return self._background_data
    
    def _update_background_data(self):
        """Aktualisiere Background-Daten aus DB-Records."""
        try:
            # Hole alle Records
            records = self.db.query(SHAPBackgroundDataModel).order_by(
                SHAPBackgroundDataModel.created_at.asc()
            ).all()
            
            if len(records) == 0:
                self._background_data = None
                self._last_update = None
                return
            
            # Konvertiere Records zu Feature-Matrix
            if self.feature_extractor is None:
                # Fallback: Manuelle Feature-Extraktion
                features_list = []
                for record in records:
                    features = self._extract_features_manually(record)
                    features_list.append(features)
                self._background_data = np.array(features_list, dtype=np.float64)
            else:
                # Verwende FeatureExtractor
                features_list = []
                for record in records:
                    # Mock Chunk für FeatureExtractor
                    chunk = {
                        'chunk_id': 'background_record',
                        'metadata': {
                            'chunk_length': record.chunk_length or 0,
                            'heading_hierarchy_depth': record.heading_hierarchy_depth or 0,
                            'confidence_score': record.confidence_score or 0.5,
                            'chunk_text': record.query,
                            'page_numbers': [1]
                        }
                    }
                    
                    features = self.feature_extractor.extract(
                        query=record.query,
                        chunk=chunk,
                        vector_score=record.vector_score or 0.5,
                        text_score=record.text_score or 0.5,
                        user_level=record.user_level or 1,
                        keyword_matches=record.keyword_matches or 0
                    )
                    features_list.append(features)
                
                self._background_data = np.array(features_list, dtype=np.float64)
            
            self._last_update = datetime.now()
            print(f"✅ Background-Daten aktualisiert: {len(self._background_data)} historische Samples")
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren von Background-Daten: {e}")
            self._background_data = None
            self._last_update = None
    
    def _extract_features_manually(self, record: SHAPBackgroundDataModel) -> np.ndarray:
        """
        Extrahiere Features manuell (Fallback ohne FeatureExtractor).
        
        Args:
            record: SHAPBackgroundDataModel
        
        Returns:
            numpy array (7,) mit normalisierten Features
        """
        return np.array([
            float(record.vector_score) if record.vector_score is not None else 0.5,
            float(record.text_score) if record.text_score is not None else 0.5,
            float(record.user_level) / 5.0 if record.user_level is not None else 0.2,  # Normalisiere auf 0-1
            min(float(record.keyword_matches) / 10.0, 1.0) if record.keyword_matches is not None else 0.0,  # Normalisiere auf 0-1
            min(float(record.chunk_length) / 2000.0, 1.0) if record.chunk_length is not None else 0.05,  # Normalisiere auf 0-1
            min(float(record.heading_hierarchy_depth) / 5.0, 1.0) if record.heading_hierarchy_depth is not None else 0.0,  # Normalisiere auf 0-1
            float(record.confidence_score) if record.confidence_score is not None else 0.5
        ], dtype=np.float64)
    
    def _generate_random_background_data(self, n_samples: int) -> np.ndarray:
        """
        Generiere zufällige Background-Daten (Fallback).
        
        Args:
            n_samples: Anzahl Samples
        
        Returns:
            numpy array (n_samples, 7) mit Random Features [0, 1]
        """
        return np.random.rand(n_samples, 7)
    
    def get_statistics(self) -> dict:
        """
        Hole Statistiken über Background-Daten.
        
        Returns:
            Dict mit:
                - total_records: int
                - background_data_shape: Optional[tuple]
                - last_update: Optional[str] (ISO-8601)
        """
        try:
            total_records = self.db.query(SHAPBackgroundDataModel).count()
            
            return {
                'total_records': total_records,
                'background_data_shape': self._background_data.shape if self._background_data is not None else None,
                'last_update': self._last_update.isoformat() if self._last_update else None
            }
            
        except Exception as e:
            print(f"Fehler beim Laden von Statistiken: {e}")
            return {
                'total_records': 0,
                'background_data_shape': None,
                'last_update': None
            }

