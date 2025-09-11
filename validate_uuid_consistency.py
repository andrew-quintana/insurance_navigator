#!/usr/bin/env python3
"""
UUID Consistency Validation Script

This script validates UUID consistency across the system to ensure
the Phase A fixes are working correctly and no UUID mismatches exist.

Validates:
1. UUID format consistency
2. Deterministic generation verification
3. Database integrity checks
4. Orphaned data detection
5. Foreign key relationships

Reference: Phase A Critical Path Resolution
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UUIDConsistencyValidator:
    """Validates UUID consistency across the system."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "validations": {},
            "overall_success": False,
            "issues_found": []
        }
    
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
    
    def validate_uuid_format(self, uuid_string: str) -> bool:
        """Validate UUID format."""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    def is_uuidv5(self, uuid_string: str) -> bool:
        """Check if UUID is version 5 (deterministic)."""
        try:
            uuid_obj = uuid.UUID(uuid_string)
            return uuid_obj.version == 5
        except (ValueError, TypeError):
            return False
    
    def is_uuidv4(self, uuid_string: str) -> bool:
        """Check if UUID is version 4 (random)."""
        try:
            uuid_obj = uuid.UUID(uuid_string)
            return uuid_obj.version == 4
        except (ValueError, TypeError):
            return False
    
    async def validate_document_uuids(self) -> Dict[str, Any]:
        """Validate document UUIDs in the database."""
        logger.info("📄 Validating document UUIDs...")
        
        try:
            # Get all documents
            documents = await self.conn.fetch("""
                SELECT document_id, user_id, file_sha256, created_at
                FROM upload_pipeline.documents
                ORDER BY created_at DESC
                LIMIT 100
            """)
            
            results = {
                "total_documents": len(documents),
                "valid_uuids": 0,
                "invalid_uuids": 0,
                "uuidv4_documents": 0,
                "uuidv5_documents": 0,
                "format_errors": [],
                "version_analysis": {}
            }
            
            for doc in documents:
                doc_id = doc['document_id']
                user_id = doc['user_id']
                file_hash = doc['file_sha256']
                
                # Validate format
                if self.validate_uuid_format(doc_id):
                    results["valid_uuids"] += 1
                    
                    # Check version
                    if self.is_uuidv4(doc_id):
                        results["uuidv4_documents"] += 1
                        results["version_analysis"][str(doc_id)] = "v4 (random)"
                    elif self.is_uuidv5(doc_id):
                        results["uuidv5_documents"] += 1
                        results["version_analysis"][str(doc_id)] = "v5 (deterministic)"
                    else:
                        results["version_analysis"][str(doc_id)] = f"v{uuid.UUID(doc_id).version}"
                else:
                    results["invalid_uuids"] += 1
                    results["format_errors"].append({
                        "document_id": str(doc_id),
                        "user_id": str(user_id),
                        "error": "Invalid UUID format"
                    })
            
            logger.info(f"✅ Document UUID validation complete: {results['valid_uuids']}/{results['total_documents']} valid")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error validating document UUIDs: {e}")
            return {"error": str(e)}
    
    async def validate_chunk_uuids(self) -> Dict[str, Any]:
        """Validate chunk UUIDs in the database."""
        logger.info("🧩 Validating chunk UUIDs...")
        
        try:
            # Get all chunks
            chunks = await self.conn.fetch("""
                SELECT chunk_id, document_id, chunker_name, chunker_version, chunk_ord
                FROM upload_pipeline.document_chunks
                ORDER BY created_at DESC
                LIMIT 100
            """)
            
            results = {
                "total_chunks": len(chunks),
                "valid_uuids": 0,
                "invalid_uuids": 0,
                "uuidv4_chunks": 0,
                "uuidv5_chunks": 0,
                "format_errors": [],
                "version_analysis": {}
            }
            
            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                doc_id = chunk['document_id']
                
                # Validate format
                if self.validate_uuid_format(chunk_id):
                    results["valid_uuids"] += 1
                    
                    # Check version
                    if self.is_uuidv4(chunk_id):
                        results["uuidv4_chunks"] += 1
                        results["version_analysis"][str(chunk_id)] = "v4 (random)"
                    elif self.is_uuidv5(chunk_id):
                        results["uuidv5_chunks"] += 1
                        results["version_analysis"][str(chunk_id)] = "v5 (deterministic)"
                    else:
                        results["version_analysis"][str(chunk_id)] = f"v{uuid.UUID(chunk_id).version}"
                else:
                    results["invalid_uuids"] += 1
                    results["format_errors"].append({
                        "chunk_id": str(chunk_id),
                        "document_id": str(doc_id),
                        "error": "Invalid UUID format"
                    })
            
            logger.info(f"✅ Chunk UUID validation complete: {results['valid_uuids']}/{results['total_chunks']} valid")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error validating chunk UUIDs: {e}")
            return {"error": str(e)}
    
    async def validate_foreign_key_relationships(self) -> Dict[str, Any]:
        """Validate foreign key relationships between documents and chunks."""
        logger.info("🔗 Validating foreign key relationships...")
        
        try:
            # Check for orphaned chunks
            orphaned_chunks = await self.conn.fetch("""
                SELECT dc.chunk_id, dc.document_id
                FROM upload_pipeline.document_chunks dc
                LEFT JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                WHERE d.document_id IS NULL
                LIMIT 50
            """)
            
            # Check for documents without chunks
            documents_without_chunks = await self.conn.fetch("""
                SELECT d.document_id, d.user_id
                FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                WHERE dc.document_id IS NULL
                LIMIT 50
            """)
            
            results = {
                "orphaned_chunks": len(orphaned_chunks),
                "documents_without_chunks": len(documents_without_chunks),
                "orphaned_chunk_details": [{"chunk_id": str(c['chunk_id']), "document_id": str(c['document_id'])} for c in orphaned_chunks],
                "document_details": [{"document_id": str(d['document_id']), "user_id": str(d['user_id'])} for d in documents_without_chunks]
            }
            
            if orphaned_chunks:
                logger.warning(f"⚠️ Found {len(orphaned_chunks)} orphaned chunks")
            else:
                logger.info("✅ No orphaned chunks found")
            
            if documents_without_chunks:
                logger.warning(f"⚠️ Found {len(documents_without_chunks)} documents without chunks")
            else:
                logger.info("✅ All documents have associated chunks")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error validating foreign key relationships: {e}")
            return {"error": str(e)}
    
    async def validate_deterministic_generation(self) -> Dict[str, Any]:
        """Validate that UUIDs are generated deterministically."""
        logger.info("🎯 Validating deterministic UUID generation...")
        
        try:
            from utils.uuid_generation import UUIDGenerator
            
            # Test deterministic generation
            test_user_id = "test-user-123"
            test_content_hash = "test-content-hash-456"
            
            # Generate same UUID multiple times
            uuid1 = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            uuid2 = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            uuid3 = UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            
            is_deterministic = (uuid1 == uuid2 == uuid3)
            
            # Test chunk generation
            chunk_uuid1 = UUIDGenerator.chunk_uuid(uuid1, "markdown", "1.0", 0)
            chunk_uuid2 = UUIDGenerator.chunk_uuid(uuid1, "markdown", "1.0", 0)
            
            chunk_deterministic = (chunk_uuid1 == chunk_uuid2)
            
            results = {
                "document_uuid_deterministic": is_deterministic,
                "chunk_uuid_deterministic": chunk_deterministic,
                "test_uuids": {
                    "uuid1": uuid1,
                    "uuid2": uuid2,
                    "uuid3": uuid3,
                    "chunk_uuid1": chunk_uuid1,
                    "chunk_uuid2": chunk_uuid2
                }
            }
            
            if is_deterministic and chunk_deterministic:
                logger.info("✅ UUID generation is deterministic")
            else:
                logger.error("❌ UUID generation is not deterministic")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error validating deterministic generation: {e}")
            return {"error": str(e)}
    
    async def detect_uuid_mismatches(self) -> Dict[str, Any]:
        """Detect potential UUID mismatches in the system."""
        logger.info("🔍 Detecting UUID mismatches...")
        
        try:
            # Check for documents with v4 UUIDs (should be v5 after Phase A)
            v4_documents = await self.conn.fetch("""
                SELECT document_id, user_id, file_sha256, created_at
                FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            # Check for chunks with v4 UUIDs (should be v5)
            v4_chunks = await self.conn.fetch("""
                SELECT chunk_id, document_id, chunker_name, chunker_version, chunk_ord
                FROM upload_pipeline.document_chunks
                WHERE chunk_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            results = {
                "v4_documents_found": len(v4_documents),
                "v4_chunks_found": len(v4_chunks),
                "v4_document_details": [{"document_id": str(d['document_id']), "user_id": str(d['user_id']), "created_at": str(d['created_at'])} for d in v4_documents],
                "v4_chunk_details": [{"chunk_id": str(c['chunk_id']), "document_id": str(c['document_id']), "chunker": c['chunker_name']} for c in v4_chunks]
            }
            
            if v4_documents:
                logger.warning(f"⚠️ Found {len(v4_documents)} documents with v4 UUIDs (should be v5 after Phase A)")
            else:
                logger.info("✅ No v4 document UUIDs found")
            
            if v4_chunks:
                logger.warning(f"⚠️ Found {len(v4_chunks)} chunks with v4 UUIDs (should be v5)")
            else:
                logger.info("✅ No v4 chunk UUIDs found")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error detecting UUID mismatches: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive UUID consistency validation."""
        logger.info("🚀 Starting UUID Consistency Validation")
        logger.info("=" * 60)
        
        try:
            # Connect to database
            if not await self.connect_database():
                return self.validation_results
            
            # Run all validations
            validations = [
                ("document_uuids", self.validate_document_uuids()),
                ("chunk_uuids", self.validate_chunk_uuids()),
                ("foreign_key_relationships", self.validate_foreign_key_relationships()),
                ("deterministic_generation", self.validate_deterministic_generation()),
                ("uuid_mismatches", self.detect_uuid_mismatches())
            ]
            
            for validation_name, validation_coro in validations:
                logger.info(f"\n📋 Running {validation_name} validation...")
                result = await validation_coro
                self.validation_results["validations"][validation_name] = result
                
                # Check for issues
                if "error" in result:
                    self.validation_results["issues_found"].append(f"{validation_name}: {result['error']}")
                elif validation_name == "uuid_mismatches":
                    if result.get("v4_documents_found", 0) > 0 or result.get("v4_chunks_found", 0) > 0:
                        self.validation_results["issues_found"].append(f"{validation_name}: Found v4 UUIDs that should be v5")
                elif validation_name == "foreign_key_relationships":
                    if result.get("orphaned_chunks", 0) > 0:
                        self.validation_results["issues_found"].append(f"{validation_name}: Found orphaned chunks")
            
            # Calculate overall success
            self.validation_results["overall_success"] = len(self.validation_results["issues_found"]) == 0
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("📊 UUID CONSISTENCY VALIDATION RESULTS")
            logger.info("=" * 60)
            
            for validation_name, result in self.validation_results["validations"].items():
                if "error" in result:
                    logger.error(f"{validation_name}: ❌ ERROR - {result['error']}")
                else:
                    logger.info(f"{validation_name}: ✅ COMPLETED")
            
            if self.validation_results["issues_found"]:
                logger.warning(f"\n⚠️ Issues found: {len(self.validation_results['issues_found'])}")
                for issue in self.validation_results["issues_found"]:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("\n✅ No issues found - UUID consistency is good!")
            
            overall_status = "✅ VALIDATION PASSED" if self.validation_results["overall_success"] else "❌ VALIDATION FAILED"
            logger.info(f"\nOverall Result: {overall_status}")
            
            return self.validation_results
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            self.validation_results["error"] = str(e)
            return self.validation_results
        
        finally:
            await self.disconnect_database()

async def main():
    """Run UUID consistency validation."""
    # Get database URL from environment or use default
    import os
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:54321/postgres")
    
    validator = UUIDConsistencyValidator(database_url)
    results = await validator.run_comprehensive_validation()
    
    # Save results
    timestamp = int(datetime.utcnow().timestamp())
    results_file = f"uuid_consistency_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: {results_file}")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
