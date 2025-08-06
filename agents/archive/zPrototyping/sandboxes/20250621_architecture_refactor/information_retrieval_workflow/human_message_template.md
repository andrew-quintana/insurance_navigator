# Information Retrieval Request

## Task Description
Retrieve and synthesize relevant information to answer the user's query, ensuring accuracy and consistency in the response.

## Context
User ID: {user_id}
Programs: {programs}
Document Types: {document_types}
Search Priority: {search_priority} // "RELEVANCE" | "RECENCY" | "AUTHORITY"

## Query
{{input}}

## Requirements
- Expert reframing of the query
- Relevant information retrieval
- Consistent response synthesis
- Clear, direct answers
- Source attribution

## Constraints
- Use only specified document types
- Stay within authorized programs
- Maintain user context
- Preserve source metadata

## Success Criteria
- Accurate information retrieval
- Consistent response elements
- Clear, concise answer
- High confidence score
- Maintained context for follow-ups

## Search Parameters
Minimum Relevance Score: {min_relevance_score} // e.g., 0.7
Maximum Results: {max_results} // e.g., 10
Include Context: {include_context} // true/false

## Special Instructions
Time Range: {time_range} // e.g., "last 6 months" or "all"
Source Preferences: {source_preferences} // e.g., ["user_documents", "program_policies"]
Excluded Sources: {excluded_sources} // e.g., ["archived", "deprecated"]

## Required Analysis
Please:
1. Analyze the query for key concepts
2. Perform semantic search across specified documents
3. Verify consistency across retrieved information
4. Synthesize findings with source attribution
5. Report any information gaps or conflicts

## Output Requirements
Provide results in the format specified in your system prompt, including:
- Query analysis
- Ranked search results
- Consistency verification
- Information synthesis
- Source attribution
- Confidence scores

Please solve this using the ReAct framework, showing your Thought-Action-Observation cycle clearly until you reach the final answer.