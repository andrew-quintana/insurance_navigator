import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class LLMIntegration:
    """
    LLM Integration Module
    
    Handles both OpenAI API calls and mock responses with:
    - Rate limiting and token management
    - Error handling with fallback to mock responses
    - Response validation and parsing
    - Performance monitoring
    """
    
    def __init__(self, use_mock: bool = False, api_key: Optional[str] = None):
        """
        Initialize LLM integration.
        
        Args:
            use_mock: If True, use mock responses instead of API calls
            api_key: OpenAI API key (if not provided, will try to get from environment)
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.request_times: List[float] = []
        self.max_requests_per_minute = 60
        self.max_tokens_per_request = 4000
        
        if not use_mock:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not available. Install with: pip install openai")
            
            # Initialize OpenAI client
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set in environment")
            
            self.client = AsyncOpenAI(
                api_key=api_key,
                max_retries=3,
                timeout=30.0
            )
            self.logger.info("Initialized OpenAI client for real API calls (Claude 4 Haiku for completions, OpenAI for embeddings)")
        else:
            self.logger.info("Using mock responses for LLM integration")
    
    async def generate_completion(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion using OpenAI API or mock response.
        
        Args:
            prompt: The prompt to send to the LLM
            model: The model to use for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails and no fallback available
        """
        if self.use_mock:
            return await self._generate_mock_completion(prompt, model)
        
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Make API call
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Record request time for rate limiting
            self.request_times.append(time.time())
            
            # Clean up old request times (keep last minute)
            current_time = time.time()
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            completion = response.choices[0].message.content
            if not completion:
                raise ValueError("Empty response from OpenAI API")
            
            self.logger.debug(f"Generated completion in {time.time() - start_time:.2f}s")
            return completion
            
        except Exception as error:
            self.logger.error(f"OpenAI API call failed: {error}")
            
            # Fallback to mock response
            self.logger.warning("Falling back to mock response due to API failure")
            return await self._generate_mock_completion(prompt, model)
    
    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"  # OpenAI embedding model (Claude doesn't have embeddings API)
    ) -> List[float]:
        """
        Generate embedding using OpenAI API or mock response.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            List of embedding values (1536 dimensions for text-embedding-3-small)
            
        Raises:
            Exception: If API call fails and no fallback available
        """
        if self.use_mock:
            return self._generate_mock_embedding(text)
        
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Make OpenAI API call for embedding
            start_time = time.time()
            response = await self.client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            
            # Record request time for rate limiting
            self.request_times.append(time.time())
            
            # Clean up old request times
            current_time = time.time()
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            embedding = response.data[0].embedding
            if not embedding:
                raise ValueError("Empty embedding from OpenAI API")
            
            # Validate embedding dimensions
            if len(embedding) != 1536:
                raise ValueError(f"Invalid embedding dimensions: expected 1536, got {len(embedding)}")
            
            self.logger.debug(f"Generated OpenAI embedding in {time.time() - start_time:.2f}s")
            return embedding
            
        except Exception as error:
            self.logger.error(f"OpenAI embedding API call failed: {error}")
            
            # Fallback to mock embedding
            self.logger.warning("Falling back to mock embedding due to API failure")
            return self._generate_mock_embedding(text)
    
    async def _check_rate_limits(self) -> None:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            # Calculate wait time
            oldest_request = min(self.request_times)
            wait_time = 60 - (current_time - oldest_request)
            
            if wait_time > 0:
                self.logger.warning(f"Rate limit reached. Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    async def _generate_mock_completion(self, prompt: str, model: str) -> str:
        """Generate mock completion for testing."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate context-aware mock response based on prompt content
        if "strategy" in prompt.lower() and "speed" in prompt.lower():
            return json.dumps({
                "title": "Fast-Track Specialist Consultation",
                "category": "speed-optimized",
                "approach": "Direct specialist consultation with expedited scheduling",
                "rationale": "Bypasses primary care gatekeeping for immediate specialist access",
                "actionable_steps": [
                    "Contact specialist directly using plan's direct access feature",
                    "Request expedited appointment with urgent care classification",
                    "Prepare medical documentation for immediate review"
                ],
                "llm_scores": {
                    "speed": 0.9,
                    "cost": 0.6,
                    "effort": 0.7
                }
            })
        
        elif "strategy" in prompt.lower() and "cost" in prompt.lower():
            return json.dumps({
                "title": "Cost-Effective Care Pathway",
                "category": "cost-optimized",
                "approach": "Step-by-step care escalation to minimize costs",
                "rationale": "Follows insurance plan's preferred care pathway for maximum coverage",
                "actionable_steps": [
                    "Start with in-network primary care visit",
                    "Follow recommended diagnostic testing sequence",
                    "Use plan's preferred specialist network"
                ],
                "llm_scores": {
                    "speed": 0.5,
                    "cost": 0.9,
                    "effort": 0.6
                }
            })
        
        elif "strategy" in prompt.lower() and "effort" in prompt.lower():
            return json.dumps({
                "title": "Minimal Effort Care Coordination",
                "category": "effort-optimized",
                "approach": "Care coordination service to handle all arrangements",
                "rationale": "Minimizes patient effort through professional care coordination",
                "actionable_steps": [
                    "Contact plan's care coordination service",
                    "Provide medical history and preferences",
                    "Let coordinator arrange all appointments and follow-up"
                ],
                "llm_scores": {
                    "speed": 0.7,
                    "cost": 0.8,
                    "effort": 0.9
                }
            })
        
        elif "validation" in prompt.lower() or "compliance" in prompt.lower():
            return json.dumps({
                "compliance_status": "approved",
                "validation_reasons": [
                    {
                        "category": "legal",
                        "description": "Strategy follows standard healthcare protocols",
                        "severity": "info"
                    }
                ],
                "confidence_score": 0.85,
                "source_references": [
                    {
                        "source": "Healthcare Best Practices",
                        "url": None,
                        "confidence": 0.9
                    }
                ]
            })
        
        else:
            # Generic mock response
            return json.dumps({
                "response": "Mock response for testing",
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing."""
        # Generate deterministic mock embedding based on text content
        import hashlib
        
        # Create hash of text for deterministic embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to list of floats (1536 dimensions like text-embedding-3-small)
        embedding = []
        for i in range(0, len(text_hash), 2):
            if len(embedding) >= 1536:
                break
            hex_pair = text_hash[i:i+2]
            embedding.append(float(int(hex_pair, 16)) / 255.0)
        
        # Pad to 1536 dimensions if needed
        while len(embedding) < 1536:
            embedding.append(0.0)
        
        return embedding[:1536]
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        current_time = time.time()
        recent_requests = [t for t in self.request_times if current_time - t < 60]
        
        return {
            "requests_in_last_minute": len(recent_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "rate_limit_remaining": max(0, self.max_requests_per_minute - len(recent_requests)),
            "using_mock": self.use_mock
        }
    
    def validate_response(self, response: str, expected_format: str = "json") -> bool:
        """
        Validate LLM response format.
        
        Args:
            response: The response to validate
            expected_format: Expected format ("json", "text", etc.)
            
        Returns:
            True if response is valid, False otherwise
        """
        if not response or not response.strip():
            return False
        
        if expected_format == "json":
            try:
                json.loads(response)
                return True
            except json.JSONDecodeError:
                return False
        
        return True 