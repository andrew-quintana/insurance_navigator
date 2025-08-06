# Information Retrieval Agent Design Notes

## Core Concept
The Information Retrieval Agent serves as a direct interface between user queries and the RAG system, focusing on providing concise, accurate responses while maintaining additional context for follow-up questions.

## Key Components

### 1. Query Processing
- Take raw user query
- Generate an "expert reframe" of the question
- Use both original and reframed versions for vector search
- No need for complex query analysis - keep it simple and direct

### 2. RAG Integration
- Perform similarity search using both query versions
- Retrieve relevant chunks with context
- Maintain chunk metadata for source attribution

### 3. Response Generation
- Focus on concise, direct answers
- Rank information by relevance
- Summarize key points
- Keep additional context in memory for follow-ups

### 4. Self-Consistency Approach
Instead of checking consistency between programs/documents, use self-consistency to:
- Generate multiple potential responses
- Compare responses for consistency
- Select the most reliable/consistent answer
- Maintain confidence in the selected response

## Output Structure

### Primary Response
```json
{
    "expert_reframe": "Reframed question from expert perspective",
    "direct_answer": "Concise, focused answer to the query",
    "key_points": [
        "Ranked list of most relevant information"
    ],
    "confidence_score": 0.95  // Based on self-consistency checks
}
```

### Maintained Context (Not in primary response, but kept for follow-ups)
```json
{
    "supporting_chunks": [
        {
            "content": "Full chunk content",
            "source": "Source document",
            "relevance_score": 0.92
        }
    ],
    "additional_details": [
        "Related information not included in primary response"
    ]
}
```

## Self-Consistency Implementation
1. Generate 3-5 potential responses using slightly different perspectives
2. Compare responses for common elements
3. Identify the most consistent information
4. Use this to form the final response

## Benefits of This Approach
1. **Simplicity**: Direct path from query to response
2. **Accuracy**: Self-consistency checks ensure reliable information
3. **Efficiency**: Concise primary responses with backup context
4. **Flexibility**: Easy follow-up using maintained context

## Example Flow
1. User asks: "What are my physical therapy benefits?"
2. Agent reframes: "What are the specific physical therapy coverage limits, requirements, and copayments under the current insurance plan?"
3. RAG search using both versions
4. Generate multiple response versions
5. Compare for consistency
6. Provide concise answer with key points
7. Maintain full context for follow-ups 