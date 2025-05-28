#!/usr/bin/env python3
"""
Data encryption migration script.
Migrates existing plaintext vector data to encrypted format and removes user_id denormalization.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Database imports
import asyncpg
from db.services.db_pool import get_db_pool
from db.services.encryption_aware_embedding_service import MockEncryptionManager

logger = logging.getLogger(__name__)

class VectorEncryptionMigrator:
    """Handles migration of existing vector data to encrypted format."""
    
    def __init__(self):
        self.encryption_manager = MockEncryptionManager()  # Use real encryption in production
        self.migration_stats = {
            "policy_vectors_processed": 0,
            "policy_vectors_encrypted": 0,
            "user_vectors_processed": 0,
            "user_vectors_encrypted": 0,
            "errors": []
        }
    
    async def migrate_all_vectors(self) -> Dict[str, Any]:
        """Main migration function - encrypts all existing vector data."""
        logger.info("Starting vector encryption migration...")
        
        try:
            # Migrate policy content vectors
            await self._migrate_policy_vectors()
            
            # Migrate user document vectors
            await self._migrate_user_vectors()
            
            # Final cleanup - remove deprecated user_id column
            await self._cleanup_deprecated_columns()
            
            logger.info("Vector encryption migration completed successfully!")
            return self._generate_migration_report()
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.migration_stats["errors"].append(str(e))
            raise
    
    async def _migrate_policy_vectors(self):
        """Migrate policy content vectors to encrypted format."""
        logger.info("Migrating policy content vectors...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Temporarily disable constraints to allow migration
            await conn.execute("ALTER TABLE policy_content_vectors DROP CONSTRAINT IF EXISTS chk_content_encryption")
            await conn.execute("ALTER TABLE policy_content_vectors DROP CONSTRAINT IF EXISTS chk_metadata_encryption")
            
            # Drop NOT NULL constraints temporarily
            await conn.execute("ALTER TABLE policy_content_vectors ALTER COLUMN content_text DROP NOT NULL")
            await conn.execute("ALTER TABLE policy_content_vectors ALTER COLUMN policy_metadata DROP NOT NULL")
            await conn.execute("ALTER TABLE policy_content_vectors ALTER COLUMN document_metadata DROP NOT NULL")
            
            # Get all plaintext policy vectors
            plaintext_vectors = await conn.fetch("""
                SELECT id, policy_id, content_text, policy_metadata, document_metadata, user_id
                FROM policy_content_vectors 
                WHERE content_text IS NOT NULL 
                AND encrypted_content_text IS NULL
                AND is_active = true
            """)
            
            logger.info(f"Found {len(plaintext_vectors)} policy vectors to encrypt")
            
            active_key = await self.encryption_manager.get_active_key()
            
            for vector in plaintext_vectors:
                try:
                    self.migration_stats["policy_vectors_processed"] += 1
                    
                    # Encrypt content and metadata
                    encrypted_content = await self.encryption_manager.encrypt_data(
                        vector['content_text'].encode()
                    )
                    
                    encrypted_policy_metadata = await self.encryption_manager.encrypt_data(
                        json.dumps(vector['policy_metadata']).encode()
                    )
                    
                    encrypted_doc_metadata = await self.encryption_manager.encrypt_data(
                        json.dumps(vector['document_metadata']).encode()
                    )
                    
                    # Update record with encrypted data (keep plaintext temporarily)
                    await conn.execute("""
                        UPDATE policy_content_vectors 
                        SET encrypted_content_text = $1,
                            encrypted_policy_metadata = $2,
                            encrypted_document_metadata = $3,
                            encryption_key_id = $4,
                            updated_at = NOW()
                        WHERE id = $5
                    """, 
                    encrypted_content, encrypted_policy_metadata, 
                    encrypted_doc_metadata, active_key['id'], vector['id'])
                    
                    self.migration_stats["policy_vectors_encrypted"] += 1
                    
                    if self.migration_stats["policy_vectors_processed"] % 10 == 0:
                        logger.info(f"Encrypted {self.migration_stats['policy_vectors_encrypted']} policy vectors...")
                        
                except Exception as e:
                    error_msg = f"Failed to encrypt policy vector {vector['id']}: {str(e)}"
                    logger.error(error_msg)
                    self.migration_stats["errors"].append(error_msg)
                    continue
    
    async def _migrate_user_vectors(self):
        """Migrate user document vectors to encrypted format."""
        logger.info("Migrating user document vectors...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Temporarily disable constraints to allow migration
            await conn.execute("ALTER TABLE user_document_vectors DROP CONSTRAINT IF EXISTS chk_chunk_encryption")
            await conn.execute("ALTER TABLE user_document_vectors DROP CONSTRAINT IF EXISTS chk_chunk_metadata_encryption")
            
            # Drop NOT NULL constraints temporarily
            await conn.execute("ALTER TABLE user_document_vectors ALTER COLUMN chunk_text DROP NOT NULL")
            await conn.execute("ALTER TABLE user_document_vectors ALTER COLUMN chunk_metadata DROP NOT NULL")
            
            # Get all plaintext user vectors
            plaintext_vectors = await conn.fetch("""
                SELECT id, user_id, document_id, chunk_index, chunk_text, chunk_metadata
                FROM user_document_vectors 
                WHERE chunk_text IS NOT NULL 
                AND encrypted_chunk_text IS NULL
                AND is_active = true
            """)
            
            logger.info(f"Found {len(plaintext_vectors)} user document vectors to encrypt")
            
            active_key = await self.encryption_manager.get_active_key()
            
            for vector in plaintext_vectors:
                try:
                    self.migration_stats["user_vectors_processed"] += 1
                    
                    # Encrypt chunk content and metadata
                    encrypted_chunk_text = await self.encryption_manager.encrypt_data(
                        vector['chunk_text'].encode()
                    )
                    
                    encrypted_chunk_metadata = await self.encryption_manager.encrypt_data(
                        json.dumps(vector['chunk_metadata']).encode()
                    )
                    
                    # Update record with encrypted data (keep plaintext temporarily)
                    await conn.execute("""
                        UPDATE user_document_vectors 
                        SET encrypted_chunk_text = $1,
                            encrypted_chunk_metadata = $2,
                            encryption_key_id = $3
                        WHERE id = $4
                    """, 
                    encrypted_chunk_text, encrypted_chunk_metadata, 
                    active_key['id'], vector['id'])
                    
                    self.migration_stats["user_vectors_encrypted"] += 1
                    
                    if self.migration_stats["user_vectors_processed"] % 10 == 0:
                        logger.info(f"Encrypted {self.migration_stats['user_vectors_encrypted']} user vectors...")
                        
                except Exception as e:
                    error_msg = f"Failed to encrypt user vector {vector['id']}: {str(e)}"
                    logger.error(error_msg)
                    self.migration_stats["errors"].append(error_msg)
                    continue
    
    async def _cleanup_deprecated_columns(self):
        """Remove deprecated user_id column from policy_content_vectors."""
        logger.info("Cleaning up deprecated columns...")
        
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            # Step 1: Clear plaintext data now that encryption is complete
            await conn.execute("""
                UPDATE policy_content_vectors 
                SET content_text = NULL, 
                    policy_metadata = NULL, 
                    document_metadata = NULL
                WHERE encrypted_content_text IS NOT NULL
            """)
            
            await conn.execute("""
                UPDATE user_document_vectors 
                SET chunk_text = NULL, 
                    chunk_metadata = NULL
                WHERE encrypted_chunk_text IS NOT NULL
            """)
            
            # Step 2: Verify all data is encrypted before dropping columns
            plaintext_check = await conn.fetchval("""
                SELECT COUNT(*) FROM policy_content_vectors 
                WHERE content_text IS NOT NULL 
                OR policy_metadata IS NOT NULL 
                OR document_metadata IS NOT NULL
            """)
            
            if plaintext_check > 0:
                raise Exception(f"Cannot drop columns: {plaintext_check} records still have plaintext data")
            
            user_plaintext_check = await conn.fetchval("""
                SELECT COUNT(*) FROM user_document_vectors 
                WHERE chunk_text IS NOT NULL 
                OR chunk_metadata IS NOT NULL
            """)
            
            if user_plaintext_check > 0:
                raise Exception(f"Cannot drop user vector columns: {user_plaintext_check} records still have plaintext data")
            
            # Step 3: Drop deprecated user_id column and plaintext columns
            await conn.execute("""
                ALTER TABLE policy_content_vectors 
                DROP COLUMN IF EXISTS user_id,
                DROP COLUMN IF EXISTS content_text,
                DROP COLUMN IF EXISTS policy_metadata,
                DROP COLUMN IF EXISTS document_metadata;
            """)
            
            await conn.execute("""
                ALTER TABLE user_document_vectors 
                DROP COLUMN IF EXISTS chunk_text,
                DROP COLUMN IF EXISTS chunk_metadata;
            """)
            
            # Step 4: Add new constraints that require encryption
            await conn.execute("""
                ALTER TABLE policy_content_vectors 
                ADD CONSTRAINT chk_encryption_required CHECK (
                    encrypted_content_text IS NOT NULL AND 
                    encrypted_policy_metadata IS NOT NULL AND 
                    encrypted_document_metadata IS NOT NULL AND
                    encryption_key_id IS NOT NULL
                );
            """)
            
            await conn.execute("""
                ALTER TABLE user_document_vectors 
                ADD CONSTRAINT chk_encryption_required CHECK (
                    encrypted_chunk_text IS NOT NULL AND 
                    encrypted_chunk_metadata IS NOT NULL AND
                    encryption_key_id IS NOT NULL
                );
            """)
            
            logger.info("Deprecated columns removed and encryption constraints added")
    
    def _generate_migration_report(self) -> Dict[str, Any]:
        """Generate migration report."""
        return {
            "migration_completed_at": datetime.now().isoformat(),
            "migration_type": "vector_encryption",
            "statistics": self.migration_stats,
            "success_rate": {
                "policy_vectors": f"{(self.migration_stats['policy_vectors_encrypted'] / max(self.migration_stats['policy_vectors_processed'], 1) * 100):.1f}%",
                "user_vectors": f"{(self.migration_stats['user_vectors_encrypted'] / max(self.migration_stats['user_vectors_processed'], 1) * 100):.1f}%"
            },
            "next_steps": [
                "Test vector search functionality with encrypted data",
                "Verify RLS policies work correctly with new schema", 
                "Monitor performance impact of encryption/decryption",
                "Consider implementing decryption caching for performance"
            ]
        }


async def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO)
    
    migrator = VectorEncryptionMigrator()
    
    try:
        report = await migrator.migrate_all_vectors()
        
        print("\n" + "="*60)
        print("VECTOR ENCRYPTION MIGRATION REPORT")
        print("="*60)
        print(json.dumps(report, indent=2, default=str))
        print("="*60)
        
        # Save report to file
        report_file = f"db/scripts/encryption_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 