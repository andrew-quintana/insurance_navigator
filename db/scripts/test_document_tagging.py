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
                'test_id': 'tag_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'completed',
        'content': 'Test content for Medicare coverage guidelines.'
    },
    {
        'original_filename': 'Medicare Claims Processing Updates',
        'storage_path': 'test/medicare_claims_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 4000,
            'extraction_method': 'doc_parser',
            'test_metadata': {
                'test_id': 'tag_test_002',
                'test_type': 'integration'
            }
        },
        'tags': ['claims', 'processing'],
        'status': 'completed',
        'content': 'Test content for Medicare claims processing.'
    }
]

async def test_document_tagging():
    """Test document tagging functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document tagging...")
        
        document_ids = []
        for idx, doc in enumerate(test_documents, 1):
            # Insert document
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
            
            document_ids.append(result['id'])
            print(f"✅ Document {idx} inserted successfully (ID: {result['id']})")
            
            # Insert content
            await conn.execute(
                '''
                INSERT INTO document_contents (
                    document_id, content, created_at, updated_at
                ) VALUES ($1, $2, $3, $4);
                ''',
                result['id'],
                doc['content'],
                datetime.now(),
                datetime.now()
            )
            print(f"✅ Content for document {idx} inserted successfully")
        
        # Test tag operations
        print("\n🏷️ Testing tag operations...")
        
        # Test 1: Add tags
        print("\n📝 Testing tag addition...")
        for document_id in document_ids:
            new_tags = ['test_tag', 'automated_test']
            
            await conn.execute(
                '''
                UPDATE documents
                SET tags = array_cat(tags, $1::text[]),
                    updated_at = $2,
                    metadata = jsonb_set(
                        metadata::jsonb,
                        '{tag_history}',
                        (COALESCE(metadata::jsonb->'tag_history', '[]'::jsonb) || 
                         jsonb_build_object(
                             'action', 'add',
                             'tags', $1,
                             'timestamp', $3
                         )::jsonb)
                    )
                WHERE id = $4;
                ''',
                new_tags,
                datetime.now(),
                datetime.now().isoformat(),
                document_id
            )
            print(f"✅ Added tags to document {document_id}")
        
        # Test 2: Remove tags
        print("\n🗑️ Testing tag removal...")
        for document_id in document_ids:
            remove_tags = ['test_tag']
            
            await conn.execute(
                '''
                UPDATE documents
                SET tags = array_remove(tags, ALL ($1::text[])),
                    updated_at = $2,
                    metadata = jsonb_set(
                        metadata::jsonb,
                        '{tag_history}',
                        (COALESCE(metadata::jsonb->'tag_history', '[]'::jsonb) || 
                         jsonb_build_object(
                             'action', 'remove',
                             'tags', $1,
                             'timestamp', $3
                         )::jsonb)
                    )
                WHERE id = $4;
                ''',
                remove_tags,
                datetime.now(),
                datetime.now().isoformat(),
                document_id
            )
            print(f"✅ Removed tags from document {document_id}")
        
        # Test 3: Search by tags
        print("\n🔎 Testing tag search...")
        
        # Search for documents with specific tags
        result = await conn.fetch(
            '''
            SELECT id, original_filename, tags
            FROM documents
            WHERE tags && $1;
            ''',
            ['automated_test']
        )
        
        print("Documents with 'automated_test' tag:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Tags: {row['tags']}")
        
        # Test 4: Tag history
        print("\n📊 Testing tag history...")
        
        for document_id in document_ids:
            metadata = await conn.fetchrow(
                '''
                SELECT metadata->'tag_history' as tag_history
                FROM documents
                WHERE id = $1;
                ''',
                document_id
            )
            
            tag_history = metadata['tag_history']
            print(f"\nTag history for document {document_id}:")
            for entry in tag_history:
                print(f"  Action: {entry['action']}")
                print(f"  Tags: {entry['tags']}")
                print(f"  Timestamp: {entry['timestamp']}")
        
        print("\n✨ Document tagging test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document tagging test."""
    await test_document_tagging()

if __name__ == "__main__":
    asyncio.run(main())