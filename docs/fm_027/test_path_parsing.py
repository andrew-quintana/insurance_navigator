#!/usr/bin/env python3
"""
Test the storage path parsing logic
"""

def _parse_storage_path(path: str) -> tuple[str, str]:
    """Parse storage path to extract bucket and key"""
    # Handle both formats:
    # 1. storage://{bucket}/user/{user_id}/{document_id}.{ext}
    # 2. files/user/{user_id}/{document_id}.{ext} (legacy format from database)
    
    if path.startswith("storage://"):
        # Remove storage:// prefix
        path_without_prefix = path[10:]
    elif path.startswith("files/"):
        # Legacy format: files/user/... -> bucket=files, key=user/...
        path_without_prefix = path
    else:
        raise ValueError(f"Invalid storage path format: {path}. Expected 'storage://' or 'files/' prefix")
    
    # Split by first slash to get bucket
    parts = path_without_prefix.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid storage path format: {path}")
    
    bucket, key = parts
    return bucket, key

# Test with the actual file path
actual_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"

print(f"Input path: {actual_file_path}")
bucket, key = _parse_storage_path(actual_file_path)
print(f"Parsed bucket: {bucket}")
print(f"Parsed key: {key}")

# The correct parsing should be:
# bucket = "files"
# key = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf"

print(f"\nExpected bucket: files")
print(f"Expected key: user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf")
print(f"Actual bucket: {bucket}")
print(f"Actual key: {key}")
print(f"Bucket correct: {bucket == 'files'}")
print(f"Key correct: {key == 'user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf'}")
