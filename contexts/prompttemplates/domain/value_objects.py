"""
Domain Value Objects: PromptTemplates Context

Immutable Value Objects die fachliche Konzepte kapseln.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AIModelConfig:
    """
    Value Object: AI Model Configuration
    
    Kapselt die Konfiguration für ein AI-Modell.
    """
    model_id: str
    temperature: float = 0.0
    max_tokens: int = 4000
    top_p: float = 1.0
    detail_level: str = "high"
    
    def __post_init__(self):
        """Validate on creation"""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2: {self.temperature}")
        if self.max_tokens <= 0:
            raise ValueError(f"Max tokens must be positive: {self.max_tokens}")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError(f"Top P must be between 0 and 1: {self.top_p}")
        if self.detail_level not in ["high", "low"]:
            raise ValueError(f"Detail level must be 'high' or 'low': {self.detail_level}")


@dataclass(frozen=True)
class PromptVersion:
    """
    Value Object: Prompt Version
    
    Semantic Versioning für Prompts.
    """
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def from_string(cls, version_str: str) -> "PromptVersion":
        """Parse version string (e.g. "1.2.3")"""
        try:
            parts = version_str.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return cls(major, minor, patch)
        except (ValueError, IndexError):
            return cls(1, 0, 0)


@dataclass(frozen=True)
class TemplateMetadata:
    """
    Value Object: Template Metadata
    
    Zusätzliche Metadaten für ein Template.
    """
    tested_successfully: bool
    success_count: int
    average_tokens_sent: Optional[int] = None
    average_tokens_received: Optional[int] = None
    average_response_time_ms: Optional[float] = None
    
    def has_performance_data(self) -> bool:
        """Check if performance metrics are available"""
        return (
            self.average_tokens_sent is not None and
            self.average_tokens_received is not None and
            self.average_response_time_ms is not None
        )
    
    def get_estimated_cost(self, cost_per_1k_tokens_sent: float = 0.0001, 
                          cost_per_1k_tokens_received: float = 0.0002) -> Optional[float]:
        """
        Estimate cost per use based on average tokens
        
        Args:
            cost_per_1k_tokens_sent: Cost per 1000 input tokens
            cost_per_1k_tokens_received: Cost per 1000 output tokens
            
        Returns:
            Estimated cost in USD or None if no data
        """
        if not self.has_performance_data():
            return None
        
        sent_cost = (self.average_tokens_sent / 1000) * cost_per_1k_tokens_sent
        received_cost = (self.average_tokens_received / 1000) * cost_per_1k_tokens_received
        return sent_cost + received_cost


@dataclass(frozen=True)
class PromptExample:
    """
    Value Object: Prompt Example
    
    Beispiel Input/Output für Dokumentation.
    """
    input_description: str
    expected_output: str
    actual_output: Optional[str] = None
    
    def matches_expectation(self) -> bool:
        """Check if actual output matches expectation (wenn vorhanden)"""
        if self.actual_output is None:
            return False
        # Simplified check - könnte mit fuzzy matching verbessert werden
        return self.expected_output.strip() in self.actual_output.strip()

