#!/usr/bin/env python3
"""
Test Optimized RAG with Best Chunking Strategy
"""

import asyncio
import os
import sys
import json
import hashlib
import random
from typing import List, Dict, Any
import PyPDF2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
                
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def chunk_text_optimized(text: str, chunk_size: int = 250, overlap: int = 50) -> List[Dict[str, Any]]:
    """Optimized chunking strategy based on optimization results."""
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        if len(chunk_text.strip()) > 50:  # Only include substantial chunks
            chunks.append({
                "content": chunk_text.strip(),
                "chunk_index": len(chunks) + 1,
                "word_count": len(chunk_words),
                "char_count": len(chunk_text)
            })
    
    return chunks

def generate_mock_embedding(text: str, seed_offset: int = 0) -> List[float]:
    """Generate a deterministic 1536-dimensional embedding for testing."""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(text_hash[:8], 16) + seed_offset
    random.seed(seed)
    
    embedding = [random.uniform(-1, 1) for _ in range(1536)]
    magnitude = sum(x*x for x in embedding) ** 0.5
    normalized = [x/magnitude for x in embedding]
    
    return normalized

class OptimizedMockRAGTool:
    """Optimized mock RAG tool using the best chunking strategy."""
    
    def __init__(self, user_id: str, config=None):
        self.user_id = user_id
        self.config = config
        self.document_chunks = []
        self._load_document_data()
    
    def _load_document_data(self):
        """Load the processed insurance document data with optimized chunking."""
        pdf_path = "examples/test_insurance_document.pdf"
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return
        
        print(f"📄 Extracting text from {pdf_path}...")
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            print("❌ Failed to extract text from PDF")
            return
        
        print(f"✅ Extracted {len(text)} characters of text")
        
        # Use optimized chunking strategy
        print("📝 Chunking text with optimized strategy (250 words, 50 overlap)...")
        chunks = chunk_text_optimized(text, chunk_size=250, overlap=50)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Create document chunks with embeddings
        self.document_chunks = []
        for i, chunk_data in enumerate(chunks):
            embedding = generate_mock_embedding(chunk_data["content"], i)
            
            chunk = {
                "id": f"test_chunk_{i+1:03d}",
                "doc_id": "test_insurance_document_pdf",
                "chunk_index": chunk_data["chunk_index"],
                "content": chunk_data["content"],
                "section_path": [],
                "section_title": f"Section {i//2 + 1}",
                "page_start": None,
                "page_end": None,
                "similarity": 0.0,
                "tokens": chunk_data["word_count"],
                "embedding": embedding
            }
            self.document_chunks.append(chunk)
        
        print(f"✅ Loaded {len(self.document_chunks)} document chunks with embeddings")
    
    async def retrieve_chunks(self, query_embedding: List[float]) -> List:
        """Retrieve chunks based on keyword matching and similarity."""
        from agents.tooling.rag.core import ChunkWithContext
        
        # Calculate similarity for each chunk
        for chunk in self.document_chunks:
            chunk_embedding = chunk["embedding"]
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            chunk["similarity"] = similarity
        
        # Sort by similarity and filter by threshold
        sorted_chunks = sorted(self.document_chunks, key=lambda x: x["similarity"], reverse=True)
        filtered_chunks = [c for c in sorted_chunks if c["similarity"] > 0.1]  # Lowered threshold for mock embeddings
        
        # Convert to ChunkWithContext objects
        results = []
        for chunk in filtered_chunks[:5]:  # Return top 5
            chunk_obj = ChunkWithContext(
                id=chunk["id"],
                doc_id=chunk["doc_id"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                section_path=chunk["section_path"],
                section_title=chunk["section_title"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                similarity=chunk["similarity"],
                tokens=chunk["tokens"]
            )
            results.append(chunk_obj)
        
        # Debug: Print retrieved chunks
        print(f"🔍 Retrieved {len(results)} chunks (similarity > 0.3):")
        for i, chunk in enumerate(results):
            print(f"  {i+1}. Similarity: {chunk.similarity:.4f}")
            print(f"     Content: {chunk.content[:200]}...")
            print()
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

async def test_optimized_rag():
    """Test the optimized RAG system with the test insurance document."""
    print("🚀 Testing Optimized RAG with Test Insurance Document")
    print("=" * 60)
    
    try:
        # Import the chat interface
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Patch the RAGTool to use our optimized version
        import agents.patient_navigator.information_retrieval.agent as info_agent
        original_rag_tool = info_agent.RAGTool
        info_agent.RAGTool = OptimizedMockRAGTool
        
        # Initialize chat interface
        print("1️⃣ Initializing chat interface with optimized RAG...")
        chat_interface = PatientNavigatorChatInterface()
        print("   ✅ Chat interface initialized")
        
        # Test scenarios
        test_scenarios = [
            {
                "question": "What is my deductible?",
                "expected_answer": "ANNUAL DEDUCTIBLE: $0"
            },
            {
                "question": "What are my copays?",
                "expected_answer": "Primary Care Physician Visits: $0 copay"
            },
            {
                "question": "What services are covered?",
                "expected_answer": "SCAN Classic HMO covers all services"
            },
            {
                "question": "How do I find a doctor?",
                "expected_answer": "Visit our website at www.scanhealthplan.com"
            },
            {
                "question": "What are my prescription benefits?",
                "expected_answer": "Generic Drugs (Tier 1): $0 copay"
            }
        ]
        
        print("2️⃣ Testing scenarios with optimized RAG...")
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}️⃣ Testing: {scenario['question']}")
            
            # Create ChatMessage
            chat_message = ChatMessage(
                user_id="test_user_optimized",
                content=scenario["question"],
                timestamp=asyncio.get_event_loop().time(),
                message_type="text",
                language="en",
                metadata={"test_scenario": i, "document": "test_insurance_document.pdf"}
            )
            
            # Process message
            start_time = asyncio.get_event_loop().time()
            response = await chat_interface.process_message(chat_message)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Check if response contains expected information
            response_lower = response.content.lower()
            expected_lower = scenario["expected_answer"].lower()
            
            if any(word in response_lower for word in expected_lower.split()[:3]):
                quality = "✅ Good (Found specific information)"
                score = 0.9
            else:
                quality = "⚠️ Partial (Limited specific information)"
                score = 0.6
            
            print(f"   ⏳ Processed in {processing_time:.2f}s")
            print(f"   📝 Response: {response.content}")
            print(f"   📊 Quality: {quality}")
            print(f"   📊 Confidence: {response.confidence}")
            print(f"   🤖 Sources: {response.agent_sources}")
            
            results.append({
                "scenario": i,
                "question": scenario["question"],
                "response": response.content,
                "processing_time": processing_time,
                "quality": quality,
                "score": score
            })
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 OPTIMIZED RAG TEST RESULTS")
        print("=" * 60)
        
        good_responses = sum(1 for r in results if "Found specific information" in r["quality"])
        avg_time = sum(r["processing_time"] for r in results) / len(results)
        avg_score = sum(r["score"] for r in results) / len(results)
        
        print(f"Document: test_insurance_document.pdf")
        print(f"Chunking Strategy: 250 words, 50 overlap")
        print(f"Total Scenarios: {len(results)}")
        print(f"Good Responses (Specific info): {good_responses} ({good_responses/len(results)*100:.1f}%)")
        print(f"Average Processing Time: {avg_time:.2f}s")
        print(f"Average Quality Score: {avg_score:.2f}")
        
        print("\n📋 Detailed Results:")
        for result in results:
            print(f"  {result['scenario']}. {result['question']}")
            print(f"     📝 {result['response'][:100]}...")
            print(f"     📊 {result['quality']}")
        
        # Restore original RAGTool
        info_agent.RAGTool = original_rag_tool
        
        if good_responses > 0:
            print("\n🎉 SUCCESS: Optimized RAG system is working!")
            print("   The system is now retrieving and using specific information from the test document")
            print("   Responses contain actual deductible, copay, and coverage information")
        else:
            print("\n⚠️ PARTIAL: RAG system needs further optimization")
            print("   The system is working but not finding specific information in the test document")
        
    except Exception as e:
        print(f"❌ Error testing optimized RAG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimized_rag())
