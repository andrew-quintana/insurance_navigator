#!/usr/bin/env python3
"""
Optimize Chunking Strategy for RAG
Test different chunk sizes and strategies to find the best configuration
"""

import asyncio
import os
import sys
import json
import hashlib
import random
import time
from typing import List, Dict, Any
import PyPDF2
import openai

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

def chunk_text_word_based(text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks based on word count."""
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

def chunk_text_sentence_based(text: str, max_sentences: int, overlap_sentences: int) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks based on sentence count."""
    import re
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    for i in range(0, len(sentences), max_sentences - overlap_sentences):
        chunk_sentences = sentences[i:i + max_sentences]
        chunk_text = ". ".join(chunk_sentences) + "."
        
        if len(chunk_text.strip()) > 50:
            chunks.append({
                "content": chunk_text.strip(),
                "chunk_index": len(chunks) + 1,
                "sentence_count": len(chunk_sentences),
                "word_count": len(chunk_text.split()),
                "char_count": len(chunk_text)
            })
    
    return chunks

def chunk_text_paragraph_based(text: str, max_paragraphs: int, overlap_paragraphs: int) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks based on paragraph count."""
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    chunks = []
    for i in range(0, len(paragraphs), max_paragraphs - overlap_paragraphs):
        chunk_paragraphs = paragraphs[i:i + max_paragraphs]
        chunk_text = "\n\n".join(chunk_paragraphs)
        
        if len(chunk_text.strip()) > 50:
            chunks.append({
                "content": chunk_text.strip(),
                "chunk_index": len(chunks) + 1,
                "paragraph_count": len(chunk_paragraphs),
                "word_count": len(chunk_text.split()),
                "char_count": len(chunk_text)
            })
    
    return chunks

def generate_openai_embedding(text: str) -> List[float]:
    """Generate real OpenAI text-embedding-3-small embedding."""
    try:
        # Set OpenAI API key if not already set
        if not openai.api_key:
            openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai.api_key:
            print("Warning: OPENAI_API_KEY not found, falling back to mock embeddings")
            return generate_mock_embedding(text)
        
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: OpenAI embedding failed ({e}), falling back to mock embeddings")
        return generate_mock_embedding(text)

def generate_mock_embedding(text: str, seed_offset: int = 0) -> List[float]:
    """Generate a deterministic 1536-dimensional embedding for testing."""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(text_hash[:8], 16) + seed_offset
    random.seed(seed)
    
    embedding = [random.uniform(-1, 1) for _ in range(1536)]
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

def test_chunking_strategy(text: str, strategy_name: str, chunk_func, params: Dict[str, Any], test_queries: List[str]) -> Dict[str, Any]:
    """Test a specific chunking strategy."""
    print(f"  Testing {strategy_name} with params: {params}")
    
    # Create chunks
    start_time = time.time()
    chunks = chunk_func(text, **params)
    chunking_time = time.time() - start_time
    
    # Generate embeddings for chunks using OpenAI
    start_time = time.time()
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = generate_openai_embedding(chunk["content"])
    embedding_time = time.time() - start_time
    
    # Test queries and collect all similarity scores for histogram
    all_similarities = []
    results = []
    
    for query in test_queries:
        query_embedding = generate_openai_embedding(query)
        
        # Calculate similarities
        similarities = []
        for chunk in chunks:
            similarity = cosine_similarity(query_embedding, chunk["embedding"])
            similarities.append((chunk, similarity))
            all_similarities.append(similarity)  # Collect for histogram
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Check if top chunks contain relevant keywords
        query_lower = query.lower()
        relevant_chunks = []
        
        for chunk, similarity in similarities[:5]:  # Top 5
            content_lower = chunk["content"].lower()
            relevance_score = 0
            
            if "deductible" in query_lower and "deductible" in content_lower:
                relevance_score += 1
            if "copay" in query_lower and ("copay" in content_lower or "copayment" in content_lower):
                relevance_score += 1
            if "covered" in query_lower and ("covered" in content_lower or "coverage" in content_lower):
                relevance_score += 1
            if "doctor" in query_lower and ("doctor" in content_lower or "physician" in content_lower):
                relevance_score += 1
            if "prescription" in query_lower and ("prescription" in content_lower or "drug" in content_lower):
                relevance_score += 1
            
            if relevance_score > 0:
                relevant_chunks.append((chunk, similarity, relevance_score))
        
        results.append({
            "query": query,
            "total_chunks": len(chunks),
            "relevant_chunks": len(relevant_chunks),
            "top_similarity": similarities[0][1] if similarities else 0,
            "relevance_score": sum(rc[2] for rc in relevant_chunks)
        })
    
    # Calculate adaptive similarity histogram buckets
    if all_similarities:
        min_sim = min(all_similarities)
        max_sim = max(all_similarities)
        sim_range = max_sim - min_sim
        
        # Create adaptive buckets based on actual range
        if sim_range < 0.01:  # Very narrow range, use 0.001 buckets
            bucket_size = 0.001
            num_buckets = min(20, int(sim_range / bucket_size) + 1)
        elif sim_range < 0.1:  # Narrow range, use 0.01 buckets
            bucket_size = 0.01
            num_buckets = min(20, int(sim_range / bucket_size) + 1)
        elif sim_range < 0.5:  # Medium range, use 0.05 buckets
            bucket_size = 0.05
            num_buckets = min(20, int(sim_range / bucket_size) + 1)
        else:  # Wide range, use 0.1 buckets
            bucket_size = 0.1
            num_buckets = min(20, int(sim_range / bucket_size) + 1)
        
        # Create buckets
        similarity_buckets = {}
        bucket_labels = []
        for i in range(num_buckets):
            bucket_start = min_sim + (i * bucket_size)
            bucket_end = min_sim + ((i + 1) * bucket_size)
            bucket_label = f"{bucket_start:.3f}-{bucket_end:.3f}"
            similarity_buckets[bucket_label] = 0
            bucket_labels.append(bucket_label)
        
        # Distribute similarities into buckets
        for sim in all_similarities:
            bucket_index = min(int((sim - min_sim) / bucket_size), num_buckets - 1)
            bucket_label = bucket_labels[bucket_index]
            similarity_buckets[bucket_label] += 1
        
        # Debug: print bucket info for first strategy
        if strategy_name == "word_100":  # First strategy for debugging
            print(f"    Debug - Min: {min_sim:.6f}, Max: {max_sim:.6f}, Range: {sim_range:.6f}")
            print(f"    Debug - Bucket size: {bucket_size:.6f}, Num buckets: {num_buckets}")
            print(f"    Debug - Bucket labels: {bucket_labels[:3]}...")  # Show first 3
    else:
        similarity_buckets = {}
        bucket_labels = []
    
    # Calculate percentages
    total_similarities = len(all_similarities)
    similarity_percentages = {}
    for bucket, count in similarity_buckets.items():
        similarity_percentages[bucket] = (count / total_similarities * 100) if total_similarities > 0 else 0
    
    # Calculate overall metrics
    avg_relevance = sum(r["relevance_score"] for r in results) / len(results)
    avg_similarity = sum(r["top_similarity"] for r in results) / len(results)
    total_relevant = sum(r["relevant_chunks"] for r in results)
    
    return {
        "strategy": strategy_name,
        "params": params,
        "chunk_count": len(chunks),
        "chunking_time": chunking_time,
        "embedding_time": embedding_time,
        "total_time": chunking_time + embedding_time,
        "avg_relevance_score": avg_relevance,
        "avg_similarity": avg_similarity,
        "total_relevant_chunks": total_relevant,
        "similarity_buckets": similarity_buckets,
        "similarity_percentages": similarity_percentages,
        "query_results": results
    }

def optimize_chunking():
    """Run chunking optimization tests."""
    print("🔧 Chunking Strategy Optimization")
    print("=" * 60)
    
    # Load test document
    pdf_path = "examples/test_insurance_document.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ Test document not found: {pdf_path}")
        return
    
    print(f"📄 Loading test document: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("❌ Failed to extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters of text")
    
    # Test queries
    test_queries = [
        "What is my deductible?",
        "What are my copays?",
        "What services are covered?",
        "How do I find a doctor?",
        "What are my prescription benefits?"
    ]
    
    print(f"🔍 Testing with {len(test_queries)} queries")
    
    # Define chunking strategies to test
    strategies = [
        # Word-based strategies
        ("word_100", chunk_text_word_based, {"chunk_size": 100, "overlap": 25}),
        ("word_150", chunk_text_word_based, {"chunk_size": 150, "overlap": 30}),
        ("word_200", chunk_text_word_based, {"chunk_size": 200, "overlap": 40}),
        ("word_250", chunk_text_word_based, {"chunk_size": 250, "overlap": 50}),
        ("word_300", chunk_text_word_based, {"chunk_size": 300, "overlap": 60}),
        ("word_400", chunk_text_word_based, {"chunk_size": 400, "overlap": 80}),
        ("word_500", chunk_text_word_based, {"chunk_size": 500, "overlap": 100}),
        
        # Sentence-based strategies
        ("sentence_3", chunk_text_sentence_based, {"max_sentences": 3, "overlap_sentences": 1}),
        ("sentence_5", chunk_text_sentence_based, {"max_sentences": 5, "overlap_sentences": 1}),
        ("sentence_7", chunk_text_sentence_based, {"max_sentences": 7, "overlap_sentences": 2}),
        ("sentence_10", chunk_text_sentence_based, {"max_sentences": 10, "overlap_sentences": 2}),
        
        # Paragraph-based strategies
        ("paragraph_2", chunk_text_paragraph_based, {"max_paragraphs": 2, "overlap_paragraphs": 1}),
        ("paragraph_3", chunk_text_paragraph_based, {"max_paragraphs": 3, "overlap_paragraphs": 1}),
        ("paragraph_4", chunk_text_paragraph_based, {"max_paragraphs": 4, "overlap_paragraphs": 1}),
    ]
    
    print(f"\n🧪 Testing {len(strategies)} chunking strategies...")
    
    results = []
    for strategy_name, chunk_func, params in strategies:
        try:
            result = test_chunking_strategy(text, strategy_name, chunk_func, params, test_queries)
            results.append(result)
            print(f"  ✅ {strategy_name}: {result['chunk_count']} chunks, relevance: {result['avg_relevance_score']:.2f}")
        except Exception as e:
            print(f"  ❌ {strategy_name}: Error - {e}")
    
    # Sort results by relevance score
    results.sort(key=lambda x: x["avg_relevance_score"], reverse=True)
    
    print(f"\n📊 OPTIMIZATION RESULTS")
    print("=" * 60)
    
    print(f"{'Strategy':<15} {'Chunks':<8} {'Relevance':<10} {'Similarity':<12} {'Time (s)':<10}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['strategy']:<15} {result['chunk_count']:<8} {result['avg_relevance_score']:<10.2f} {result['avg_similarity']:<12.4f} {result['total_time']:<10.2f}")
    
    # Show similarity histogram for all strategies
    print(f"\n📈 SIMILARITY DISTRIBUTION FOR ALL STRATEGIES")
    print("=" * 80)
    
    for i, result in enumerate(results):
        print(f"\n🔍 {result['strategy']} (Rank #{i+1})")
        print("-" * 60)
        print(f"{'Range':<15} {'Count':<8} {'Percentage':<12} {'Bar'}")
        print("-" * 60)
        
        # Get bucket labels from the result
        bucket_labels = list(result['similarity_buckets'].keys())
        bucket_labels.sort()  # Sort by range
        
        for bucket in bucket_labels:
            count = result['similarity_buckets'][bucket]
            percentage = result['similarity_percentages'][bucket]
            bar = "█" * int(percentage / 2)  # Scale bar to fit in terminal
            print(f"{bucket:<15} {count:<8} {percentage:<11.1f}% {bar}")
        
        # Show key stats for this strategy
        if bucket_labels:
            try:
                first_bucket = bucket_labels[0]
                last_bucket = bucket_labels[-1]
                min_val = float(first_bucket.split('-')[0])
                max_val = float(last_bucket.split('-')[1])
                print(f"  Range: {min_val:.4f} to {max_val:.4f} (span: {max_val-min_val:.4f})")
            except (ValueError, IndexError):
                print(f"  Range: Unable to parse")
    
    # Show best strategy summary
    best_result = results[0]
    print(f"\n🏆 BEST STRATEGY: {best_result['strategy']}")
    print(f"   Parameters: {best_result['params']}")
    print(f"   Chunks: {best_result['chunk_count']}")
    print(f"   Relevance Score: {best_result['avg_relevance_score']:.2f}")
    print(f"   Processing Time: {best_result['total_time']:.2f}s")
    
    # Show threshold analysis
    print(f"\n🎯 THRESHOLD ANALYSIS:")
    print("=" * 60)
    print(f"{'Threshold':<12} {'Chunks Above':<15} {'Percentage':<12}")
    print("-" * 60)
    
    for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
        chunks_above = 0
        for bucket, count in best_result['similarity_buckets'].items():
            try:
                bucket_min = float(bucket.split('-')[0])
                if bucket_min >= threshold:
                    chunks_above += count
            except (ValueError, IndexError):
                continue
        
        percentage = (chunks_above / best_result['chunk_count'] * 100) if best_result['chunk_count'] > 0 else 0
        print(f"{threshold:<12} {chunks_above:<15} {percentage:<11.1f}%")
    
    # Show detailed results for best strategy
    print(f"\n📋 DETAILED RESULTS FOR BEST STRATEGY:")
    for query_result in best_result['query_results']:
        print(f"  Query: {query_result['query']}")
        print(f"    Relevant chunks: {query_result['relevant_chunks']}/{query_result['total_chunks']}")
        print(f"    Top similarity: {query_result['top_similarity']:.4f}")
        print(f"    Relevance score: {query_result['relevance_score']}")
        print()
    
    # Save results
    output_file = "chunking_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved to: {output_file}")
    
    return best_result

if __name__ == "__main__":
    optimize_chunking()
