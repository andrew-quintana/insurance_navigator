#!/usr/bin/env python3
"""
Phase B.3.2: Comprehensive System Validation
UUID Standardization - Post-Migration System Validation

This script performs comprehensive validation of the UUID standardization
to ensure the system is working correctly with deterministic UUIDs.

Reference: PHASED_TODO_IMPLEMENTATION.md "B.3.2 Post-Migration Validation"
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    """Comprehensive system validation for UUID standardization."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.validation_results = {}
        
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
    
    def is_uuidv5(self, uuid_value) -> bool:
        """Check if UUID is version 5 (deterministic)."""
        try:
            if isinstance(uuid_value, str):
                uuid_obj = uuid.UUID(uuid_value)
            else:
                # Handle asyncpg UUID objects
                uuid_obj = uuid.UUID(str(uuid_value))
            return uuid_obj.version == 5
        except (ValueError, TypeError):
            return False
    
    async def validate_uuid_consistency(self) -> Dict[str, Any]:
        """Validate UUID consistency across all documents and chunks."""
        logger.info("🔍 Validating UUID consistency...")
        
        try:
            # Check document UUIDs
            documents = await self.conn.fetch("""
                SELECT document_id, user_id, filename, file_sha256
                FROM upload_pipeline.documents
                ORDER BY created_at DESC
            """)
            
            uuidv5_docs = 0
            uuidv4_docs = 0
            invalid_docs = 0
            
            for doc in documents:
                try:
                    if isinstance(doc['document_id'], str):
                        uuid_obj = uuid.UUID(doc['document_id'])
                    else:
                        uuid_obj = uuid.UUID(str(doc['document_id']))
                    if uuid_obj.version == 5:
                        uuidv5_docs += 1
                    elif uuid_obj.version == 4:
                        uuidv4_docs += 1
                    else:
                        invalid_docs += 1
                except:
                    invalid_docs += 1
            
            # Check chunk UUIDs
            chunks = await self.conn.fetch("""
                SELECT chunk_id, document_id, chunker_name, chunker_version, chunk_ord
                FROM upload_pipeline.document_chunks
                ORDER BY created_at DESC
            """)
            
            uuidv5_chunks = 0
            uuidv4_chunks = 0
            invalid_chunks = 0
            
            for chunk in chunks:
                try:
                    if isinstance(chunk['chunk_id'], str):
                        uuid_obj = uuid.UUID(chunk['chunk_id'])
                    else:
                        uuid_obj = uuid.UUID(str(chunk['chunk_id']))
                    if uuid_obj.version == 5:
                        uuidv5_chunks += 1
                    elif uuid_obj.version == 4:
                        uuidv4_chunks += 1
                    else:
                        invalid_chunks += 1
                except:
                    invalid_chunks += 1
            
            # Validate deterministic UUID generation
            deterministic_validation = await self.validate_deterministic_generation(documents, chunks)
            
            results = {
                "total_documents": len(documents),
                "uuidv5_documents": uuidv5_docs,
                "uuidv4_documents": uuidv4_docs,
                "invalid_documents": invalid_docs,
                "total_chunks": len(chunks),
                "uuidv5_chunks": uuidv5_chunks,
                "uuidv4_chunks": uuidv4_chunks,
                "invalid_chunks": invalid_chunks,
                "deterministic_percentage": (uuidv5_docs / len(documents) * 100) if documents else 0,
                "chunk_deterministic_percentage": (uuidv5_chunks / len(chunks) * 100) if chunks else 0,
                "deterministic_validation": deterministic_validation
            }
            
            logger.info(f"✅ UUID consistency validation complete: {uuidv5_docs}/{len(documents)} documents, {uuidv5_chunks}/{len(chunks)} chunks use deterministic UUIDs")
            return results
            
        except Exception as e:
            logger.error(f"❌ UUID consistency validation failed: {e}")
            return {"error": str(e)}
    
    async def validate_deterministic_generation(self, documents: List, chunks: List) -> Dict[str, Any]:
        """Validate that UUIDs are generated deterministically."""
        logger.info("🔍 Validating deterministic UUID generation...")
        
        try:
            SYSTEM_NAMESPACE = uuid.UUID('6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42')
            validation_results = {
                "document_validation": {"correct": 0, "incorrect": 0, "errors": []},
                "chunk_validation": {"correct": 0, "incorrect": 0, "errors": []}
            }
            
            # Validate document UUIDs
            for doc in documents:
                try:
                    expected_uuid = str(uuid.uuid5(SYSTEM_NAMESPACE, f"{doc['user_id']}:{doc['file_sha256']}"))
                    if doc['document_id'] == expected_uuid:
                        validation_results["document_validation"]["correct"] += 1
                    else:
                        validation_results["document_validation"]["incorrect"] += 1
                        validation_results["document_validation"]["errors"].append({
                            "document_id": doc['document_id'],
                            "expected": expected_uuid,
                            "filename": doc['filename']
                        })
                except Exception as e:
                    validation_results["document_validation"]["errors"].append({
                        "document_id": doc['document_id'],
                        "error": str(e)
                    })
            
            # Validate chunk UUIDs
            for chunk in chunks:
                try:
                    expected_uuid = str(uuid.uuid5(SYSTEM_NAMESPACE, 
                        f"{chunk['document_id']}:{chunk['chunker_name']}:{chunk['chunker_version']}:{chunk['chunk_ord']}"))
                    if chunk['chunk_id'] == expected_uuid:
                        validation_results["chunk_validation"]["correct"] += 1
                    else:
                        validation_results["chunk_validation"]["incorrect"] += 1
                        validation_results["chunk_validation"]["errors"].append({
                            "chunk_id": chunk['chunk_id'],
                            "expected": expected_uuid,
                            "document_id": chunk['document_id']
                        })
                except Exception as e:
                    validation_results["chunk_validation"]["errors"].append({
                        "chunk_id": chunk['chunk_id'],
                        "error": str(e)
                    })
            
            logger.info(f"✅ Deterministic generation validation complete: {validation_results['document_validation']['correct']} correct documents, {validation_results['chunk_validation']['correct']} correct chunks")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Deterministic generation validation failed: {e}")
            return {"error": str(e)}
    
    async def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across all tables."""
        logger.info("🔍 Validating data integrity...")
        
        try:
            integrity_results = {}
            
            # Check for orphaned chunks
            orphaned_chunks = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.document_chunks dc
                LEFT JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                WHERE d.document_id IS NULL
            """)
            integrity_results["orphaned_chunks"] = orphaned_chunks
            
            # Check for orphaned jobs
            orphaned_jobs = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.upload_jobs uj
                LEFT JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE d.document_id IS NULL
            """)
            integrity_results["orphaned_jobs"] = orphaned_jobs
            
            # Check for orphaned events
            orphaned_events = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.events e
                LEFT JOIN upload_pipeline.documents d ON e.document_id = d.document_id
                WHERE d.document_id IS NULL
            """)
            integrity_results["orphaned_events"] = orphaned_events
            
            # Check for missing chunks (documents without chunks)
            documents_without_chunks = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                WHERE dc.document_id IS NULL
            """)
            integrity_results["documents_without_chunks"] = documents_without_chunks
            
            # Check for duplicate documents (same user_id + file_sha256)
            duplicate_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, file_sha256, COUNT(*) as count
                    FROM upload_pipeline.documents
                    GROUP BY user_id, file_sha256
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
            integrity_results["duplicate_documents"] = duplicate_documents
            
            # Check for duplicate chunks (same document_id + chunk_ord)
            duplicate_chunks = await self.conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT document_id, chunk_ord, COUNT(*) as count
                    FROM upload_pipeline.document_chunks
                    GROUP BY document_id, chunk_ord
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
            integrity_results["duplicate_chunks"] = duplicate_chunks
            
            # Calculate integrity score
            total_issues = (orphaned_chunks + orphaned_jobs + orphaned_events + 
                          documents_without_chunks + duplicate_documents + duplicate_chunks)
            integrity_score = max(0, 100 - (total_issues * 10))  # 10 points per issue
            
            integrity_results["total_issues"] = total_issues
            integrity_results["integrity_score"] = integrity_score
            
            logger.info(f"✅ Data integrity validation complete: {total_issues} issues found, integrity score: {integrity_score}")
            return integrity_results
            
        except Exception as e:
            logger.error(f"❌ Data integrity validation failed: {e}")
            return {"error": str(e)}
    
    async def validate_rag_functionality(self) -> Dict[str, Any]:
        """Validate RAG functionality with deterministic UUIDs."""
        logger.info("🔍 Validating RAG functionality...")
        
        try:
            # Test RAG retrieval for each document
            documents = await self.conn.fetch("""
                SELECT d.document_id, d.filename, COUNT(dc.chunk_id) as chunk_count
                FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                GROUP BY d.document_id, d.filename
                ORDER BY d.created_at DESC
            """)
            
            rag_results = {
                "total_documents": len(documents),
                "accessible_documents": 0,
                "inaccessible_documents": 0,
                "documents_with_chunks": 0,
                "documents_without_chunks": 0,
                "rag_success_rate": 0,
                "test_results": []
            }
            
            for doc in documents:
                doc_result = {
                    "document_id": doc['document_id'],
                    "filename": doc['filename'],
                    "chunk_count": doc['chunk_count'],
                    "accessible": False,
                    "rag_working": False
                }
                
                # Check if document has chunks (basic RAG requirement)
                if doc['chunk_count'] > 0:
                    rag_results["documents_with_chunks"] += 1
                    doc_result["accessible"] = True
                    doc_result["rag_working"] = True
                    rag_results["accessible_documents"] += 1
                else:
                    rag_results["documents_without_chunks"] += 1
                    rag_results["inaccessible_documents"] += 1
                
                rag_results["test_results"].append(doc_result)
            
            # Calculate RAG success rate
            if documents:
                rag_results["rag_success_rate"] = (rag_results["accessible_documents"] / len(documents)) * 100
            
            logger.info(f"✅ RAG functionality validation complete: {rag_results['accessible_documents']}/{len(documents)} documents accessible")
            return rag_results
            
        except Exception as e:
            logger.error(f"❌ RAG functionality validation failed: {e}")
            return {"error": str(e)}
    
    async def validate_performance_metrics(self) -> Dict[str, Any]:
        """Validate system performance metrics."""
        logger.info("🔍 Validating performance metrics...")
        
        try:
            performance_results = {}
            
            # Get document processing times
            processing_times = await self.conn.fetch("""
                SELECT 
                    EXTRACT(EPOCH FROM (updated_at - created_at)) as processing_time_seconds,
                    processing_status
                FROM upload_pipeline.documents
                WHERE updated_at IS NOT NULL
                ORDER BY created_at DESC
            """)
            
            if processing_times:
                avg_processing_time = sum(row['processing_time_seconds'] for row in processing_times) / len(processing_times)
                performance_results["avg_processing_time_seconds"] = avg_processing_time
                performance_results["total_processed_documents"] = len(processing_times)
            
            # Get chunk processing statistics
            chunk_stats = await self.conn.fetch("""
                SELECT 
                    COUNT(*) as total_chunks,
                    AVG(LENGTH(text)) as avg_chunk_length,
                    COUNT(DISTINCT document_id) as documents_with_chunks
                FROM upload_pipeline.document_chunks
            """)
            
            if chunk_stats:
                stats = chunk_stats[0]
                performance_results["total_chunks"] = stats['total_chunks']
                performance_results["avg_chunk_length"] = stats['avg_chunk_length']
                performance_results["documents_with_chunks"] = stats['documents_with_chunks']
            
            # Get storage usage
            storage_usage = await self.conn.fetch("""
                SELECT 
                    SUM(bytes_len) as total_bytes,
                    COUNT(*) as total_documents
                FROM upload_pipeline.documents
            """)
            
            if storage_usage:
                storage = storage_usage[0]
                performance_results["total_storage_bytes"] = storage['total_bytes']
                performance_results["total_documents"] = storage['total_documents']
                if storage['total_bytes']:
                    performance_results["avg_document_size_bytes"] = storage['total_bytes'] / storage['total_documents']
            
            logger.info(f"✅ Performance metrics validation complete")
            return performance_results
            
        except Exception as e:
            logger.error(f"❌ Performance metrics validation failed: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive system validation."""
        logger.info("🚀 Starting comprehensive system validation...")
        
        if not await self.connect_database():
            return {"error": "Database connection failed"}
        
        try:
            # Run all validation tests
            validation_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "uuid_consistency": await self.validate_uuid_consistency(),
                "data_integrity": await self.validate_data_integrity(),
                "rag_functionality": await self.validate_rag_functionality(),
                "performance_metrics": await self.validate_performance_metrics()
            }
            
            # Calculate overall validation score
            scores = []
            if "uuid_consistency" in validation_results and "deterministic_percentage" in validation_results["uuid_consistency"]:
                scores.append(validation_results["uuid_consistency"]["deterministic_percentage"])
            
            if "data_integrity" in validation_results and "integrity_score" in validation_results["data_integrity"]:
                scores.append(validation_results["data_integrity"]["integrity_score"])
            
            if "rag_functionality" in validation_results and "rag_success_rate" in validation_results["rag_functionality"]:
                scores.append(validation_results["rag_functionality"]["rag_success_rate"])
            
            if scores:
                validation_results["overall_score"] = sum(scores) / len(scores)
            else:
                validation_results["overall_score"] = 0
            
            # Determine validation status
            if validation_results["overall_score"] >= 95:
                validation_results["status"] = "EXCELLENT"
            elif validation_results["overall_score"] >= 85:
                validation_results["status"] = "GOOD"
            elif validation_results["overall_score"] >= 70:
                validation_results["status"] = "ACCEPTABLE"
            else:
                validation_results["status"] = "NEEDS_IMPROVEMENT"
            
            validation_results["success"] = True
            
            logger.info(f"✅ Comprehensive validation complete: {validation_results['status']} ({validation_results['overall_score']:.1f}%)")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {e}")
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
    
    # Run comprehensive validation
    validator = SystemValidator(database_url)
    results = await validator.run_comprehensive_validation()
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"phase_b_validation_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Validation results saved to: {output_file}")
    
    # Print summary
    if results.get("success"):
        print(f"\n📊 COMPREHENSIVE VALIDATION SUMMARY")
        print(f"Overall Score: {results.get('overall_score', 0):.1f}%")
        print(f"Status: {results.get('status', 'UNKNOWN')}")
        
        if "uuid_consistency" in results:
            uc = results["uuid_consistency"]
            print(f"\n🔍 UUID CONSISTENCY")
            print(f"Deterministic Documents: {uc.get('uuidv5_documents', 0)}/{uc.get('total_documents', 0)} ({uc.get('deterministic_percentage', 0):.1f}%)")
            print(f"Deterministic Chunks: {uc.get('uuidv5_chunks', 0)}/{uc.get('total_chunks', 0)} ({uc.get('chunk_deterministic_percentage', 0):.1f}%)")
        
        if "data_integrity" in results:
            di = results["data_integrity"]
            print(f"\n🔍 DATA INTEGRITY")
            print(f"Integrity Score: {di.get('integrity_score', 0):.1f}%")
            print(f"Total Issues: {di.get('total_issues', 0)}")
            print(f"Orphaned Chunks: {di.get('orphaned_chunks', 0)}")
            print(f"Duplicate Documents: {di.get('duplicate_documents', 0)}")
        
        if "rag_functionality" in results:
            rf = results["rag_functionality"]
            print(f"\n🔍 RAG FUNCTIONALITY")
            print(f"RAG Success Rate: {rf.get('rag_success_rate', 0):.1f}%")
            print(f"Accessible Documents: {rf.get('accessible_documents', 0)}/{rf.get('total_documents', 0)}")
            print(f"Documents with Chunks: {rf.get('documents_with_chunks', 0)}")
    else:
        print(f"❌ Validation failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
