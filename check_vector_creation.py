#!/usr/bin/env python3
"""
Vector Creation Validation Script
Check if vectors were actually created for uploaded documents in the pipeline.
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class VectorCreationValidator:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")
    
    async def check_vector_creation(self) -> Dict[str, Any]:
        """Check vector creation for recent documents."""
        print("🔍 Checking Vector Creation for Recent Documents")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "validation_type": "vector_creation_check",
            "recent_documents": [],
            "vector_status": {},
            "summary": {}
        }
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Check recent documents (last 24 hours)
            recent_docs_query = """
                SELECT 
                    document_id,
                    title,
                    document_type,
                    status,
                    extraction_method,
                    created_at,
                    updated_at,
                    content_hash,
                    vectors_generated,
                    vector_count
                FROM regulatory_documents 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 20
            """
            
            print("\n📄 Recent Documents (last 24 hours):")
            recent_docs = await conn.fetch(recent_docs_query)
            
            if not recent_docs:
                print("   No recent documents found")
                results["recent_documents"] = []
            else:
                for doc in recent_docs:
                    doc_info = {
                        "document_id": doc['document_id'],
                        "title": doc['title'],
                        "type": doc['document_type'],
                        "status": doc['status'],
                        "extraction_method": doc['extraction_method'],
                        "created_at": doc['created_at'].isoformat(),
                        "updated_at": doc['updated_at'].isoformat() if doc['updated_at'] else None,
                        "content_hash": doc['content_hash'],
                        "vectors_generated": doc['vectors_generated'],
                        "vector_count": doc['vector_count']
                    }
                    results["recent_documents"].append(doc_info)
                    
                    print(f"   📋 Doc ID: {doc['document_id']}")
                    print(f"      Title: {doc['title']}")
                    print(f"      Status: {doc['status']}")
                    print(f"      Method: {doc['extraction_method']}")
                    print(f"      Vectors Generated: {doc['vectors_generated']}")
                    print(f"      Vector Count: {doc['vector_count']}")
                    print(f"      Created: {doc['created_at']}")
                    print()
            
            # Check vector creation for each document
            print("\n🧮 Checking Vector Creation:")
            
            for doc in recent_docs:
                doc_id = doc['document_id']
                
                # Check if vectors exist for this document
                vector_query = """
                    SELECT 
                        COUNT(*) as vector_count,
                        MIN(created_at) as first_vector_created,
                        MAX(created_at) as last_vector_created
                    FROM document_vectors 
                    WHERE regulatory_document_id = $1
                """
                
                vector_result = await conn.fetchrow(vector_query, doc_id)
                vector_count = vector_result['vector_count']
                
                # Get sample vector to check dimensions
                sample_vector_query = """
                    SELECT 
                        id,
                        chunk_index,
                        content_embedding,
                        encrypted_chunk_text
                    FROM document_vectors 
                    WHERE regulatory_document_id = $1 
                    ORDER BY chunk_index 
                    LIMIT 1
                """
                
                sample_vector = await conn.fetchrow(sample_vector_query, doc_id)
                
                vector_status = {
                    "document_id": doc_id,
                    "document_title": doc['title'],
                    "vector_count": vector_count,
                    "has_vectors": vector_count > 0,
                    "first_vector_created": vector_result['first_vector_created'].isoformat() if vector_result['first_vector_created'] else None,
                    "last_vector_created": vector_result['last_vector_created'].isoformat() if vector_result['last_vector_created'] else None
                }
                
                if sample_vector:
                    # Check embedding dimensions
                    embedding = sample_vector['content_embedding']
                    vector_status.update({
                        "sample_vector_id": sample_vector['id'],
                        "embedding_dimensions": len(embedding) if embedding else 0,
                        "encrypted_content": sample_vector['encrypted_chunk_text'][:100] if sample_vector['encrypted_chunk_text'] else None,
                        "chunk_index": sample_vector['chunk_index']
                    })
                
                results["vector_status"][doc_id] = vector_status
                
                print(f"   📋 Document: {doc['title']}")
                print(f"      ID: {doc_id}")
                print(f"      Vectors: {vector_count}")
                
                if vector_count > 0:
                    print(f"      ✅ First Vector: {vector_result['first_vector_created']}")
                    print(f"      📅 Last Vector: {vector_result['last_vector_created']}")
                    
                    if sample_vector:
                        embedding_dims = len(sample_vector['content_embedding']) if sample_vector['content_embedding'] else 0
                        print(f"      🧮 Embedding Dims: {embedding_dims}")
                        print(f"      📝 Content: {'[Encrypted]' if sample_vector['encrypted_chunk_text'] else 'None'}")
                else:
                    print(f"      ❌ No vectors found")
                print()
            
            # Check for dimension mismatches
            print("\n🔧 Checking for Dimension Issues:")
            
            dimension_query = """
                SELECT 
                    regulatory_document_id,
                    array_length(content_embedding, 1) as embedding_dimension,
                    COUNT(*) as count_with_dimension
                FROM document_vectors 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY regulatory_document_id, array_length(content_embedding, 1)
                ORDER BY regulatory_document_id, embedding_dimension
            """
            
            dimension_results = await conn.fetch(dimension_query)
            
            dimension_summary = {}
            for result in dimension_results:
                doc_id = result['regulatory_document_id']
                dimension = result['embedding_dimension']
                count = result['count_with_dimension']
                
                if doc_id not in dimension_summary:
                    dimension_summary[doc_id] = {}
                
                dimension_summary[doc_id][dimension] = count
            
            results["dimension_analysis"] = dimension_summary
            
            for doc_id, dimensions in dimension_summary.items():
                print(f"   📋 Document {doc_id}:")
                for dim, count in dimensions.items():
                    status = "✅" if dim == 1536 else "⚠️" if dim == 384 else "❌"
                    print(f"      {status} {count} vectors with {dim} dimensions")
            
            # Check processing pipeline status
            print("\n⚙️ Checking Processing Pipeline Status:")
            
            pipeline_status_query = """
                SELECT 
                    rd.document_id,
                    rd.title,
                    rd.status,
                    rd.extraction_method,
                    rd.created_at,
                    CASE 
                        WHEN dv.regulatory_document_id IS NOT NULL THEN 'vectors_created'
                        ELSE 'no_vectors'
                    END as vector_status,
                    COUNT(dv.id) as vector_count
                FROM regulatory_documents rd
                LEFT JOIN document_vectors dv ON rd.document_id = dv.regulatory_document_id
                WHERE rd.created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY rd.document_id, rd.title, rd.status, rd.extraction_method, rd.created_at, dv.regulatory_document_id
                ORDER BY rd.created_at DESC
            """
            
            pipeline_results = await conn.fetch(pipeline_status_query)
            
            pipeline_summary = {
                "total_documents": len(pipeline_results),
                "documents_with_vectors": 0,
                "documents_without_vectors": 0,
                "processing_methods": {},
                "status_breakdown": {}
            }
            
            for result in pipeline_results:
                # Count documents with/without vectors
                if result['vector_count'] > 0:
                    pipeline_summary["documents_with_vectors"] += 1
                else:
                    pipeline_summary["documents_without_vectors"] += 1
                
                # Track processing methods
                method = result['extraction_method'] or 'unknown'
                if method not in pipeline_summary["processing_methods"]:
                    pipeline_summary["processing_methods"][method] = {"total": 0, "with_vectors": 0}
                
                pipeline_summary["processing_methods"][method]["total"] += 1
                if result['vector_count'] > 0:
                    pipeline_summary["processing_methods"][method]["with_vectors"] += 1
                
                # Track status breakdown
                status = result['status'] or 'unknown'
                if status not in pipeline_summary["status_breakdown"]:
                    pipeline_summary["status_breakdown"][status] = {"total": 0, "with_vectors": 0}
                
                pipeline_summary["status_breakdown"][status]["total"] += 1
                if result['vector_count'] > 0:
                    pipeline_summary["status_breakdown"][status]["with_vectors"] += 1
                
                print(f"   📋 {result['title']}")
                print(f"      Status: {result['status']}")
                print(f"      Method: {result['extraction_method']}")
                print(f"      Vectors: {result['vector_count']}")
                print(f"      Vector Status: {result['vector_status']}")
                print()
            
            results["pipeline_summary"] = pipeline_summary
            
            print(f"\n📊 Pipeline Summary:")
            print(f"   Total Documents: {pipeline_summary['total_documents']}")
            print(f"   With Vectors: {pipeline_summary['documents_with_vectors']}")
            print(f"   Without Vectors: {pipeline_summary['documents_without_vectors']}")
            
            if pipeline_summary['total_documents'] > 0:
                vector_rate = (pipeline_summary['documents_with_vectors'] / pipeline_summary['total_documents']) * 100
                print(f"   Vector Creation Rate: {vector_rate:.1f}%")
                results["vector_creation_rate"] = vector_rate
            
            # Generate summary
            results["summary"] = self._generate_vector_summary(results)
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _generate_vector_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of vector creation validation."""
        
        total_docs = len(results.get("recent_documents", []))
        docs_with_vectors = sum(1 for vs in results.get("vector_status", {}).values() if vs.get("has_vectors", False))
        
        pipeline_summary = results.get("pipeline_summary", {})
        
        summary = {
            "overall_status": "unknown",
            "total_recent_documents": total_docs,
            "documents_with_vectors": docs_with_vectors,
            "documents_without_vectors": total_docs - docs_with_vectors,
            "vector_creation_working": docs_with_vectors > 0,
            "vector_creation_rate": (docs_with_vectors / total_docs * 100) if total_docs > 0 else 0,
            "dimension_issues": [],
            "critical_findings": [],
            "recommendations": []
        }
        
        # Analyze dimension issues
        dimension_analysis = results.get("dimension_analysis", {})
        for doc_id, dimensions in dimension_analysis.items():
            for dim, count in dimensions.items():
                if dim != 1536:  # Expected dimension
                    summary["dimension_issues"].append({
                        "document_id": doc_id,
                        "unexpected_dimension": dim,
                        "vector_count": count
                    })
        
        # Determine overall status
        if summary["vector_creation_rate"] >= 90:
            summary["overall_status"] = "excellent"
        elif summary["vector_creation_rate"] >= 70:
            summary["overall_status"] = "good"
        elif summary["vector_creation_rate"] >= 50:
            summary["overall_status"] = "fair"
        elif summary["vector_creation_rate"] > 0:
            summary["overall_status"] = "poor"
        else:
            summary["overall_status"] = "failed"
        
        # Generate findings and recommendations
        if summary["vector_creation_rate"] == 0:
            summary["critical_findings"].append("No vectors created for any recent documents")
            summary["recommendations"].append("Vector creation pipeline is completely broken - investigate edge functions")
        elif summary["vector_creation_rate"] < 50:
            summary["critical_findings"].append(f"Low vector creation rate: {summary['vector_creation_rate']:.1f}%")
            summary["recommendations"].append("Investigate partial failures in vector processing pipeline")
        
        if summary["dimension_issues"]:
            summary["critical_findings"].append(f"Dimension mismatches found in {len(summary['dimension_issues'])} documents")
            summary["recommendations"].append("Fix embedding model configuration - ensure consistent use of text-embedding-3-small (1536 dims)")
        
        if not summary["dimension_issues"] and summary["vector_creation_rate"] > 80:
            summary["recommendations"].append("Vector creation pipeline is working well - ready for production")
        
        return summary

async def main():
    """Main function to run vector creation validation."""
    print("🧮 Vector Creation Validation")
    print("=" * 40)
    
    try:
        validator = VectorCreationValidator()
        results = await validator.check_vector_creation()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vector_creation_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Display summary
        summary = results.get("summary", {})
        print(f"\n📊 Final Summary:")
        print(f"   Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"   Vector Creation Rate: {summary.get('vector_creation_rate', 0):.1f}%")
        print(f"   Documents with Vectors: {summary.get('documents_with_vectors', 0)}")
        print(f"   Documents without Vectors: {summary.get('documents_without_vectors', 0)}")
        
        if summary.get("dimension_issues"):
            print(f"   ⚠️ Dimension Issues: {len(summary['dimension_issues'])}")
        
        if summary.get("critical_findings"):
            print(f"\n🚨 Critical Findings:")
            for finding in summary["critical_findings"]:
                print(f"   • {finding}")
        
        if summary.get("recommendations"):
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")
        
        return results
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main()) 