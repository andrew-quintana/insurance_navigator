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
    # Federal document
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
            'jurisdiction_info': {
                'level': 'federal',
                'agency': 'CMS',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'supersedes': None,
                'superseded_by': None
            },
            'test_metadata': {
                'test_id': 'jurisdiction_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines', 'federal'],
        'status': 'completed',
        'content': 'Test content for federal Medicare coverage guidelines.'
    },
    # State document
    {
        'original_filename': 'California Medicare Savings Programs',
        'storage_path': 'test/ca_medicare_savings_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'state',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 4000,
            'extraction_method': 'doc_parser',
            'jurisdiction_info': {
                'level': 'state',
                'state': 'CA',
                'agency': 'DHCS',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'supersedes': None,
                'superseded_by': None
            },
            'test_metadata': {
                'test_id': 'jurisdiction_test_002',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'state', 'california'],
        'status': 'completed',
        'content': 'Test content for California Medicare Savings Programs.'
    },
    # County document
    {
        'original_filename': 'Los Angeles County Medicare Resources',
        'storage_path': 'test/la_medicare_resources_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'county',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 3000,
            'extraction_method': 'doc_parser',
            'jurisdiction_info': {
                'level': 'county',
                'state': 'CA',
                'county': 'Los Angeles',
                'agency': 'DPSS',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'supersedes': None,
                'superseded_by': None
            },
            'test_metadata': {
                'test_id': 'jurisdiction_test_003',
                'test_type': 'integration'
            }
        },
        'tags': ['resources', 'county', 'los_angeles'],
        'status': 'completed',
        'content': 'Test content for Los Angeles County Medicare resources.'
    }
]

async def test_document_jurisdiction():
    """Test document jurisdiction functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document jurisdiction...")
        
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
        
        # Test jurisdiction queries
        print("\n🔍 Testing jurisdiction queries...")
        
        # Test 1: Query by jurisdiction level
        print("\n📊 Testing jurisdiction level queries...")
        for level in ['federal', 'state', 'county']:
            result = await conn.fetch(
                '''
                SELECT 
                    d.id,
                    d.original_filename,
                    d.jurisdiction,
                    d.metadata->'jurisdiction_info' as jurisdiction_info
                FROM documents d
                WHERE d.jurisdiction = $1;
                ''',
                level
            )
            
            print(f"\nDocuments with {level} jurisdiction:")
            for row in result:
                print(f"  Document {row['id']}: {row['original_filename']}")
                print(f"  Jurisdiction info: {json.dumps(row['jurisdiction_info'], indent=2)}")
        
        # Test 2: Query by state
        print("\n🗺️ Testing state-specific queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.jurisdiction,
                d.metadata->'jurisdiction_info' as jurisdiction_info
            FROM documents d
            WHERE d.metadata->'jurisdiction_info'->>'state' = $1;
            ''',
            'CA'
        )
        
        print("\nDocuments for California:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Jurisdiction: {row['jurisdiction']}")
            print(f"  Jurisdiction info: {json.dumps(row['jurisdiction_info'], indent=2)}")
        
        # Test 3: Query by county
        print("\n🏛️ Testing county-specific queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.jurisdiction,
                d.metadata->'jurisdiction_info' as jurisdiction_info
            FROM documents d
            WHERE d.metadata->'jurisdiction_info'->>'county' = $1;
            ''',
            'Los Angeles'
        )
        
        print("\nDocuments for Los Angeles County:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Jurisdiction: {row['jurisdiction']}")
            print(f"  Jurisdiction info: {json.dumps(row['jurisdiction_info'], indent=2)}")
        
        # Test 4: Query by effective date
        print("\n📅 Testing effective date queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.jurisdiction,
                d.metadata->'jurisdiction_info' as jurisdiction_info
            FROM documents d
            WHERE d.metadata->'jurisdiction_info'->>'effective_date' >= $1
            ORDER BY d.metadata->'jurisdiction_info'->>'effective_date';
            ''',
            '2024-01-01'
        )
        
        print("\nDocuments effective from 2024:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Jurisdiction: {row['jurisdiction']}")
            print(f"  Effective date: {row['jurisdiction_info']['effective_date']}")
        
        print("\n✨ Document jurisdiction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document jurisdiction test."""
    await test_document_jurisdiction()

if __name__ == "__main__":
    asyncio.run(main())
""" 