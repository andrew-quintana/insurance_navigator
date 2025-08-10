"""Translation Router implementation for managing translation services."""

import asyncio
import logging
from typing import Dict, Optional
from functools import lru_cache

from .types import TranslationResult, TranslationProvider, TranslationError
from .config import get_translation_config
from .providers.elevenlabs import ElevenLabsProvider
from .providers.flash import FlashProvider

logger = logging.getLogger(__name__)


class TranslationRouter:
    """Router for translation services with fallback support."""
    
    def __init__(self):
        """Initialize the translation router."""
        self.config = get_translation_config()
        self.providers: Dict[str, TranslationProvider] = {}
        self.source_language = self.config["default_language"]
        self.target_language = self.config["target_language"]
        
        self._initialize_providers()
        logger.info(f"Translation router initialized with providers: {list(self.providers.keys())}")
    
    def _initialize_providers(self):
        """Initialize available translation providers."""
        provider_configs = self.config["providers"]
        
        # Initialize ElevenLabs if API key available
        if "elevenlabs" in provider_configs and provider_configs["elevenlabs"]:
            try:
                self.providers["elevenlabs"] = ElevenLabsProvider(provider_configs["elevenlabs"])
                logger.info("ElevenLabs provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs provider: {e}")
        
        # Initialize Flash if API key available
        if "flash" in provider_configs and provider_configs["flash"]:
            try:
                self.providers["flash"] = FlashProvider(provider_configs["flash"])
                logger.info("Flash provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Flash provider: {e}")
        
        if not self.providers:
            logger.warning("No translation providers initialized - translation will not work")
    
    async def route(self, text: str, source_language: Optional[str] = None) -> TranslationResult:
        """Route translation request to optimal provider.
        
        Args:
            text: Text to translate
            source_language: Source language (defaults to configured default)
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: If all providers fail
        """
        if not text.strip():
            raise TranslationError("Empty text provided for translation")
        
        source_lang = source_language or self.source_language
        target_lang = self.target_language
        
        # If source and target are the same, no translation needed
        if source_lang == target_lang:
            logger.debug("Source and target languages are the same - no translation needed")
            return TranslationResult(
                text=text,
                confidence=1.0,
                provider="no_translation_needed",
                cost_estimate=0.0,
                source_language=source_lang,
                target_language=target_lang
            )
        
        # Check cache first
        cache_key = f"{text}:{source_lang}:{target_lang}"
        cached_result = self._get_cached_translation(cache_key)
        if cached_result:
            logger.debug("Using cached translation")
            return cached_result
        
        # Try providers in priority order
        provider_order = self.config["provider_priority"]
        last_error = None
        
        for provider_name in provider_order:
            if provider_name not in self.providers:
                logger.warning(f"Provider {provider_name} not available, skipping")
                continue
            
            provider = self.providers[provider_name]
            
            try:
                # Check provider health first
                if not await provider.health_check():
                    logger.warning(f"Provider {provider_name} health check failed, skipping")
                    continue
                
                logger.info(f"Attempting translation with provider: {provider_name}")
                result = await provider.translate(text, source_lang, target_lang)
                
                # Validate translation quality
                if result.confidence < self.config["min_confidence"]:
                    logger.warning(f"Translation confidence {result.confidence} below threshold {self.config['min_confidence']}")
                    continue
                
                # Cache successful translation
                self._cache_translation(cache_key, result)
                
                logger.info(f"Translation successful with provider {provider_name}")
                return result
                
            except Exception as e:
                logger.error(f"Translation failed with provider {provider_name}: {e}")
                last_error = e
                continue
        
        # If all providers failed
        error_msg = f"All translation providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise TranslationError(error_msg)
    
    def set_source_language(self, language: str) -> None:
        """Set the source language configuration.
        
        Args:
            language: ISO language code
        """
        if not language or not isinstance(language, str):
            raise ValueError("Language must be a non-empty string")
        
        self.source_language = language
        logger.info(f"Source language set to: {language}")
    
    def get_source_language(self) -> str:
        """Get current source language configuration."""
        return self.source_language
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of available providers."""
        return {name: name in self.providers for name in ["elevenlabs", "flash"]}
    
    @lru_cache(maxsize=1000)
    def _get_cached_translation(self, cache_key: str) -> Optional[TranslationResult]:
        """Get cached translation result.
        
        Note: This is a simple in-memory cache for Phase 1.
        In Phase 2, implement proper cache management with TTL.
        """
        # Placeholder for cache lookup
        # In Phase 2, implement proper caching with TTL
        return None
    
    def _cache_translation(self, cache_key: str, result: TranslationResult) -> None:
        """Cache translation result.
        
        Note: This is a placeholder for Phase 1.
        In Phase 2, implement proper cache storage with TTL.
        """
        # Placeholder for cache storage
        # In Phase 2, implement proper caching with TTL
        pass
    
    async def get_cost_estimate(self, text: str, source_language: Optional[str] = None) -> float:
        """Get cost estimate for translation.
        
        Args:
            text: Text to translate
            source_language: Source language (defaults to configured default)
            
        Returns:
            Estimated cost in USD
        """
        if not text.strip():
            return 0.0
        
        source_lang = source_language or self.source_language
        
        # If no translation needed
        if source_lang == self.target_language:
            return 0.0
        
        # Get estimate from preferred provider
        provider_order = self.config["provider_priority"]
        
        for provider_name in provider_order:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                try:
                    return provider.get_cost_estimate(text, source_lang, self.target_language)
                except Exception as e:
                    logger.warning(f"Cost estimate failed for {provider_name}: {e}")
                    continue
        
        # Fallback estimate
        return 0.01  # $0.01 default estimate