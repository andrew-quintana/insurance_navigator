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
    # Medicare document
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
            'program_info': {
                'name': 'Medicare',
                'type': 'federal_health_insurance',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'target_population': ['seniors', 'disabled'],
                'coverage_type': ['medical', 'prescription']
            },
            'test_metadata': {
                'test_id': 'program_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines', 'medicare'],
        'status': 'completed',
        'content': 'Test content for Medicare coverage guidelines.'
    },
    # Medicaid document
    {
        'original_filename': 'California Medicaid Eligibility Guide',
        'storage_path': 'test/ca_medicaid_eligibility_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'state',
        'program': ['Medicaid'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 4000,
            'extraction_method': 'doc_parser',
            'program_info': {
                'name': 'Medicaid',
                'type': 'state_health_insurance',
                'state': 'CA',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'target_population': ['low_income', 'disabled'],
                'coverage_type': ['medical', 'prescription', 'dental']
            },
            'test_metadata': {
                'test_id': 'program_test_002',
                'test_type': 'integration'
            }
        },
        'tags': ['eligibility', 'medicaid', 'california'],
        'status': 'completed',
        'content': 'Test content for California Medicaid eligibility guide.'
    },
    # Dual Eligible document
    {
        'original_filename': 'Medicare-Medicaid Dual Eligible Benefits',
        'storage_path': 'test/dual_eligible_benefits_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'federal',
        'program': ['Medicare', 'Medicaid'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 3000,
            'extraction_method': 'doc_parser',
            'program_info': {
                'name': ['Medicare', 'Medicaid'],
                'type': 'dual_eligible',
                'effective_date': '2024-01-01',
                'expiration_date': None,
                'target_population': ['seniors', 'disabled', 'low_income'],
                'coverage_type': ['medical', 'prescription', 'dental', 'vision']
            },
            'test_metadata': {
                'test_id': 'program_test_003',
                'test_type': 'integration'
            }
        },
        'tags': ['dual_eligible', 'benefits', 'medicare', 'medicaid'],
        'status': 'completed',
        'content': 'Test content for Medicare-Medicaid dual eligible benefits.'
    }
]

async def test_document_program():
    """Test document program functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document program...")
        
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
        
        # Test program queries
        print("\n🔍 Testing program queries...")
        
        # Test 1: Query by single program
        print("\n📊 Testing single program queries...")
        for program in ['Medicare', 'Medicaid']:
            result = await conn.fetch(
                '''
                SELECT 
                    d.id,
                    d.original_filename,
                    d.program,
                    d.metadata->'program_info' as program_info
                FROM documents d
                WHERE $1 = ANY(d.program);
                ''',
                program
            )
            
            print(f"\nDocuments for {program}:")
            for row in result:
                print(f"  Document {row['id']}: {row['original_filename']}")
                print(f"  Programs: {row['program']}")
                print(f"  Program info: {json.dumps(row['program_info'], indent=2)}")
        
        # Test 2: Query by multiple programs
        print("\n🔄 Testing multiple program queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.program,
                d.metadata->'program_info' as program_info
            FROM documents d
            WHERE array_length(d.program, 1) > 1;
            '''
        )
        
        print("\nDocuments with multiple programs:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Programs: {row['program']}")
            print(f"  Program info: {json.dumps(row['program_info'], indent=2)}")
        
        # Test 3: Query by program type
        print("\n📋 Testing program type queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.program,
                d.metadata->'program_info' as program_info
            FROM documents d
            WHERE d.metadata->'program_info'->>'type' = $1;
            ''',
            'dual_eligible'
        )
        
        print("\nDual eligible program documents:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Programs: {row['program']}")
            print(f"  Program info: {json.dumps(row['program_info'], indent=2)}")
        
        # Test 4: Query by target population
        print("\n👥 Testing target population queries...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.program,
                d.metadata->'program_info' as program_info
            FROM documents d,
                jsonb_array_elements_text(d.metadata->'program_info'->'target_population') as population
            WHERE population = $1;
            ''',
            'seniors'
        )
        
        print("\nDocuments targeting seniors:")
        for row in result:
            print(f"  Document {row['id']}: {row['original_filename']}")
            print(f"  Programs: {row['program']}")
            print(f"  Target population: {row['program_info']['target_population']}")
        
        print("\n✨ Document program test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document program test."""
    await test_document_program()

if __name__ == "__main__":
    asyncio.run(main())
""" 