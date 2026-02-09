"""
Shared Langfuse client for observability across the agent workflow.

Provides a lazy singleton Langfuse client that reads configuration from
environment variables. All functions gracefully no-op when Langfuse is
not configured, so the application works identically with or without it.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("langfuse_client")

_langfuse_client = None
_langfuse_init_attempted = False


def get_langfuse():
    """
    Return the singleton Langfuse client, or None if not configured.

    Lazily initializes on first call. If LANGFUSE_SECRET_KEY is not set
    in the environment, returns None and all tracing becomes a no-op.
    """
    global _langfuse_client, _langfuse_init_attempted

    if _langfuse_init_attempted:
        return _langfuse_client

    _langfuse_init_attempted = True

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")

    if not secret_key or not public_key:
        logger.info("Langfuse keys not configured — tracing disabled")
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host,
        )
        logger.info("Langfuse client initialized (host=%s)", host)
    except Exception as e:
        logger.warning("Failed to initialize Langfuse client: %s", e)
        _langfuse_client = None

    return _langfuse_client


def create_trace(
    name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    input: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Create a new Langfuse trace, or return None if Langfuse is not available.
    """
    client = get_langfuse()
    if client is None:
        return None

    try:
        return client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            input=input,
            metadata=metadata or {},
        )
    except Exception as e:
        logger.warning("Failed to create Langfuse trace: %s", e)
        return None


def flush():
    """
    Flush any pending Langfuse events. Safe to call even if Langfuse is
    not configured.
    """
    client = get_langfuse()
    if client is None:
        return
    try:
        client.flush()
    except Exception as e:
        logger.warning("Langfuse flush failed: %s", e)
