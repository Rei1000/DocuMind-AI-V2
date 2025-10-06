"""
AI Playground Service

Application Service - Orchestriert Use Cases und Provider Adapters.
"""

from typing import List, Dict, Optional
import asyncio

from contexts.aiplayground.domain.entities import TestResult, ConnectionTest
from contexts.aiplayground.domain.value_objects import (
    ModelConfig,
    ModelDefinition,
    AVAILABLE_MODELS,
    OPENAI_PROVIDER,
    GOOGLE_PROVIDER
)
from contexts.aiplayground.infrastructure.ai_providers.base import AIProviderAdapter
from contexts.aiplayground.infrastructure.ai_providers.openai_adapter import OpenAIAdapter
from contexts.aiplayground.infrastructure.ai_providers.google_adapter import GoogleAIAdapter


class AIPlaygroundService:
    """
    Application Service: AI Playground
    
    Orchestriert AI Provider Adapters und Use Cases.
    Keine Business Logic hier - nur Koordination!
    
    Beispiel:
        service = AIPlaygroundService()
        models = service.get_available_models()
        result = await service.test_model("gpt-4", "Hello World")
    """
    
    def __init__(self):
        """Initialize Service mit Provider Adapters"""
        self._adapters: Dict[str, AIProviderAdapter] = {
            "openai": OpenAIAdapter(),
            "google": GoogleAIAdapter()
        }
    
    def get_available_models(self) -> List[Dict]:
        """
        Use Case: Get Available Models
        
        Liefert alle verfügbaren AI-Modelle mit Status.
        
        Returns:
            Liste von Model-Dictionaries mit is_configured Flag
        """
        models = []
        
        for model in AVAILABLE_MODELS:
            adapter = self._get_adapter_for_provider(model.provider.name)
            
            model_dict = model.to_dict()
            model_dict["is_configured"] = adapter.is_configured if adapter else False
            
            models.append(model_dict)
        
        return models
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelDefinition]:
        """
        Get Model Definition by ID
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            
        Returns:
            ModelDefinition oder None
        """
        for model in AVAILABLE_MODELS:
            if model.id == model_id:
                return model
        return None
    
    async def test_connection(self, model_id: str) -> ConnectionTest:
        """
        Use Case: Test Model Connection
        
        Testet ob die Verbindung zum AI-Provider funktioniert.
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            
        Returns:
            ConnectionTest Entity
            
        Raises:
            ValueError: Wenn Model nicht gefunden
        """
        model = self.get_model_by_id(model_id)
        
        if not model:
            return ConnectionTest(
                provider="Unknown",
                model_name=model_id,
                success=False,
                error_message=f"Model '{model_id}' nicht gefunden"
            )
        
        adapter = self._get_adapter_for_provider(model.provider.name)
        
        if not adapter:
            return ConnectionTest(
                provider=model.provider.display_name,
                model_name=model.name,
                success=False,
                error_message=f"Adapter für Provider '{model.provider.name}' nicht gefunden"
            )
        
        return await adapter.test_connection(model.model_id)
    
    async def test_model(
        self,
        model_id: str,
        prompt: str,
        config: Optional[ModelConfig] = None
    ) -> TestResult:
        """
        Use Case: Test Model mit Prompt
        
        Sendet einen Prompt an ein AI-Model und liefert Ergebnis.
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            prompt: User Prompt
            config: Optional Model Configuration
            
        Returns:
            TestResult Entity mit Response und Metrics
            
        Raises:
            ValueError: Wenn Model nicht gefunden
        """
        model = self.get_model_by_id(model_id)
        
        if not model:
            return TestResult(
                model_name=model_id,
                provider="Unknown",
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=0.0,
                success=False,
                error_message=f"Model '{model_id}' nicht gefunden"
            )
        
        adapter = self._get_adapter_for_provider(model.provider.name)
        
        if not adapter:
            return TestResult(
                model_name=model.name,
                provider=model.provider.display_name,
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=0.0,
                success=False,
                error_message=f"Adapter für Provider '{model.provider.name}' nicht gefunden"
            )
        
        # Use default config if not provided
        if config is None:
            config = ModelConfig()
        
        return await adapter.send_prompt(model.model_id, prompt, config)
    
    async def compare_models(
        self,
        model_ids: List[str],
        prompt: str,
        config: Optional[ModelConfig] = None
    ) -> List[TestResult]:
        """
        Use Case: Compare Multiple Models
        
        Sendet denselben Prompt an mehrere Modelle parallel.
        
        Args:
            model_ids: Liste von Model IDs
            prompt: User Prompt
            config: Optional Model Configuration
            
        Returns:
            Liste von TestResult Entities (eins pro Model)
        """
        # Run all tests in parallel
        tasks = [
            self.test_model(model_id, prompt, config)
            for model_id in model_ids
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    def _get_adapter_for_provider(self, provider_name: str) -> Optional[AIProviderAdapter]:
        """
        Get Adapter für Provider
        
        Args:
            provider_name: Provider Name (z.B. "openai")
            
        Returns:
            AIProviderAdapter oder None
        """
        return self._adapters.get(provider_name.lower())

