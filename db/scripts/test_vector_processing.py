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
                'test_id': 'vector_test_001',
                'test_type': 'integration'
            }
        },
        'tags': ['coverage', 'guidelines'],
        'status': 'pending',
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
                'test_id': 'vector_test_002',
                'test_type': 'integration'
            }
        },
        'tags': ['claims', 'processing'],
        'status': 'pending',
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
        
        print("🔄 Inserting test documents for vector processing...")
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

async def test_vector_similarity(document_ids):
    """Test vector similarity calculations."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("\n🔄 Testing vector similarity...")
        
        # Calculate cosine similarity between document vectors
        for i in range(len(document_ids)):
            for j in range(i + 1, len(document_ids)):
                result = await conn.fetchrow(
                    '''
                    SELECT 
                        d1.document_id as doc1_id,
                        d2.document_id as doc2_id,
                        1 - (d1.vector <=> d2.vector) as similarity
                    FROM document_vectors d1
                    CROSS JOIN document_vectors d2
                    WHERE d1.document_id = $1
                    AND d2.document_id = $2
                    AND d1.vector_type = 'text_embedding'
                    AND d2.vector_type = 'text_embedding';
                    ''',
                    document_ids[i],
                    document_ids[j]
                )
                
                print(f"✅ Similarity between documents {result['doc1_id']} and {result['doc2_id']}: {result['similarity']:.4f}")
        
        print("\n✨ Vector similarity test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing vector similarity: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the vector processing test."""
    try:
        # Insert test documents and vectors
        document_ids = await insert_test_documents()
        
        # Test vector similarity
        await test_vector_similarity(document_ids)
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())