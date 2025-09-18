#!/usr/bin/env python3
"""
Phase B.1.1: Data Inventory and Analysis Script
UUID Standardization - Existing Data Assessment

This script performs comprehensive analysis of existing data to:
1. Identify all documents with random UUIDs (UUIDv4 pattern detection)
2. Count affected documents by user, upload date, and processing status
3. Find orphaned chunks referencing non-existent document UUIDs
4. Calculate storage impact of UUID-affected data
5. Identify high-priority documents (recent, frequently accessed)
6. Map user impact distribution across affected documents
7. Analyze pipeline failure patterns

Reference: PHASED_TODO_IMPLEMENTATION.md "B.1.1 Data Inventory and Analysis"
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DocumentAnalysis:
    """Analysis results for a single document."""
    document_id: str
    user_id: str
    filename: str
    file_sha256: str
    created_at: datetime
    processing_status: Optional[str]
    uuid_version: int
    is_deterministic: bool
    has_chunks: bool
    chunk_count: int
    is_orphaned: bool
    priority_score: float

@dataclass
class MigrationImpact:
    """Overall migration impact assessment."""
    total_documents: int
    uuidv4_documents: int
    uuidv5_documents: int
    orphaned_chunks: int
    affected_users: int
    storage_impact_mb: float
    high_priority_documents: int
    recent_documents: int
    failed_pipeline_documents: int

class PhaseBDataAnalyzer:
    """Comprehensive data analysis for Phase B migration planning."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.analysis_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "B.1.1 - Data Inventory and Analysis",
            "documents": [],
            "migration_impact": None,
            "user_impact": {},
            "pipeline_failures": {},
            "recommendations": []
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
    
    def is_uuidv5(self, uuid_value) -> bool:
        """Check if UUID is version 5 (deterministic)."""
        try:
            if isinstance(uuid_value, str):
                uuid_obj = uuid.UUID(uuid_value)
            else:
                uuid_obj = uuid_value
            return uuid_obj.version == 5
        except (ValueError, TypeError):
            return False
    
    def calculate_priority_score(self, doc: Dict[str, Any], chunk_count: int) -> float:
        """Calculate priority score for document migration."""
        score = 0.0
        
        # Recency factor (higher for newer documents)
        try:
            # Handle timezone-aware datetimes
            created_at = doc['created_at']
            if created_at.tzinfo is not None:
                # Convert to UTC for comparison
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
            # If datetime comparison fails, use default score
            score += 0.1
        
        # Processing status factor
        if doc.get('processing_status') == 'embedded':
            score += 0.3
        elif doc.get('processing_status') in ['chunked', 'embedding']:
            score += 0.2
        elif doc.get('processing_status') in ['parsed', 'chunking']:
            score += 0.1
        
        # Chunk count factor (more chunks = higher priority)
        if chunk_count > 0:
            score += min(0.3, chunk_count * 0.01)
        
        return min(1.0, score)
    
    async def analyze_documents(self) -> List[DocumentAnalysis]:
        """Analyze all documents in the database."""
        logger.info("📄 Analyzing documents...")
        
        try:
            # Get all documents with their processing status
            documents = await self.conn.fetch("""
                SELECT 
                    d.document_id,
                    d.user_id,
                    d.filename,
                    d.file_sha256,
                    d.created_at,
                    d.processing_status,
                    d.bytes_len
                FROM upload_pipeline.documents d
                ORDER BY d.created_at DESC
            """)
            
            logger.info(f"📊 Found {len(documents)} documents to analyze")
            
            document_analyses = []
            
            for doc in documents:
                # Determine UUID version
                is_v4 = self.is_uuidv4(doc['document_id'])
                is_v5 = self.is_uuidv5(doc['document_id'])
                uuid_version = 4 if is_v4 else (5 if is_v5 else 0)
                
                # Check for chunks
                chunk_result = await self.conn.fetchrow("""
                    SELECT COUNT(*) as chunk_count
                    FROM upload_pipeline.document_chunks dc
                    WHERE dc.document_id = $1
                """, doc['document_id'])
                
                chunk_count = chunk_result['chunk_count'] if chunk_result else 0
                has_chunks = chunk_count > 0
                
                # Check if document is orphaned (has chunks but no valid processing)
                is_orphaned = has_chunks and (not doc['processing_status'] or 
                            doc['processing_status'] not in ['embedded', 'chunked', 'embedding'])
                
                # Calculate priority score
                priority_score = self.calculate_priority_score(doc, chunk_count)
                
                analysis = DocumentAnalysis(
                    document_id=doc['document_id'],
                    user_id=doc['user_id'],
                    filename=doc['filename'],
                    file_sha256=doc['file_sha256'],
                    created_at=doc['created_at'],
                    processing_status=doc['processing_status'],
                    uuid_version=uuid_version,
                    is_deterministic=is_v5,
                    has_chunks=has_chunks,
                    chunk_count=chunk_count,
                    is_orphaned=is_orphaned,
                    priority_score=priority_score
                )
                
                document_analyses.append(analysis)
            
            logger.info(f"✅ Document analysis complete: {len(document_analyses)} documents analyzed")
            return document_analyses
            
        except Exception as e:
            logger.error(f"❌ Document analysis failed: {e}")
            return []
    
    async def analyze_orphaned_chunks(self) -> int:
        """Find orphaned chunks referencing non-existent document UUIDs."""
        logger.info("🔍 Analyzing orphaned chunks...")
        
        try:
            # Find chunks that reference non-existent documents
            orphaned_chunks = await self.conn.fetch("""
                SELECT COUNT(*) as orphaned_count
                FROM upload_pipeline.document_chunks dc
                LEFT JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                WHERE d.document_id IS NULL
            """)
            
            orphaned_count = orphaned_chunks[0]['orphaned_count'] if orphaned_chunks else 0
            logger.info(f"🔍 Found {orphaned_count} orphaned chunks")
            return orphaned_count
            
        except Exception as e:
            logger.error(f"❌ Orphaned chunk analysis failed: {e}")
            return 0
    
    async def calculate_storage_impact(self, documents: List[DocumentAnalysis]) -> float:
        """Calculate storage impact of UUID-affected data."""
        logger.info("💾 Calculating storage impact...")
        
        try:
            # Get storage information for documents
            total_bytes = 0
            uuidv4_bytes = 0
            
            for doc in documents:
                # Get document size
                size_result = await self.conn.fetchrow("""
                    SELECT bytes_len
                    FROM upload_pipeline.documents
                    WHERE document_id = $1
                """, doc.document_id)
                
                if size_result:
                    doc_bytes = size_result['bytes_len'] or 0
                    total_bytes += doc_bytes
                    
                    if doc.uuid_version == 4:
                        uuidv4_bytes += doc_bytes
            
            # Convert to MB
            total_mb = total_bytes / (1024 * 1024)
            uuidv4_mb = uuidv4_bytes / (1024 * 1024)
            
            logger.info(f"💾 Storage impact: {uuidv4_mb:.2f} MB of {total_mb:.2f} MB total")
            return uuidv4_mb
            
        except Exception as e:
            logger.error(f"❌ Storage impact calculation failed: {e}")
            return 0.0
    
    async def analyze_user_impact(self, documents: List[DocumentAnalysis]) -> Dict[str, Any]:
        """Analyze user impact distribution."""
        logger.info("👥 Analyzing user impact...")
        
        user_stats = {}
        
        for doc in documents:
            user_id = str(doc.user_id)  # Convert UUID to string for JSON serialization
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'total_documents': 0,
                    'uuidv4_documents': 0,
                    'uuidv5_documents': 0,
                    'orphaned_documents': 0,
                    'high_priority_documents': 0,
                    'total_chunks': 0,
                    'first_upload': None,
                    'last_upload': None
                }
            
            stats = user_stats[user_id]
            stats['total_documents'] += 1
            
            if doc.uuid_version == 4:
                stats['uuidv4_documents'] += 1
            elif doc.uuid_version == 5:
                stats['uuidv5_documents'] += 1
            
            if doc.is_orphaned:
                stats['orphaned_documents'] += 1
            
            if doc.priority_score > 0.7:
                stats['high_priority_documents'] += 1
            
            stats['total_chunks'] += doc.chunk_count
            
            if not stats['first_upload'] or doc.created_at < stats['first_upload']:
                stats['first_upload'] = doc.created_at
            
            if not stats['last_upload'] or doc.created_at > stats['last_upload']:
                stats['last_upload'] = doc.created_at
        
        logger.info(f"👥 User impact analysis complete: {len(user_stats)} users affected")
        return user_stats
    
    async def analyze_pipeline_failures(self, documents: List[DocumentAnalysis]) -> Dict[str, Any]:
        """Analyze pipeline failure patterns."""
        logger.info("🔧 Analyzing pipeline failure patterns...")
        
        failures = {
            'uuid_mismatch_documents': 0,
            'uploaded_never_processed': 0,
            'processed_but_no_chunks': 0,
            'chunks_but_not_embedded': 0,
            'recent_failures': 0
        }
        
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        
        for doc in documents:
            # UUID mismatch (v4 documents that should be v5)
            if doc.uuid_version == 4:
                failures['uuid_mismatch_documents'] += 1
                
                try:
                    # Handle timezone-aware datetimes
                    created_at = doc.created_at
                    if created_at.tzinfo is not None:
                        cutoff = recent_cutoff.replace(tzinfo=created_at.tzinfo)
                    else:
                        cutoff = recent_cutoff
                    
                    if created_at > cutoff:
                        failures['recent_failures'] += 1
                except Exception:
                    # If datetime comparison fails, skip recent check
                    pass
            
            # Uploaded but never processed
            if not doc.processing_status or doc.processing_status == 'queued':
                failures['uploaded_never_processed'] += 1
            
            # Processed but no chunks
            if doc.processing_status in ['parsed', 'chunking'] and not doc.has_chunks:
                failures['processed_but_no_chunks'] += 1
            
            # Chunks but not embedded
            if doc.has_chunks and doc.processing_status not in ['embedded', 'embedding']:
                failures['chunks_but_not_embedded'] += 1
        
        logger.info(f"🔧 Pipeline failure analysis complete")
        return failures
    
    def generate_recommendations(self, impact: MigrationImpact, user_impact: Dict[str, Any], 
                               failures: Dict[str, Any]) -> List[str]:
        """Generate migration recommendations based on analysis."""
        recommendations = []
        
        # Migration approach recommendation
        if impact.uuidv4_documents > impact.total_documents * 0.8:
            recommendations.append("FULL MIGRATION: >80% of documents use random UUIDs - recommend complete migration")
        elif impact.uuidv4_documents > impact.total_documents * 0.5:
            recommendations.append("HYBRID MIGRATION: ~50% of documents use random UUIDs - recommend selective migration")
        else:
            recommendations.append("MINIMAL MIGRATION: <50% of documents use random UUIDs - recommend forward-only fix")
        
        # Priority users
        high_impact_users = [uid for uid, stats in user_impact.items() 
                           if stats['high_priority_documents'] > 0 or stats['uuidv4_documents'] > 5]
        if high_impact_users:
            recommendations.append(f"PRIORITY USERS: {len(high_impact_users)} users with high-impact documents need immediate attention")
        
        # Storage considerations
        if impact.storage_impact_mb > 1000:  # > 1GB
            recommendations.append("STORAGE IMPACT: Large storage footprint - consider staged migration to avoid performance impact")
        elif impact.storage_impact_mb > 100:  # > 100MB
            recommendations.append("STORAGE IMPACT: Moderate storage footprint - monitor performance during migration")
        else:
            recommendations.append("STORAGE IMPACT: Low storage footprint - migration should be fast")
        
        # Pipeline failure urgency
        if failures['recent_failures'] > 0:
            recommendations.append(f"URGENT: {failures['recent_failures']} recent uploads affected by UUID mismatch - immediate fix needed")
        
        if failures['uploaded_never_processed'] > 0:
            recommendations.append(f"CRITICAL: {failures['uploaded_never_processed']} documents uploaded but never processed - user experience severely impacted")
        
        return recommendations
    
    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete Phase B.1.1 data analysis."""
        logger.info("🚀 Starting Phase B.1.1 comprehensive data analysis...")
        
        if not await self.connect_database():
            return {"error": "Database connection failed"}
        
        try:
            # Step 1: Analyze all documents
            documents = await self.analyze_documents()
            
            # Step 2: Analyze orphaned chunks
            orphaned_chunks = await self.analyze_orphaned_chunks()
            
            # Step 3: Calculate storage impact
            storage_impact_mb = await self.calculate_storage_impact(documents)
            
            # Step 4: Analyze user impact
            user_impact = await self.analyze_user_impact(documents)
            
            # Step 5: Analyze pipeline failures
            pipeline_failures = await self.analyze_pipeline_failures(documents)
            
            # Step 6: Calculate migration impact
            uuidv4_docs = [d for d in documents if d.uuid_version == 4]
            uuidv5_docs = [d for d in documents if d.uuid_version == 5]
            high_priority_docs = [d for d in documents if d.priority_score > 0.7]
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_docs = []
            for d in documents:
                try:
                    created_at = d.created_at
                    if created_at.tzinfo is not None:
                        cutoff = recent_cutoff.replace(tzinfo=created_at.tzinfo)
                    else:
                        cutoff = recent_cutoff
                    
                    if created_at > cutoff:
                        recent_docs.append(d)
                except Exception:
                    # If datetime comparison fails, skip this document
                    pass
            
            migration_impact = MigrationImpact(
                total_documents=len(documents),
                uuidv4_documents=len(uuidv4_docs),
                uuidv5_documents=len(uuidv5_docs),
                orphaned_chunks=orphaned_chunks,
                affected_users=len(user_impact),
                storage_impact_mb=storage_impact_mb,
                high_priority_documents=len(high_priority_docs),
                recent_documents=len(recent_docs),
                failed_pipeline_documents=pipeline_failures['uploaded_never_processed']
            )
            
            # Step 7: Generate recommendations
            recommendations = self.generate_recommendations(migration_impact, user_impact, pipeline_failures)
            
            # Compile results
            self.analysis_results.update({
                "documents": [
                    {
                        "document_id": doc.document_id,
                        "user_id": doc.user_id,
                        "filename": doc.filename,
                        "created_at": doc.created_at.isoformat(),
                        "processing_status": doc.processing_status,
                        "uuid_version": doc.uuid_version,
                        "is_deterministic": doc.is_deterministic,
                        "has_chunks": doc.has_chunks,
                        "chunk_count": doc.chunk_count,
                        "is_orphaned": doc.is_orphaned,
                        "priority_score": doc.priority_score
                    }
                    for doc in documents
                ],
                "migration_impact": {
                    "total_documents": migration_impact.total_documents,
                    "uuidv4_documents": migration_impact.uuidv4_documents,
                    "uuidv5_documents": migration_impact.uuidv5_documents,
                    "orphaned_chunks": migration_impact.orphaned_chunks,
                    "affected_users": migration_impact.affected_users,
                    "storage_impact_mb": migration_impact.storage_impact_mb,
                    "high_priority_documents": migration_impact.high_priority_documents,
                    "recent_documents": migration_impact.recent_documents,
                    "failed_pipeline_documents": migration_impact.failed_pipeline_documents
                },
                "user_impact": user_impact,
                "pipeline_failures": pipeline_failures,
                "recommendations": recommendations
            })
            
            logger.info("✅ Phase B.1.1 analysis complete!")
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
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
    
    # Run analysis
    analyzer = PhaseBDataAnalyzer(database_url)
    results = await analyzer.run_comprehensive_analysis()
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"phase_b_data_analysis_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Analysis results saved to: {output_file}")
    
    # Print summary
    if "error" not in results:
        impact = results["migration_impact"]
        print(f"\n📊 PHASE B.1.1 ANALYSIS SUMMARY")
        print(f"Total Documents: {impact['total_documents']}")
        
        if impact['total_documents'] > 0:
            print(f"Random UUID Documents: {impact['uuidv4_documents']} ({impact['uuidv4_documents']/impact['total_documents']*100:.1f}%)")
            print(f"Deterministic UUID Documents: {impact['uuidv5_documents']} ({impact['uuidv5_documents']/impact['total_documents']*100:.1f}%)")
        else:
            print(f"Random UUID Documents: {impact['uuidv4_documents']} (0.0%)")
            print(f"Deterministic UUID Documents: {impact['uuidv5_documents']} (0.0%)")
        
        print(f"Affected Users: {impact['affected_users']}")
        print(f"Storage Impact: {impact['storage_impact_mb']:.2f} MB")
        print(f"High Priority Documents: {impact['high_priority_documents']}")
        print(f"Recent Documents: {impact['recent_documents']}")
        print(f"Failed Pipeline Documents: {impact['failed_pipeline_documents']}")
        print(f"Orphaned Chunks: {impact['orphaned_chunks']}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(main())
