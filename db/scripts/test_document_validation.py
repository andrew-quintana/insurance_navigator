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
    # Valid document
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
                'test_id': 'validation_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'completed',
        'content': 'Valid test content for Medicare coverage guidelines.'
    },
    # Invalid document - missing required fields
    {
        'original_filename': None,  # Required field
        'storage_path': None,  # Required field
        'document_type': 'user_uploaded',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': None,  # Required field
        'priority_score': None,  # Required field
        'metadata': None,  # Required field
        'tags': None,  # Required field
        'status': None,  # Required field
        'content': 'Invalid test document missing required fields.'
    },
    # Invalid document - invalid field values
    {
        'original_filename': 'Medicare Coverage Guidelines 2024',
        'storage_path': 'test/medicare_coverage_2024.pdf',
        'document_type': 'invalid_type',  # Invalid value
        'jurisdiction': 'invalid_jurisdiction',  # Invalid value
        'program': 'Medicare',  # Should be an array
        'source_url': 'not_a_valid_url',  # Invalid URL format
        'source_last_checked': 'not_a_date',  # Invalid date format
        'priority_score': 'not_a_number',  # Invalid number format
        'metadata': 'not_a_json_object',  # Invalid JSON format
        'tags': 'not_an_array',  # Should be an array
        'status': 'invalid_status',  # Invalid value
        'content': 'Invalid test document with invalid field values.'
    }
]

async def test_document_validation():
    """Test document validation rules."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document validation...")
        
        for idx, doc in enumerate(test_documents, 1):
            print(f"\n📝 Testing document {idx}...")
            
            try:
                # Attempt to insert document
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
                    json.dumps(doc['metadata']) if doc['metadata'] else None,
                    doc['tags'],
                    doc['status'],
                    datetime.now(),
                    datetime.now()
                )
                
                print(f"✅ Document {idx} inserted successfully (ID: {result['id']})")
                
                # Test content insertion
                try:
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
                    
                except Exception as e:
                    print(f"❌ Content insertion failed for document {idx}: {str(e)}")
                
            except Exception as e:
                print(f"❌ Document {idx} validation failed: {str(e)}")
                print("Expected failure for invalid test documents")
        
        print("\n✨ Document validation test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document validation test."""
    await test_document_validation()

if __name__ == "__main__":
    asyncio.run(main())