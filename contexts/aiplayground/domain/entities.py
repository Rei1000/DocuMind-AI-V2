"""
Domain Entities für AI Playground

Pure Business Objects - KEINE Dependencies zu Infrastructure!
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TestResult:
    """
    Domain Entity: AI Model Test Result
    
    In-Memory Entity - wird NICHT persistiert.
    Repräsentiert das Ergebnis eines einzelnen Prompt-Tests.
    
    Args:
        model_name: Name des Modells (z.B. "GPT-4")
        provider: Provider-Name (z.B. "OpenAI")
        prompt: Der gesendete Prompt
        response: Die Antwort des Modells
        tokens_sent: Anzahl gesendeter Tokens
        tokens_received: Anzahl empfangener Tokens
        response_time: Antwortzeit in Sekunden
        success: Ob der Test erfolgreich war
        error_message: Fehlermeldung falls nicht erfolgreich
        timestamp: Zeitpunkt des Tests
    """
    model_name: str
    provider: str
    prompt: str
    response: str
    tokens_sent: int
    tokens_received: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    # Token Breakdown für Transparenz
    text_tokens: Optional[int] = None  # Nur Text-Prompt
    image_tokens: Optional[int] = None  # Nur Bild (wenn vorhanden)
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    @property
    def total_tokens(self) -> int:
        """Business Logic: Berechne Gesamt-Token-Count"""
        return self.tokens_sent + self.tokens_received
    
    @property
    def response_time_ms(self) -> float:
        """Business Logic: Antwortzeit in Millisekunden"""
        return self.response_time * 1000
    
    def to_dict(self) -> dict:
        """Convert to dict for API response"""
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "prompt": self.prompt,
            "response": self.response,
            "tokens_sent": self.tokens_sent,
            "tokens_received": self.tokens_received,
            "total_tokens": self.total_tokens,
            "response_time": self.response_time,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "text_tokens": self.text_tokens,
            "image_tokens": self.image_tokens
        }


@dataclass
class ConnectionTest:
    """
    Domain Entity: AI Provider Connection Test
    
    Testet ob die API-Verbindung zum Provider funktioniert.
    
    Args:
        provider: Provider-Name
        model_name: Modell-Name
        success: Verbindung erfolgreich?
        latency: Latenz in Sekunden (für erfolgreiche Tests)
        error_message: Fehlermeldung falls nicht erfolgreich
    """
    provider: str
    model_name: str
    success: bool
    latency: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    @property
    def latency_ms(self) -> Optional[float]:
        """Business Logic: Latenz in Millisekunden"""
        return self.latency * 1000 if self.latency else None
    
    def to_dict(self) -> dict:
        """Convert to dict for API response"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "success": self.success,
            "latency": self.latency,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

