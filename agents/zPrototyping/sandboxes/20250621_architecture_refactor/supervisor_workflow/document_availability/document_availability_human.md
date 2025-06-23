Task: Use ReAct methodology to systematically check each required document in the user's Supabase storage and determine workflow execution readiness.

Context:
You have access to mock Supabase document storage functions that simulate real database operations. For each required document, you must follow the ReAct framework to search, assess quality, and determine usability.

Your ReAct Process Should:
1. For EACH required document:
   - Thought: Plan what to check and why
   - Action: SearchDocument[document_name] 
   - Observation: Report search results
   - Action: AssessQuality[document_name] (if document exists)
   - Observation: Report quality assessment
   - Action: CheckValidity[document_name] (if needed)
   - Observation: Report validity status

2. After checking all documents:
   - Thought: Synthesize findings and determine readiness
   - Action: Finish[comprehensive_assessment]

Remember: Be systematic, thorough, and use the exact ReAct format for each document check.

Input:
{{input}} 