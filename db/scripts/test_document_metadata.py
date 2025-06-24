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
            'document_info': {
                'title': 'Medicare Coverage Guidelines 2024',
                'author': 'Test Author',
                'creation_date': '2024-01-01',
                'last_modified': '2024-01-15',
                'page_count': 50,
                'sections': [
                    {
                        'title': 'Introduction',
                        'page_number': 1,
                        'content_length': 500
                    },
                    {
                        'title': 'Coverage Policies',
                        'page_number': 10,
                        'content_length': 2000
                    },
                    {
                        'title': 'Eligibility Requirements',
                        'page_number': 25,
                        'content_length': 1500
                    }
                ]
            },
            'processing_info': {
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': 120,
                'processor_version': '1.0.0',
                'processing_steps': [
                    {
                        'step': 'document_upload',
                        'status': 'completed',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'step': 'text_extraction',
                        'status': 'completed',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'step': 'metadata_extraction',
                        'status': 'completed',
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            },
            'test_metadata': {
                'test_id': 'metadata_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'completed',
        'content': 'Test content for Medicare coverage guidelines.'
    }
]

async def test_document_metadata():
    """Test document metadata handling."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document metadata handling...")
        
        for idx, doc in enumerate(test_documents, 1):
            print(f"\n📝 Testing document {idx} metadata...")
            
            # Insert document with metadata
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
            print(f"✅ Document {idx} inserted successfully (ID: {document_id})")
            
            # Test metadata retrieval
            metadata = await conn.fetchrow(
                '''
                SELECT metadata
                FROM documents
                WHERE id = $1;
                ''',
                document_id
            )
            
            print("\n📊 Testing metadata retrieval...")
            retrieved_metadata = metadata['metadata']
            print(f"✅ Retrieved metadata: {json.dumps(retrieved_metadata, indent=2)}")
            
            # Test metadata update
            print("\n🔄 Testing metadata update...")
            new_metadata = doc['metadata'].copy()
            new_metadata['processing_info']['status'] = 'updated'
            new_metadata['processing_info']['last_updated'] = datetime.now().isoformat()
            
            await conn.execute(
                '''
                UPDATE documents
                SET metadata = $1,
                    updated_at = $2
                WHERE id = $3;
                ''',
                json.dumps(new_metadata),
                datetime.now(),
                document_id
            )
            print("✅ Metadata updated successfully")
            
            # Verify metadata update
            updated_metadata = await conn.fetchrow(
                '''
                SELECT metadata
                FROM documents
                WHERE id = $1;
                ''',
                document_id
            )
            
            print("\n🔍 Verifying metadata update...")
            print(f"✅ Updated metadata: {json.dumps(updated_metadata['metadata'], indent=2)}")
            
            # Test metadata search
            print("\n🔎 Testing metadata search...")
            search_result = await conn.fetch(
                '''
                SELECT id, original_filename
                FROM documents
                WHERE metadata->>'processing_timestamp' IS NOT NULL
                AND metadata->'document_info'->>'title' = $1;
                ''',
                'Medicare Coverage Guidelines 2024'
            )
            
            print("Search results:")
            for row in search_result:
                print(f"✅ Found document {row['id']}: {row['original_filename']}")
        
        print("\n✨ Document metadata test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document metadata test."""
    await test_document_metadata()

if __name__ == "__main__":
    asyncio.run(main())