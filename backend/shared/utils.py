import uuid
import hashlib
import json
from typing import Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

# Namespace UUID for deterministic ID generation
NAMESPACE_UUID = uuid.UUID('6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42')

def canonicalize_string(input_str: str) -> str:
    """Canonicalize string for deterministic UUID generation"""
    if not input_str:
        return ""
    
    # Convert to lowercase
    result = input_str.lower()
    
    # Remove control characters
    result = ''.join(char for char in result if ord(char) >= 32)
    
    # Normalize whitespace
    result = ' '.join(result.split())
    
    return result

def canonicalize_json(data: Union[Dict[str, Any], list]) -> str:
    """Canonicalize JSON data for deterministic UUID generation"""
    if isinstance(data, dict):
        # Sort keys and create canonical representation
        sorted_items = sorted(data.items())
        canonical_dict = {k: canonicalize_json(v) for k, v in sorted_items}
        return json.dumps(canonical_dict, separators=(',', ':'), sort_keys=True)
    elif isinstance(data, list):
        # Canonicalize list items
        canonical_list = [canonicalize_json(item) for item in data]
        return json.dumps(canonical_list, separators=(',', ':'), sort_keys=True)
    else:
        # Convert to string and canonicalize
        return canonicalize_string(str(data))

def generate_document_id(user_id: str, file_sha256: str) -> uuid.UUID:
    """Generate deterministic document ID using UUIDv5"""
    canonical_input = f"{user_id}:{file_sha256}"
    canonical_input = canonicalize_string(canonical_input)
    return uuid.uuid5(NAMESPACE_UUID, canonical_input)

def generate_chunk_id(document_id: str, chunker_name: str, chunker_version: str, chunk_ord: int) -> uuid.UUID:
    """Generate deterministic chunk ID using UUIDv5"""
    canonical_input = f"{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
    canonical_input = canonicalize_string(canonical_input)
    return uuid.uuid5(NAMESPACE_UUID, canonical_input)

def generate_parse_id(document_id: str, parser_name: str, parser_version: str) -> uuid.UUID:
    """Generate deterministic parse ID using UUIDv5"""
    canonical_input = f"{document_id}:{parser_name}:{parser_version}"
    canonical_input = canonicalize_string(canonical_input)
    return uuid.uuid5(NAMESPACE_UUID, canonical_input)

def compute_content_sha256(content: str) -> str:
    """Compute SHA256 hash of content"""
    if not content:
        return hashlib.sha256(b"").hexdigest()
    
    # Normalize content for consistent hashing
    normalized = content.encode('utf-8')
    return hashlib.sha256(normalized).hexdigest()

def compute_vector_sha256(vector: list) -> str:
    """Compute SHA256 hash of vector data"""
    if not vector:
        return hashlib.sha256(b"").hexdigest()
    
    # Convert vector to canonical string representation
    vector_str = json.dumps(vector, separators=(',', ':'), sort_keys=True)
    return hashlib.sha256(vector_str.encode('utf-8')).hexdigest()

def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID string format"""
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False

def generate_correlation_id() -> uuid.UUID:
    """Generate unique correlation ID for request tracking"""
    return uuid.uuid4()

def log_operation(operation: str, **kwargs):
    """Log operation with structured data"""
    log_data = {
        "operation": operation,
        "timestamp": str(uuid.uuid1().time),
        **kwargs
    }
    logger.info(f"Operation: {operation}", extra=log_data)
