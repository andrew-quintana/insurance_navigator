#!/usr/bin/env python3
"""
Phase B.2.1: Safe UUID Migration Tools
UUID Standardization - Safe Data Migration with Foreign Key Handling

This module provides a safer approach to UUID migration that handles foreign key
constraints properly by using temporary tables and careful sequencing.

Reference: PHASED_TODO_IMPLEMENTATION.md "B.2.1 UUID Migration Tools"
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class MigrationRecord:
    """Record of a single document migration."""
    original_document_id: str
    new_document_id: str
    user_id: str
    file_sha256: str
    status: MigrationStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    chunk_count: int = 0
    priority_score: float = 0.0

class SafeUUIDMigration:
    """Safe UUID migration with proper foreign key handling."""
    
    # System namespace UUID (consistent with Phase A implementation)
    SYSTEM_NAMESPACE = uuid.UUID('6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42')
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.migration_log = []
        
    async def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            logger.info("🔌 Connecting to database...")
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect_database(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            logger.info("🔌 Database disconnected")
    
    def generate_deterministic_document_id(self, user_id: str, file_sha256: str) -> str:
        """Generate deterministic document UUID using Phase A standards."""
        canonical = f"{user_id}:{file_sha256}"
        return str(uuid.uuid5(self.SYSTEM_NAMESPACE, canonical))
    
    def generate_deterministic_chunk_id(self, document_id: str, chunker_name: str, 
                                      chunker_version: str, chunk_ord: int) -> str:
        """Generate deterministic chunk UUID using Phase A standards."""
        canonical = f"{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
        return str(uuid.uuid5(self.SYSTEM_NAMESPACE, canonical))
    
    def is_uuidv4(self, uuid_value) -> bool:
        """Check if UUID is version 4 (random)."""
        try:
            if isinstance(uuid_value, str):
                uuid_obj = uuid.UUID(uuid_value)
            else:
                uuid_obj = uuid_value
            return uuid_obj.version == 4
        except (ValueError, TypeError):
            return False
    
    async def get_documents_for_migration(self) -> List[Dict[str, Any]]:
        """Get all documents that need UUID migration."""
        logger.info("📄 Retrieving documents for migration...")
        
        try:
            documents = await self.conn.fetch("""
                SELECT 
                    d.document_id,
                    d.user_id,
                    d.filename,
                    d.file_sha256,
                    d.created_at,
                    d.processing_status,
                    d.bytes_len,
                    COUNT(dc.chunk_id) as chunk_count
                FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                WHERE d.document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                GROUP BY d.document_id, d.user_id, d.filename, d.file_sha256, 
                         d.created_at, d.processing_status, d.bytes_len
                ORDER BY d.created_at DESC
            """)
            
            # Filter for UUIDv4 documents only
            uuidv4_documents = []
            for doc in documents:
                if self.is_uuidv4(doc['document_id']):
                    uuidv4_documents.append(dict(doc))
            
            logger.info(f"📊 Found {len(uuidv4_documents)} documents requiring migration")
            return uuidv4_documents
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve documents: {e}")
            return []
    
    async def create_migration_plan(self) -> List[MigrationRecord]:
        """Create migration plan with priority scoring."""
        logger.info("📋 Creating migration plan...")
        
        documents = await self.get_documents_for_migration()
        migration_records = []
        
        for doc in documents:
            # Calculate priority score
            priority_score = self.calculate_priority_score(doc)
            
            # Generate new deterministic UUID
            new_document_id = self.generate_deterministic_document_id(
                str(doc['user_id']), 
                doc['file_sha256']
            )
            
            migration_record = MigrationRecord(
                original_document_id=str(doc['document_id']),
                new_document_id=new_document_id,
                user_id=str(doc['user_id']),
                file_sha256=doc['file_sha256'],
                status=MigrationStatus.PENDING,
                chunk_count=doc['chunk_count'],
                priority_score=priority_score
            )
            
            migration_records.append(migration_record)
        
        # Sort by priority score (highest first)
        migration_records.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"📋 Migration plan created: {len(migration_records)} documents")
        return migration_records
    
    def calculate_priority_score(self, doc: Dict[str, Any]) -> float:
        """Calculate priority score for document migration."""
        score = 0.0
        
        # Recency factor
        try:
            created_at = doc['created_at']
            if created_at.tzinfo is not None:
                now = datetime.utcnow().replace(tzinfo=created_at.tzinfo)
            else:
                now = datetime.utcnow()
            
            days_old = (now - created_at).days
            if days_old <= 7:
                score += 0.4
            elif days_old <= 30:
                score += 0.3
            elif days_old <= 90:
                score += 0.2
            else:
                score += 0.1
        except Exception:
            score += 0.1
        
        # Processing status factor
        if doc.get('processing_status') == 'embedded':
            score += 0.3
        elif doc.get('processing_status') in ['chunked', 'embedding']:
            score += 0.2
        elif doc.get('processing_status') in ['parsed', 'chunking']:
            score += 0.1
        
        # Chunk count factor
        chunk_count = doc.get('chunk_count', 0)
        if chunk_count > 0:
            score += min(0.3, chunk_count * 0.01)
        
        return min(1.0, score)
    
    async def migrate_document_safe(self, migration_record: MigrationRecord) -> bool:
        """Safely migrate a single document using temporary table approach."""
        logger.info(f"🔄 Safely migrating document {migration_record.original_document_id}...")
        
        try:
            migration_record.status = MigrationStatus.IN_PROGRESS
            migration_record.started_at = datetime.utcnow()
            
            # Start transaction
            async with self.conn.transaction():
                # 1. Create a temporary document with the new UUID
                await self.conn.execute("""
                    INSERT INTO upload_pipeline.documents (
                        document_id, user_id, filename, mime, bytes_len, 
                        file_sha256, parsed_sha256, raw_path, parsed_path, 
                        processing_status, created_at, updated_at
                    )
                    SELECT 
                        $1 as document_id,
                        user_id, filename, mime, bytes_len,
                        file_sha256, parsed_sha256, raw_path, parsed_path,
                        processing_status, created_at, updated_at
                    FROM upload_pipeline.documents
                    WHERE document_id = $2
                """, migration_record.new_document_id, migration_record.original_document_id)
                
                # 2. Copy and update chunks with new UUIDs
                chunks = await self.conn.fetch("""
                    SELECT chunk_id, chunker_name, chunker_version, chunk_ord,
                           text, chunk_sha, embed_model, embed_version, 
                           vector_dim, embedding, embed_updated_at, created_at, updated_at
                    FROM upload_pipeline.document_chunks
                    WHERE document_id = $1
                """, migration_record.original_document_id)
                
                for chunk in chunks:
                    # Generate new chunk UUID
                    new_chunk_id = self.generate_deterministic_chunk_id(
                        migration_record.new_document_id,
                        chunk['chunker_name'],
                        chunk['chunker_version'],
                        chunk['chunk_ord']
                    )
                    
                    # Insert new chunk with new UUIDs
                    await self.conn.execute("""
                        INSERT INTO upload_pipeline.document_chunks (
                            chunk_id, document_id, chunker_name, chunker_version, chunk_ord,
                            text, chunk_sha, embed_model, embed_version, vector_dim,
                            embedding, embed_updated_at, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """, 
                        new_chunk_id, migration_record.new_document_id,
                        chunk['chunker_name'], chunk['chunker_version'], chunk['chunk_ord'],
                        chunk['text'], chunk['chunk_sha'], chunk['embed_model'], 
                        chunk['embed_version'], chunk['vector_dim'], chunk['embedding'],
                        chunk['embed_updated_at'], chunk['created_at'], chunk['updated_at']
                    )
                    
                    # Copy buffer entries if they exist
                    await self.conn.execute("""
                        INSERT INTO upload_pipeline.document_vector_buffer (
                            buffer_id, chunk_id, embed_model, embed_version, 
                            vector_dim, embedding, created_at
                        )
                        SELECT 
                            gen_random_uuid() as buffer_id,
                            $1 as chunk_id,
                            embed_model, embed_version, vector_dim, embedding, created_at
                        FROM upload_pipeline.document_vector_buffer
                        WHERE chunk_id = $2
                    """, new_chunk_id, chunk['chunk_id'])
                
                # 3. Copy and update jobs with new document_id
                jobs = await self.conn.fetch("""
                    SELECT job_id, stage, state, retry_count, idempotency_key,
                           payload, last_error, claimed_by, claimed_at,
                           started_at, finished_at, created_at, updated_at
                    FROM upload_pipeline.upload_jobs
                    WHERE document_id = $1
                """, migration_record.original_document_id)
                
                for job in jobs:
                    # Generate new job UUID (jobs can remain random)
                    new_job_id = str(uuid.uuid4())
                    
                    await self.conn.execute("""
                        INSERT INTO upload_pipeline.upload_jobs (
                            job_id, document_id, stage, state, retry_count,
                            idempotency_key, payload, last_error, claimed_by,
                            claimed_at, started_at, finished_at, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """,
                        new_job_id, migration_record.new_document_id,
                        job['stage'], job['state'], job['retry_count'],
                        job['idempotency_key'], job['payload'], job['last_error'],
                        job['claimed_by'], job['claimed_at'], job['started_at'],
                        job['finished_at'], job['created_at'], job['updated_at']
                    )
                    
                    # Copy events with new job_id and document_id
                    await self.conn.execute("""
                        INSERT INTO upload_pipeline.events (
                            event_id, job_id, document_id, ts, type, severity,
                            code, payload, correlation_id
                        )
                        SELECT 
                            gen_random_uuid() as event_id,
                            $1 as job_id,
                            $2 as document_id,
                            ts, type, severity, code, payload, correlation_id
                        FROM upload_pipeline.events
                        WHERE job_id = $3
                    """, new_job_id, migration_record.new_document_id, job['job_id'])
                
                # 4. Delete old document and all its references
                # Delete in reverse order of dependencies
                await self.conn.execute("""
                    DELETE FROM upload_pipeline.document_vector_buffer
                    WHERE chunk_id IN (
                        SELECT chunk_id FROM upload_pipeline.document_chunks
                        WHERE document_id = $1
                    )
                """, migration_record.original_document_id)
                
                await self.conn.execute("""
                    DELETE FROM upload_pipeline.document_chunks
                    WHERE document_id = $1
                """, migration_record.original_document_id)
                
                await self.conn.execute("""
                    DELETE FROM upload_pipeline.events
                    WHERE document_id = $1
                """, migration_record.original_document_id)
                
                await self.conn.execute("""
                    DELETE FROM upload_pipeline.upload_jobs
                    WHERE document_id = $1
                """, migration_record.original_document_id)
                
                await self.conn.execute("""
                    DELETE FROM upload_pipeline.documents
                    WHERE document_id = $1
                """, migration_record.original_document_id)
            
            migration_record.status = MigrationStatus.COMPLETED
            migration_record.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Document {migration_record.original_document_id} migrated successfully")
            return True
            
        except Exception as e:
            migration_record.status = MigrationStatus.FAILED
            migration_record.error_message = str(e)
            migration_record.completed_at = datetime.utcnow()
            
            logger.error(f"❌ Document {migration_record.original_document_id} migration failed: {e}")
            return False
    
    async def run_safe_migration(self, batch_size: int = 5) -> Dict[str, Any]:
        """Run safe migration process."""
        logger.info("🚀 Starting safe UUID migration process...")
        
        if not await self.connect_database():
            return {"error": "Database connection failed"}
        
        try:
            # Create migration plan
            migration_records = await self.create_migration_plan()
            if not migration_records:
                return {"error": "No documents found for migration"}
            
            # Execute migration in batches
            total_success = 0
            total_errors = 0
            
            for i in range(0, len(migration_records), batch_size):
                batch = migration_records[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"📦 Processing batch {batch_num} ({len(batch)} documents)...")
                
                for migration_record in batch:
                    success = await self.migrate_document_safe(migration_record)
                    if success:
                        total_success += 1
                    else:
                        total_errors += 1
                
                logger.info(f"📦 Batch {batch_num} completed: {total_success} success, {total_errors} errors so far")
            
            # Generate results
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_documents": len(migration_records),
                "successful_migrations": total_success,
                "failed_migrations": total_errors,
                "success_rate": total_success / len(migration_records) * 100 if migration_records else 0,
                "migration_records": [asdict(record) for record in migration_records]
            }
            
            logger.info(f"✅ Migration completed: {total_success} success, {total_errors} errors")
            return results
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return {"error": str(e)}
        
        finally:
            await self.disconnect_database()

async def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv('.env.production')
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return
    
    # Run safe migration
    migration_tools = SafeUUIDMigration(database_url)
    results = await migration_tools.run_safe_migration(batch_size=3)
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"phase_b_safe_migration_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Migration results saved to: {output_file}")
    
    # Print summary
    if "error" not in results:
        print(f"\n📊 SAFE MIGRATION SUMMARY")
        print(f"Total Documents: {results['total_documents']}")
        print(f"Successful Migrations: {results['successful_migrations']}")
        print(f"Failed Migrations: {results['failed_migrations']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
    else:
        print(f"❌ Migration failed: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())
