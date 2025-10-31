"""
OpenAI Provider Adapter

Implementiert AIProviderAdapter für OpenAI API.
"""

import os
import time
import asyncio
import base64
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI, OpenAIError
from io import BytesIO

from .base import AIProviderAdapter
from contexts.aiplayground.domain.entities import TestResult, ConnectionTest
from contexts.aiplayground.domain.value_objects import ModelConfig

# PDF to Image conversion (for OpenAI which doesn't support PDF directly)
try:
    from pdf2image import convert_from_bytes
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("[OPENAI] WARNING: pdf2image not installed, PDF conversion disabled")


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
            request_params = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            # Use max_completion_tokens for newer models (GPT-4o, GPT-5), max_tokens for older
            if model_id in ["gpt-4o", "gpt-4o-mini"] or "gpt-5" in model_id.lower():
                request_params["max_completion_tokens"] = 5
            else:
                request_params["max_tokens"] = 5
                
            response = await self.client.chat.completions.create(**request_params)
            
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
                # Decode base64 to check file type
                image_bytes = base64.b64decode(image_data)
                
                # Check if it's a PDF (PDFs start with %PDF- signature)
                is_pdf = image_bytes[:4] == b'%PDF'
                
                if is_pdf:
                    # OpenAI doesn't support PDF directly - convert first page to PNG
                    if not PDF_SUPPORT:
                        return TestResult(
                            model_name=model_id,
                            provider=self.provider_name,
                            prompt=prompt,
                            response="",
                            tokens_sent=0,
                            tokens_received=0,
                            response_time=0.0,
                            success=False,
                            error_message="PDF conversion not available (pdf2image not installed). Please convert PDF to PNG manually."
                        )
                    
                    try:
                        # Convert first page of PDF to PNG image
                        # Run in executor as pdf2image can be slow
                        loop = asyncio.get_event_loop()
                        images = await loop.run_in_executor(
                            None,
                            lambda: convert_from_bytes(image_bytes, first_page=1, last_page=1, dpi=300)
                        )
                        
                        if not images or len(images) == 0:
                            raise ValueError("PDF conversion failed - no pages extracted")
                        
                        # Convert PIL Image to PNG bytes
                        png_buffer = BytesIO()
                        images[0].save(png_buffer, format='PNG')
                        png_bytes = png_buffer.getvalue()
                        
                        # Encode PNG as base64
                        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
                        
                        # Use PNG for OpenAI
                        detail = config.detail_level if hasattr(config, 'detail_level') else "high"
                        content = [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{png_base64}",
                                    "detail": detail
                                }
                            }
                        ]
                    except Exception as e:
                        return TestResult(
                            model_name=model_id,
                            provider=self.provider_name,
                            prompt=prompt,
                            response="",
                            tokens_sent=0,
                            tokens_received=0,
                            response_time=0.0,
                            success=False,
                            error_message=f"PDF conversion failed: {str(e)}"
                        )
                else:
                    # Regular image - determine MIME type from file signature
                    # Check if it's PNG, JPEG, GIF, or WEBP
                    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                        mime_type = "image/png"
                    elif image_bytes[:2] == b'\xff\xd8':
                        mime_type = "image/jpeg"
                    elif image_bytes[:6] == b'GIF87a' or image_bytes[:6] == b'GIF89a':
                        mime_type = "image/gif"
                    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
                        mime_type = "image/webp"
                    else:
                        # Default to PNG (legacy behavior)
                        mime_type = "image/png"
                    
                    # Vision API format with detail level
                    detail = config.detail_level if hasattr(config, 'detail_level') else "high"
                    content = [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": detail  # "high" oder "low"
                            }
                        }
                    ]
            else:
                # Text-only
                content = prompt
            
            # OpenAI API Call
            # Prepare base parameters
            api_params = {
                "model": model_id,
                "messages": [{"role": "user", "content": content}]
            }
            
            # Model-specific parameter handling
            # GPT-4o and GPT-5 series use max_completion_tokens
            # Older models use max_tokens
            if model_id in ["gpt-4o", "gpt-4o-mini"] or "gpt-5" in model_id.lower():
                api_params["max_completion_tokens"] = config.max_tokens
            else:
                api_params["max_tokens"] = config.max_tokens
            
            # Temperature and top_p für alle Modelle außer GPT-5
            # (GPT-5 nutzt eigene Defaults)
            if "gpt-5" not in model_id.lower():
                api_params["temperature"] = config.temperature
                api_params["top_p"] = config.top_p
            
            response = await self.client.chat.completions.create(**api_params)
            
            elapsed = time.time() - start_time
            
            # Extract Response
            content = response.choices[0].message.content or ""
            
            # Extract Model Verification (tatsächlich verwendetes Modell)
            verified_model = response.model if hasattr(response, 'model') else None
            
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
                image_tokens=image_tokens,
                verified_model_id=verified_model
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
    
    async def test_model_stream(
        self,
        model_id: str,
        prompt: str,
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        OpenAI Streaming Implementation
        
        Args:
            model_id: Model ID (z.B. "gpt-4o-mini")
            prompt: User Prompt
            config: Model Configuration
            image_data: Optional Base64-encoded image
            
        Yields:
            str: Einzelne Chunks der Response
        """
        if not self.is_configured:
            yield "❌ OpenAI API Key nicht konfiguriert"
            return
        
        # GPT-5 models don't support streaming (requires verified organization)
        # Fallback to non-streaming mode
        if "gpt-5" in model_id.lower():
            print(f"[OPENAI] GPT-5 streaming not supported, using non-streaming mode")
            try:
                # Use regular send_prompt and yield result at once
                result = await self.send_prompt(model_id, prompt, config, image_data)
                if result.success:
                    yield result.response
                else:
                    yield f"❌ {result.error_message}"
            except Exception as e:
                yield f"❌ Error: {str(e)}"
            return
        
        try:
            print(f"[OPENAI] Starting stream for model: {model_id}")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Add image if provided
            if image_data:
                # Decode base64 to check file type
                image_bytes = base64.b64decode(image_data)
                
                # Check if it's a PDF
                is_pdf = image_bytes[:4] == b'%PDF'
                
                if is_pdf:
                    # Convert PDF first page to PNG
                    if not PDF_SUPPORT:
                        yield f"❌ PDF conversion not available (pdf2image not installed)"
                        return
                    
                    try:
                        loop = asyncio.get_event_loop()
                        images = await loop.run_in_executor(
                            None,
                            lambda: convert_from_bytes(image_bytes, first_page=1, last_page=1, dpi=300)
                        )
                        
                        if not images or len(images) == 0:
                            yield f"❌ PDF conversion failed - no pages extracted"
                            return
                        
                        # Convert PIL Image to PNG bytes
                        png_buffer = BytesIO()
                        images[0].save(png_buffer, format='PNG')
                        png_bytes = png_buffer.getvalue()
                        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
                        
                        image_data = png_base64
                    except Exception as e:
                        yield f"❌ PDF conversion failed: {str(e)}"
                        return
                
                # Determine MIME type for images
                if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                    mime_type = "image/png"
                elif image_bytes[:2] == b'\xff\xd8':
                    mime_type = "image/jpeg"
                elif image_bytes[:6] == b'GIF87a' or image_bytes[:6] == b'GIF89a':
                    mime_type = "image/gif"
                elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
                    mime_type = "image/webp"
                else:
                    mime_type = "image/png"
                
                messages[0]["content"] = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                            "detail": config.detail_level
                        }
                    }
                ]
            
            # Prepare request parameters
            request_params = {
                "model": model_id,
                "messages": messages,
                "stream": True  # Enable streaming
            }
            
            # Use max_completion_tokens for newer models (GPT-4o, GPT-5), max_tokens for older
            if model_id in ["gpt-4o", "gpt-4o-mini"] or "gpt-5" in model_id.lower():
                request_params["max_completion_tokens"] = config.max_tokens
            else:
                request_params["max_tokens"] = config.max_tokens
            
            # Temperature and top_p nur für nicht-GPT-5 Modelle
            if "gpt-5" not in model_id.lower():
                request_params["temperature"] = config.temperature
                request_params["top_p"] = config.top_p
            
            # Add structured JSON output if requested
            if "json" in prompt.lower() or "structure" in prompt.lower():
                request_params["response_format"] = {"type": "json_object"}
                print(f"[OPENAI] JSON mode enabled for structured output")
            
            print(f"[OPENAI] Request params: {request_params}")
            
            # Stream response
            stream = await self.client.chat.completions.create(**request_params)
            
            chunk_count = 0
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    chunk_count += 1
                    content = chunk.choices[0].delta.content
                    print(f"[OPENAI] Chunk {chunk_count}: '{content}'")
                    yield content
                    
            print(f"[OPENAI] Stream completed with {chunk_count} chunks")
                    
        except OpenAIError as e:
            print(f"[OPENAI] API Error: {str(e)}")
            yield f"❌ OpenAI API Error: {str(e)}"
        except Exception as e:
            print(f"[OPENAI] Unexpected error: {str(e)}")
            yield f"❌ Unexpected error: {str(e)}"

