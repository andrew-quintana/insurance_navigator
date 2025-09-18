#!/usr/bin/env python3
"""
Debug RAG Retrieval
Debug what chunks are being retrieved from the real insurance document
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

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks for RAG."""
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        if len(chunk_text.strip()) > 50:  # Only include substantial chunks
            chunks.append({
                "content": chunk_text.strip(),
                "chunk_index": len(chunks) + 1,
                "word_count": len(chunk_words)
            })
    
    return chunks

def generate_mock_embedding(text: str, seed_offset: int = 0) -> List[float]:
    """Generate a deterministic 1536-dimensional embedding for testing."""
    # Create deterministic seed from text content
    text_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(text_hash[:8], 16) + seed_offset
    
    # Set random seed for deterministic generation
    random.seed(seed)
    
    # Generate 1536-dimensional vector (OpenAI text-embedding-3-small)
    embedding = [random.uniform(-1, 1) for _ in range(1536)]
    
    # Normalize to unit vector for consistency
    magnitude = sum(x*x for x in embedding) ** 0.5
    normalized = [x/magnitude for x in embedding]
    
    return normalized

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def debug_rag_retrieval():
    """Debug what chunks are being retrieved from the insurance document."""
    print("🔍 Debugging RAG Retrieval from Real Insurance Document")
    print("=" * 60)
    
    # Extract text from PDF
    pdf_path = "examples/scan_classic_hmo.pdf"
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print(f"📄 Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("❌ Failed to extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters of text")
    
    # Chunk the text
    print("📝 Chunking text for RAG...")
    chunks = chunk_text(text)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Show some sample chunks
    print("\n📋 Sample chunks from the document:")
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nChunk {i+1}:")
        print(f"  Content: {chunk['content'][:200]}...")
        print(f"  Word count: {chunk['word_count']}")
    
    # Test queries
    test_queries = [
        "What is my deductible?",
        "What are my copays?",
        "What services are covered?",
        "How do I find a doctor?",
        "What are my prescription benefits?"
    ]
    
    print(f"\n🔍 Testing retrieval for {len(test_queries)} queries...")
    
    for query in test_queries:
        print(f"\n--- Query: '{query}' ---")
        
        # Generate query embedding
        query_embedding = generate_mock_embedding(query)
        
        # Calculate similarity for each chunk
        similarities = []
        for i, chunk in enumerate(chunks):
            chunk_embedding = generate_mock_embedding(chunk['content'], i)
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((i, similarity, chunk['content']))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Show top 5 matches
        print(f"Top 5 matches:")
        for i, (chunk_idx, sim, content) in enumerate(similarities[:5]):
            print(f"  {i+1}. Similarity: {sim:.4f}")
            print(f"     Content: {content[:150]}...")
            print()
        
        # Check if any chunks contain relevant keywords
        query_lower = query.lower()
        relevant_chunks = []
        
        for i, chunk in enumerate(chunks):
            content_lower = chunk['content'].lower()
            
            # Check for relevant keywords
            if 'deductible' in query_lower and 'deductible' in content_lower:
                relevant_chunks.append((i, chunk['content']))
            elif 'copay' in query_lower and ('copay' in content_lower or 'copayment' in content_lower):
                relevant_chunks.append((i, chunk['content']))
            elif 'covered' in query_lower and ('covered' in content_lower or 'coverage' in content_lower):
                relevant_chunks.append((i, chunk['content']))
            elif 'doctor' in query_lower and ('doctor' in content_lower or 'physician' in content_lower):
                relevant_chunks.append((i, chunk['content']))
            elif 'prescription' in query_lower and ('prescription' in content_lower or 'drug' in content_lower):
                relevant_chunks.append((i, chunk['content']))
        
        if relevant_chunks:
            print(f"Found {len(relevant_chunks)} chunks with relevant keywords:")
            for i, (chunk_idx, content) in enumerate(relevant_chunks[:3]):
                print(f"  {i+1}. Chunk {chunk_idx}: {content[:200]}...")
        else:
            print("No chunks found with relevant keywords")
        
        print("-" * 50)

if __name__ == "__main__":
    debug_rag_retrieval()
