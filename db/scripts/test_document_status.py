"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'insurance_navigator')
}

test_documents = [
    {
        'original_filename': 'Medicare Coverage Guidelines 2024',
        'storage_path': 'test/medicare_coverage_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 5000,
            'extraction_method': 'doc_parser',
            'test_metadata': {
                'test_id': 'status_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'pending',
        'content': 'Test content for Medicare coverage guidelines.'
    }
]

async def test_document_status():
    """Test document status transitions."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document status transitions...")
        
        # Insert test document
        doc = test_documents[0]
        result = await conn.fetchrow(
            '''
            INSERT INTO documents (
                original_filename, storage_path, document_type, jurisdiction,
                program, source_url, source_last_checked, priority_score,
                metadata, tags, status, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            ) RETURNING id;
            ''',
            doc['original_filename'],
            doc['storage_path'],
            doc['document_type'],
            doc['jurisdiction'],
            doc['program'],
            doc['source_url'],
            doc['source_last_checked'],
            doc['priority_score'],
            json.dumps(doc['metadata']),
            doc['tags'],
            doc['status'],
            datetime.now(),
            datetime.now()
        )
        
        document_id = result['id']
        print(f"✅ Document inserted successfully (ID: {document_id})")
        
        # Test status transitions
        status_transitions = [
            ('pending', 'processing'),
            ('processing', 'validating'),
            ('validating', 'indexing'),
            ('indexing', 'completed'),
            ('completed', 'error'),  # Test error transition
            ('error', 'pending'),    # Test recovery
            ('pending', 'completed') # Final state
        ]
        
        for old_status, new_status in status_transitions:
            print(f"\n🔄 Testing status transition: {old_status} -> {new_status}")
            
            # Update status
            await conn.execute(
                '''
                UPDATE documents
                SET status = $1,
                    updated_at = $2,
                    metadata = jsonb_set(
                        metadata::jsonb,
                        '{processing_info,status_history}',
                        (COALESCE(metadata::jsonb->'processing_info'->'status_history', '[]'::jsonb) || 
                         jsonb_build_object(
                             'from_status', $3,
                             'to_status', $1,
                             'timestamp', $4,
                             'reason', $5
                         )::jsonb)
                    )
                WHERE id = $6;
                ''',
                new_status,
                datetime.now(),
                old_status,
                datetime.now().isoformat(),
                f"Test transition from {old_status} to {new_status}",
                document_id
            )
            
            # Verify status update
            status = await conn.fetchrow(
                '''
                SELECT status, metadata
                FROM documents
                WHERE id = $1;
                ''',
                document_id
            )
            
            print(f"✅ Status updated to: {status['status']}")
            print("Status history:")
            status_history = status['metadata']['processing_info']['status_history']
            for entry in status_history:
                print(f"  {entry['from_status']} -> {entry['to_status']} ({entry['reason']})")
        
        print("\n✨ Document status test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document status test."""
    await test_document_status()

if __name__ == "__main__":
    asyncio.run(main())
""" 