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

test_document = {
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
            'test_id': 'version_test_001',
            'test_type': 'integration'
        }
    },
    'tags': ['coverage', 'guidelines'],
    'status': 'completed',
    'content': '''
    Medicare Coverage Guidelines 2024 - Version 1
    
    This document outlines the coverage guidelines for Medicare services in 2024.
    
    1. Preventive Services
       - Annual wellness visits
       - Vaccinations
       - Cancer screenings
    
    2. Hospital Services
       - Inpatient care
       - Emergency services
       - Outpatient procedures
    
    3. Prescription Drug Coverage
       - Part D plans
       - Formulary requirements
       - Coverage gaps
    '''
}

async def test_document_versioning():
    """Test document versioning functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document versioning...")
        
        # Insert initial version
        print("\n📝 Creating initial document version...")
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
            test_document['original_filename'],
            test_document['storage_path'],
            test_document['document_type'],
            test_document['jurisdiction'],
            test_document['program'],
            test_document['source_url'],
            test_document['source_last_checked'],
            test_document['priority_score'],
            json.dumps(test_document['metadata']),
            test_document['tags'],
            test_document['status'],
            datetime.now(),
            datetime.now()
        )
        
        document_id = result['id']
        print(f"✅ Initial document version created (ID: {document_id})")
        
        # Insert initial content
        await conn.execute(
            '''
            INSERT INTO document_contents (
                document_id, content, created_at, updated_at
            ) VALUES ($1, $2, $3, $4);
            ''',
            document_id,
            test_document['content'],
            datetime.now(),
            datetime.now()
        )
        print("✅ Initial content inserted")
        
        # Create document versions
        print("\n📝 Testing document versioning...")
        
        versions = [
            {
                'version_number': 2,
                'changes': 'Updated preventive services section',
                'content': test_document['content'].replace('Version 1', 'Version 2').replace(
                    'Annual wellness visits',
                    'Annual wellness visits (updated coverage)'
                )
            },
            {
                'version_number': 3,
                'changes': 'Updated hospital services section',
                'content': test_document['content'].replace('Version 1', 'Version 3').replace(
                    'Hospital Services',
                    'Hospital Services (expanded coverage)'
                )
            },
            {
                'version_number': 4,
                'changes': 'Updated prescription drug coverage section',
                'content': test_document['content'].replace('Version 1', 'Version 4').replace(
                    'Prescription Drug Coverage',
                    'Prescription Drug Coverage (new formulary)'
                )
            }
        ]
        
        for version in versions:
            # Create version record
            await conn.execute(
                '''
                INSERT INTO document_versions (
                    document_id, version_number, changes,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5);
                ''',
                document_id,
                version['version_number'],
                version['changes'],
                datetime.now(),
                datetime.now()
            )
            
            # Update document content
            await conn.execute(
                '''
                UPDATE document_contents
                SET content = $1,
                    updated_at = $2
                WHERE document_id = $3;
                ''',
                version['content'],
                datetime.now(),
                document_id
            )
            
            # Update document metadata
            await conn.execute(
                '''
                UPDATE documents
                SET metadata = jsonb_set(
                    metadata::jsonb,
                    '{version_history}',
                    (COALESCE(metadata::jsonb->'version_history', '[]'::jsonb) || 
                     jsonb_build_object(
                         'version_number', $1,
                         'changes', $2,
                         'timestamp', $3
                     )::jsonb)
                ),
                updated_at = $4
                WHERE id = $5;
                ''',
                version['version_number'],
                version['changes'],
                datetime.now().isoformat(),
                datetime.now(),
                document_id
            )
            
            print(f"✅ Created version {version['version_number']}")
        
        # Test version retrieval
        print("\n📄 Testing version retrieval...")
        
        versions = await conn.fetch(
            '''
            SELECT version_number, changes, created_at
            FROM document_versions
            WHERE document_id = $1
            ORDER BY version_number;
            ''',
            document_id
        )
        
        print("Document versions:")
        for version in versions:
            print(f"  Version {version['version_number']}: {version['changes']}")
            print(f"  Created at: {version['created_at']}")
        
        # Test version metadata
        print("\n📊 Testing version metadata...")
        
        metadata = await conn.fetchrow(
            '''
            SELECT metadata->'version_history' as version_history
            FROM documents
            WHERE id = $1;
            ''',
            document_id
        )
        
        version_history = metadata['version_history']
        print("Version history from metadata:")
        for version in version_history:
            print(f"  Version {version['version_number']}: {version['changes']}")
            print(f"  Timestamp: {version['timestamp']}")
        
        print("\n✨ Document versioning test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document versioning test."""
    await test_document_versioning()

if __name__ == "__main__":
    asyncio.run(main())