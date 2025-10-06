"""
OpenAI Provider Adapter

Implementiert AIProviderAdapter für OpenAI API.
"""

import os
import time
from typing import Optional
from openai import AsyncOpenAI, OpenAIError

from .base import AIProviderAdapter
from contexts.aiplayground.domain.entities import TestResult, ConnectionTest
from contexts.aiplayground.domain.value_objects import ModelConfig


class OpenAIAdapter(AIProviderAdapter):
    """
    Adapter: OpenAI API Integration
    
    Implementiert das AIProviderAdapter Interface für OpenAI.
    
    Args:
        api_key: OpenAI API Key (optional, default aus ENV)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI Adapter
        
        Args:
            api_key: OpenAI API Key (falls None, wird aus ENV gelesen)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    @property
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return self.api_key is not None and len(self.api_key) > 0
    
    async def test_connection(self, model_id: str) -> ConnectionTest:
        """
        Test OpenAI API Connection
        
        Sendet einen minimalen Request um Verbindung zu testen.
        
        Args:
            model_id: OpenAI Model ID (z.B. "gpt-3.5-turbo")
            
        Returns:
            ConnectionTest Entity
        """
        if not self.is_configured:
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=False,
                error_message="OpenAI API Key nicht konfiguriert"
            )
        
        start_time = time.time()
        
        try:
            # Minimaler Test-Request
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            latency = time.time() - start_time
            
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=True,
                latency=latency
            )
            
        except OpenAIError as e:
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=False,
                error_message=f"OpenAI Error: {str(e)}"
            )
        except Exception as e:
            return ConnectionTest(
                provider=self.provider_name,
                model_name=model_id,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def send_prompt(
        self,
        model_id: str,
        prompt: str,
        config: ModelConfig
    ) -> TestResult:
        """
        Send Prompt to OpenAI API
        
        Args:
            model_id: OpenAI Model ID
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
                error_message="OpenAI API Key nicht konfiguriert"
            )
        
        start_time = time.time()
        
        try:
            # OpenAI API Call
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p
            )
            
            elapsed = time.time() - start_time
            
            # Extract Response
            content = response.choices[0].message.content or ""
            
            # Extract Token Usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response=content,
                tokens_sent=prompt_tokens,
                tokens_received=completion_tokens,
                response_time=elapsed,
                success=True
            )
            
        except OpenAIError as e:
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
                error_message=f"OpenAI Error: {str(e)}"
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
                error_message=f"Unexpected error: {str(e)}"
            )

