"""
AI Playground Service

Application Service - Orchestriert Use Cases und Provider Adapters.
"""

from typing import List, Dict, Optional, AsyncGenerator
import asyncio

from contexts.aiplayground.domain.entities import TestResult, ConnectionTest, StreamingChunk
from contexts.aiplayground.domain.value_objects import (
    ModelConfig,
    ModelDefinition,
    AVAILABLE_MODELS,
    OPENAI_PROVIDER,
    OPENAI_GPT5_PROVIDER,
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
            "openai_gpt5": OpenAIAdapter(api_key_env_var="OPENAI_GPT5_MINI_API_KEY"),
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
    
    def _find_model_by_id(self, model_id: str) -> Optional[ModelDefinition]:
        """
        Private Helper: Finde Model Definition by ID
        
        Args:
            model_id: Model ID (z.B. "gpt-4o-mini")
            
        Returns:
            ModelDefinition oder None wenn nicht gefunden
        """
        return self.get_model_by_id(model_id)
    
    async def test_model(
        self,
        model_id: str,
        prompt: str,
        config: Optional[ModelConfig] = None,
        image_data: Optional[str] = None
    ) -> TestResult:
        """
        Use Case: Test Model mit Prompt (und optional Bild)
        
        Sendet einen Prompt an ein AI-Model und liefert Ergebnis.
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            prompt: User Prompt
            config: Optional Model Configuration
            image_data: Optional Base64-encoded image
            
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
        
        return await adapter.send_prompt(model.model_id, prompt, config, image_data=image_data)
    
    async def compare_models(
        self,
        model_ids: List[str],
        prompt: str,
        config: Optional[ModelConfig] = None,
        image_data: Optional[str] = None
    ) -> List[TestResult]:
        """
        Use Case: Compare Multiple Models
        
        Sendet denselben Prompt an mehrere Modelle parallel.
        Mit 180s Timeout pro Modell.
        
        Args:
            model_ids: Liste von Model IDs
            prompt: User Prompt
            config: Optional Model Configuration
            image_data: Optional Base64-encoded image
            
        Returns:
            Liste von TestResult Entities (eins pro Model)
        """
        # Run all tests in parallel with timeout per model
        async def test_with_timeout(model_id: str):
            try:
                return await asyncio.wait_for(
                    self.test_model(model_id, prompt, config, image_data),
                    timeout=240.0  # 4 minutes timeout per model (für komplexe Prompts + Bilder)
                )
            except asyncio.TimeoutError:
                model = self.get_model_by_id(model_id)
                return TestResult(
                    model_name=model.name if model else model_id,
                    provider=model.provider.display_name if model else "Unknown",
                    prompt=prompt,
                    response="",
                    tokens_sent=0,
                    tokens_received=0,
                    response_time=240.0,
                    success=False,
                    error_message="Timeout: Modell hat nach 4 Minuten nicht geantwortet"
                )
        
        tasks = [test_with_timeout(model_id) for model_id in model_ids]
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
    
    async def test_model_stream(
        self, 
        model_id: str, 
        prompt: str, 
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Use Case: Test Model with Streaming
        
        Testet ein AI-Modell mit Streaming-Response.
        Gibt Chunks zurück, sobald sie verfügbar sind.
        
        Args:
            model_id: Model ID (z.B. "gpt-4o-mini")
            prompt: Der Prompt-Text
            config: Model-Konfiguration
            image_data: Optional: Base64-encoded image
            
        Yields:
            StreamingChunk: Einzelne Chunks der Response
        """
        # Finde das Modell
        model_def = self._find_model_by_id(model_id)
        if not model_def:
            yield StreamingChunk(
                content=f"❌ Modell '{model_id}' nicht gefunden",
                is_final=True,
                model_name=model_id,
                provider="unknown"
            )
            return
        
        # Hole den Provider Adapter
        adapter = self._get_adapter_for_provider(model_def.provider.name)
        if not adapter:
            yield StreamingChunk(
                content=f"❌ Provider '{model_def.provider.name}' nicht verfügbar",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name  # Convert to string
            )
            return
        
        try:
            print(f"[SERVICE] Starting streaming for model: {model_id}")
            # Starte Streaming
            chunk_index = 0
            async for chunk_content in adapter.test_model_stream(
                model_id=model_id,
                prompt=prompt,
                config=config,
                image_data=image_data
            ):
                print(f"[SERVICE] Received chunk {chunk_index}: '{chunk_content}'")
                yield StreamingChunk(
                    content=chunk_content,
                    is_final=False,
                    model_name=model_def.name,
                    provider=model_def.provider.name,  # Convert to string
                    chunk_index=chunk_index
                )
                chunk_index += 1
            
            print(f"[SERVICE] Streaming completed with {chunk_index} chunks")
            # Finaler Chunk mit Token-Metriken
            yield StreamingChunk(
                content="",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name,  # Convert to string
                chunk_index=chunk_index
            )
            
        except Exception as e:
            yield StreamingChunk(
                content=f"❌ Fehler beim Streaming: {str(e)}",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name  # Convert to string
            )

