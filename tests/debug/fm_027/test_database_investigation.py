#!/usr/bin/env python3
"""
FM-027: Database Investigation
Check the failed job details in the database
"""

import asyncio
import json
from config.database import get_database

async def investigate_failed_job():
    """Investigate the failed job in the database"""
    
    print('🔍 INVESTIGATING FAILED JOB IN DATABASE')
    print('=' * 50)
    
    # Job details from the error
    job_id = 'd2318f14-0473-42e6-8e82-d3c63b25220c'
    document_id = '2f064818-4568-5ca2-ad05-e26484d8f1c4'
    user_id = '74a635ac-4bfe-4b6e-87d2-c0f54a366fbe'
    
    print(f'Job ID: {job_id}')
    print(f'Document ID: {document_id}')
    print(f'User ID: {user_id}')
    
    try:
        db = get_database()
        async with db.get_connection() as conn:
            
            # Get job details
            print('\n1️⃣ JOB DETAILS FROM DATABASE')
            print('-' * 40)
            
            job_query = '''
                SELECT job_id, document_id, user_id, status, state, last_error, 
                       created_at, updated_at, storage_path
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            '''
            
            job_result = await conn.fetchrow(job_query, job_id)
            if job_result:
                print(f'  Job ID: {job_result["job_id"]}')
                print(f'  Document ID: {job_result["document_id"]}')
                print(f'  User ID: {job_result["user_id"]}')
                print(f'  Status: {job_result["status"]}')
                print(f'  State: {job_result["state"]}')
                print(f'  Storage Path: {job_result.get("storage_path", "None")}')
                print(f'  Last Error: {job_result.get("last_error", "None")}')
                print(f'  Created: {job_result["created_at"]}')
                print(f'  Updated: {job_result["updated_at"]}')
            else:
                print('❌ Job not found in database')
            
            # Get document details
            print('\n2️⃣ DOCUMENT DETAILS FROM DATABASE')
            print('-' * 40)
            
            doc_query = '''
                SELECT document_id, user_id, filename, raw_path, created_at
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            '''
            
            doc_result = await conn.fetchrow(doc_query, document_id)
            if doc_result:
                print(f'  Document ID: {doc_result["document_id"]}')
                print(f'  User ID: {doc_result["user_id"]}')
                print(f'  Filename: {doc_result["filename"]}')
                print(f'  Raw Path: {doc_result.get("raw_path", "None")}')
                print(f'  Created: {doc_result["created_at"]}')
            else:
                print('❌ Document not found in database')
            
            # Check recent jobs for this user
            print('\n3️⃣ RECENT JOBS FOR USER')
            print('-' * 40)
            
            recent_jobs_query = '''
                SELECT job_id, document_id, status, state, storage_path, created_at
                FROM upload_pipeline.upload_jobs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            '''
            
            recent_jobs = await conn.fetch(recent_jobs_query, user_id)
            print(f'Found {len(recent_jobs)} recent jobs for user {user_id}:')
            for i, job in enumerate(recent_jobs):
                print(f'  {i+1}. Job: {job["job_id"]}')
                print(f'     Document: {job["document_id"]}')
                print(f'     Status: {job["status"]}')
                print(f'     Storage Path: {job.get("storage_path", "None")}')
                print(f'     Created: {job["created_at"]}')
                print()
            
            # Check recent documents for this user
            print('\n4️⃣ RECENT DOCUMENTS FOR USER')
            print('-' * 40)
            
            recent_docs_query = '''
                SELECT document_id, filename, raw_path, created_at
                FROM upload_pipeline.documents 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            '''
            
            recent_docs = await conn.fetch(recent_docs_query, user_id)
            print(f'Found {len(recent_docs)} recent documents for user {user_id}:')
            for i, doc in enumerate(recent_docs):
                print(f'  {i+1}. Document: {doc["document_id"]}')
                print(f'     Filename: {doc["filename"]}')
                print(f'     Raw Path: {doc.get("raw_path", "None")}')
                print(f'     Created: {doc["created_at"]}')
                print()
                
    except Exception as e:
        print(f'❌ Database access failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_failed_job())
