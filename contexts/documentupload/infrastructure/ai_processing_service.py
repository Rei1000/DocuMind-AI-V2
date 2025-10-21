"""
AI Processing Service - Adapter für aiplayground Context

Dieser Service ist die Implementierung (Adapter) des AIProcessingService Ports.
Er nutzt den aiplayground Context für die AI-Verarbeitung.
"""

from typing import Dict, Any, Optional
import os
import time
import base64
from pathlib import Path
from contexts.aiplayground.domain.value_objects import ModelConfig


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
        ai_model_id: str,  # String Model ID (z.B. "gpt-5-mini")
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
            ai_model_id: Model ID als String (z.B. "gpt-5-mini")
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
        print(f"[AIProcessingService] Processing page: {page_image_path}")
        full_path = self._get_full_path(page_image_path)
        print(f"[AIProcessingService] Full path: {full_path}")
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Page image not found: {page_image_path}")
        
        # 2. Lade Bild und konvertiere zu Base64
        try:
            print(f"[AIProcessingService] Loading image...")
            with open(full_path, 'rb') as image_file:
                image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"[AIProcessingService] Image loaded: {len(image_base64)} bytes (base64)")
        except Exception as e:
            raise AIProcessingError(f"Failed to load image: {e}") from e
        
        # 3. Lade AI-Modell
        print(f"[AIProcessingService] Getting model: {ai_model_id}")
        model = self.ai_playground_service.get_model_by_id(ai_model_id)
        if not model:
            raise ValueError(f"AI Model {ai_model_id} not found")
        print(f"[AIProcessingService] Model found: {model.name}")
        
        # 4. Erstelle ModelConfig (mit expliziten Type-Casts)
        print(f"[AIProcessingService] Creating ModelConfig - temp: {temperature}, max_tokens: {max_tokens}, top_p: {top_p}")
        model_config = ModelConfig(
            temperature=float(temperature),  # Ensure float
            max_tokens=int(max_tokens),      # Ensure int
            top_p=float(top_p),              # Ensure float
            detail_level=str(detail_level)   # Ensure string
        )
        print(f"[AIProcessingService] ModelConfig created successfully")
        
        # 5. Bereite Request vor
        start_time = time.time()
        
        try:
            # 6. Sende Request an AI-Modell (via aiplayground)
            print(f"[AIProcessingService] Sending request to AI model...")
            result = await self.ai_playground_service.test_model(
                model_id=ai_model_id,
                prompt=prompt_text,
                config=model_config,
                image_data=image_base64
            )
            print(f"[AIProcessingService] AI model response received")
            
            # 7. Berechne Response-Zeit
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 8. Parse Response (TestResult Entity)
            return {
                "json_response": result.response,  # TestResult.response
                "model_name": result.model_name,
                "tokens_sent": result.tokens_sent,
                "tokens_received": result.tokens_received,
                "total_tokens": result.total_tokens,
                "response_time_ms": int(result.response_time * 1000) if result.response_time else response_time_ms
            }
            
        except Exception as e:
            # Log Error und re-raise
            print(f"[AIProcessingService] Error processing page: {e}")
            import traceback
            traceback.print_exc()
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

