#!/usr/bin/env python3
"""
Script to update buffer table references to direct-write architecture
Following Phase 3.7 buffer table bypass optimization
"""

import os
import re
from pathlib import Path

def fix_file_references(file_path):
    """Fix buffer table references in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace buffer table queries with document_chunks queries
    content = re.sub(
        r'SELECT COUNT\(\*\) FROM upload_pipeline\.document_chunk_buffer',
        'SELECT COUNT(*) FROM upload_pipeline.document_chunks',
        content
    )
    
    content = re.sub(
        r'SELECT COUNT\(\*\) FROM upload_pipeline\.document_vector_buffer',
        'SELECT COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) FROM upload_pipeline.document_chunks',
        content
    )
    
    # Replace buffer table deletions
    content = re.sub(
        r'DELETE FROM upload_pipeline\.document_vector_buffer\s+WHERE document_id = \$1',
        'UPDATE upload_pipeline.document_chunks SET embedding = NULL WHERE document_id = $1',
        content
    )
    
    content = re.sub(
        r'DELETE FROM upload_pipeline\.document_chunk_buffer\s+WHERE document_id = \$1',
        'DELETE FROM upload_pipeline.document_chunks WHERE document_id = $1',
        content
    )
    
    # Replace buffer operation logging
    content = re.sub(
        r'table="document_chunk_buffer"',
        'table="document_chunks"',
        content
    )
    
    content = re.sub(
        r'table="document_vector_buffer"',
        'table="document_chunks"',
        content
    )
    
    # Add comment for buffer-related code sections
    if 'document_chunk_buffer' in original_content or 'document_vector_buffer' in original_content:
        if content != original_content:
            content = f"""# Buffer table references updated for Phase 3.7 direct-write architecture
# Original buffer-based approach replaced with direct writes to document_chunks

{content}"""
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated {file_path}")
        return True
    
    return False

def main():
    """Update all buffer table references in backend code"""
    backend_dir = Path('/Users/aq_home/1Projects/accessa/insurance_navigator/backend')
    
    # Find all Python files that might have buffer table references
    files_to_fix = [
        backend_dir / 'tests/e2e/test_security_validation.py',
        backend_dir / 'tests/e2e/test_complete_pipeline.py', 
        backend_dir / 'tests/e2e/test_performance_validation.py',
        backend_dir / 'test_embedding_stage.py',
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_file_references(file_path):
                fixed_count += 1
        else:
            print(f"⚠ File not found: {file_path}")
    
    print(f"\n✅ Updated {fixed_count} files for Phase 3.7 direct-write architecture")
    print("🔄 Buffer table bypass optimization complete")

if __name__ == "__main__":
    main()