"""Translation Router implementation for managing translation services."""

import asyncio
import logging
import hashlib
import time
from typing import Dict, Optional
from functools import lru_cache
from collections import OrderedDict

from .types import TranslationResult, TranslationProvider, TranslationError, CacheEntry
from .config import get_translation_config, get_cache_config
from .providers.elevenlabs import ElevenLabsProvider
from .providers.flash import FlashProvider
from .providers.mock import MockTranslationProvider

logger = logging.getLogger(__name__)


class TranslationRouter:
    """Router for translation services with fallback support."""
    
    def __init__(self):
        """Initialize the translation router."""
        self.config = get_translation_config()
        self.cache_config = get_cache_config()
        self.providers: Dict[str, TranslationProvider] = {}
        self.source_language = self.config["default_language"]
        self.target_language = self.config["target_language"]
        
        # Initialize LRU cache
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_size = self.cache_config["size"]
        self.cache_ttl = self.cache_config["ttl"]
        
        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        
        self._initialize_providers()
        logger.info(f"Translation router initialized with providers: {list(self.providers.keys())}")
        logger.info(f"Cache initialized: size={self.cache_size}, TTL={self.cache_ttl}s")
    
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
        
        # Add mock provider as fallback if no real providers available
        if not self.providers:
            logger.warning("No real translation providers available, adding mock provider as fallback")
            self.providers["mock"] = MockTranslationProvider("mock_fallback")
            logger.info("Mock fallback provider initialized")
    
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
        cache_key = self._generate_cache_key(text, source_lang, target_lang)
        cached_result = self._get_cached_translation(cache_key)
        if cached_result:
            logger.debug("Using cached translation")
            self.cache_hits += 1
            return cached_result
        
        self.cache_misses += 1
        
        # Try providers in priority order
        provider_order = self.config["provider_priority"]
        
        # Ensure mock provider is available as ultimate fallback
        if "mock" not in self.providers:
            self.providers["mock"] = MockTranslationProvider("mock_fallback")
        
        # Make sure mock is in the priority order as fallback
        if "mock" not in provider_order:
            provider_order = provider_order + ["mock"]
        
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
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate a cache key for the translation request.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Cache key string
        """
        # Create a hash of the translation parameters
        key_data = f"{text}:{source_lang}:{target_lang}"
        cache_key = hashlib.md5(key_data.encode('utf-8')).hexdigest()
        return cache_key
    
    def _get_cached_translation(self, cache_key: str) -> Optional[TranslationResult]:
        """Get cached translation result with TTL check.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            TranslationResult if found and not expired, None otherwise
        """
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        current_time = time.time()
        
        # Check if entry has expired
        if current_time - entry.timestamp > entry.ttl:
            logger.debug(f"Cache entry expired, removing: {cache_key}")
            del self.cache[cache_key]
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(cache_key)
        entry.access_count += 1
        
        logger.debug(f"Cache hit for key: {cache_key} (accessed {entry.access_count} times)")
        return entry.translation_result
    
    def _cache_translation(self, cache_key: str, result: TranslationResult) -> None:
        """Cache translation result with LRU eviction.
        
        Args:
            cache_key: Cache key for the result
            result: Translation result to cache
        """
        current_time = time.time()
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            translation_result=result,
            timestamp=current_time,
            access_count=1,
            ttl=self.cache_ttl
        )
        
        # If key already exists, update it
        if cache_key in self.cache:
            self.cache[cache_key] = entry
            self.cache.move_to_end(cache_key)
            logger.debug(f"Updated cache entry: {cache_key}")
            return
        
        # Check if cache is full and evict LRU entry
        while len(self.cache) >= self.cache_size:
            oldest_key, oldest_entry = self.cache.popitem(last=False)
            logger.debug(f"Evicted LRU cache entry: {oldest_key} (accessed {oldest_entry.access_count} times)")
        
        # Add new entry
        self.cache[cache_key] = entry
        logger.debug(f"Cached translation: {cache_key} (cache size: {len(self.cache)}/{self.cache_size})")
    
    def clear_cache(self) -> None:
        """Clear the entire translation cache."""
        cleared_count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {cleared_count} cache entries")
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry.timestamp > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self.cache),
            "max_size": self.cache_size,
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
        }
    
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