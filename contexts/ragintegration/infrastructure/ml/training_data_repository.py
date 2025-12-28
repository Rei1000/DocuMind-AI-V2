"""
Training Data Repository für LTR-Modelle.

Infrastructure Layer: Speichert und lädt Training-Daten für Learning-to-Rank.

Features:
- File-basierte Persistenz (JSON Lines Format)
- Feedback-Integration
- Datum-Filter
- Relevance-Mapping
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
from pathlib import Path


def map_feedback_to_relevance(rating: Any) -> float:
    """
    Mappe Feedback-Rating zu Relevance-Score (0-1).
    
    Args:
        rating: 'positive', 'negative', 'neutral' oder numerisches Rating (1-5)
        
    Returns:
        Relevance-Score (0-1)
    """
    if isinstance(rating, str):
        rating_lower = rating.lower()
        if rating_lower == 'positive':
            return 1.0
        elif rating_lower == 'negative':
            return 0.0
        elif rating_lower == 'neutral':
            return 0.5
        else:
            # Fallback
            return 0.5
    elif isinstance(rating, (int, float)):
        # Numerisches Rating (1-5) → 0.2-1.0
        return float(rating) / 5.0
    else:
        # Fallback
        return 0.5


class FileBasedTrainingDataRepository:
    """
    File-basiertes Repository für Training-Daten.
    
    Speichert Training-Samples im JSON Lines Format (eine Zeile pro Sample).
    Ideal für kontinuierliches Sammeln von Feedback-Daten.
    """
    
    def __init__(
        self,
        data_dir: str = 'data/ml_training_data',
        filename: str = 'training_samples.jsonl'
    ):
        """
        Initialisiere Repository.
        
        Args:
            data_dir: Verzeichnis für Training-Daten
            filename: Dateiname (JSON Lines Format)
        """
        self.data_dir = data_dir
        self.filename = filename
        self.filepath = os.path.join(data_dir, filename)
        
        # Erstelle Verzeichnis falls nicht vorhanden
        Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    def save_training_sample(self, sample: Dict[str, Any]) -> bool:
        """
        Speichere Training-Sample.
        
        Args:
            sample: Training-Sample Dict
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # Füge Timestamp hinzu falls nicht vorhanden
            if 'timestamp' not in sample:
                sample['timestamp'] = datetime.now().isoformat()
            elif isinstance(sample['timestamp'], datetime):
                sample['timestamp'] = sample['timestamp'].isoformat()
            
            # Append zu File (JSON Lines Format)
            with open(self.filepath, 'a') as f:
                f.write(json.dumps(sample) + '\n')
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern von Training-Sample: {e}")
            return False
    
    def get_training_samples(
        self,
        min_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lade Training-Samples.
        
        Args:
            min_date: Optional - Nur Samples nach diesem Datum
            limit: Optional - Maximale Anzahl Samples
            
        Returns:
            Liste von Training-Samples
        """
        if not os.path.exists(self.filepath):
            return []
        
        samples = []
        
        try:
            with open(self.filepath, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    sample = json.loads(line)
                    
                    # Datum-Filter
                    if min_date:
                        sample_date = datetime.fromisoformat(sample['timestamp'])
                        if sample_date < min_date:
                            continue
                    
                    samples.append(sample)
                    
                    # Limit
                    if limit and len(samples) >= limit:
                        break
            
        except Exception as e:
            print(f"Fehler beim Laden von Training-Samples: {e}")
        
        return samples
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Hole Statistiken über Training-Daten.
        
        Returns:
            Dict mit Statistiken
        """
        samples = self.get_training_samples()
        
        if not samples:
            return {
                'total_samples': 0,
                'oldest_sample': None,
                'newest_sample': None,
                'unique_queries': 0
            }
        
        # Statistiken berechnen
        timestamps = [datetime.fromisoformat(s['timestamp']) for s in samples]
        queries = set(s['query'] for s in samples)
        
        return {
            'total_samples': len(samples),
            'oldest_sample': min(timestamps).isoformat(),
            'newest_sample': max(timestamps).isoformat(),
            'unique_queries': len(queries)
        }

