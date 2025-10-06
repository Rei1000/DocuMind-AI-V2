"""
Google AI (Gemini) Provider Adapter

Implementiert AIProviderAdapter für Google AI API.
"""

import os
import time
from typing import Optional
import google.generativeai as genai

from .base import AIProviderAdapter
from contexts.aiplayground.domain.entities import TestResult, ConnectionTest
from contexts.aiplayground.domain.value_objects import ModelConfig


class GoogleAIAdapter(AIProviderAdapter):
    """
    Adapter: Google AI (Gemini) API Integration
    
    Implementiert das AIProviderAdapter Interface für Google AI.
    
    Args:
        api_key: Google AI API Key (optional, default aus ENV)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google AI Adapter
        
        Args:
            api_key: Google AI API Key (falls None, wird aus ENV gelesen)
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
    
    @property
    def provider_name(self) -> str:
        return "Google AI"
    
    @property
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return self.api_key is not None and len(self.api_key) > 0
    
    async def test_connection(self, model_id: str) -> ConnectionTest:
        """
        Test Google AI API Connection
        
        Sendet einen minimalen Request um Verbindung zu testen.
        
        Args:
            model_id: Google AI Model ID (z.B. "gemini-pro")
            
        Returns:
            ConnectionTest Entity
        """
        if not self.is_configured:
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=False,
                error_message="Google AI API Key nicht konfiguriert"
            )
        
        start_time = time.time()
        
        try:
            # Minimaler Test-Request
            model = genai.GenerativeModel(model_id)
            response = model.generate_content("Hello")
            
            latency = time.time() - start_time
            
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=True,
                latency=latency
            )
            
        except Exception as e:
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=False,
                error_message=f"Google AI Error: {str(e)}"
            )
    
    async def send_prompt(
        self,
        model_id: str,
        prompt: str,
        config: ModelConfig
    ) -> TestResult:
        """
        Send Prompt to Google AI API
        
        Args:
            model_id: Google AI Model ID
            prompt: User Prompt
            config: Model Configuration
            
        Returns:
            TestResult Entity mit Response und Token Metrics
        """
        if not self.is_configured:
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=0.0,
                success=False,
                error_message="Google AI API Key nicht konfiguriert"
            )
        
        start_time = time.time()
        
        try:
            # Configure model
            model = genai.GenerativeModel(model_id)
            
            # Generation Config
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
                top_k=config.top_k if config.top_k else None
            )
            
            # Google AI API Call
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            elapsed = time.time() - start_time
            
            # Extract Response
            content = response.text if response.text else ""
            
            # Extract Token Usage (Google AI provides this)
            prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            completion_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            
            # Fallback: Estimate tokens if not provided
            if prompt_tokens == 0:
                prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
            if completion_tokens == 0:
                completion_tokens = len(content.split()) * 1.3
            
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response=content,
                tokens_sent=int(prompt_tokens),
                tokens_received=int(completion_tokens),
                response_time=elapsed,
                success=True
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=elapsed,
                success=False,
                error_message=f"Google AI Error: {str(e)}"
            )

