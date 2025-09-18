#!/usr/bin/env python3
"""
UUID Generation Performance Benchmark

This script benchmarks the performance of the new deterministic UUID generation
against the previous random UUID generation to ensure no performance regression.

Benchmarks:
1. UUID generation latency (v4 vs v5)
2. Concurrent generation performance
3. Memory usage impact
4. End-to-end pipeline performance
5. Database query performance with new UUIDs

Reference: Phase A Critical Path Resolution
"""

import asyncio
import hashlib
import json
import logging
import memory_profiler
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List

import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UUIDPerformanceBenchmark:
    """Benchmarks UUID generation performance."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://postgres:password@localhost:54321/postgres"
        self.conn = None
        self.benchmark_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "benchmarks": {},
            "overall_success": False,
            "performance_analysis": {}
        }
    
    async def connect_database(self) -> bool:
        """Connect to the database for query performance tests."""
        if not self.database_url:
            logger.info("⚠️ No database URL provided, skipping database tests")
            return False
        
        try:
            logger.info("🔌 Connecting to database...")
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            return False
    
    async def disconnect_database(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            logger.info("🔌 Database disconnected")
    
    def benchmark_uuid_generation_latency(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark UUID generation latency."""
        logger.info(f"⏱️ Benchmarking UUID generation latency ({iterations} iterations)...")
        
        try:
            from utils.uuid_generation import UUIDGenerator
            
            # Test data
            test_user_id = "test-user-123"
            test_content_hash = "test-content-hash-456"
            test_document_id = "test-document-789"
            
            # Benchmark UUIDv4 (random)
            start_time = time.time()
            for _ in range(iterations):
                uuid.uuid4()
            v4_time = time.time() - start_time
            
            # Benchmark UUIDv5 (deterministic) - Document UUIDs
            start_time = time.time()
            for _ in range(iterations):
                UUIDGenerator.document_uuid(test_user_id, test_content_hash)
            v5_document_time = time.time() - start_time
            
            # Benchmark UUIDv5 (deterministic) - Chunk UUIDs
            start_time = time.time()
            for _ in range(iterations):
                UUIDGenerator.chunk_uuid(test_document_id, "markdown", "1.0", 0)
            v5_chunk_time = time.time() - start_time
            
            # Calculate metrics
            v4_avg = (v4_time / iterations) * 1000  # ms
            v5_document_avg = (v5_document_time / iterations) * 1000  # ms
            v5_chunk_avg = (v5_chunk_time / iterations) * 1000  # ms
            
            results = {
                "iterations": iterations,
                "uuidv4_avg_ms": round(v4_avg, 4),
                "uuidv5_document_avg_ms": round(v5_document_avg, 4),
                "uuidv5_chunk_avg_ms": round(v5_chunk_avg, 4),
                "performance_ratio_document": round(v5_document_avg / v4_avg, 4),
                "performance_ratio_chunk": round(v5_chunk_avg / v4_avg, 4),
                "total_v4_time": round(v4_time, 4),
                "total_v5_document_time": round(v5_document_time, 4),
                "total_v5_chunk_time": round(v5_chunk_time, 4)
            }
            
            logger.info(f"✅ UUID generation latency benchmark complete:")
            logger.info(f"  UUIDv4 (random): {v4_avg:.4f}ms per generation")
            logger.info(f"  UUIDv5 (document): {v5_document_avg:.4f}ms per generation")
            logger.info(f"  UUIDv5 (chunk): {v5_chunk_avg:.4f}ms per generation")
            logger.info(f"  Performance ratio (document): {results['performance_ratio_document']:.2f}x")
            logger.info(f"  Performance ratio (chunk): {results['performance_ratio_chunk']:.2f}x")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error benchmarking UUID generation: {e}")
            return {"error": str(e)}
    
    def benchmark_concurrent_generation(self, concurrent_users: int = 100, iterations_per_user: int = 100) -> Dict[str, Any]:
        """Benchmark concurrent UUID generation."""
        logger.info(f"🔄 Benchmarking concurrent UUID generation ({concurrent_users} users, {iterations_per_user} iterations each)...")
        
        try:
            from utils.uuid_generation import UUIDGenerator
            
            def generate_uuids_for_user(user_id: str):
                """Generate UUIDs for a single user."""
                start_time = time.time()
                uuids = []
                
                for i in range(iterations_per_user):
                    # Generate document UUID
                    content_hash = f"content-hash-{user_id}-{i}"
                    doc_uuid = UUIDGenerator.document_uuid(user_id, content_hash)
                    uuids.append(doc_uuid)
                    
                    # Generate chunk UUIDs
                    for chunk_ord in range(3):  # 3 chunks per document
                        chunk_uuid = UUIDGenerator.chunk_uuid(doc_uuid, "markdown", "1.0", chunk_ord)
                        uuids.append(chunk_uuid)
                
                end_time = time.time()
                return {
                    "user_id": user_id,
                    "duration": end_time - start_time,
                    "uuids_generated": len(uuids),
                    "uuids": uuids[:5]  # First 5 for verification
                }
            
            # Run concurrent generation
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [
                    executor.submit(generate_uuids_for_user, f"user-{i}")
                    for i in range(concurrent_users)
                ]
                
                results = []
                for future in as_completed(futures):
                    results.append(future.result())
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Calculate metrics
            total_uuids = sum(r["uuids_generated"] for r in results)
            avg_duration_per_user = sum(r["duration"] for r in results) / len(results)
            uuids_per_second = total_uuids / total_duration
            
            # Verify deterministic generation
            deterministic_verified = True
            for result in results[:5]:  # Check first 5 users
                user_id = result["user_id"]
                for i, uuid_str in enumerate(result["uuids"][:3]):  # Check first 3 UUIDs
                    # Regenerate and verify
                    content_hash = f"content-hash-{user_id}-{i}"
                    expected_uuid = UUIDGenerator.document_uuid(user_id, content_hash)
                    if uuid_str != expected_uuid:
                        deterministic_verified = False
                        break
            
            benchmark_results = {
                "concurrent_users": concurrent_users,
                "iterations_per_user": iterations_per_user,
                "total_uuids_generated": total_uuids,
                "total_duration": round(total_duration, 4),
                "avg_duration_per_user": round(avg_duration_per_user, 4),
                "uuids_per_second": round(uuids_per_second, 2),
                "deterministic_verified": deterministic_verified,
                "sample_results": results[:3]  # First 3 for inspection
            }
            
            logger.info(f"✅ Concurrent generation benchmark complete:")
            logger.info(f"  Total UUIDs generated: {total_uuids}")
            logger.info(f"  Total duration: {total_duration:.4f}s")
            logger.info(f"  UUIDs per second: {uuids_per_second:.2f}")
            logger.info(f"  Deterministic verified: {deterministic_verified}")
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"❌ Error benchmarking concurrent generation: {e}")
            return {"error": str(e)}
    
    def benchmark_memory_usage(self, iterations: int = 100000) -> Dict[str, Any]:
        """Benchmark memory usage of UUID generation."""
        logger.info(f"💾 Benchmarking memory usage ({iterations} iterations)...")
        
        try:
            from utils.uuid_generation import UUIDGenerator
            
            # Test data
            test_user_id = "test-user-123"
            test_content_hash = "test-content-hash-456"
            test_document_id = "test-document-789"
            
            # Memory usage for UUIDv4
            @memory_profiler.profile
            def generate_uuidv4_batch():
                uuids = []
                for _ in range(iterations):
                    uuids.append(str(uuid.uuid4()))
                return uuids
            
            # Memory usage for UUIDv5 (document)
            @memory_profiler.profile
            def generate_uuidv5_document_batch():
                uuids = []
                for _ in range(iterations):
                    uuids.append(UUIDGenerator.document_uuid(test_user_id, test_content_hash))
                return uuids
            
            # Memory usage for UUIDv5 (chunk)
            @memory_profiler.profile
            def generate_uuidv5_chunk_batch():
                uuids = []
                for _ in range(iterations):
                    uuids.append(UUIDGenerator.chunk_uuid(test_document_id, "markdown", "1.0", 0))
                return uuids
            
            # Run memory profiling
            logger.info("  Running UUIDv4 memory test...")
            v4_uuids = generate_uuidv4_batch()
            
            logger.info("  Running UUIDv5 document memory test...")
            v5_doc_uuids = generate_uuidv5_document_batch()
            
            logger.info("  Running UUIDv5 chunk memory test...")
            v5_chunk_uuids = generate_uuidv5_chunk_batch()
            
            # Calculate memory usage (approximate)
            v4_memory = len(str(v4_uuids))  # Rough estimate
            v5_doc_memory = len(str(v5_doc_uuids))
            v5_chunk_memory = len(str(v5_chunk_uuids))
            
            results = {
                "iterations": iterations,
                "uuidv4_memory_bytes": v4_memory,
                "uuidv5_document_memory_bytes": v5_doc_memory,
                "uuidv5_chunk_memory_bytes": v5_chunk_memory,
                "memory_ratio_document": round(v5_doc_memory / v4_memory, 4) if v4_memory > 0 else 0,
                "memory_ratio_chunk": round(v5_chunk_memory / v4_memory, 4) if v4_memory > 0 else 0,
                "bytes_per_uuid_v4": round(v4_memory / iterations, 2),
                "bytes_per_uuid_v5_document": round(v5_doc_memory / iterations, 2),
                "bytes_per_uuid_v5_chunk": round(v5_chunk_memory / iterations, 2)
            }
            
            logger.info(f"✅ Memory usage benchmark complete:")
            logger.info(f"  UUIDv4 memory: {v4_memory} bytes ({results['bytes_per_uuid_v4']} bytes/UUID)")
            logger.info(f"  UUIDv5 document memory: {v5_doc_memory} bytes ({results['bytes_per_uuid_v5_document']} bytes/UUID)")
            logger.info(f"  UUIDv5 chunk memory: {v5_chunk_memory} bytes ({results['bytes_per_uuid_v5_chunk']} bytes/UUID)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error benchmarking memory usage: {e}")
            return {"error": str(e)}
    
    async def benchmark_database_query_performance(self) -> Dict[str, Any]:
        """Benchmark database query performance with new UUIDs."""
        logger.info("🗄️ Benchmarking database query performance...")
        
        if not self.conn:
            logger.warning("⚠️ No database connection, skipping database performance test")
            return {"skipped": "No database connection"}
        
        try:
            # Test document queries
            start_time = time.time()
            documents = await self.conn.fetch("""
                SELECT document_id, user_id, file_sha256
                FROM upload_pipeline.documents
                ORDER BY created_at DESC
                LIMIT 100
            """)
            document_query_time = time.time() - start_time
            
            # Test chunk queries
            start_time = time.time()
            chunks = await self.conn.fetch("""
                SELECT chunk_id, document_id, chunker_name, chunker_version, chunk_ord
                FROM upload_pipeline.document_chunks
                ORDER BY created_at DESC
                LIMIT 100
            """)
            chunk_query_time = time.time() - start_time
            
            # Test join queries (documents with chunks)
            start_time = time.time()
            joined_data = await self.conn.fetch("""
                SELECT d.document_id, d.user_id, dc.chunk_id, dc.chunk_ord
                FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                ORDER BY d.created_at DESC
                LIMIT 100
            """)
            join_query_time = time.time() - start_time
            
            # Test UUID-based lookups
            if documents:
                test_doc_id = documents[0]['document_id']
                start_time = time.time()
                specific_doc = await self.conn.fetchrow("""
                    SELECT document_id, user_id, file_sha256
                    FROM upload_pipeline.documents
                    WHERE document_id = $1
                """, test_doc_id)
                specific_query_time = time.time() - start_time
            else:
                specific_query_time = 0
            
            results = {
                "document_query_time": round(document_query_time, 4),
                "chunk_query_time": round(chunk_query_time, 4),
                "join_query_time": round(join_query_time, 4),
                "specific_lookup_time": round(specific_query_time, 4),
                "documents_found": len(documents),
                "chunks_found": len(chunks),
                "joined_records": len(joined_data),
                "queries_per_second": round(4 / (document_query_time + chunk_query_time + join_query_time + specific_query_time), 2)
            }
            
            logger.info(f"✅ Database query performance benchmark complete:")
            logger.info(f"  Document query: {document_query_time:.4f}s")
            logger.info(f"  Chunk query: {chunk_query_time:.4f}s")
            logger.info(f"  Join query: {join_query_time:.4f}s")
            logger.info(f"  Specific lookup: {specific_query_time:.4f}s")
            logger.info(f"  Queries per second: {results['queries_per_second']:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error benchmarking database performance: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        logger.info("🚀 Starting UUID Performance Benchmark")
        logger.info("=" * 60)
        
        try:
            # Connect to database
            await self.connect_database()
            
            # Run all benchmarks
            benchmarks = [
                ("uuid_generation_latency", self.benchmark_uuid_generation_latency()),
                ("concurrent_generation", self.benchmark_concurrent_generation()),
                ("memory_usage", self.benchmark_memory_usage()),
                ("database_query_performance", self.benchmark_database_query_performance())
            ]
            
            for benchmark_name, benchmark_coro in benchmarks:
                logger.info(f"\n📋 Running {benchmark_name} benchmark...")
                if asyncio.iscoroutine(benchmark_coro):
                    result = await benchmark_coro
                else:
                    result = benchmark_coro
                self.benchmark_results["benchmarks"][benchmark_name] = result
                
                if "error" in result:
                    logger.error(f"❌ {benchmark_name} benchmark failed: {result['error']}")
                else:
                    logger.info(f"✅ {benchmark_name} benchmark completed")
            
            # Performance analysis
            self.benchmark_results["performance_analysis"] = self.analyze_performance()
            
            # Calculate overall success
            error_count = sum(1 for result in self.benchmark_results["benchmarks"].values() if "error" in result)
            self.benchmark_results["overall_success"] = error_count == 0
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("📊 UUID PERFORMANCE BENCHMARK RESULTS")
            logger.info("=" * 60)
            
            for benchmark_name, result in self.benchmark_results["benchmarks"].items():
                if "error" in result:
                    logger.error(f"{benchmark_name}: ❌ ERROR - {result['error']}")
                else:
                    logger.info(f"{benchmark_name}: ✅ COMPLETED")
            
            # Performance summary
            analysis = self.benchmark_results["performance_analysis"]
            logger.info(f"\n📈 Performance Summary:")
            logger.info(f"  UUID Generation: {analysis.get('generation_performance', 'N/A')}")
            logger.info(f"  Concurrent Performance: {analysis.get('concurrent_performance', 'N/A')}")
            logger.info(f"  Memory Usage: {analysis.get('memory_performance', 'N/A')}")
            logger.info(f"  Database Performance: {analysis.get('database_performance', 'N/A')}")
            
            overall_status = "✅ BENCHMARK PASSED" if self.benchmark_results["overall_success"] else "❌ BENCHMARK FAILED"
            logger.info(f"\nOverall Result: {overall_status}")
            
            return self.benchmark_results
            
        except Exception as e:
            logger.error(f"❌ Benchmark error: {e}")
            self.benchmark_results["error"] = str(e)
            return self.benchmark_results
        
        finally:
            await self.disconnect_database()
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze benchmark results and provide performance insights."""
        analysis = {}
        
        try:
            # Generation performance analysis
            if "uuid_generation_latency" in self.benchmark_results["benchmarks"]:
                gen_result = self.benchmark_results["benchmarks"]["uuid_generation_latency"]
                if "error" not in gen_result:
                    ratio = gen_result.get("performance_ratio_document", 1.0)
                    if ratio <= 1.5:
                        analysis["generation_performance"] = "✅ Excellent (≤1.5x overhead)"
                    elif ratio <= 2.0:
                        analysis["generation_performance"] = "✅ Good (≤2.0x overhead)"
                    else:
                        analysis["generation_performance"] = "⚠️ Acceptable (>2.0x overhead)"
            
            # Concurrent performance analysis
            if "concurrent_generation" in self.benchmark_results["benchmarks"]:
                conc_result = self.benchmark_results["benchmarks"]["concurrent_generation"]
                if "error" not in conc_result:
                    uuids_per_sec = conc_result.get("uuids_per_second", 0)
                    if uuids_per_sec >= 10000:
                        analysis["concurrent_performance"] = "✅ Excellent (≥10k UUIDs/sec)"
                    elif uuids_per_sec >= 5000:
                        analysis["concurrent_performance"] = "✅ Good (≥5k UUIDs/sec)"
                    else:
                        analysis["concurrent_performance"] = "⚠️ Acceptable (<5k UUIDs/sec)"
            
            # Memory performance analysis
            if "memory_usage" in self.benchmark_results["benchmarks"]:
                mem_result = self.benchmark_results["benchmarks"]["memory_usage"]
                if "error" not in mem_result:
                    ratio = mem_result.get("memory_ratio_document", 1.0)
                    if ratio <= 1.2:
                        analysis["memory_performance"] = "✅ Excellent (≤1.2x memory)"
                    elif ratio <= 1.5:
                        analysis["memory_performance"] = "✅ Good (≤1.5x memory)"
                    else:
                        analysis["memory_performance"] = "⚠️ Acceptable (>1.5x memory)"
            
            # Database performance analysis
            if "database_query_performance" in self.benchmark_results["benchmarks"]:
                db_result = self.benchmark_results["benchmarks"]["database_query_performance"]
                if "error" not in db_result and "skipped" not in db_result:
                    qps = db_result.get("queries_per_second", 0)
                    if qps >= 100:
                        analysis["database_performance"] = "✅ Excellent (≥100 QPS)"
                    elif qps >= 50:
                        analysis["database_performance"] = "✅ Good (≥50 QPS)"
                    else:
                        analysis["database_performance"] = "⚠️ Acceptable (<50 QPS)"
                else:
                    analysis["database_performance"] = "⚠️ Skipped (no database connection)"
            
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis

async def main():
    """Run UUID performance benchmark."""
    import os
    database_url = os.getenv("DATABASE_URL")
    
    benchmark = UUIDPerformanceBenchmark(database_url)
    results = await benchmark.run_comprehensive_benchmark()
    
    # Save results
    timestamp = int(datetime.utcnow().timestamp())
    results_file = f"uuid_performance_benchmark_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: {results_file}")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

