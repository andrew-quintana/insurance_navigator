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
                'test_id': 'link_test_001',
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
                'test_id': 'link_test_002',
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
                'test_id': 'link_test_003',
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

async def test_document_linking():
    """Test document linking functionality."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Testing document linking...")
        
        # Insert test documents and generate vectors
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
            print(f"✅ Vector for document {idx} inserted successfully")
        
        # Test document linking
        print("\n🔗 Testing document linking...")
        
        # Test 1: Create links based on vector similarity
        print("\n📊 Creating links based on vector similarity...")
        for i in range(len(document_ids)):
            for j in range(i + 1, len(document_ids)):
                # Calculate similarity between documents
                similarity = await conn.fetchval(
                    '''
                    SELECT 1 - (v1.vector <=> v2.vector) as similarity
                    FROM document_vectors v1
                    CROSS JOIN document_vectors v2
                    WHERE v1.document_id = $1
                    AND v2.document_id = $2
                    AND v1.vector_type = 'text_embedding'
                    AND v2.vector_type = 'text_embedding';
                    ''',
                    document_ids[i],
                    document_ids[j]
                )
                
                # Create link if similarity is above threshold
                if similarity > 0.5:
                    await conn.execute(
                        '''
                        INSERT INTO document_links (
                            source_document_id, target_document_id,
                            link_type, link_strength, metadata,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7);
                        ''',
                        document_ids[i],
                        document_ids[j],
                        'similar_content',
                        similarity,
                        json.dumps({
                            'link_method': 'vector_similarity',
                            'test_metadata': {
                                'test_id': f'link_{document_ids[i]}_{document_ids[j]}',
                                'test_type': 'integration'
                            }
                        }),
                        datetime.now(),
                        datetime.now()
                    )
                    print(f"✅ Created link between documents {document_ids[i]} and {document_ids[j]} (similarity: {similarity:.4f})")
        
        # Test 2: Create links based on shared tags
        print("\n🏷️ Creating links based on shared tags...")
        for i in range(len(document_ids)):
            for j in range(i + 1, len(document_ids)):
                # Get shared tags between documents
                shared_tags = await conn.fetchval(
                    '''
                    SELECT array_agg(tag)
                    FROM (
                        SELECT unnest(d1.tags) as tag
                        INTERSECT
                        SELECT unnest(d2.tags) as tag
                    ) t
                    FROM documents d1
                    CROSS JOIN documents d2
                    WHERE d1.id = $1
                    AND d2.id = $2;
                    ''',
                    document_ids[i],
                    document_ids[j]
                )
                
                if shared_tags:
                    await conn.execute(
                        '''
                        INSERT INTO document_links (
                            source_document_id, target_document_id,
                            link_type, link_strength, metadata,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7);
                        ''',
                        document_ids[i],
                        document_ids[j],
                        'shared_tags',
                        len(shared_tags) / 5.0,  # Normalize strength
                        json.dumps({
                            'link_method': 'tag_similarity',
                            'shared_tags': shared_tags,
                            'test_metadata': {
                                'test_id': f'link_{document_ids[i]}_{document_ids[j]}',
                                'test_type': 'integration'
                            }
                        }),
                        datetime.now(),
                        datetime.now()
                    )
                    print(f"✅ Created link between documents {document_ids[i]} and {document_ids[j]} (shared tags: {shared_tags})")
        
        # Test 3: Query document links
        print("\n🔍 Testing link queries...")
        
        # Get all links for a document
        for document_id in document_ids:
            links = await conn.fetch(
                '''
                SELECT 
                    dl.source_document_id,
                    dl.target_document_id,
                    dl.link_type,
                    dl.link_strength,
                    d1.original_filename as source_filename,
                    d2.original_filename as target_filename
                FROM document_links dl
                JOIN documents d1 ON dl.source_document_id = d1.id
                JOIN documents d2 ON dl.target_document_id = d2.id
                WHERE dl.source_document_id = $1
                OR dl.target_document_id = $1;
                ''',
                document_id
            )
            
            print(f"\nLinks for document {document_id}:")
            for link in links:
                print(f"  {link['source_filename']} -> {link['target_filename']}")
                print(f"  Type: {link['link_type']}")
                print(f"  Strength: {link['link_strength']:.4f}")
        
        print("\n✨ Document linking test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
        
    finally:
        await conn.close()

async def main():
    """Run the document linking test."""
    await test_document_linking()

if __name__ == "__main__":
    asyncio.run(main())