"""
SHAP Cache Repository SQLite Implementation.

Infrastructure Layer: SQLite-basierte Persistenz für SHAP Cache.
Ersetzt In-Memory Cache in SHAPCacheService.

Features:
- SQLite-Persistenz (shap_cache Tabelle)
- LRU Cache (max 100 Einträge)
- TTL (Time-To-Live) Support
- Cache Key als MD5 Hash
- JSON-Serialisierung für Explanations

Version: 2.7.0
Stand: 2025-11-14
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import hashlib
import json

from backend.app.models import SHAPCacheEntryModel


class SHAPCacheRepositorySQLite:
    """
    SQLite-basiertes Repository für SHAP Cache.
    
    Speichert gecachte SHAP-Erklärungen in SQLite-DB (shap_cache Tabelle).
    Ersetzt In-Memory Cache für bessere Persistenz.
    """
    
    def __init__(
        self,
        db_session: Session,
        max_size: int = 100,
        ttl_seconds: int = 3600  # 1 Stunde
    ):
        """
        Initialisiere Repository.
        
        Args:
            db_session: SQLAlchemy Session
            max_size: Maximale Anzahl gecachter Erklärungen
            ttl_seconds: Time-To-Live in Sekunden (3600 = 1 Stunde)
        """
        self.db = db_session
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0
    
    def _generate_cache_key(
        self,
        query: str,
        features: Dict[str, float]
    ) -> str:
        """
        Generiere Cache-Key aus Query und Features.
        
        Args:
            query: Query-String
            features: Feature-Dict (normalisierte Werte)
        
        Returns:
            MD5 Hash als Cache-Key
        """
        # Sortiere Features für konsistente Keys
        sorted_features = dict(sorted(features.items()))
        
        # Erstelle String-Repräsentation
        key_data = {
            'query': query.lower().strip(),
            'features': sorted_features
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        
        # MD5 Hash
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(
        self,
        query: str,
        features: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Hole gecachte SHAP-Erklärung.
        
        Args:
            query: Query-String
            features: Feature-Dict
        
        Returns:
            Gecachte Explanation (Dict) oder None bei Miss
        """
        cache_key = self._generate_cache_key(query, features)
        
        try:
            # Prüfe ob im Cache
            cache_entry = self.db.query(SHAPCacheEntryModel).filter(
                SHAPCacheEntryModel.cache_key == cache_key
            ).first()
            
            if cache_entry is None:
                self._misses += 1
                return None
            
            # Prüfe TTL
            expires_at = datetime.fromisoformat(cache_entry.expires_at)
            if datetime.now() > expires_at:
                # Abgelaufen - entferne
                self.db.delete(cache_entry)
                self.db.commit()
                self._misses += 1
                return None
            
            # Cache Hit!
            self._hits += 1
            
            # Deserialisiere Explanation
            explanation = json.loads(cache_entry.shap_values_json)
            return explanation
            
        except Exception as e:
            print(f"Fehler beim Laden von Cache-Eintrag: {e}")
            self._misses += 1
            return None
    
    def put(
        self,
        query: str,
        features: Dict[str, float],
        explanation: Any
    ):
        """
        Speichere SHAP-Erklärung im Cache.
        
        Args:
            query: Query-String
            features: Feature-Dict
            explanation: SHAPExplanation (wird als JSON gespeichert)
        """
        cache_key = self._generate_cache_key(query, features)
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        
        try:
            # Erklärung muss JSON-serialisierbar sein (Dataclass → Dict)
            explanation_jsonable: Dict[str, Any]
            if isinstance(explanation, dict):
                explanation_jsonable = explanation
            elif hasattr(explanation, "__dict__"):
                explanation_jsonable = dict(explanation.__dict__)
                # datetime → ISO
                ts = explanation_jsonable.get("timestamp")
                if hasattr(ts, "isoformat"):
                    explanation_jsonable["timestamp"] = ts.isoformat()
            else:
                explanation_jsonable = {"value": str(explanation)}

            # Prüfe ob bereits vorhanden (Update)
            existing = self.db.query(SHAPCacheEntryModel).filter(
                SHAPCacheEntryModel.cache_key == cache_key
            ).first()
            
            if existing:
                # Update existierenden Eintrag
                existing.shap_values_json = json.dumps(explanation_jsonable)
                existing.created_at = now.isoformat()
                existing.expires_at = expires_at.isoformat()
                self.db.commit()
                return
            
            # Prüfe Cache-Größe
            total_count = self.db.query(SHAPCacheEntryModel).count()
            
            if total_count >= self.max_size:
                # Entferne ältesten Eintrag (LRU)
                oldest = self.db.query(SHAPCacheEntryModel).order_by(
                    SHAPCacheEntryModel.created_at.asc()
                ).first()
                
                if oldest:
                    self.db.delete(oldest)
            
            # Erstelle neuen Eintrag
            cache_entry = SHAPCacheEntryModel(
                cache_key=cache_key,
                shap_values_json=json.dumps(explanation_jsonable),
                created_at=now.isoformat(),
                expires_at=expires_at.isoformat()
            )
            
            self.db.add(cache_entry)
            self.db.commit()
            
        except Exception as e:
            print(f"Fehler beim Speichern von Cache-Eintrag: {e}")
            self.db.rollback()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Hole Cache-Statistiken.
        
        Returns:
            Dict mit:
                - cache_size: int
                - max_size: int
                - hits: int
                - misses: int
                - total_requests: int
                - hit_rate: float (0-1)
                - ttl_seconds: int
        """
        try:
            # Lösche abgelaufene Einträge zuerst
            self.clear_expired()
            
            cache_size = self.db.query(SHAPCacheEntryModel).count()
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0
            
            return {
                'cache_size': cache_size,
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 4),
                'hit_rate_percent': round(hit_rate * 100, 2),
                'ttl_seconds': self.ttl_seconds
            }
            
        except Exception as e:
            print(f"Fehler beim Laden von Statistiken: {e}")
            return {
                'cache_size': 0,
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'total_requests': self._hits + self._misses,
                'hit_rate': 0.0,
                'hit_rate_percent': 0.0,
                'ttl_seconds': self.ttl_seconds
            }
    
    def clear_expired(self) -> int:
        """
        Entferne abgelaufene Cache-Einträge.
        
        Returns:
            Anzahl gelöschter Einträge
        """
        try:
            now = datetime.now()
            now_str = now.isoformat()
            
            # Finde abgelaufene Einträge
            expired = self.db.query(SHAPCacheEntryModel).filter(
                SHAPCacheEntryModel.expires_at < now_str
            ).all()
            
            count = len(expired)
            
            # Lösche abgelaufene Einträge
            for entry in expired:
                self.db.delete(entry)
            
            self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"Fehler beim Löschen abgelaufener Einträge: {e}")
            self.db.rollback()
            return 0
    
    def clear(self):
        """Lösche alle Cache-Einträge."""
        try:
            self.db.query(SHAPCacheEntryModel).delete()
            self.db.commit()
            self._hits = 0
            self._misses = 0
        except Exception as e:
            print(f"Fehler beim Löschen aller Einträge: {e}")
            self.db.rollback()

