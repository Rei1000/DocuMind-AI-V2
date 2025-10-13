"""
AI Processing Service - Adapter für aiplayground Context

Dieser Service ist die Implementierung (Adapter) des AIProcessingService Ports.
Er nutzt den aiplayground Context für die AI-Verarbeitung.
"""

from typing import Dict, Any, Optional
import os
import time
from pathlib import Path


class AIPlaygroundProcessingService:
    """
    AI Processing Service Adapter.
    
    Nutzt den aiplayground Context für die Verarbeitung von Dokumentseiten.
    
    Workflow:
    1. Lade Seiten-Bild
    2. Hole AI-Modell-Config
    3. Sende Request an AI-Modell (via aiplayground Service)
    4. Parse Response
    5. Returniere strukturierte Daten
    
    Dependencies:
    - aiplayground.AIPlaygroundService (Cross-Context Dependency)
    """
    
    def __init__(self, ai_playground_service):
        """
        Initialize AI Processing Service.
        
        Args:
            ai_playground_service: AIPlaygroundService aus aiplayground Context
        """
        self.ai_playground_service = ai_playground_service
    
    async def process_page(
        self,
        page_image_path: str,
        prompt_text: str,
        ai_model_id: int,
        temperature: float,
        max_tokens: int,
        top_p: float,
        detail_level: str
    ) -> Dict[str, Any]:
        """
        Verarbeite eine Dokumentseite mit AI-Modell.
        
        Args:
            page_image_path: Pfad zum Seiten-Bild (relativ zu data/uploads/)
            prompt_text: Prompt für AI-Modell
            ai_model_id: ID des AI-Modells
            temperature: Temperature-Wert (0.0-1.0)
            max_tokens: Max Tokens
            top_p: Top-P Wert (0.0-1.0)
            detail_level: Detail Level (high/low)
            
        Returns:
            Dict mit:
                - json_response: Strukturierte JSON-Antwort (String)
                - model_name: Name des AI-Modells
                - tokens_sent: Anzahl gesendeter Tokens
                - tokens_received: Anzahl empfangener Tokens
                - total_tokens: Gesamtzahl Tokens
                - response_time_ms: Response-Zeit in Millisekunden
                
        Raises:
            FileNotFoundError: Wenn Seiten-Bild nicht gefunden
            AIProcessingError: Bei Verarbeitungsfehler
        """
        # 1. Validiere Seiten-Bild
        full_path = self._get_full_path(page_image_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Page image not found: {page_image_path}")
        
        # 2. Lade AI-Modell
        model = await self.ai_playground_service.get_model_by_id(ai_model_id)
        if not model:
            raise ValueError(f"AI Model {ai_model_id} not found")
        
        # 3. Bereite Request vor
        start_time = time.time()
        
        try:
            # 4. Sende Request an AI-Modell (via aiplayground)
            result = await self.ai_playground_service.test_single_model(
                model_id=ai_model_id,
                prompt=prompt_text,
                image_path=full_path,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                detail_level=detail_level
            )
            
            # 5. Berechne Response-Zeit
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 6. Parse Response
            return {
                "json_response": result.get("response", "{}"),
                "model_name": result.get("model_name", model.name),
                "tokens_sent": result.get("tokens_sent", 0),
                "tokens_received": result.get("tokens_received", 0),
                "total_tokens": result.get("total_tokens", 0),
                "response_time_ms": result.get("response_time_ms", response_time_ms)
            }
            
        except Exception as e:
            # Log Error und re-raise
            print(f"[AIProcessingService] Error processing page: {e}")
            raise AIProcessingError(f"Failed to process page: {e}") from e
    
    def _get_full_path(self, relative_path: str) -> str:
        """
        Konvertiere relativen Pfad zu absolutem Pfad.
        
        Args:
            relative_path: Relativer Pfad (z.B. "uploads/2025/01/preview.png")
            
        Returns:
            Absoluter Pfad (z.B. "/Users/.../data/uploads/2025/01/preview.png")
        """
        # Base directory ist data/
        base_dir = Path(__file__).parent.parent.parent.parent / "data"
        
        # Entferne führendes "uploads/" falls vorhanden
        if relative_path.startswith("uploads/"):
            relative_path = relative_path[8:]
        
        return str(base_dir / "uploads" / relative_path)


class AIProcessingError(Exception):
    """Exception für AI-Processing Fehler."""
    pass

