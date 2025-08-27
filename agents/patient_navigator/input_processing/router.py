"""Enhanced Translation Router with Intelligent Fallback Chain.

This module provides intelligent routing and fallback logic for translation
services with performance monitoring, cost optimization, and circuit breaker
integration.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from .providers.elevenlabs import ElevenLabsProvider
from .providers.flash import FlashProvider, FlashProviderFactory
from .performance_monitor import track_performance, get_performance_monitor
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .types import TranslationResult, TranslationError

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels for routing decisions."""
    PRIMARY = "primary"      # First choice (ElevenLabs)
    FALLBACK = "fallback"    # Second choice (Flash)
    EMERGENCY = "emergency"  # Last resort (Browser API if available)


@dataclass
class ProviderConfig:
    """Configuration for a translation provider."""
    
    name: str
    priority: ProviderPriority
    provider: Any
    enabled: bool = True
    max_retries: int = 3
    timeout: float = 30.0
    cost_per_char: float = 0.0
    performance_weight: float = 1.0
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.cost_per_char < 0:
            raise ValueError("Cost per character must be non-negative")
        if self.performance_weight <= 0:
            raise ValueError("Performance weight must be positive")


@dataclass
class RoutingDecision:
    """Result of routing decision logic."""
    
    selected_provider: str
    reason: str
    confidence: float
    estimated_cost: float
    estimated_latency: float
    fallback_plan: List[str]


class IntelligentTranslationRouter:
    """Intelligent translation router with fallback chain and optimization.
    
    This class provides intelligent routing decisions for translation requests,
    automatically selecting the best provider based on text complexity, language
    pairs, cost considerations, and provider health. It implements a robust
    fallback chain to ensure translation reliability.
    
    The router analyzes multiple factors to make optimal routing decisions:
    - Text complexity and language pair difficulty
    - Provider performance and health status
    - Cost optimization based on user preferences
    - Quality requirements and fallback strategies
    
    Attributes:
        config: Router configuration with provider settings
        performance_monitor: Performance monitoring instance
        providers: Dictionary of configured translation providers
        router_circuit_breaker: Circuit breaker for router-level protection
        routing_decisions: History of routing decisions made
        fallback_usage_stats: Statistics on fallback provider usage
        total_cost_tracked: Total cost tracked across all providers
        cost_by_provider: Cost breakdown by provider
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the intelligent translation router.
        
        Sets up all translation providers, configures circuit breakers,
        and initializes performance tracking and cost monitoring.
        
        Args:
            config: Router configuration dictionary containing:
                - elevenlabs: ElevenLabs provider configuration
                - flash: Flash v2.5 provider configuration
                - preferred_provider: User's preferred provider
                - enable_fallback: Whether fallback is enabled
                - default_language: Default source language
                - target_language: Target language for translations
                
        Raises:
            ValueError: If no translation providers are available
            ConfigurationError: If provider configuration is invalid
        """
        self.config = config
        self.performance_monitor = get_performance_monitor()
        
        # Initialize providers
        self.providers: Dict[str, ProviderConfig] = {}
        self._initialize_providers()
        
        # Circuit breaker for the entire router
        router_circuit_config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            expected_timeout=30.0,
            success_threshold=3,
            max_concurrent_half_open=2
        )
        self.router_circuit_breaker = CircuitBreaker(
            "translation_router",
            router_circuit_config
        )
        
        # Performance tracking
        self.routing_decisions: List[RoutingDecision] = []
        self.fallback_usage_stats: Dict[str, int] = defaultdict(int)
        
        # Cost optimization
        self.total_cost_tracked = 0.0
        self.cost_by_provider: Dict[str, float] = defaultdict(float)
        
        logger.info("Intelligent translation router initialized")
    
    def _initialize_providers(self) -> None:
        """Initialize translation providers based on configuration."""
        try:
            # Initialize ElevenLabs provider
            if self.config.get("elevenlabs", {}).get("enabled", True):
                elevenlabs_config = self.config["elevenlabs"]
                elevenlabs_provider = ElevenLabsProvider(
                    api_key=elevenlabs_config["api_key"]
                )
                
                self.providers["elevenlabs"] = ProviderConfig(
                    name="elevenlabs",
                    priority=ProviderPriority.PRIMARY,
                    provider=elevenlabs_provider,
                    enabled=True,
                    max_retries=elevenlabs_config.get("max_retries", 3),
                    timeout=elevenlabs_config.get("timeout", 30.0),
                    cost_per_char=elevenlabs_config.get("cost_per_char", 0.0001),
                    performance_weight=elevenlabs_config.get("performance_weight", 1.0)
                )
                logger.info("ElevenLabs provider initialized")
            
            # Initialize Flash provider
            if self.config.get("flash", {}).get("enabled", True):
                flash_config = self.config["flash"]
                flash_provider = FlashProviderFactory.create_provider_from_env()
                
                if flash_provider:
                    self.providers["flash"] = ProviderConfig(
                        name="flash",
                        priority=ProviderPriority.FALLBACK,
                        provider=flash_provider,
                        enabled=True,
                        max_retries=flash_config.get("max_retries", 3),
                        timeout=flash_config.get("timeout", 30.0),
                        cost_per_char=flash_config.get("cost_per_char", 0.00005),  # Cheaper
                        performance_weight=flash_config.get("performance_weight", 0.8)
                    )
                    logger.info("Flash provider initialized")
                else:
                    logger.warning("Flash provider not available - API key missing")
            
            # Validate we have at least one provider
            if not self.providers:
                raise ValueError("No translation providers available")
                
        except Exception as e:
            logger.error(f"Failed to initialize providers: {e}")
            raise
    
    @track_performance("router_decision")
    async def make_routing_decision(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Make intelligent routing decision for translation request.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            user_preferences: User preferences for cost/quality trade-offs
            
        Returns:
            Routing decision with provider selection and fallback plan
        """
        # Analyze request characteristics
        text_complexity = self._analyze_text_complexity(text)
        language_complexity = self._analyze_language_complexity(source_lang, target_lang)
        
        # Get provider health and performance data
        provider_health = await self._get_provider_health()
        provider_performance = self._get_provider_performance()
        
        # Apply user preferences
        user_preferences = user_preferences or {}
        cost_sensitivity = user_preferences.get("cost_sensitivity", "balanced")
        quality_preference = user_preferences.get("quality_preference", "balanced")
        
        # Score providers based on multiple factors
        provider_scores = self._score_providers(
            text_complexity=text_complexity,
            language_complexity=language_complexity,
            provider_health=provider_health,
            provider_performance=provider_performance,
            cost_sensitivity=cost_sensitivity,
            quality_preference=quality_preference
        )
        
        # Check if we have any available providers
        if not provider_scores:
            raise ValueError("No healthy translation providers available")
        
        # Select best provider
        best_provider_name = max(provider_scores.keys(), key=provider_scores.get)
        best_provider_config = self.providers[best_provider_name]
        
        # Create fallback plan
        fallback_plan = self._create_fallback_plan(
            selected_provider=best_provider_name,
            provider_scores=provider_scores
        )
        
        # Calculate estimates
        estimated_cost = self._estimate_cost(text, best_provider_config)
        estimated_latency = self._estimate_latency(best_provider_config, provider_performance)
        
        # Calculate confidence (handle single provider case)
        if len(provider_scores) == 1:
            confidence = 1.0
        else:
            confidence = provider_scores[best_provider_name] / max(provider_scores.values())
        
        # Create routing decision
        decision = RoutingDecision(
            selected_provider=best_provider_name,
            reason=f"Best score: {provider_scores[best_provider_name]:.2f}",
            confidence=confidence,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
            fallback_plan=fallback_plan
        )
        
        # Store decision for analysis
        self.routing_decisions.append(decision)
        
        logger.info(
            f"Routing decision: {best_provider_name} selected for "
            f"{source_lang}->{target_lang} translation "
            f"(score: {provider_scores[best_provider_name]:.2f})"
        )
        
        return decision
    
    def _analyze_text_complexity(self, text: str) -> float:
        """Analyze text complexity for routing decisions."""
        if not text:
            return 0.0
        
        # Simple complexity analysis
        words = text.split()
        sentences = text.split('.')
        
        factors = {
            "length": min(len(words) / 50, 2.0),
            "sentence_complexity": min(len(words) / max(len(sentences), 1) / 15, 1.5),
            "special_content": min(
                (text.count(',') + text.count(';') + text.count(':') + 
                 text.count('(') + text.count(')')) / 20, 1.0
            ),
            "technical_terms": min(
                sum(1 for word in words if len(word) > 12) / len(words) * 10, 1.0
            )
        }
        
        # Weighted complexity score
        weights = {"length": 0.3, "sentence_complexity": 0.3, 
                  "special_content": 0.2, "technical_terms": 0.2}
        
        complexity = sum(factors[factor] * weights[factor] for factor in factors)
        return min(complexity, 3.0)
    
    def _analyze_language_complexity(self, source_lang: str, target_lang: str) -> float:
        """Analyze language pair complexity."""
        # Language complexity mapping (similar to Flash provider)
        complexity_map = {
            "en": 1.0, "es": 1.2, "fr": 1.3, "de": 1.4, "it": 1.2,
            "pt": 1.2, "ru": 1.5, "zh": 1.6, "ja": 1.7, "ko": 1.6,
            "ar": 1.8, "hi": 1.3, "auto": 1.5
        }
        
        source_complexity = complexity_map.get(source_lang, 1.5)
        target_complexity = complexity_map.get(target_lang, 1.0)
        
        # Language pair complexity (some combinations are harder)
        pair_complexity = (source_complexity + target_complexity) / 2
        
        # Adjust for difficult language pairs
        difficult_pairs = [
            ("zh", "en"), ("ja", "en"), ("ko", "en"),
            ("ar", "en"), ("ru", "en"), ("en", "zh"),
            ("en", "ja"), ("en", "ko"), ("en", "ar"), ("en", "ru")
        ]
        
        if (source_lang, target_lang) in difficult_pairs or (target_lang, source_lang) in difficult_pairs:
            pair_complexity *= 1.3
        
        return min(pair_complexity, 3.0)
    
    async def _get_provider_health(self) -> Dict[str, bool]:
        """Get health status of all providers."""
        health_status = {}
        
        for name, config in self.providers.items():
            try:
                if hasattr(config.provider, 'health_check'):
                    health_status[name] = await config.provider.health_check()
                else:
                    health_status[name] = True  # Assume healthy if no health check
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                health_status[name] = False
        
        return health_status
    
    def _get_provider_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all providers."""
        performance_data = {}
        
        for name in self.providers.keys():
            stats = self.performance_monitor.get_operation_stats(f"{name}_translate")
            if stats:
                performance_data[name] = {
                    "avg_duration": stats.avg_duration,
                    "success_rate": stats.success_rate,
                    "error_rate": stats.error_rate
                }
            else:
                # Default performance if no data available
                performance_data[name] = {
                    "avg_duration": 1.0,
                    "success_rate": 0.95,
                    "error_rate": 0.05
                }
        
        return performance_data
    
    def _score_providers(
        self,
        text_complexity: float,
        language_complexity: float,
        provider_health: Dict[str, bool],
        provider_performance: Dict[str, Dict[str, float]],
        cost_sensitivity: str,
        quality_preference: str
    ) -> Dict[str, float]:
        """Score providers based on multiple factors."""
        provider_scores = {}
        
        for name, config in self.providers.items():
            if not config.enabled or not provider_health.get(name, False):
                continue
            
            # Base score starts at 100
            score = 100.0
            
            # Health penalty (unhealthy providers get heavy penalty)
            if not provider_health.get(name, False):
                score -= 50.0
            
            # Performance scoring
            perf = provider_performance.get(name, {})
            if perf.get("success_rate", 0.95) < 0.9:
                score -= 20.0
            if perf.get("avg_duration", 1.0) > 2.0:
                score -= 15.0
            
            # Cost optimization
            cost_score = self._calculate_cost_score(
                config, text_complexity, language_complexity, cost_sensitivity
            )
            score += cost_score
            
            # Quality preference
            quality_score = self._calculate_quality_score(
                config, text_complexity, language_complexity, quality_preference
            )
            score += quality_score
            
            # Priority bonus
            if config.priority == ProviderPriority.PRIMARY:
                score += 10.0
            elif config.priority == ProviderPriority.FALLBACK:
                score += 5.0
            
            # Apply performance weight
            score *= config.performance_weight
            
            provider_scores[name] = max(score, 0.0)  # Ensure non-negative
        
        return provider_scores
    
    def _calculate_cost_score(
        self, 
        config: ProviderConfig, 
        text_complexity: float, 
        language_complexity: float,
        cost_sensitivity: str
    ) -> float:
        """Calculate cost optimization score."""
        # Base cost score
        base_cost = config.cost_per_char * 100  # Cost per 100 characters
        
        # Adjust for complexity
        adjusted_cost = base_cost * (1 + text_complexity * 0.2) * (1 + language_complexity * 0.1)
        
        # Cost sensitivity adjustments
        if cost_sensitivity == "high":
            # Prefer cheaper options
            if adjusted_cost < 0.001:
                return 20.0
            elif adjusted_cost < 0.005:
                return 10.0
            else:
                return -10.0
        elif cost_sensitivity == "low":
            # Cost is less important
            return 0.0
        else:  # balanced
            if adjusted_cost < 0.001:
                return 15.0
            elif adjusted_cost < 0.005:
                return 5.0
            else:
                return -5.0
    
    def _calculate_quality_score(
        self, 
        config: ProviderConfig, 
        text_complexity: float, 
        language_complexity: float,
        quality_preference: str
    ) -> float:
        """Calculate quality preference score."""
        # Quality scoring based on provider capabilities
        if config.name == "elevenlabs":
            quality_score = 15.0  # High quality
        elif config.name == "flash":
            quality_score = 10.0  # Good quality, cost-optimized
        else:
            quality_score = 5.0   # Basic quality
        
        # Adjust for complexity requirements
        if text_complexity > 2.0 or language_complexity > 2.0:
            if config.name == "elevenlabs":
                quality_score += 10.0  # Better for complex content
            elif config.name == "flash":
                quality_score += 5.0   # Good for complex content
        
        # Quality preference adjustments
        if quality_preference == "high":
            quality_score *= 1.2
        elif quality_preference == "low":
            quality_score *= 0.8
        
        return quality_score
    
    def _create_fallback_plan(
        self, 
        selected_provider: str, 
        provider_scores: Dict[str, float]
    ) -> List[str]:
        """Create fallback plan for translation request."""
        # Sort providers by score (excluding selected)
        sorted_providers = sorted(
            [(name, score) for name, score in provider_scores.items() if name != selected_provider],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Create fallback chain
        fallback_plan = [name for name, _ in sorted_providers]
        
        logger.debug(f"Fallback plan for {selected_provider}: {fallback_plan}")
        return fallback_plan
    
    def _estimate_cost(self, text: str, provider_config: ProviderConfig) -> float:
        """Estimate translation cost."""
        char_count = len(text)
        base_cost = char_count * provider_config.cost_per_char
        
        # Adjust for complexity (more complex = more expensive)
        complexity_multiplier = 1.0 + (len(text.split()) / 100) * 0.1
        estimated_cost = base_cost * complexity_multiplier
        
        return round(estimated_cost, 6)
    
    def _estimate_latency(
        self, 
        provider_config: ProviderConfig, 
        provider_performance: Dict[str, Dict[str, float]]
    ) -> float:
        """Estimate translation latency."""
        perf = provider_performance.get(provider_config.name, {})
        base_latency = perf.get("avg_duration", 1.0)
        
        # Add some buffer for network latency
        estimated_latency = base_latency * 1.2
        
        return round(estimated_latency, 2)
    
    @track_performance("router_translate")
    async def translate_with_fallback(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> TranslationResult:
        """Translate text with intelligent fallback chain.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            user_preferences: User preferences for cost/quality trade-offs
            
        Returns:
            Translation result from best available provider
            
        Raises:
            TranslationError: If all providers fail
        """
        # Use circuit breaker for fault tolerance
        from .circuit_breaker import circuit_breaker_protection
        
        async with circuit_breaker_protection("translation_router"):
            # Make routing decision
            routing_decision = await self.make_routing_decision(
                text, source_lang, target_lang, user_preferences
            )
            
            # Try primary provider
            try:
                result = await self._try_provider(
                    routing_decision.selected_provider,
                    text, source_lang, target_lang
                )
                
                # Track successful translation
                self._track_successful_translation(
                    routing_decision.selected_provider,
                    routing_decision.estimated_cost
                )
                
                return result
                
            except Exception as e:
                logger.warning(
                    f"Primary provider {routing_decision.selected_provider} failed: {e}"
                )
                
                # Try fallback providers
                for fallback_provider in routing_decision.fallback_plan:
                    try:
                        result = await self._try_provider(
                            fallback_provider,
                            text, source_lang, target_lang
                        )
                        
                        # Track fallback usage
                        self.fallback_usage_stats[fallback_provider] += 1
                        self._track_successful_translation(
                            fallback_provider,
                            routing_decision.estimated_cost
                        )
                        
                        logger.info(f"Fallback to {fallback_provider} successful")
                        return result
                        
                    except Exception as fallback_error:
                        logger.warning(
                            f"Fallback provider {fallback_provider} failed: {fallback_error}"
                        )
                        continue
                
                # All providers failed
                error_msg = f"All translation providers failed. Last error: {e}"
                logger.error(error_msg)
                raise TranslationError(error_msg)
    
    async def _try_provider(
        self, 
        provider_name: str, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> TranslationResult:
        """Try translation with a specific provider."""
        provider_config = self.providers[provider_name]
        
        if not provider_config.enabled:
            raise Exception(f"Provider {provider_name} is disabled")
        
        # Check provider-specific circuit breaker
        if hasattr(provider_config.provider, 'circuit_breaker'):
            async with provider_config.provider.circuit_breaker:
                return await self._execute_translation(
                    provider_config, text, source_lang, target_lang
                )
        else:
            return await self._execute_translation(
                provider_config, text, source_lang, target_lang
            )
    
    async def _execute_translation(
        self, 
        provider_config: ProviderConfig, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> TranslationResult:
        """Execute translation with retry logic."""
        last_error = None
        
        for attempt in range(provider_config.max_retries):
            try:
                if provider_config.name == "elevenlabs":
                    result = await provider_config.provider.translate(
                        text, source_lang, target_lang
                    )
                elif provider_config.name == "flash":
                    # Convert to Flash request format
                    from .providers.flash import FlashTranslationRequest
                    flash_request = FlashTranslationRequest(
                        text=text,
                        source_language=source_lang,
                        target_language=target_lang
                    )
                    flash_response = await provider_config.provider.translate(flash_request)
                    
                    # Convert Flash response to TranslationResult
                    result = TranslationResult(
                        text=flash_response.translated_text,
                        confidence=flash_response.confidence,
                        provider=provider_config.name,
                        cost_estimate=flash_response.cost_credits,
                        source_language=flash_response.source_language,
                        target_language=flash_response.target_language
                    )
                else:
                    raise Exception(f"Unknown provider: {provider_config.name}")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Translation attempt {attempt + 1} failed for {provider_config.name}: {e}"
                )
                
                if attempt < provider_config.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        raise last_error or Exception(f"Translation failed for {provider_config.name}")
    
    def _track_successful_translation(self, provider_name: str, estimated_cost: float) -> None:
        """Track successful translation for analytics."""
        self.total_cost_tracked += estimated_cost
        self.cost_by_provider[provider_name] += estimated_cost
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Get comprehensive router statistics."""
        return {
            "total_translations": len(self.routing_decisions),
            "fallback_usage": dict(self.fallback_usage_stats),
            "cost_tracking": {
                "total_cost": self.total_cost_tracked,
                "cost_by_provider": dict(self.cost_by_provider)
            },
            "provider_health": {
                name: config.provider.get_health_status() if hasattr(config.provider, 'get_health_status') else {"status": "unknown"}
                for name, config in self.providers.items()
            },
            "circuit_breaker_status": {
                "router_state": self.router_circuit_breaker.state.value,
                "router_failures": self.router_circuit_breaker.failure_count
            }
        }
    
    async def health_check(self) -> bool:
        """Check health of all providers."""
        try:
            provider_health = await self._get_provider_health()
            healthy_providers = sum(1 for healthy in provider_health.values() if healthy)
            total_providers = len(provider_health)
            
            logger.info(f"Router health check: {healthy_providers}/{total_providers} providers healthy")
            return healthy_providers > 0
            
        except Exception as e:
            logger.error(f"Router health check failed: {e}")
            return False