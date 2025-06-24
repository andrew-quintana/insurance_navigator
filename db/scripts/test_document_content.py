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
                'test_id': 'content_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'completed',
        'content': '''
        Medicare Coverage Guidelines 2024
        
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
        ''',
        'sections': [
            {
                'title': 'Preventive Services',
                'content': '''
                Annual wellness visits
                - Covered once per year
                - No copayment required
                - Must be provided by participating provider
                
                Vaccinations
                - Flu shots
                - Pneumonia vaccines
                - COVID-19 vaccines
                
                Cancer screenings
                - Mammograms
                - Colonoscopies
                - PSA tests
                '''
            },
            {
                'title': 'Hospital Services',
                'content': '''
                Inpatient care
                - Room and board
                - Nursing services
                - Medications
                
                Emergency services
                - ER visits
                - Ambulance services
                - Urgent care
                
                Outpatient procedures
                - Same-day surgery
                - Diagnostic tests
                - Therapy services
                '''
            },
            {
                'title': 'Prescription Drug Coverage',
                'content': '''
                Part D plans
                - Monthly premiums
                - Annual deductibles
                - Coverage phases
                
                Formulary requirements
                - Covered drugs
                - Prior authorization
                - Quantity limits
                
                Coverage gaps
                - Donut hole explanation
                - Catastrophic coverage
                - Out-of-pocket costs
                '''
            }
        ]
    }
]

async def test_document_content():
    """Test document content handling."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document content handling...")
        
        for idx, doc in enumerate(test_documents, 1):
            print(f"\n📝 Testing document {idx} content...")
            
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
            
            document_id = result['id']
            print(f"✅ Document {idx} inserted successfully (ID: {document_id})")
            
            # Insert main content
            await conn.execute(
                '''
                INSERT INTO document_contents (
                    document_id, content, created_at, updated_at
                ) VALUES ($1, $2, $3, $4);
                ''',
                document_id,
                doc['content'],
                datetime.now(),
                datetime.now()
            )
            print("✅ Main content inserted successfully")
            
            # Insert section contents
            for section in doc['sections']:
                await conn.execute(
                    '''
                    INSERT INTO document_sections (
                        document_id, title, content, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5);
                    ''',
                    document_id,
                    section['title'],
                    section['content'],
                    datetime.now(),
                    datetime.now()
                )
                print(f"✅ Section '{section['title']}' inserted successfully")
            
            # Test content retrieval
            print("\n📄 Testing content retrieval...")
            
            # Get main content
            main_content = await conn.fetchrow(
                '''
                SELECT content
                FROM document_contents
                WHERE document_id = $1;
                ''',
                document_id
            )
            print("✅ Retrieved main content")
            
            # Get sections
            sections = await conn.fetch(
                '''
                SELECT title, content
                FROM document_sections
                WHERE document_id = $1
                ORDER BY created_at;
                ''',
                document_id
            )
            print(f"✅ Retrieved {len(sections)} sections")
            
            # Test content search
            print("\n🔎 Testing content search...")
            
            # Search in main content
            main_search = await conn.fetch(
                '''
                SELECT d.id, d.original_filename
                FROM documents d
                JOIN document_contents dc ON d.id = dc.document_id
                WHERE to_tsvector('english', dc.content) @@ to_tsquery('english', $1);
                ''',
                'medicare & coverage'
            )
            print(f"✅ Found {len(main_search)} documents in main content search")
            
            # Search in sections
            section_search = await conn.fetch(
                '''
                SELECT d.id, d.original_filename, ds.title
                FROM documents d
                JOIN document_sections ds ON d.id = ds.document_id
                WHERE to_tsvector('english', ds.content) @@ to_tsquery('english', $1);
                ''',
                'coverage & plans'
            )
            print(f"✅ Found {len(section_search)} sections in section content search")
        
        print("\n✨ Document content test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document content test."""
    await test_document_content()

if __name__ == "__main__":
    asyncio.run(main())