#!/usr/bin/env python3
"""
Check Document Completion Status
"""

import os
from supabase import create_client

def check_completion_status():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(supabase_url, supabase_key)

    print('🔍 Checking Document Status Distribution')
    print('=' * 50)

    # Get all document statuses
    docs = supabase.table('documents').select('status').execute()
    status_counts = {}
    for doc in docs.data:
        status = doc['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    print('📊 Document Status Distribution:')
    total = len(docs.data)
    for status, count in sorted(status_counts.items()):
        percentage = (count / total) * 100
        print(f'   {status}: {count} ({percentage:.1f}%)')

    print(f'\nTotal documents: {total}')

    # Check completed documents
    completed = supabase.table('documents').select('id, original_filename, status, progress_percentage').eq('status', 'completed').execute()
    print(f'\n✅ Completed documents: {len(completed.data)}')
    for doc in completed.data:
        print(f'   • {doc["original_filename"]} - Progress: {doc.get("progress_percentage", 0)}%')

    # Check for any documents that moved from parsing to another status recently
    recent_docs = supabase.table('documents').select('id, original_filename, status, progress_percentage, updated_at').order('updated_at', desc=True).limit(10).execute()
    print(f'\n📅 Recently Updated Documents (last 10):')
    for doc in recent_docs.data:
        print(f'   • {doc["original_filename"]} | Status: {doc["status"]} | Progress: {doc.get("progress_percentage", 0)}% | Updated: {doc.get("updated_at", "unknown")}')

    print(f'\n⚠️ Your success criteria: ALL parsing documents should move to completed status')
    
    return {
        'total': total,
        'status_counts': status_counts,
        'completed_count': len(completed.data)
    }

if __name__ == '__main__':
    check_completion_status() 