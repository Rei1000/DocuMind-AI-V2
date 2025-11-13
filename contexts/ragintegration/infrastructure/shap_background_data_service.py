"""
SHAP Background Data Service für RAG Integration.

Infrastructure Layer: Sammelt historische Search-Daten für bessere SHAP-Qualität.

Echte Background-Daten verbessern die SHAP-Attribution deutlich im Vergleich zu
zufällig generierten Daten.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class SearchRecord:
    """Record für einen historischen Search."""
    query: str
    vector_score: float
    text_score: float
    user_level: int
    keyword_matches: int
    chunk_length: int
    heading_hierarchy_depth: int
    confidence_score: float
    timestamp: datetime


class SHAPBackgroundDataService:
    """
    Service für historische Search-Daten.
    
    Sammelt und verwaltet historische Search-Daten für echte SHAP-Background-Data.
    Verbessert SHAP-Qualität deutlich gegenüber zufälligen Daten.
    
    Features:
    - Automatisches Sammeln von Search-Daten
    - Rolling Window (letzte N Searches)
    - Periodische Aktualisierung
    - Export/Import für Persistenz
    """
    
    def __init__(
        self,
        max_records: int = 1000,
        feature_extractor = None
    ):
        """
        Initialisiere Background Data Service.
        
        Args:
            max_records: Max Anzahl historischer Records (Rolling Window)
            feature_extractor: FeatureExtractor für Feature-Extraktion
        """
        self.max_records = max_records
        self.feature_extractor = feature_extractor
        self.records: List[SearchRecord] = []
        self._background_data: Optional[np.ndarray] = None
        self._last_update: Optional[datetime] = None
    
    def add_search_record(
        self,
        query: str,
        vector_score: float,
        text_score: float,
        user_level: int,
        keyword_matches: int,
        chunk_length: int,
        heading_hierarchy_depth: int,
        confidence_score: float
    ):
        """
        Füge einen neuen Search-Record hinzu.
        
        Automatisch in Rolling Window (älteste Records werden entfernt wenn max_records erreicht).
        
        Args:
            query: Search-Query
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            user_level: User-Level (1-5)
            keyword_matches: Anzahl Keyword-Matches
            chunk_length: Chunk-Länge
            heading_hierarchy_depth: Heading-Hierarchie-Tiefe
            confidence_score: Confidence-Score (0-1)
        """
        record = SearchRecord(
            query=query,
            vector_score=vector_score,
            text_score=text_score,
            user_level=user_level,
            keyword_matches=keyword_matches,
            chunk_length=chunk_length,
            heading_hierarchy_depth=heading_hierarchy_depth,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
        
        # Füge Record hinzu
        self.records.append(record)
        
        # Rolling Window: Entferne älteste Records wenn max_records überschritten
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]
        
        # Invalidiere Background-Daten (müssen neu berechnet werden)
        self._background_data = None
        self._last_update = None
    
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
            len(self.records) == 0
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
        """Aktualisiere Background-Daten aus Records."""
        if len(self.records) == 0:
            self._background_data = None
            self._last_update = None
            return
        
        # Konvertiere Records zu Feature-Matrix
        if self.feature_extractor is None:
            # Fallback: Manuelle Feature-Extraktion
            features_list = []
            for record in self.records:
                features = self._extract_features_manually(record)
                features_list.append(features)
            self._background_data = np.array(features_list, dtype=np.float64)
        else:
            # Verwende FeatureExtractor
            features_list = []
            for record in self.records:
                # Mock Chunk für FeatureExtractor
                chunk = {
                    'chunk_id': 'background_record',
                    'metadata': {
                        'chunk_length': record.chunk_length,
                        'heading_hierarchy_depth': record.heading_hierarchy_depth,
                        'confidence_score': record.confidence_score,
                        'chunk_text': record.query,
                        'page_numbers': [1]
                    }
                }
                
                features = self.feature_extractor.extract(
                    query=record.query,
                    chunk=chunk,
                    vector_score=record.vector_score,
                    text_score=record.text_score,
                    user_level=record.user_level,
                    keyword_matches=record.keyword_matches
                )
                features_list.append(features)
            
            self._background_data = np.array(features_list, dtype=np.float64)
        
        self._last_update = datetime.now()
        print(f"✅ Background-Daten aktualisiert: {len(self._background_data)} historische Samples")
    
    def _extract_features_manually(self, record: SearchRecord) -> np.ndarray:
        """
        Extrahiere Features manuell (Fallback ohne FeatureExtractor).
        
        Args:
            record: SearchRecord
            
        Returns:
            numpy array (7,) mit normalisierten Features
        """
        return np.array([
            float(record.vector_score),
            float(record.text_score),
            float(record.user_level) / 5.0,  # Normalisiere auf 0-1
            min(float(record.keyword_matches) / 10.0, 1.0),  # Normalisiere auf 0-1
            min(float(record.chunk_length) / 2000.0, 1.0),  # Normalisiere auf 0-1
            min(float(record.heading_hierarchy_depth) / 5.0, 1.0),  # Normalisiere auf 0-1
            float(record.confidence_score)
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Hole Statistiken über Background-Daten.
        
        Returns:
            Dict mit Statistiken
        """
        if len(self.records) == 0:
            return {
                'total_records': 0,
                'background_data_shape': None,
                'last_update': None,
                'oldest_record': None,
                'newest_record': None
            }
        
        return {
            'total_records': len(self.records),
            'background_data_shape': self._background_data.shape if self._background_data is not None else None,
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'oldest_record': self.records[0].timestamp.isoformat(),
            'newest_record': self.records[-1].timestamp.isoformat()
        }
    
    def export_to_json(self, filepath: str):
        """
        Exportiere Records zu JSON-Datei.
        
        Nützlich für Persistenz und Backup.
        
        Args:
            filepath: Pfad zur JSON-Datei
        """
        data = {
            'max_records': self.max_records,
            'records': [
                {
                    'query': record.query,
                    'vector_score': record.vector_score,
                    'text_score': record.text_score,
                    'user_level': record.user_level,
                    'keyword_matches': record.keyword_matches,
                    'chunk_length': record.chunk_length,
                    'heading_hierarchy_depth': record.heading_hierarchy_depth,
                    'confidence_score': record.confidence_score,
                    'timestamp': record.timestamp.isoformat()
                }
                for record in self.records
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Background-Daten exportiert zu: {filepath}")
    
    def import_from_json(self, filepath: str):
        """
        Importiere Records von JSON-Datei.
        
        Args:
            filepath: Pfad zur JSON-Datei
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.max_records = data.get('max_records', 1000)
        self.records = []
        
        for record_data in data.get('records', []):
            record = SearchRecord(
                query=record_data['query'],
                vector_score=record_data['vector_score'],
                text_score=record_data['text_score'],
                user_level=record_data['user_level'],
                keyword_matches=record_data['keyword_matches'],
                chunk_length=record_data['chunk_length'],
                heading_hierarchy_depth=record_data['heading_hierarchy_depth'],
                confidence_score=record_data['confidence_score'],
                timestamp=datetime.fromisoformat(record_data['timestamp'])
            )
            self.records.append(record)
        
        # Aktualisiere Background-Daten
        self._update_background_data()
        
        print(f"✅ Background-Daten importiert von: {filepath} ({len(self.records)} Records)")
    
    def clear(self):
        """Lösche alle Records (für Tests)."""
        self.records = []
        self._background_data = None
        self._last_update = None

