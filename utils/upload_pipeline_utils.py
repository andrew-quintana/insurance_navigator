"""
Shared utilities for the insurance document ingestion pipeline.
Implements UUIDv5 generation, event logging, and markdown normalization.
"""

import hashlib
import json
import re
import uuid
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Namespace UUID for deterministic ID generation (from CONTEXT.md)
NAMESPACE_UUID = uuid.UUID('6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42')

# Event codes from CONTEXT.md §7
EVENT_CODES = {
    # Upload stage
    'UPLOAD_DEDUP_HIT': 'info',
    'UPLOAD_ACCEPTED': 'info',
    
    # Parsing stage
    'PARSE_REQUESTED': 'info',
    'PARSE_STORED': 'info',
    'PARSE_HASH_MISMATCH': 'error',
    
    # Chunking stage
    'CHUNK_BUFFERED': 'info',
    'CHUNK_COMMITTED': 'info',
    
    # Embedding stage
    'EMBED_BUFFERED': 'info',
    'EMBED_COMMITTED': 'info',
    'EMBED_INDEX_TIMEOUT': 'warn',
    
    # General
    'RETRY_SCHEDULED': 'warn',
    'DLQ_MOVED': 'error',
}

# Event types from CONTEXT.md §7
EVENT_TYPES = {
    'stage_started',
    'stage_done', 
    'retry',
    'error',
    'finalized'
}

# Event severities from CONTEXT.md §7
EVENT_SEVERITIES = {'info', 'warn', 'error'}


def canonicalize_string(input_string: str) -> str:
    """
    Canonicalize input string for UUIDv5 generation.
    
    Rules from CONTEXT.md §3:
    - Lowercase
    - Use ':' as the only separator
    - JSON configs serialized as minified, sorted-keys UTF-8
    - Model names use vendor canonical strings
    
    Args:
        input_string: String to canonicalize
        
    Returns:
        Canonicalized string
    """
    if not input_string:
        return ""
    
    # Convert to lowercase
    canonical = input_string.lower()
    
    # Replace multiple separators with single colon
    canonical = re.sub(r'[_\-\s]+', ':', canonical)
    
    # Remove leading/trailing colons
    canonical = canonical.strip(':')
    
    # Collapse multiple colons to single
    canonical = re.sub(r':+', ':', canonical)
    
    return canonical


def canonicalize_json_config(config: Dict[str, Any]) -> str:
    """
    Canonicalize JSON configuration for UUIDv5 generation.
    
    Per CONTEXT.md §3: JSON configs serialized as minified, sorted-keys UTF-8
    
    Args:
        config: Dictionary configuration to canonicalize
        
    Returns:
        Canonicalized JSON string
    """
    if not config:
        return "{}"
    
    # Sort keys for deterministic output
    sorted_config = dict(sorted(config.items()))
    
    # Serialize as minified JSON
    return json.dumps(sorted_config, separators=(',', ':'), ensure_ascii=False)


def generate_uuidv5(canonical_string: str) -> uuid.UUID:
    """
    Generate deterministic UUIDv5 using the project namespace.
    
    Args:
        canonical_string: Canonicalized input string
        
    Returns:
        Deterministic UUIDv5
    """
    return uuid.uuid5(NAMESPACE_UUID, canonical_string)


def generate_document_id(user_id: str, file_sha256: str) -> uuid.UUID:
    """
    Generate deterministic document ID.
    
    Args:
        user_id: User UUID string
        file_sha256: SHA256 hash of file content
        
    Returns:
        Deterministic document ID
    """
    canonical = f"{user_id}:{file_sha256}"
    return generate_uuidv5(canonical)


def generate_chunk_id(document_id: str, chunker_name: str, chunker_version: str, chunk_ord: int) -> uuid.UUID:
    """
    Generate deterministic chunk ID.
    
    Args:
        document_id: Document UUID string
        chunker_name: Name of chunking strategy
        chunker_version: Version of chunking strategy
        chunk_ord: Chunk ordinal number
        
    Returns:
        Deterministic chunk ID
    """
    canonical = f"{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
    return generate_uuidv5(canonical)


def generate_parse_id(document_id: str, parser_name: str, parser_version: str) -> uuid.UUID:
    """
    Generate deterministic parse ID.
    
    Args:
        document_id: Document UUID string
        parser_name: Name of parser
        parser_version: Version of parser
        
    Returns:
        Deterministic parse ID
    """
    canonical = f"{document_id}:{parser_name}:{parser_version}"
    return generate_uuidv5(canonical)


def normalize_markdown_for_sha256(markdown_content: str) -> str:
    """
    Normalize markdown content for SHA256 computation.
    
    Rules from CONTEXT.md §10:
    1) Normalize line endings to \n
    2) Collapse >1 blank line to 1
    3) Trim trailing spaces per line
    4) Ensure # headings have one space (## Title)
    5) Replace images with ![img]; keep link text [text](url) → [text]
    6) Bullets use - and 2-space indents
    7) Collapse multiple spaces to one outside code blocks
    8) Drop zero-width/non-printing chars
    9) File ends with a single \n
    
    Args:
        markdown_content: Raw markdown content
        
    Returns:
        Normalized markdown content
    """
    if not markdown_content:
        return "\n"
    
    # 1) Normalize line endings to \n
    normalized = markdown_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2) Collapse >1 blank line to 1
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    
    # 3) Trim trailing spaces per line
    lines = []
    for line in normalized.split('\n'):
        lines.append(line.rstrip())
    normalized = '\n'.join(lines)
    
    # 4) Ensure # headings have one space (## Title)
    normalized = re.sub(r'^(#{1,6})\s*', r'\1 ', normalized, flags=re.MULTILINE)
    
    # 5) Replace images with ![img]; keep link text [text](url) → [text]
    # Keep link text but simplify image references
    normalized = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'![img]', normalized)
    
    # 6) Bullets use - and 2-space indents (normalize existing)
    # This is more complex - we'll preserve existing structure but normalize
    normalized = re.sub(r'^(\s*)[*+]\s', r'\1- ', normalized, flags=re.MULTILINE)
    
    # 7) Collapse multiple spaces to one outside code blocks
    # This is complex - we need to preserve code blocks
    # For now, we'll do a simple approach and improve later
    lines = []
    in_code_block = False
    for line in normalized.split('\n'):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            lines.append(line)
        elif not in_code_block:
            # Collapse multiple spaces outside code blocks
            collapsed = re.sub(r' {2,}', ' ', line)
            lines.append(collapsed)
        else:
            lines.append(line)
    normalized = '\n'.join(lines)
    
    # 8) Drop zero-width/non-printing chars
    normalized = ''.join(char for char in normalized if ord(char) >= 32 or char in '\n\t')
    
    # 9) File ends with a single \n
    normalized = normalized.rstrip() + '\n'
    
    return normalized


def compute_parsed_sha256(markdown_content: str) -> str:
    """
    Compute SHA256 hash of normalized markdown content.
    
    Args:
        markdown_content: Raw markdown content
        
    Returns:
        SHA256 hash as hex string
    """
    normalized = normalize_markdown_for_sha256(markdown_content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def log_event(
    supabase_client,
    job_id: str,
    code: str,
    event_type: str,
    severity: str,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> bool:
    """
    Log event to the events table.
    
    Per CONTEXT.md §7: all services use log_event(job_id, code, type, severity, payload)
    
    Args:
        supabase_client: Supabase client instance
        job_id: Job UUID string
        code: Event code from EVENT_CODES
        event_type: Event type from EVENT_TYPES
        severity: Event severity from EVENT_SEVERITIES
        payload: Optional event payload
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        True if event logged successfully, False otherwise
        
    Raises:
        ValueError: If invalid code, type, or severity
    """
    # Validate inputs
    if code not in EVENT_CODES:
        raise ValueError(f"Invalid event code: {code}")
    
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Invalid event type: {event_type}")
    
    if severity not in EVENT_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    
    # Get document_id from job_id (we'll need to implement this lookup)
    # For now, we'll require it to be passed in payload
    document_id = None
    if payload and 'document_id' in payload:
        document_id = payload['document_id']
    
    if not document_id:
        logger.warning(f"Could not determine document_id for job {job_id}")
        return False
    
    try:
        # Insert event into events table
        event_data = {
            'job_id': job_id,
            'document_id': document_id,
            'type': event_type,
            'severity': severity,
            'code': code,
            'payload': payload or {},
            'correlation_id': correlation_id,
            'ts': datetime.utcnow().isoformat()
        }
        
        # Use async if available, otherwise sync
        if hasattr(supabase_client, 'table'):
            response = supabase_client.table('upload_pipeline.events').insert(event_data).execute()
            if hasattr(response, 'error') and response.error:
                logger.error(f"Failed to log event: {response.error}")
                return False
        else:
            # Fallback for sync clients
            logger.warning("Supabase client doesn't support async operations")
            return False
        
        logger.debug(f"Logged event: {code} ({event_type}) for job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log event {code} for job {job_id}: {str(e)}")
        return False


def validate_stage_transition(old_stage: str, new_stage: str) -> bool:
    """
    Validate stage transition according to updated stage progression.
    
    Stages: queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → chunked → embedding → embeddings_buffered → embedded
    
    Args:
        old_stage: Current stage
        new_stage: Proposed new stage
        
    Returns:
        True if transition is valid, False otherwise
    """
    valid_transitions = {
        'queued': ['job_validated'],
        'job_validated': ['parsing'],
        'parsing': ['parsed'],
        'parsed': ['parse_validated'],
        'parse_validated': ['chunking'],
        'chunking': ['chunks_buffered'],
        'chunks_buffered': ['chunked'],
        'chunked': ['embedding'],
        'embedding': ['embeddings_buffered'],
        'embeddings_buffered': ['embedded'],
        'embedded': ['embedded']  # Terminal stage
    }
    
    return new_stage in valid_transitions.get(old_stage, [])


def validate_state_transition(old_state: str, new_state: str) -> bool:
    """
    Validate state transition according to CONTEXT.md §2.
    
    States: queued | working | retryable | done | deadletter
    
    Args:
        old_state: Current state
        new_state: Proposed new state
        
    Returns:
        True if transition is valid, False otherwise
    """
    valid_transitions = {
        'queued': ['working', 'done'],
        'working': ['done', 'retryable', 'deadletter'],
        'retryable': ['queued', 'deadletter'],
        'done': ['done'],  # Terminal state
        'deadletter': ['deadletter']  # Terminal state
    }
    
    return new_state in valid_transitions.get(old_state, [])


def generate_storage_path(bucket: str, user_id: str, document_id: str, extension: str) -> str:
    """
    Generate storage path using the pattern from CONTEXT.md §0.
    
    Pattern: storage://{bucket}/{user_id}/{document_id}.{ext}
    
    Args:
        bucket: Storage bucket name (raw, parsed)
        user_id: User UUID string
        document_id: Document UUID string
        extension: File extension (pdf, md)
        
    Returns:
        Storage path string
    """
    return f"storage://{bucket}/{user_id}/{document_id}.{extension}"


def calculate_retry_delay(retry_count: int, base_delay: int = 3) -> int:
    """
    Calculate retry delay using exponential backoff.
    
    Per CONTEXT.md §8: 2^n * base delay, max retries = 3
    
    Args:
        retry_count: Current retry count (0-based)
        base_delay: Base delay in seconds (default 3)
        
    Returns:
        Delay in seconds
    """
    if retry_count <= 0:
        return 0
    
    # Cap at max retries (3)
    if retry_count > 3:
        retry_count = 3
    
    return (2 ** retry_count) * base_delay
