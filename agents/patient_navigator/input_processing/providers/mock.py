"""Mock translation provider for testing and development."""

import asyncio
import logging
from typing import List

from ..types import TranslationProvider, TranslationResult, TranslationError

logger = logging.getLogger(__name__)


class MockTranslationProvider(TranslationProvider):
    """Mock translation service provider for testing."""
    
    def __init__(self, provider_name: str = "mock"):
        """Initialize the mock provider.
        
        Args:
            provider_name: Name of the mock provider
        """
        self.provider_name = provider_name
        
        # Supported languages (comprehensive list for testing)
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi", "cs",
            "bg", "hr", "et", "lv", "lt", "sk", "sl", "hu", "ro", "el"
        ]
        
        # Simple translation mappings for common phrases
        self.translations = {
            ("es", "en"): {
                "hola": "hello",
                "necesito ayuda": "I need help",
                "necesito ayuda con mi seguro médico": "I need help with my medical insurance",
                "mi póliza de seguro fue rechazada": "my insurance policy was rejected",
                "mi póliza": "my policy",
                "mi seguro": "my insurance",
                "fue rechazada": "was rejected",
                "rechazada": "rejected",
                "reclamo": "claim",
                "cobertura": "coverage",
                "deducible": "deductible",
                "prima": "premium",
                "beneficios": "benefits",
                "médico": "doctor",
                "hospital": "hospital",
                "medicamento": "medication",
                "receta": "prescription",
                "póliza": "policy",
                "seguro": "insurance"
            }
        }
        
        logger.info(f"Mock translation provider '{provider_name}' initialized")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str = "en"
    ) -> TranslationResult:
        """Translate text from source to target language using mock logic.
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: If translation fails
        """
        logger.debug(f"Mock translating '{text[:50]}...' from {source_lang} to {target_lang}")
        
        # Validate inputs
        if not text or not text.strip():
            raise TranslationError("Empty text provided for translation")
        
        # Validate language support
        if source_lang not in self.supported_languages:
            raise TranslationError(f"Source language '{source_lang}' not supported by mock provider")
        
        if target_lang not in self.supported_languages:
            raise TranslationError(f"Target language '{target_lang}' not supported by mock provider")
        
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
        
        # Simulate API delay
        await asyncio.sleep(0.2)
        
        # Perform mock translation
        translated_text = self._mock_translate(text, source_lang, target_lang)
        
        # Calculate confidence based on translation quality
        confidence = self._calculate_mock_confidence(text, translated_text, source_lang, target_lang)
        
        # Calculate cost
        cost_estimate = self.get_cost_estimate(text, source_lang, target_lang)
        
        result = TranslationResult(
            text=translated_text,
            confidence=confidence,
            provider=self.provider_name,
            cost_estimate=cost_estimate,
            source_language=source_lang,
            target_language=target_lang
        )
        
        logger.info(f"Mock translation successful: {len(translated_text)} chars, confidence {confidence}")
        return result
    
    def _mock_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Perform mock translation using simple rules.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        text_lower = text.lower().strip()
        translation_map = self.translations.get((source_lang, target_lang), {})
        
        # Try exact match first
        if text_lower in translation_map:
            return translation_map[text_lower]
        
        # Try partial matches for common phrases
        translated_parts = []
        words = text_lower.split()
        
        for word in words:
            if word in translation_map:
                translated_parts.append(translation_map[word])
            else:
                # Keep original word if no translation found
                translated_parts.append(word)
        
        if translated_parts:
            result = " ".join(translated_parts)
            # Capitalize first letter
            if result:
                result = result[0].upper() + result[1:]
            return result
        
        # Fallback: indicate it's been "translated" by mock provider
        return f"[MOCK-TRANSLATED from {source_lang}] {text}"
    
    def _calculate_mock_confidence(self, original: str, translated: str, source_lang: str, target_lang: str) -> float:
        """Calculate confidence score for mock translation.
        
        Args:
            original: Original text
            translated: Translated text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # If we have a direct translation mapping, high confidence
        text_lower = original.lower().strip()
        translation_map = self.translations.get((source_lang, target_lang), {})
        
        if text_lower in translation_map:
            return 0.95
        
        # If partial matches were found, moderate confidence
        words = text_lower.split()
        matched_words = sum(1 for word in words if word in translation_map)
        
        if matched_words > 0:
            return 0.7 + (matched_words / len(words)) * 0.2
        
        # If no matches found, low confidence
        return 0.4
    
    def get_cost_estimate(self, text: str, source_lang: str, target_lang: str = "en") -> float:
        """Estimate cost for translation (mock provider is free).
        
        Args:
            text: Text to translate
            source_lang: Source language ISO code
            target_lang: Target language ISO code
            
        Returns:
            Estimated cost in USD (always 0.0 for mock)
        """
        return 0.0  # Mock provider is free
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return self.supported_languages.copy()
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.provider_name
    
    async def health_check(self) -> bool:
        """Check if the provider service is available.
        
        Returns:
            True (mock provider is always available)
        """
        logger.debug("Performing mock provider health check")
        
        # Simulate brief delay
        await asyncio.sleep(0.05)
        
        logger.debug("Mock provider health check result: True")
        return True