"""
Google AI (Gemini) Provider Adapter

Implementiert AIProviderAdapter für Google AI API.
"""

import os
import time
import base64
import asyncio
from io import BytesIO
from typing import Optional
import google.generativeai as genai
from PIL import Image

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
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> TestResult:
        """
        Send Prompt to Google AI API (mit optional Bild)
        
        Args:
            model_id: Google AI Model ID
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
                error_message="Google AI API Key nicht konfiguriert"
            )
        
        start_time = time.time()
        
        try:
            # Safety Settings - Sehr permissiv für QMS-Dokumente (technische Inhalte)
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            # Configure model with safety settings
            model = genai.GenerativeModel(
                model_id,
                safety_settings=safety_settings
            )
            
            # Generation Config
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
                top_k=config.top_k if config.top_k else None
            )
            
            # Build content (text or text+image)
            if image_data:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
                # Google AI accepts [image, text] format
                content = [image, prompt]
            else:
                content = prompt
            
            # Google AI API Call (run in thread pool for async compatibility)
            # Google's SDK is synchronous, so we need to run it in an executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                lambda: model.generate_content(content, generation_config=generation_config)
            )
            
            elapsed = time.time() - start_time
            
            # Extract Response (handle safety blocks)
            try:
                content = response.text if response.text else ""
            except ValueError as e:
                # Response was blocked (e.g., safety filters)
                # Try to get the reason
                error_details = []
                
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else None
                    safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else []
                    
                    # Map finish reasons
                    finish_reason_names = {
                        0: "FINISH_REASON_UNSPECIFIED",
                        1: "STOP (normal completion)",
                        2: "MAX_TOKENS (length limit)",
                        3: "SAFETY (content blocked by safety filters)",
                        4: "RECITATION (content blocked due to recitation)",
                        5: "OTHER"
                    }
                    
                    reason_name = finish_reason_names.get(finish_reason, f"Unknown ({finish_reason})")
                    error_details.append(f"Finish Reason: {reason_name}")
                    
                    # Detailed safety ratings
                    if safety_ratings:
                        error_details.append("\nSafety Ratings:")
                        for rating in safety_ratings:
                            category = rating.category if hasattr(rating, 'category') else 'UNKNOWN'
                            probability = rating.probability if hasattr(rating, 'probability') else 'UNKNOWN'
                            blocked = rating.blocked if hasattr(rating, 'blocked') else False
                            error_details.append(f"  • {category}: {probability} (blocked: {blocked})")
                    
                    # Check prompt feedback (sometimes Gemini blocks the prompt itself)
                    if hasattr(response, 'prompt_feedback'):
                        pf = response.prompt_feedback
                        if hasattr(pf, 'block_reason') and pf.block_reason:
                            error_details.append(f"\nPrompt blocked: {pf.block_reason}")
                        if hasattr(pf, 'safety_ratings') and pf.safety_ratings:
                            error_details.append("\nPrompt Safety Ratings:")
                            for rating in pf.safety_ratings:
                                error_details.append(f"  • {rating.category}: {rating.probability}")
                    
                    error_msg = "\n".join(error_details) if error_details else f"Response blocked: {str(e)}"
                    
                    return TestResult(
                        model_name=model_id,
                        provider=self.provider_name,
                        prompt=prompt,
                        response="",
                        tokens_sent=0,
                        tokens_received=0,
                        response_time=elapsed,
                        success=False,
                        error_message=error_msg
                    )
                else:
                    return TestResult(
                        model_name=model_id,
                        provider=self.provider_name,
                        prompt=prompt,
                        response="",
                        tokens_sent=0,
                        tokens_received=0,
                        response_time=elapsed,
                        success=False,
                        error_message="No valid response returned (possibly blocked by safety filters)"
                    )
            
            # Extract Token Usage (Google AI provides this)
            prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            completion_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            
            # Fallback: Estimate tokens if not provided
            if prompt_tokens == 0:
                prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
            if completion_tokens == 0:
                completion_tokens = len(content.split()) * 1.3
            
            # Token Breakdown (schätze Text vs. Bild)
            text_tokens = None
            image_tokens = None
            if image_data:
                # Schätze Text-Tokens
                estimated_text_tokens = int(len(prompt.split()) * 1.3)
                text_tokens = estimated_text_tokens
                image_tokens = int(prompt_tokens) - estimated_text_tokens
            else:
                text_tokens = int(prompt_tokens)
                image_tokens = 0
            
            return TestResult(
                model_name=model_id,
                provider=self.provider_name,
                prompt=prompt,
                response=content,
                tokens_sent=int(prompt_tokens),
                tokens_received=int(completion_tokens),
                response_time=elapsed,
                success=True,
                text_tokens=text_tokens,
                image_tokens=image_tokens
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

