"""
Mock Translation Provider for MVP Testing.

This provider simulates translation functionality without requiring external API keys.
It's used for testing and development when real translation services are not available.
"""

import logging
from typing import Dict, Any, List
from ..types import TranslationProvider, TranslationResult

logger = logging.getLogger(__name__)


class MockTranslationProvider(TranslationProvider):
    """Mock translation provider for MVP testing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the mock translation provider."""
        self.config = config or {}
        self.supported_languages = ["en", "es", "fr", "de", "it", "pt"]
        logger.info("Mock Translation Provider initialized")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en"
    ) -> TranslationResult:
        """
        Mock translation that returns the input text with mock metadata.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            TranslationResult with mock translation data
        """
        logger.info(f"Mock translation: {source_lang} -> {target_lang}")
        
        # For MVP, just return the input text with mock confidence
        translated_text = text
        
        # Simulate some basic language-specific behavior
        if source_lang == "es" and target_lang == "en":
            # Mock Spanish to English translation
            if "deducible" in text.lower():
                translated_text = text.replace("deducible", "deductible")
            elif "copago" in text.lower():
                translated_text = text.replace("copago", "copay")
        
        return TranslationResult(
            text=translated_text,
            confidence=0.95,  # High confidence for mock
            provider="mock",
            cost_estimate=0.0,  # No cost for mock
            source_language=source_lang,
            target_language=target_lang
        )
    
    def get_cost_estimate(self, text: str, source_lang: str, target_lang: str = "en") -> float:
        """Get cost estimate for translation (always 0 for mock)."""
        return 0.0
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return self.supported_languages
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return "mock"
    
    async def health_check(self) -> bool:
        """Check if the provider service is available (always true for mock)."""
        return True