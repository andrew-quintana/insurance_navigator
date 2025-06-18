#!/usr/bin/env python3
"""
Investigate documents with null file_path values
"""

import sys
import os
from datetime import datetime, timedelta
from supabase import create_client, Client

def investigate_null_filepaths():
    print('🔍 Investigating Documents with Null File Paths')
    print('=' * 60)
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables')
        return None
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Check documents with null file_path
    print('\n📊 Step 1: Documents with null file_path')
    print('-' * 40)
    result = supabase.table('documents').select('id, original_filename, status, file_path, storage_path, progress_percentage, created_at').is_('file_path', 'null').execute()
    
    print(f'Found {len(result.data)} documents with null file_path:')
    for doc in result.data:
        storage_info = f"storage_path: {doc.get('storage_path', 'null')}"
        print(f'  • {doc["id"][:8]}... | {doc["original_filename"]} | {doc["status"]} | {storage_info}')
    
    # Check documents with null storage_path too
    print('\n📊 Step 2: Documents with null storage_path')
    print('-' * 40)
    storage_result = supabase.table('documents').select('id, original_filename, status, file_path, storage_path, progress_percentage').is_('storage_path', 'null').execute()
    
    print(f'Found {len(storage_result.data)} documents with null storage_path:')
    for doc in storage_result.data:
        file_info = f"file_path: {doc.get('file_path', 'null')}"
        print(f'  • {doc["id"][:8]}... | {doc["original_filename"]} | {doc["status"]} | {file_info}')
    
    # Check stuck parsing documents
    print('\n📊 Step 3: Stuck parsing documents analysis')
    print('-' * 40)
    parsing_result = supabase.table('documents').select('id, original_filename, file_path, storage_path, progress_percentage, created_at').eq('status', 'parsing').execute()
    
    # Find parsing docs with no file reference
    null_parsing = []
    for doc in parsing_result.data:
        has_file_path = doc.get('file_path') and doc.get('file_path') != 'null'
        has_storage_path = doc.get('storage_path') and doc.get('storage_path') != 'null'
        if not has_file_path and not has_storage_path:
            null_parsing.append(doc)
    
    print(f'Parsing documents with no file reference: {len(null_parsing)}/{len(parsing_result.data)}')
    
    for doc in null_parsing:
        age = (datetime.now() - datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))).total_seconds() / 60
        print(f'  • {doc["id"][:8]}... | {doc["original_filename"]} | progress: {doc.get("progress_percentage", 0)}% | age: {age:.1f}m')
    
    # Check recent uploads (last 24h) with issues
    print('\n📊 Step 4: Recent uploads with file path issues')
    print('-' * 40)
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    recent_result = supabase.table('documents').select('id, original_filename, status, file_path, storage_path, created_at').gte('created_at', yesterday).execute()
    
    recent_issues = []
    for doc in recent_result.data:
        has_file_path = doc.get('file_path') and doc.get('file_path') != 'null'
        has_storage_path = doc.get('storage_path') and doc.get('storage_path') != 'null'
        if not has_file_path and not has_storage_path:
            recent_issues.append(doc)
    
    print(f'Recent uploads (24h) with file path issues: {len(recent_issues)}/{len(recent_result.data)}')
    
    for doc in recent_issues:
        age = (datetime.now() - datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))).total_seconds() / 60
        print(f'  • {doc["id"][:8]}... | {doc["original_filename"]} | {doc["status"]} | age: {age:.1f}m')
    
    return {
        'null_file_path': result.data,
        'null_storage_path': storage_result.data,
        'stuck_parsing': null_parsing,
        'recent_issues': recent_issues
    }

if __name__ == '__main__':
    results = investigate_null_filepaths()
    
    print(f'\n📋 Summary:')
    print(f'  • Documents with null file_path: {len(results["null_file_path"])}')
    print(f'  • Documents with null storage_path: {len(results["null_storage_path"])}')
    print(f'  • Stuck parsing docs (no file ref): {len(results["stuck_parsing"])}')
    print(f'  • Recent issues (24h): {len(results["recent_issues"])}')
    
    if results['stuck_parsing']:
        print(f'\n⚠️  {len(results["stuck_parsing"])} documents are stuck in parsing with no file reference!')
        print('   These will never complete and should be cleaned up.') 