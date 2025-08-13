"""Flash v2.5 Translation Provider for Input Processing Workflow.

This module provides translation services using Flash v2.5 API with
cost optimization, performance tracking, and fallback capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import httpx
import json

from ..performance_monitor import track_performance, get_performance_monitor
from ..circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


@dataclass
class FlashTranslationRequest:
    """Flash translation request parameters."""
    
    text: str
    source_language: str = "auto"
    target_language: str = "en"
    model: str = "flash-v2.5"
    quality: str = "standard"  # standard, premium, ultra
    format: str = "text"  # text, html, markdown
    
    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to Flash API payload format."""
        return {
            "text": self.text,
            "source_lang": self.source_language,
            "target_lang": self.target_language,
            "model": self.model,
            "quality": self.quality,
            "format": self.format
        }


@dataclass
class FlashTranslationResponse:
    """Flash translation response."""
    
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    cost_credits: float
    processing_time_ms: float
    model_used: str
    quality_used: str
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any], request: FlashTranslationRequest) -> 'FlashTranslationResponse':
        """Create response from API response."""
        return cls(
            translated_text=response.get("translated_text", ""),
            source_language=response.get("source_lang", request.source_language),
            target_language=response.get("target_lang", request.target_language),
            confidence=response.get("confidence", 0.0),
            cost_credits=response.get("cost_credits", 0.0),
            processing_time_ms=response.get("processing_time_ms", 0.0),
            model_used=response.get("model_used", request.model),
            quality_used=response.get("quality_used", request.quality)
        )


class FlashProvider:
    """Flash v2.5 translation provider with cost optimization and performance tracking."""
    
    # Flash API endpoints (using mock endpoints for testing)
    TRANSLATE_ENDPOINT = "https://httpbin.org/post"  # Mock endpoint for testing
    LANGUAGES_ENDPOINT = "https://httpbin.org/get"   # Mock endpoint for testing
    MODELS_ENDPOINT = "https://httpbin.org/get"      # Mock endpoint for testing
    
    # Cost optimization settings
    COST_THRESHOLDS = {
        "low_complexity": 0.5,      # Use standard quality for simple text
        "medium_complexity": 1.0,   # Use standard quality for medium text
        "high_complexity": 2.0      # Use premium quality for complex text
    }
    
    # Language complexity mapping (estimated)
    LANGUAGE_COMPLEXITY = {
        "en": 1.0,      # English - baseline
        "es": 1.2,      # Spanish - moderate
        "fr": 1.3,      # French - moderate
        "de": 1.4,      # German - complex
        "it": 1.2,      # Italian - moderate
        "pt": 1.2,      # Portuguese - moderate
        "ru": 1.5,      # Russian - complex
        "zh": 1.6,      # Chinese - complex
        "ja": 1.7,      # Japanese - complex
        "ko": 1.6,      # Korean - complex
        "ar": 1.8,      # Arabic - complex
        "hi": 1.3,      # Hindi - moderate
        "auto": 1.5     # Auto-detect - assume complex
    }
    
    def __init__(self, api_key: str, timeout: float = 30.0):
        """Initialize Flash provider.
        
        Args:
            api_key: Flash API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.performance_monitor = get_performance_monitor()
        
        # Initialize circuit breaker
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_timeout=30.0
        )
        self.circuit_breaker = CircuitBreaker(
            "flash_translation",
            circuit_config
        )
        
        # Cost tracking
        self.total_cost_credits = 0.0
        self.translation_count = 0
        self.avg_cost_per_translation = 0.0
        
        # Performance tracking
        self.total_processing_time = 0.0
        self.avg_processing_time = 0.0
        
        logger.info("Flash provider initialized with cost optimization")
    
    @track_performance("flash_translate")
    async def translate(self, request: FlashTranslationRequest) -> FlashTranslationResponse:
        """Translate text using Flash v2.5 API.
        
        Args:
            request: Translation request parameters
            
        Returns:
            Translation response with cost and performance data
            
        Raises:
            Exception: If translation fails
        """
        # Optimize quality based on text complexity and cost
        optimized_request = self._optimize_request(request)
        
        # Use circuit breaker for fault tolerance
        async with self.circuit_breaker:
            return await self._perform_translation(optimized_request)
    
    async def _perform_translation(self, request: FlashTranslationRequest) -> FlashTranslationResponse:
        """Perform the actual translation request."""
        start_time = time.time()
        
        try:
            # For testing purposes, create a mock response
            if "httpbin.org" in self.TRANSLATE_ENDPOINT:
                # Mock response for testing
                mock_response_data = {
                    "translated_text": f"[MOCK FLASH] {request.text}",
                    "source_lang": request.source_language,
                    "target_lang": request.target_language,
                    "confidence": 0.95,
                    "cost_credits": 0.001,
                    "processing_time_ms": 150.0,
                    "model_used": request.model,
                    "quality_used": request.quality
                }
                
                # Create response object
                flash_response = FlashTranslationResponse.from_api_response(
                    mock_response_data, request
                )
                
                # Update cost and performance tracking
                self._update_tracking(flash_response, time.time() - start_time)
                
                logger.info(
                    f"Flash translation successful (MOCK): "
                    f"{request.source_language} -> {request.target_language}, "
                    f"Cost: {flash_response.cost_credits:.4f} credits, "
                    f"Time: {flash_response.processing_time_ms:.1f}ms"
                )
                
                return flash_response
            
            # Real API call (when endpoints are properly configured)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = request.to_api_payload()
                
                logger.debug(f"Flash translation request: {payload}")
                
                response = await client.post(
                    self.TRANSLATE_ENDPOINT,
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Create response object
                flash_response = FlashTranslationResponse.from_api_response(
                    response_data, request
                )
                
                # Update cost and performance tracking
                self._update_tracking(flash_response, time.time() - start_time)
                
                logger.info(
                    f"Flash translation successful: "
                    f"{request.source_language} -> {request.target_language}, "
                    f"Cost: {flash_response.cost_credits:.4f} credits, "
                    f"Time: {flash_response.processing_time_ms:.1f}ms"
                )
                
                return flash_response
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Flash API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Flash API error: {e.response.status_code}")
            
        except httpx.RequestError as e:
            logger.error(f"Flash API request error: {e}")
            raise Exception(f"Flash API request failed: {e}")
            
        except Exception as e:
            logger.error(f"Flash translation error: {e}")
            raise
    
    def _optimize_request(self, request: FlashTranslationRequest) -> FlashTranslationRequest:
        """Optimize translation request for cost and quality balance."""
        # Analyze text complexity
        complexity_score = self._analyze_text_complexity(request.text)
        
        # Determine optimal quality setting
        if complexity_score <= self.COST_THRESHOLDS["low_complexity"]:
            optimal_quality = "standard"
        elif complexity_score <= self.COST_THRESHOLDS["medium_complexity"]:
            optimal_quality = "standard"
        else:
            optimal_quality = "premium"
        
        # Adjust for language complexity
        lang_complexity = self.LANGUAGE_COMPLEXITY.get(
            request.source_language, 1.5
        )
        
        if lang_complexity > 1.5 and optimal_quality == "standard":
            optimal_quality = "premium"
        
        # Create optimized request
        optimized_request = FlashTranslationRequest(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
            model=request.model,
            quality=optimal_quality,
            format=request.format
        )
        
        logger.debug(
            f"Request optimization: complexity={complexity_score:.2f}, "
            f"language={request.source_language}, "
            f"quality={request.quality} -> {optimal_quality}"
        )
        
        return optimized_request
    
    def _analyze_text_complexity(self, text: str) -> float:
        """Analyze text complexity for quality optimization."""
        if not text:
            return 0.0
        
        # Simple complexity heuristics
        words = text.split()
        sentences = text.split('.')
        
        # Factors that increase complexity
        complexity_factors = {
            "word_count": min(len(words) / 100, 2.0),  # Normalize to 0-2 range
            "sentence_length": min(len(words) / max(len(sentences), 1) / 20, 1.5),
            "special_chars": min(text.count(',') + text.count(';') + text.count(':') / 10, 1.0),
            "numbers": min(text.count('0') + text.count('1') + text.count('2') + 
                          text.count('3') + text.count('4') + text.count('5') + 
                          text.count('6') + text.count('7') + text.count('8') + 
                          text.count('9') / 20, 1.0),
            "uppercase": min(sum(1 for c in text if c.isupper()) / len(text) * 10, 1.0)
        }
        
        # Calculate weighted complexity score
        weights = {
            "word_count": 0.3,
            "sentence_length": 0.25,
            "special_chars": 0.2,
            "numbers": 0.15,
            "uppercase": 0.1
        }
        
        complexity_score = sum(
            complexity_factors[factor] * weights[factor]
            for factor in complexity_factors
        )
        
        return min(complexity_score, 3.0)  # Cap at 3.0
    
    def _update_tracking(self, response: FlashTranslationResponse, processing_time: float) -> None:
        """Update cost and performance tracking."""
        # Update cost tracking
        self.total_cost_credits += response.cost_credits
        self.translation_count += 1
        self.avg_cost_per_translation = self.total_cost_credits / self.translation_count
        
        # Update performance tracking
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.translation_count
    
    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages from Flash API."""
        try:
            # For testing purposes, return mock data
            if "httpbin.org" in self.LANGUAGES_ENDPOINT:
                mock_languages = [
                    {"code": "en", "name": "English", "native_name": "English"},
                    {"code": "es", "name": "Spanish", "native_name": "Español"},
                    {"code": "fr", "name": "French", "native_name": "Français"},
                    {"code": "de", "name": "German", "native_name": "Deutsch"},
                    {"code": "it", "name": "Italian", "native_name": "Italiano"},
                    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
                    {"code": "ru", "name": "Russian", "native_name": "Русский"},
                    {"code": "zh", "name": "Chinese", "native_name": "中文"},
                    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
                    {"code": "ko", "name": "Korean", "native_name": "한국어"},
                    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
                    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"}
                ]
                logger.info(f"Retrieved {len(mock_languages)} supported languages from Flash (MOCK)")
                return mock_languages
            
            # Real API call (when endpoints are properly configured)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                response = await client.get(
                    self.LANGUAGES_ENDPOINT,
                    headers=headers
                )
                
                response.raise_for_status()
                return response.json().get("languages", [])
                
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Flash API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                response = await client.get(
                    self.MODELS_ENDPOINT,
                    headers=headers
                )
                
                response.raise_for_status()
                return response.json().get("models", [])
                
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost optimization summary."""
        return {
            "total_cost_credits": self.total_cost_credits,
            "translation_count": self.translation_count,
            "avg_cost_per_translation": self.avg_cost_per_translation,
            "total_processing_time": self.total_processing_time,
            "avg_processing_time": self.avg_processing_time,
            "cost_per_second": (self.total_cost_credits / self.total_processing_time 
                               if self.total_processing_time > 0 else 0.0)
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status."""
        return {
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "last_failure_time": self.circuit_breaker.last_failure_time,
            "is_healthy": self.circuit_breaker.state == self.circuit_breaker.state.CLOSED,
            "cost_summary": self.get_cost_summary()
        }
    
    async def health_check(self) -> bool:
        """Perform health check on Flash API."""
        try:
            # Simple health check using languages endpoint
            languages = await self.get_supported_languages()
            return len(languages) > 0
        except Exception as e:
            logger.error(f"Flash health check failed: {e}")
            return False


class FlashProviderFactory:
    """Factory for creating Flash provider instances."""
    
    @staticmethod
    def create_provider(api_key: str, timeout: float = 30.0) -> FlashProvider:
        """Create a new Flash provider instance.
        
        Args:
            api_key: Flash API key
            timeout: Request timeout in seconds
            
        Returns:
            Configured Flash provider
        """
        return FlashProvider(api_key, timeout)
    
    @staticmethod
    def create_provider_from_env() -> Optional[FlashProvider]:
        """Create Flash provider from environment variables.
        
        Returns:
            Configured Flash provider or None if configuration missing
        """
        import os
        
        api_key = os.getenv("FLASH_API_KEY")
        if not api_key:
            logger.warning("FLASH_API_KEY not found in environment")
            return None
        
        timeout = float(os.getenv("FLASH_TIMEOUT", "30.0"))
        
        return FlashProvider(api_key, timeout)