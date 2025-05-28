"""
Migration script to move data from old schema to new vector tables.
Processes existing policy_records and policy_documents into unified vector storage.
"""

import asyncio
import asyncpg
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db.services.embedding_service import get_embedding_service
from db.services.db_pool import get_db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorMigrationManager:
    """Manages the migration process from old schema to vector tables."""
    
    def __init__(self):
        self.embedding_service = None
        self.migration_stats = {
            "policies_processed": 0,
            "policies_successful": 0,
            "policies_failed": 0,
            "documents_processed": 0,
            "documents_successful": 0,
            "documents_failed": 0,
            "errors": []
        }
    
    async def initialize(self):
        """Initialize services and connections."""
        self.embedding_service = await get_embedding_service()
        logger.info("Migration manager initialized")
    
    async def migrate_policy_data(self):
        """Migrate existing policy_records and policy_documents to policy_content_vectors."""
        
        pool = await get_db_pool()
        
        async with pool.get_connection() as conn:
            # Check if old tables exist
            tables_exist = await self._check_legacy_tables(conn)
            if not tables_exist:
                logger.warning("Legacy tables not found. Migration may already be complete or tables don't exist.")
                return
            
            # Get all policy records with their associated documents
            policies = await conn.fetch("""
                SELECT 
                    pr.policy_id,
                    pr.summary,
                    pr.structured_metadata,
                    pr.coverage_start_date,
                    pr.coverage_end_date,
                    pr.source_type,
                    pr.created_at,
                    COALESCE(
                        array_agg(
                            json_build_object(
                                'id', pd.id,
                                'file_path', pd.file_path,
                                'original_filename', pd.original_filename,
                                'content_type', pd.content_type,
                                'file_size', pd.file_size,
                                'document_type', pd.document_type,
                                'uploaded_by', pd.uploaded_by,
                                'metadata', pd.metadata
                            )
                        ) FILTER (WHERE pd.id IS NOT NULL),
                        ARRAY[]::json[]
                    ) as documents
                FROM policy_records pr
                LEFT JOIN policy_documents pd ON pd.policy_id = pr.policy_id::text
                WHERE pr.policy_id IS NOT NULL
                GROUP BY pr.policy_id, pr.summary, pr.structured_metadata, 
                         pr.coverage_start_date, pr.coverage_end_date, 
                         pr.source_type, pr.created_at
                ORDER BY pr.created_at
            """)
            
            logger.info(f"Found {len(policies)} policies to migrate")
            
            for i, policy in enumerate(policies, 1):
                try:
                    success = await self._migrate_single_policy(policy, i, len(policies))
                    if success:
                        self.migration_stats["policies_successful"] += 1
                    else:
                        self.migration_stats["policies_failed"] += 1
                    
                    self.migration_stats["policies_processed"] += 1
                    
                    # Progress update every 10 policies
                    if i % 10 == 0:
                        logger.info(f"Progress: {i}/{len(policies)} policies processed")
                        
                except Exception as e:
                    logger.error(f"Error migrating policy {policy['policy_id']}: {str(e)}")
                    self.migration_stats["policies_failed"] += 1
                    self.migration_stats["errors"].append({
                        "type": "policy_migration",
                        "policy_id": str(policy['policy_id']),
                        "error": str(e)
                    })
                    continue
    
    async def _check_legacy_tables(self, conn: asyncpg.Connection) -> bool:
        """Check if legacy tables exist."""
        try:
            policy_records_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'policy_records'
                )
            """)
            
            policy_documents_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'policy_documents'
                )
            """)
            
            return policy_records_exists or policy_documents_exists
        except Exception as e:
            logger.warning(f"Error checking legacy tables: {e}")
            return False
    
    async def _migrate_single_policy(self, policy: Dict[str, Any], index: int, total: int) -> bool:
        """Migrate a single policy record to vector storage."""
        try:
            # Extract user_id from documents or try to find from user_policy_links
            user_id = await self._get_policy_user_id(policy)
            if not user_id:
                logger.warning(f"No user_id found for policy {policy['policy_id']}, skipping")
                return False
            
            # Build content text from summary and metadata
            content_text = await self._build_policy_content_text(policy)
            if not content_text.strip():
                logger.warning(f"No content found for policy {policy['policy_id']}, skipping")
                return False
            
            # Build policy metadata
            policy_metadata = await self._build_policy_metadata(policy)
            
            # Build document metadata
            document_metadata = await self._build_document_metadata(policy)
            
            # Process and store
            record_id = await self.embedding_service.process_policy_document(
                policy_id=str(policy['policy_id']),
                user_id=user_id,
                content_text=content_text,
                policy_metadata=policy_metadata,
                document_metadata=document_metadata
            )
            
            logger.info(f"[{index}/{total}] Migrated policy {policy['policy_id']} -> {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating policy {policy['policy_id']}: {str(e)}")
            return False
    
    async def _get_policy_user_id(self, policy: Dict[str, Any]) -> str:
        """Extract user_id from policy data."""
        try:
            # First, try to get from documents
            documents = policy.get('documents', [])
            if documents and len(documents) > 0:
                for doc in documents:
                    if doc and 'uploaded_by' in doc and doc['uploaded_by']:
                        return doc['uploaded_by']
            
            # If not found in documents, try user_policy_links
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                user_id = await conn.fetchval("""
                    SELECT user_id FROM user_policy_links 
                    WHERE policy_id = $1 
                    ORDER BY linked_at DESC 
                    LIMIT 1
                """, policy['policy_id'])
                
                if user_id:
                    return str(user_id)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting user_id for policy {policy['policy_id']}: {e}")
            return None
    
    async def _build_policy_content_text(self, policy: Dict[str, Any]) -> str:
        """Build searchable content text from policy data."""
        content_parts = []
        
        # Add summary content
        summary = policy.get('summary')
        if summary:
            try:
                if isinstance(summary, str):
                    summary_data = json.loads(summary)
                else:
                    summary_data = summary
                
                if isinstance(summary_data, dict) and 'text' in summary_data:
                    content_parts.append(summary_data['text'])
                elif isinstance(summary_data, str):
                    content_parts.append(summary_data)
                elif isinstance(summary_data, dict):
                    # Extract text from all string values in the summary
                    for key, value in summary_data.items():
                        if isinstance(value, str) and len(value) > 10:
                            content_parts.append(f"{key}: {value}")
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, treat as plain text
                if isinstance(summary, str):
                    content_parts.append(summary)
        
        # Add structured metadata as searchable text
        metadata = policy.get('structured_metadata')
        if metadata:
            try:
                if isinstance(metadata, str):
                    metadata_data = json.loads(metadata)
                else:
                    metadata_data = metadata
                
                if isinstance(metadata_data, dict):
                    for key, value in metadata_data.items():
                        if isinstance(value, str) and len(value) > 3:
                            content_parts.append(f"{key}: {value}")
                        elif isinstance(value, (int, float)):
                            content_parts.append(f"{key}: {value}")
            except (json.JSONDecodeError, TypeError):
                if isinstance(metadata, str):
                    content_parts.append(metadata)
        
        # Add basic policy information
        if policy.get('coverage_start_date'):
            content_parts.append(f"Coverage start date: {policy['coverage_start_date']}")
        if policy.get('coverage_end_date'):
            content_parts.append(f"Coverage end date: {policy['coverage_end_date']}")
        if policy.get('source_type'):
            content_parts.append(f"Source type: {policy['source_type']}")
        
        return "\n".join(content_parts)
    
    async def _build_policy_metadata(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Build structured policy metadata."""
        metadata = {
            "policy_number": str(policy['policy_id']),
            "source_type": policy.get('source_type'),
            "migration_source": "policy_records"
        }
        
        # Add dates if available
        if policy.get('coverage_start_date'):
            metadata["coverage_start_date"] = policy['coverage_start_date'].isoformat()
        if policy.get('coverage_end_date'):
            metadata["coverage_end_date"] = policy['coverage_end_date'].isoformat()
        
        # Add original summary and metadata
        if policy.get('summary'):
            try:
                summary_data = json.loads(policy['summary']) if isinstance(policy['summary'], str) else policy['summary']
                metadata["original_summary"] = summary_data
            except (json.JSONDecodeError, TypeError):
                metadata["original_summary"] = policy['summary']
        
        if policy.get('structured_metadata'):
            try:
                struct_data = json.loads(policy['structured_metadata']) if isinstance(policy['structured_metadata'], str) else policy['structured_metadata']
                metadata["original_metadata"] = struct_data
            except (json.JSONDecodeError, TypeError):
                metadata["original_metadata"] = policy['structured_metadata']
        
        return metadata
    
    async def _build_document_metadata(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Build document metadata."""
        documents = policy.get('documents', [])
        
        metadata = {
            "migration_source": "policy_records",
            "original_created_at": policy['created_at'].isoformat() if policy.get('created_at') else None,
            "document_count": len(documents) if documents else 0,
            "processing_status": "migrated",
            "migration_timestamp": datetime.now().isoformat()
        }
        
        # Add document information if available
        if documents and len(documents) > 0:
            metadata["documents"] = documents
            
            # Aggregate document types
            doc_types = set()
            total_size = 0
            for doc in documents:
                if doc and isinstance(doc, dict):
                    if 'document_type' in doc:
                        doc_types.add(doc['document_type'])
                    if 'file_size' in doc and isinstance(doc['file_size'], (int, float)):
                        total_size += doc['file_size']
            
            metadata["document_types"] = list(doc_types)
            metadata["total_file_size"] = total_size
        
        return metadata
    
    async def create_migration_report(self):
        """Generate a report of the migration results."""
        pool = await get_db_pool()
        
        async with pool.get_connection() as conn:
            # Count original records (if tables exist)
            old_policy_count = 0
            old_document_count = 0
            
            try:
                old_policy_count = await conn.fetchval("SELECT COUNT(*) FROM policy_records") or 0
            except:
                pass
                
            try:
                old_document_count = await conn.fetchval("SELECT COUNT(*) FROM policy_documents") or 0
            except:
                pass
            
            # Count new records
            new_policy_vectors = await conn.fetchval("SELECT COUNT(*) FROM policy_content_vectors") or 0
            new_user_vectors = await conn.fetchval("SELECT COUNT(*) FROM user_document_vectors") or 0
            
            # Get embedding stats
            embedding_stats = await self.embedding_service.get_embedding_stats()
            
            report = {
                "migration_completed_at": datetime.now().isoformat(),
                "original_data": {
                    "policy_records": old_policy_count,
                    "policy_documents": old_document_count
                },
                "migrated_data": {
                    "policy_content_vectors": new_policy_vectors,
                    "user_document_vectors": new_user_vectors
                },
                "migration_stats": self.migration_stats,
                "embedding_stats": embedding_stats,
                "success_rate": f"{(self.migration_stats['policies_successful'] / max(self.migration_stats['policies_processed'], 1) * 100):.1f}%"
            }
            
            logger.info("=" * 60)
            logger.info("MIGRATION REPORT")
            logger.info("=" * 60)
            logger.info(json.dumps(report, indent=2, default=str))
            logger.info("=" * 60)
            
            # Save report to file
            report_file = Path(__file__).parent / "migration_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to: {report_file}")
            
            return report

async def main():
    """Run the complete migration process."""
    logger.info("Starting vector migration process...")
    
    migration_manager = VectorMigrationManager()
    
    try:
        # Step 1: Initialize services
        await migration_manager.initialize()
        
        # Step 2: Migrate policy data
        await migration_manager.migrate_policy_data()
        
        # Step 3: Generate migration report
        await migration_manager.create_migration_report()
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        # Still try to generate a report
        try:
            await migration_manager.create_migration_report()
        except:
            pass
        raise

if __name__ == "__main__":
    asyncio.run(main()) 