"""
Configuration for Unified Navigator Agent.

This module provides configuration management for the unified navigator
with environment variable support and validation.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from agents.tooling.rag.core import RetrievalConfig


@dataclass
class GuardrailConfig:
    """Configuration for input/output guardrails."""
    
    # Input guardrails
    enable_fast_safety_check: bool = True
    enable_llm_safety_check: bool = True
    llm_safety_timeout: float = 5.0
    
    # Output guardrails
    enable_template_sanitization: bool = True
    enable_llm_sanitization: bool = True
    llm_sanitization_timeout: float = 5.0
    
    # Safety patterns (can be extended)
    additional_unsafe_patterns: list = field(default_factory=list)
    additional_safe_patterns: list = field(default_factory=list)


@dataclass
class WebSearchConfig:
    """Configuration for web search tool."""
    
    api_key: Optional[str] = None
    base_url: str = "https://api.search.brave.com/res/v1/web/search"
    timeout: float = 5.0
    max_results: int = 10
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_minutes: int = 60
    cache_max_size: int = 1000
    
    # Search optimization
    enable_query_optimization: bool = True
    insurance_context_boost: bool = True


@dataclass
class UnifiedNavigatorConfig:
    """Main configuration for unified navigator agent."""
    
    # Model settings
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    anthropic_api_key: Optional[str] = None
    
    # Tool selection weights
    tool_selection_weights: Dict[str, float] = field(default_factory=lambda: {
        "web_score_threshold": 1.0,
        "rag_score_threshold": 1.0,
        "combined_query_length": 15,
        "personal_reference_boost": 0.5
    })
    
    # Component configurations
    guardrail_config: GuardrailConfig = field(default_factory=GuardrailConfig)
    web_search_config: WebSearchConfig = field(default_factory=WebSearchConfig)
    rag_config: RetrievalConfig = field(default_factory=RetrievalConfig.default)
    
    # Performance settings
    overall_timeout: float = 30.0
    node_timeout: float = 10.0
    enable_parallel_tools: bool = True
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_performance_tracking: bool = True
    enable_detailed_logging: bool = False

    @classmethod
    def from_environment(cls) -> "UnifiedNavigatorConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            UnifiedNavigatorConfig instance
        """
        # Main API keys
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        brave_api_key = os.getenv("BRAVE_API_KEY")
        
        # Model selection
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        
        # Performance settings
        overall_timeout = float(os.getenv("NAVIGATOR_TIMEOUT", "30.0"))
        node_timeout = float(os.getenv("NAVIGATOR_NODE_TIMEOUT", "10.0"))
        
        # Feature flags
        enable_parallel_tools = os.getenv("NAVIGATOR_PARALLEL_TOOLS", "true").lower() == "true"
        enable_performance_tracking = os.getenv("NAVIGATOR_PERFORMANCE_TRACKING", "true").lower() == "true"
        enable_detailed_logging = os.getenv("NAVIGATOR_DETAILED_LOGGING", "false").lower() == "true"
        
        # Guardrail settings
        guardrail_config = GuardrailConfig(
            enable_fast_safety_check=os.getenv("GUARDRAIL_FAST_CHECK", "true").lower() == "true",
            enable_llm_safety_check=os.getenv("GUARDRAIL_LLM_CHECK", "true").lower() == "true",
            llm_safety_timeout=float(os.getenv("GUARDRAIL_LLM_TIMEOUT", "5.0")),
            enable_template_sanitization=os.getenv("GUARDRAIL_TEMPLATE_SANITIZE", "true").lower() == "true",
            enable_llm_sanitization=os.getenv("GUARDRAIL_LLM_SANITIZE", "true").lower() == "true",
            llm_sanitization_timeout=float(os.getenv("GUARDRAIL_SANITIZE_TIMEOUT", "5.0"))
        )
        
        # Web search settings
        web_search_config = WebSearchConfig(
            api_key=brave_api_key,
            timeout=float(os.getenv("WEB_SEARCH_TIMEOUT", "5.0")),
            max_results=int(os.getenv("WEB_SEARCH_MAX_RESULTS", "10")),
            enable_cache=os.getenv("WEB_SEARCH_CACHE", "true").lower() == "true",
            cache_ttl_minutes=int(os.getenv("WEB_SEARCH_CACHE_TTL", "60")),
            cache_max_size=int(os.getenv("WEB_SEARCH_CACHE_SIZE", "1000")),
            enable_query_optimization=os.getenv("WEB_SEARCH_OPTIMIZE", "true").lower() == "true",
            insurance_context_boost=os.getenv("WEB_SEARCH_INSURANCE_BOOST", "true").lower() == "true"
        )
        
        # RAG settings (use existing RetrievalConfig)
        rag_config = RetrievalConfig(
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.25")),
            max_chunks=int(os.getenv("RAG_MAX_CHUNKS", "5")),
            token_budget=int(os.getenv("RAG_TOKEN_BUDGET", "4000"))
        )
        
        # Tool selection weights
        tool_selection_weights = {
            "web_score_threshold": float(os.getenv("TOOL_WEB_THRESHOLD", "1.0")),
            "rag_score_threshold": float(os.getenv("TOOL_RAG_THRESHOLD", "1.0")),
            "combined_query_length": int(os.getenv("TOOL_COMBINED_LENGTH", "15")),
            "personal_reference_boost": float(os.getenv("TOOL_PERSONAL_BOOST", "0.5"))
        }
        
        # Logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        return cls(
            anthropic_model=anthropic_model,
            anthropic_api_key=anthropic_api_key,
            tool_selection_weights=tool_selection_weights,
            guardrail_config=guardrail_config,
            web_search_config=web_search_config,
            rag_config=rag_config,
            overall_timeout=overall_timeout,
            node_timeout=node_timeout,
            enable_parallel_tools=enable_parallel_tools,
            log_level=log_level,
            enable_performance_tracking=enable_performance_tracking,
            enable_detailed_logging=enable_detailed_logging
        )
    
    def validate(self) -> None:
        """
        Validate configuration settings.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        if not self.web_search_config.api_key:
            raise ValueError("BRAVE_API_KEY is required for web search")
        
        if self.overall_timeout <= 0:
            raise ValueError("overall_timeout must be positive")
        
        if self.node_timeout <= 0:
            raise ValueError("node_timeout must be positive")
        
        if self.node_timeout > self.overall_timeout:
            raise ValueError("node_timeout cannot exceed overall_timeout")
        
        # Validate RAG config
        self.rag_config.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of config
        """
        return {
            "anthropic_model": self.anthropic_model,
            "has_anthropic_key": bool(self.anthropic_api_key),
            "tool_selection_weights": self.tool_selection_weights,
            "guardrail_config": {
                "enable_fast_safety_check": self.guardrail_config.enable_fast_safety_check,
                "enable_llm_safety_check": self.guardrail_config.enable_llm_safety_check,
                "llm_safety_timeout": self.guardrail_config.llm_safety_timeout,
                "enable_template_sanitization": self.guardrail_config.enable_template_sanitization,
                "enable_llm_sanitization": self.guardrail_config.enable_llm_sanitization,
                "llm_sanitization_timeout": self.guardrail_config.llm_sanitization_timeout
            },
            "web_search_config": {
                "has_api_key": bool(self.web_search_config.api_key),
                "base_url": self.web_search_config.base_url,
                "timeout": self.web_search_config.timeout,
                "max_results": self.web_search_config.max_results,
                "enable_cache": self.web_search_config.enable_cache,
                "cache_ttl_minutes": self.web_search_config.cache_ttl_minutes,
                "cache_max_size": self.web_search_config.cache_max_size,
                "enable_query_optimization": self.web_search_config.enable_query_optimization,
                "insurance_context_boost": self.web_search_config.insurance_context_boost
            },
            "rag_config": {
                "similarity_threshold": self.rag_config.similarity_threshold,
                "max_chunks": self.rag_config.max_chunks,
                "token_budget": self.rag_config.token_budget
            },
            "overall_timeout": self.overall_timeout,
            "node_timeout": self.node_timeout,
            "enable_parallel_tools": self.enable_parallel_tools,
            "log_level": self.log_level,
            "enable_performance_tracking": self.enable_performance_tracking,
            "enable_detailed_logging": self.enable_detailed_logging
        }


# Global configuration instance
_config: Optional[UnifiedNavigatorConfig] = None


def get_config() -> UnifiedNavigatorConfig:
    """
    Get the global configuration instance.
    
    Returns:
        UnifiedNavigatorConfig instance
    """
    global _config
    if _config is None:
        _config = UnifiedNavigatorConfig.from_environment()
    return _config


def set_config(config: UnifiedNavigatorConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: UnifiedNavigatorConfig instance
    """
    global _config
    _config = config


def reload_config() -> UnifiedNavigatorConfig:
    """
    Reload configuration from environment.
    
    Returns:
        New UnifiedNavigatorConfig instance
    """
    global _config
    _config = UnifiedNavigatorConfig.from_environment()
    return _config