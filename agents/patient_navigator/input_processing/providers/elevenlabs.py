"""ElevenLabs translation provider implementation."""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
import time

try:
    import httpx
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("httpx not available - ElevenLabs provider will not work")

from ..types import TranslationProvider, TranslationResult, TranslationError

logger = logging.getLogger(__name__)


class ElevenLabsProvider(TranslationProvider):
    """ElevenLabs translation service provider."""
    
    def __init__(self, api_key: str):
        """Initialize the ElevenLabs provider.
        
        Args:
            api_key: ElevenLabs API key
        """
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        
        if not HTTP_AVAILABLE:
            raise RuntimeError("httpx library required for ElevenLabs provider")
        
        self.api_key = api_key
        self.provider_name = "elevenlabs"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # HTTP client configuration
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Supported languages based on ElevenLabs API
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi", "cs",
            "bg", "hr", "et", "lv", "lt", "sk", "sl", "hu", "ro", "el"
        ]
        
        logger.info("ElevenLabs provider initialized with real API integration")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en"
    ) -> TranslationResult:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: If translation fails
        """
        logger.debug(f"ElevenLabs translating '{text[:50]}...' from {source_lang} to {target_lang}")
        
        # Validate inputs
        if not text or not text.strip():
            raise TranslationError("Empty text provided for translation")
        
        # Validate language support
        if source_lang not in self.supported_languages:
            raise TranslationError(f"Source language '{source_lang}' not supported by ElevenLabs")
        
        if target_lang not in self.supported_languages:
            raise TranslationError(f"Target language '{target_lang}' not supported by ElevenLabs")
        
        # If same language, no translation needed
        if source_lang == target_lang:
            return TranslationResult(
                text=text,
                confidence=1.0,
                provider=self.provider_name,
                cost_estimate=0.0,
                source_language=source_lang,
                target_language=target_lang
            )
        
        # Rate limiting
        await self._enforce_rate_limit()
        
        # Prepare request
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # ElevenLabs translation request body
        request_body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        
        # Make API request with retries
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/text-translation",
                        headers=headers,
                        json=request_body
                    )
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        return self._parse_translation_response(
                            result_data, text, source_lang, target_lang
                        )
                    elif response.status_code == 429:
                        # Rate limited
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status_code == 401:
                        raise TranslationError("Invalid API key or authentication failed")
                    elif response.status_code == 400:
                        error_data = response.json() if response.content else {}
                        error_msg = error_data.get('detail', 'Bad request')
                        raise TranslationError(f"Invalid request: {error_msg}")
                    else:
                        error_msg = f"API request failed with status {response.status_code}"
                        logger.warning(f"{error_msg}, attempt {attempt + 1}/{self.max_retries}")
                        if attempt == self.max_retries - 1:
                            raise TranslationError(error_msg)
                        
            except httpx.TimeoutException:
                logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise TranslationError("Translation request timed out")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
            except httpx.RequestError as e:
                logger.warning(f"Request error: {e}, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise TranslationError(f"Network error: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                logger.error(f"Unexpected error during translation: {e}")
                raise TranslationError(f"Translation failed: {e}")
        
        # If we get here, all retries failed
        raise TranslationError("Translation failed after all retry attempts")
    
    def _parse_translation_response(
        self, 
        response_data: Dict[str, Any], 
        original_text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """Parse the ElevenLabs API response.
        
        Args:
            response_data: API response data
            original_text: Original input text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            TranslationResult with parsed data
        """
        try:
            translated_text = response_data.get("translated_text", "")
            
            # Calculate confidence based on response metadata
            confidence = response_data.get("confidence", 0.8)
            
            # If confidence not provided, estimate based on text similarity and length
            if "confidence" not in response_data:
                if len(translated_text) > 0:
                    length_ratio = len(translated_text) / len(original_text)
                    # Reasonable translations should have similar length (with some variance)
                    if 0.5 <= length_ratio <= 2.0:
                        confidence = 0.85
                    else:
                        confidence = 0.75
                else:
                    confidence = 0.0
            
            # Calculate cost
            cost_estimate = self.get_cost_estimate(original_text, source_lang, target_lang)
            
            result = TranslationResult(
                text=translated_text,
                confidence=confidence,
                provider=self.provider_name,
                cost_estimate=cost_estimate,
                source_language=source_lang,
                target_language=target_lang
            )
            
            logger.info(f"ElevenLabs translation successful: {len(translated_text)} chars, confidence {confidence}")
            return result
            
        except KeyError as e:
            logger.error(f"Missing field in translation response: {e}")
            raise TranslationError(f"Invalid response format: missing {e}")
        except Exception as e:
            logger.error(f"Error parsing translation response: {e}")
            raise TranslationError(f"Failed to parse translation response: {e}")
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def get_cost_estimate(self, text: str, source_lang: str, target_lang: str = "en") -> float:
        """Estimate cost for translation.
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code
            
        Returns:
            Estimated cost in USD
        """
        if source_lang == target_lang:
            return 0.0
        
        # ElevenLabs pricing estimate (placeholder)
        # Assume $0.01 per 100 characters for translation
        char_count = len(text)
        cost = (char_count / 100) * 0.01
        
        return round(cost, 4)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return self.supported_languages.copy()
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.provider_name
    
    async def health_check(self) -> bool:
        """Check if the provider service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        logger.debug("Performing ElevenLabs health check")
        
        if not HTTP_AVAILABLE:
            logger.warning("HTTP client not available")
            return False
        
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Accept": "application/json"
            }
            
            # Use a simple endpoint to check API availability
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/user",
                    headers=headers
                )
                
                is_healthy = response.status_code == 200
                logger.debug(f"ElevenLabs health check result: {is_healthy} (status: {response.status_code})")
                return is_healthy
                
        except Exception as e:
            logger.warning(f"ElevenLabs health check failed: {e}")
            return False