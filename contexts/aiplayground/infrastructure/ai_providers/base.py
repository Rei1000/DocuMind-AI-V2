"""
Abstract Base für AI Provider Adapters

Port Definition - alle Provider müssen dieses Interface implementieren.
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from contexts.aiplayground.domain.entities import TestResult, ConnectionTest
from contexts.aiplayground.domain.value_objects import ModelConfig


class AIProviderAdapter(ABC):
    """
    Port: Abstract Base für AI Provider
    
    Alle Provider-Adapter müssen dieses Interface implementieren.
    Dependency Inversion Principle: Domain definiert Interface, 
    Infrastructure implementiert es.
    """
    
    @abstractmethod
    async def test_connection(self, model_id: str) -> ConnectionTest:
        """
        Test Connection zu AI Provider
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            
        Returns:
            ConnectionTest Entity mit Erfolgs-Status
        """
        pass
    
    @abstractmethod
    async def send_prompt(
        self,
        model_id: str,
        prompt: str,
        config: ModelConfig
    ) -> TestResult:
        """
        Sende Prompt an AI Model
        
        Args:
            model_id: Model ID
            prompt: User Prompt
            config: Model Configuration (temperature, max_tokens, etc.)
            
        Returns:
            TestResult Entity mit Response und Metrics
        """
        pass
    
    @abstractmethod
    async def test_model_stream(
        self,
        model_id: str,
        prompt: str,
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Sende Prompt mit Streaming Response
        
        Args:
            model_id: Model ID
            prompt: User Prompt
            config: Model Configuration
            image_data: Optional Base64-encoded image
            
        Yields:
            str: Einzelne Chunks der Response
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider Name (z.B. "OpenAI")"""
        pass
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Ob Provider korrekt konfiguriert ist (API Key vorhanden)"""
        pass

