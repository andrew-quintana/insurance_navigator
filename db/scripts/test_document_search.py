"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
import json
import numpy as np

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
                'test_id': 'search_test_001',
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
        '''
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
                'test_id': 'search_test_002',
                'test_type': 'integration'
            }
        },
        'tags': ['claims', 'processing'],
        'status': 'completed',
        'content': '''
        Medicare Claims Processing Updates 2024
        
        Updated procedures for processing Medicare claims in 2024.
        
        1. Electronic Claims Submission
           - Required formats
           - Validation rules
           - Error handling
        
        2. Documentation Requirements
           - Medical necessity
           - Supporting evidence
           - Record retention
        
        3. Payment Processing
           - Fee schedules
           - Adjustments
           - Appeals process
        '''
    },
    {
        'original_filename': 'Medicare Prescription Drug Coverage',
        'storage_path': 'test/medicare_drug_coverage_2024.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'source_url': None,
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test_upload',
            'content_length': 3000,
            'extraction_method': 'doc_parser',
            'test_metadata': {
                'test_id': 'search_test_003',
                'test_type': 'integration'
            }
        },
        'tags': ['prescription', 'drugs', 'coverage'],
        'status': 'completed',
        'content': '''
        Medicare Prescription Drug Coverage 2024
        
        Comprehensive guide to Medicare prescription drug coverage.
        
        1. Part D Plans
           - Enrollment periods
           - Premium calculations
           - Plan types
        
        2. Formulary Coverage
           - Tier system
           - Prior authorization
           - Step therapy
        
        3. Coverage Gaps
           - Donut hole explanation
           - Catastrophic coverage
           - Out-of-pocket costs
        '''
    }
]

def generate_test_vectors(text, dim=1536):
    """Generate test embedding vectors."""
    # Create deterministic but unique vectors for testing
    hash_val = hash(text)
    np.random.seed(hash_val)
    vector = np.random.normal(0, 1, dim)
    # Normalize to unit length
    return vector / np.linalg.norm(vector)

async def insert_test_documents():
    """Insert test documents and generate vectors."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Inserting test documents for search testing...")
        document_ids = []
        
        for doc in test_documents:
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
            print(f"✅ Inserted document {result['id']}: {doc['original_filename']}")
            
            # Insert document content
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
            print(f"✅ Inserted content for document {result['id']}")
            
            # Generate and insert vectors
            vector = generate_test_vectors(doc['content'])
            
            await conn.execute(
                '''
                INSERT INTO document_vectors (
                    document_id, vector_type, vector, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6);
                ''',
                result['id'],
                'text_embedding',
                vector.tolist(),
                json.dumps({
                    'model': 'test_embedding_model',
                    'dimension': len(vector),
                    'test_metadata': {
                        'test_id': f'vector_{result["id"]}',
                        'test_type': 'integration'
                    }
                }),
                datetime.now(),
                datetime.now()
            )
            print(f"✅ Inserted vector for document {result['id']}")
        
        print("\n✨ All test documents and vectors inserted successfully!")
        return document_ids
        
    except Exception as e:
        print(f"❌ Error inserting test documents and vectors: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def test_document_search(document_ids):
    """Test document search functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("\n🔄 Testing document search...")
        
        # Test 1: Full-text search
        print("\n📝 Testing full-text search...")
        result = await conn.fetch(
            '''
            SELECT d.id, d.original_filename, ts_rank(to_tsvector('english', dc.content), query) as rank
            FROM documents d
            JOIN document_contents dc ON d.id = dc.document_id
            CROSS JOIN websearch_to_tsquery('english', $1) query
            WHERE to_tsvector('english', dc.content) @@ query
            ORDER BY rank DESC;
            ''',
            'prescription drug coverage'
        )
        
        print("Full-text search results:")
        for row in result:
            print(f"✅ Document {row['id']}: {row['original_filename']} (Rank: {row['rank']:.4f})")
        
        # Test 2: Vector similarity search
        print("\n🔍 Testing vector similarity search...")
        query_text = "Medicare prescription drug coverage and benefits"
        query_vector = generate_test_vectors(query_text)
        
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                1 - (dv.vector <=> $1::float8[]) as similarity
            FROM documents d
            JOIN document_vectors dv ON d.id = dv.document_id
            WHERE dv.vector_type = 'text_embedding'
            ORDER BY similarity DESC
            LIMIT 5;
            ''',
            query_vector.tolist()
        )
        
        print("Vector similarity search results:")
        for row in result:
            print(f"✅ Document {row['id']}: {row['original_filename']} (Similarity: {row['similarity']:.4f})")
        
        # Test 3: Combined metadata and content search
        print("\n🔎 Testing combined metadata and content search...")
        result = await conn.fetch(
            '''
            SELECT 
                d.id,
                d.original_filename,
                d.tags,
                ts_rank(to_tsvector('english', dc.content), query) as rank
            FROM documents d
            JOIN document_contents dc ON d.id = dc.document_id
            CROSS JOIN websearch_to_tsquery('english', $1) query
            WHERE to_tsvector('english', dc.content) @@ query
            AND d.tags && $2
            ORDER BY rank DESC;
            ''',
            'coverage',
            ['prescription', 'coverage']
        )
        
        print("Combined search results:")
        for row in result:
            print(f"✅ Document {row['id']}: {row['original_filename']}")
            print(f"   Tags: {row['tags']}")
            print(f"   Rank: {row['rank']:.4f}")
        
        print("\n✨ Document search test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing document search: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document search test."""
    try:
        # Insert test documents and vectors
        document_ids = await insert_test_documents()
        
        # Test document search
        await test_document_search(document_ids)
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
""" 