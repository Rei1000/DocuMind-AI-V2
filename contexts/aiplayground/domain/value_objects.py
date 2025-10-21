"""
Value Objects für AI Playground

Immutable Domain Objekte mit Value Semantics.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """
    Value Object: AI Model Configuration
    
    Immutable Configuration für AI Model Requests.
    
    Args:
        temperature: Kreativität (0.0 = deterministisch, 2.0 = sehr kreativ)
        max_tokens: Maximale Anzahl Tokens in der Response
        top_p: Nucleus Sampling Parameter (0.0 - 1.0)
        top_k: Top-K Sampling (nur für manche Modelle)
        detail_level: Bilderkennung Detail-Level (high/low, nur OpenAI)
    """
    temperature: float = 0.0  # Standard für alle Modelle
    max_tokens: int = 4000  # Wird modell-spezifisch überschrieben
    top_p: float = 1.0
    top_k: Optional[int] = None
    detail_level: str = "high"  # "high" oder "low" für Bilderkennung (nur OpenAI)
    
    def __post_init__(self):
        """Validate configuration"""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        if self.detail_level not in ["high", "low"]:
            raise ValueError("detail_level must be 'high' or 'low'")


@dataclass(frozen=True)
class Provider:
    """
    Value Object: AI Provider
    
    Repräsentiert einen AI-Provider (OpenAI, Google, etc.)
    
    Args:
        name: Provider-Name (z.B. "OpenAI")
        display_name: Anzeigename für UI
        requires_api_key: Ob API-Key erforderlich ist
    """
    name: str
    display_name: str
    requires_api_key: bool = True


# Vordefinierte Provider
OPENAI_PROVIDER = Provider(
    name="openai",
    display_name="OpenAI",
    requires_api_key=True
)

OPENAI_GPT5_PROVIDER = Provider(
    name="openai_gpt5",
    display_name="OpenAI GPT-5",
    requires_api_key=True
)

GOOGLE_PROVIDER = Provider(
    name="google",
    display_name="Google AI (Gemini)",
    requires_api_key=True
)


@dataclass(frozen=True)
class ModelDefinition:
    """
    Value Object: AI Model Definition
    
    Definiert ein verfügbares AI-Modell.
    
    Args:
        id: Eindeutige ID (z.B. "gpt-4")
        name: Anzeigename (z.B. "GPT-4")
        provider: Provider Value Object
        model_id: API Model ID (z.B. "gpt-4-turbo-preview")
        description: Beschreibung des Modells
        max_tokens_supported: Maximale Token-Kapazität
    """
    id: str
    name: str
    provider: Provider
    model_id: str
    description: str
    max_tokens_supported: int
    
    def to_dict(self) -> dict:
        """Convert to dict for API response"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.display_name,
            "model_id": self.model_id,
            "description": self.description,
            "max_tokens_supported": self.max_tokens_supported
        }


# Vordefinierte Modelle
AVAILABLE_MODELS = [
    # OpenAI Models
    ModelDefinition(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider=OPENAI_PROVIDER,
        model_id="gpt-4o-mini",
        description="OpenAI - Fast model with multimodal capabilities (text + vision)",
        max_tokens_supported=16384
    ),
    
    ModelDefinition(
        id="gpt-5-mini",
        name="GPT-5 Mini",
        provider=OPENAI_GPT5_PROVIDER,
        model_id="gpt-5-mini",
        description="OpenAI - Next-gen model with 400k context & 128k output (text + vision)",
        max_tokens_supported=128000
    ),
    
    # Google AI Model
    ModelDefinition(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider=GOOGLE_PROVIDER,
        model_id="gemini-2.5-flash",
        description="Google - Latest generation with enhanced vision and reasoning",
        max_tokens_supported=32000
    ),
]

