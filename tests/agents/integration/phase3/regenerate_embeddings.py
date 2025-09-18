#!/usr/bin/env python3
"""
Regenerate Document Chunk Embeddings
Replace mock/zero embeddings with real OpenAI text-embedding-3-small embeddings
"""

import asyncio
import asyncpg
import openai
import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

class EmbeddingRegenerator:
    """Regenerate document chunk embeddings with real OpenAI embeddings."""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = self.openai_api_key
        self.db_url = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres'
        
    async def regenerate_embeddings(self):
        """Regenerate all document chunk embeddings."""
        print("🔄 Starting Embedding Regeneration")
        print("=" * 50)
        
        try:
            # Connect to database
            conn = await asyncpg.connect(self.db_url)
            
            # Get all chunks that need embedding regeneration
            chunks = await conn.fetch("""
                SELECT chunk_id, text, embed_model, embed_version
                FROM upload_pipeline.document_chunks 
                WHERE embedding IS NOT NULL
                ORDER BY created_at
            """)
            
            print(f"📊 Found {len(chunks)} chunks to regenerate")
            
            if not chunks:
                print("❌ No chunks found to regenerate")
                return
            
            # Process chunks in batches
            batch_size = 10
            total_processed = 0
            total_updated = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                print(f"\\n🔄 Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
                
                # Extract texts for this batch
                texts = [chunk['text'] for chunk in batch]
                chunk_ids = [chunk['chunk_id'] for chunk in batch]
                
                try:
                    # Generate embeddings for this batch
                    print(f"   🔢 Generating embeddings for {len(texts)} chunks...")
                    response = openai.embeddings.create(
                        model="text-embedding-3-small",
                        input=texts
                    )
                    
                    embeddings = [item.embedding for item in response.data]
                    print(f"   ✅ Generated {len(embeddings)} embeddings")
                    
                    # Update database with new embeddings
                    updated_count = 0
                    for chunk_id, embedding in zip(chunk_ids, embeddings):
                        # Convert to PostgreSQL vector format
                        vector_string = '[' + ','.join(str(x) for x in embedding) + ']'
                        
                        # Update the embedding
                        await conn.execute("""
                            UPDATE upload_pipeline.document_chunks 
                            SET embedding = $1::vector(1536),
                                embed_model = 'text-embedding-3-small',
                                embed_version = '2',
                                embed_updated_at = now(),
                                updated_at = now()
                            WHERE chunk_id = $2
                        """, vector_string, chunk_id)
                        
                        updated_count += 1
                    
                    total_updated += updated_count
                    total_processed += len(batch)
                    
                    print(f"   ✅ Updated {updated_count} chunks in database")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ❌ Error processing batch: {e}")
                    continue
            
            print(f"\\n🎉 Embedding regeneration completed!")
            print(f"   📊 Total processed: {total_processed}")
            print(f"   ✅ Total updated: {total_updated}")
            
            # Verify the regeneration
            await self._verify_regeneration(conn)
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ Error during regeneration: {e}")
            import traceback
            traceback.print_exc()
    
    async def _verify_regeneration(self, conn):
        """Verify that embeddings were properly regenerated."""
        print("\\n🔍 Verifying embedding regeneration...")
        
        # Check embedding models
        models = await conn.fetch("""
            SELECT embed_model, embed_version, COUNT(*) as count
            FROM upload_pipeline.document_chunks 
            GROUP BY embed_model, embed_version
            ORDER BY count DESC
        """)
        
        print("📊 Embedding models in database:")
        for model in models:
            print(f"   {model['embed_model']} v{model['embed_version']}: {model['count']} chunks")
        
        # Check if embeddings are no longer zero vectors
        sample_embedding = await conn.fetchval("""
            SELECT embedding 
            FROM upload_pipeline.document_chunks 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """)
        
        if sample_embedding:
            import re
            vector_str = str(sample_embedding)
            numbers = re.findall(r'-?\\d+\\.?\\d*', vector_str)
            
            print(f"\\n📊 Sample embedding verification:")
            print(f"   Dimensions: {len(numbers)}")
            print(f"   Preview: {numbers[:5]}...")
            
            # Check if it's no longer all zeros
            try:
                float_values = [float(x) for x in numbers[:10]]
                is_zero_vector = all(v == 0.0 for v in float_values)
                print(f"   Is zero vector: {is_zero_vector}")
                print(f"   Value range: {min(float_values):.4f} to {max(float_values):.4f}")
                
                if not is_zero_vector:
                    print("   ✅ Embeddings successfully regenerated with real values!")
                else:
                    print("   ❌ Embeddings are still zero vectors")
            except:
                print("   ❌ Could not parse embedding values")

async def main():
    """Main function to run embedding regeneration."""
    try:
        regenerator = EmbeddingRegenerator()
        await regenerator.regenerate_embeddings()
    except Exception as e:
        print(f"❌ Failed to initialize regenerator: {e}")

if __name__ == "__main__":
    asyncio.run(main())
