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
    
    def __init__(self, api_key: Optional[str] = None, api_key_env_var: str = "OPENAI_API_KEY"):
        """
        Initialize OpenAI Adapter
        
        Args:
            api_key: OpenAI API Key (falls None, wird aus ENV gelesen)
            api_key_env_var: Name der ENV-Variable für API-Key (default: OPENAI_API_KEY)
        """
        self.api_key_env_var = api_key_env_var
        self.api_key = api_key or os.getenv(api_key_env_var)
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
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> TestResult:
        """
        Send Prompt to OpenAI API (mit optional Bild)
        
        Args:
            model_id: OpenAI Model ID
            prompt: User Prompt
            config: Model Configuration
            image_data: Optional Base64-encoded image
            
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
            # Build message content (text or text+image)
            if image_data:
                # Vision API format with detail level
                detail = config.detail_level if hasattr(config, 'detail_level') else "high"
                content = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}",
                            "detail": detail  # "high" oder "low"
                        }
                    }
                ]
            else:
                # Text-only
                content = prompt
            
            # OpenAI API Call
            # GPT-5 models have different parameter requirements
            is_gpt5 = "gpt-5" in model_id.lower()
            
            api_params = {
                "model": model_id,
                "messages": [{"role": "user", "content": content}]
            }
            
            # GPT-5: temperature must be 1.0 (default), top_p not supported
            # GPT-4/older: full parameter support
            if is_gpt5:
                api_params["max_completion_tokens"] = config.max_tokens
                # Temperature must be 1.0 for GPT-5 (omit to use default)
                # top_p is not supported
            else:
                api_params["temperature"] = config.temperature
                api_params["max_tokens"] = config.max_tokens
                api_params["top_p"] = config.top_p
            
            response = await self.client.chat.completions.create(**api_params)
            
            elapsed = time.time() - start_time
            
            # Extract Response
            content = response.choices[0].message.content or ""
            
            # Extract Token Usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            
            # Token Breakdown (schätze Text vs. Bild)
            text_tokens = None
            image_tokens = None
            if image_data:
                # Schätze Text-Tokens (1 Wort ≈ 1.3 Tokens)
                estimated_text_tokens = int(len(prompt.split()) * 1.3)
                text_tokens = estimated_text_tokens
                image_tokens = prompt_tokens - estimated_text_tokens
            else:
                text_tokens = prompt_tokens
                image_tokens = 0
            
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response=content,
                tokens_sent=prompt_tokens,
                tokens_received=completion_tokens,
                response_time=elapsed,
                success=True,
                text_tokens=text_tokens,
                image_tokens=image_tokens
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

