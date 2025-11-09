# Phase 2B: Deep Dive Internal Flow Analysis Notebook

**Date:** 2025-10-09  
**Phase:** 2B - Internal Flow Deep Dive  
**Objective:** Create interactive notebook for step-by-step internal system analysis  
**Status:** 🔴 **New Scope - Supersedes Phase 2 High-Level Notebook**

---

## Problem with Phase 2 Notebook

The Phase 2 notebook (`FM_038_Debug_Notebook.ipynb`) provides **client-side analysis only**:
- ✅ Tests API endpoints
- ✅ Tracks request/response
- ✅ Measures external performance
- ❌ **Does NOT show internal agent flow**
- ❌ **Does NOT show agent handoffs**
- ❌ **Does NOT show tool execution details**
- ❌ **Does NOT show RAG internals**

**Gap:** We can see the system works/fails externally, but we cannot see **WHY** it fails internally.

---

## New Objective: Internal Flow Analysis

### What We Need to See

1. **Complete Request Flow**
   ```
   Chat Request → Main Endpoint → Agent Router → Patient Navigator Agent
                                                          ↓
   LLM Response ← Response Builder ← Tool Execution ← RAG Tool Call
   ```

2. **Agent State Transitions**
   - Agent initialization
   - Agent function calls
   - Agent state changes
   - Agent handoffs to other agents
   - Agent completion

3. **Tool Execution Internals**
   - Tool selection logic
   - Tool input preparation
   - Tool execution steps
   - Tool output processing
   - Tool error handling

4. **RAG Operation Breakdown**
   ```
   retrieve_chunks_from_text()
       ↓
   _generate_embedding()
       ↓ (Threading issues?)
   OpenAI API call
       ↓
   retrieve_chunks() [Database query]
       ↓
   Similarity calculation
       ↓
   Filter by threshold
       ↓
   Return chunks
   ```

5. **Database Operations**
   - Connection pool status
   - Query execution
   - Query parameters
   - Query results
   - Vector similarity calculations

6. **Performance at Each Step**
   - Function entry/exit timing
   - Thread switching overhead
   - Database query latency
   - Embedding generation time
   - Agent processing time

---

## Scope Definition

### Investigation Layers

#### Layer 1: Request Processing
- `/chat` endpoint receives request
- JWT validation
- User context loading
- Request parsing
- Agent selection logic

#### Layer 2: Agent Orchestration
- **Agent initialization**
  - Which agent is selected?
  - How is it initialized?
  - What context is passed?

- **Agent execution**
  - Function call planning
  - Tool selection
  - Tool invocation
  - Result processing

- **Agent handoffs**
  - When does agent hand off to another?
  - What data is passed?
  - How is state maintained?

#### Layer 3: Tool Execution (Focus: RAG Tool)
- **Tool call initiation**
  - Tool name
  - Tool parameters
  - Execution context

- **RAG tool execution**
  - `retrieve_chunks_from_text()` entry
  - User ID extraction
  - Query text preparation
  - Embedding generation request

- **Embedding generation**
  - `_generate_embedding()` entry
  - Threading wrapper execution
  - OpenAI client call (sync vs async)
  - API response
  - Embedding validation

- **Database query**
  - `retrieve_chunks()` entry
  - SQL query construction
  - Vector similarity operation
  - Results retrieval
  - Similarity filtering

- **Result processing**
  - Chunk formatting
  - Context preparation
  - Return to agent

#### Layer 4: Response Generation
- Context assembly
- LLM prompt construction
- LLM API call
- Response formatting
- Return to client

---

## Implementation Approach

### Option A: Instrumented Local Server
Run the system locally with enhanced instrumentation:

```python
# Add detailed logging to key functions
@log_entry_exit
@track_performance
def retrieve_chunks_from_text(user_id: str, query_text: str):
    logger.info(f"ENTRY: retrieve_chunks_from_text")
    logger.info(f"  user_id: {user_id}")
    logger.info(f"  query_text: {query_text[:100]}")
    # ... execution ...
    logger.info(f"EXIT: retrieve_chunks_from_text - chunks: {len(chunks)}")
```

**Notebook Structure:**
1. Start local server with instrumentation
2. Make requests from notebook
3. Parse server logs in real-time
4. Visualize flow and timing

### Option B: Direct Function Testing
Import and test functions directly in notebook:

```python
# Import system components
from agents.patient_navigator.agent import PatientNavigatorAgent
from agents.tooling.rag.core import RAGTool

# Test directly
agent = PatientNavigatorAgent(user_id="test-user")
result = agent.process_message("What mental health services are covered?")

# Analyze internal state
print(f"Agent state: {agent.state}")
print(f"Tools called: {agent.tools_called}")
print(f"RAG results: {agent.rag_results}")
```

**Notebook Structure:**
1. Import all necessary components
2. Mock external dependencies
3. Execute functions with instrumentation
4. Analyze results step-by-step

### Option C: Production Log Analysis (Recommended)
Analyze production logs with enhanced parsing:

```python
# Fetch production logs
logs = fetch_render_logs(service_id="srv-d0v2nqvdiees73cejf0g")

# Parse specific operation
operation_id = "f287de61-81be-4e4d-99a1-486e29849b1f"
flow = parse_operation_flow(logs, operation_id)

# Visualize
display_flow_timeline(flow)
display_function_calls(flow)
display_agent_handoffs(flow)
```

**Notebook Structure:**
1. Fetch production logs for specific time range
2. Parse logs into structured data
3. Reconstruct execution flow
4. Visualize each layer
5. Identify bottlenecks and failures

---

## Required Notebook Cells

### Setup Section
1. **Imports and Configuration**
2. **Logging Setup** - Enhanced logging configuration
3. **Data Structures** - Classes for tracking flow

### Analysis Section (One cell per layer)

#### Request Processing Cells
4. **Request Entry** - Analyze initial request
5. **Authentication** - JWT validation flow
6. **Agent Selection** - How agent is chosen

#### Agent Orchestration Cells
7. **Agent Initialization** - Agent startup
8. **Agent State** - Current agent state
9. **Tool Planning** - How tools are selected
10. **Tool Invocation** - Tool call details

#### RAG Tool Deep Dive Cells
11. **RAG Entry** - `retrieve_chunks_from_text()` analysis
12. **User Context** - User ID and context loading
13. **Query Preparation** - Text preprocessing
14. **Embedding Request** - `_generate_embedding()` analysis
15. **Threading Analysis** - Thread execution details
16. **OpenAI API Call** - API request/response
17. **Embedding Validation** - Verify embedding dimensions
18. **Database Query** - `retrieve_chunks()` analysis
19. **SQL Execution** - Actual SQL and parameters
20. **Vector Similarity** - Similarity calculation
21. **Result Filtering** - Threshold application
22. **Chunk Processing** - Format and return

#### Response Generation Cells
23. **Context Assembly** - Building LLM context
24. **LLM Call** - API request to LLM
25. **Response Formatting** - Format response
26. **Return to Client** - Final response

### Visualization Section
27. **Flow Timeline** - Complete execution timeline
28. **Performance Waterfall** - Waterfall chart of timing
29. **Agent Handoff Graph** - Visualize agent transitions
30. **Bottleneck Analysis** - Identify slow operations
31. **Error Propagation** - Track error flow

### Analysis Section
32. **Function I/O Analysis** - Detailed input/output
33. **State Transitions** - Agent state changes
34. **Performance Metrics** - Aggregate statistics
35. **Comparison Analysis** - Compare successful vs failed
36. **Root Cause Identification** - Analyze patterns

---

## Key Insights to Extract

### 1. Agent Flow Questions
- Which agent handles the request?
- Does it hand off to other agents?
- What triggers handoffs?
- Is state preserved correctly?

### 2. RAG Operation Questions
- Is `retrieve_chunks_from_text()` called?
- What are the exact inputs?
- Is `_generate_embedding()` called?
- Does it enter the threading wrapper?
- Does OpenAI API get called?
- What is the response?
- Are embeddings valid (1536 dimensions)?
- Is `retrieve_chunks()` called?
- What SQL is executed?
- What are the query results?
- How many chunks match?
- What are similarity scores?
- Why are 0 chunks returned?

### 3. Performance Questions
- What is slowest operation?
- Where is time spent?
- Are there blocking operations?
- Is threading helping or hurting?
- Are database queries efficient?

### 4. Error Questions
- Where do errors occur?
- Are errors caught and handled?
- Are there silent failures?
- How do errors propagate?

---

## Data Sources

### Production Logs (Render)
```
Service: srv-d0v2nqvdiees73cejf0g
Look for:
- RAG Operation Started [operation_id]
- CHECKPOINT A-H logs
- PRE-EMBEDDING / POST-EMBEDDING
- Function entry/exit logs
- Error messages
```

### Local Development Logs
```
Run locally with enhanced logging:
- Set LOG_LEVEL=DEBUG
- Enable performance monitoring
- Add custom instrumentation
```

### Database Queries
```sql
-- Check chunks exist
SELECT COUNT(*) FROM chunks WHERE user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858';

-- Check embeddings exist
SELECT COUNT(*) FROM chunks 
WHERE user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858' 
  AND embedding IS NOT NULL;

-- Test similarity search manually
SELECT id, document_id, similarity
FROM chunks
WHERE user_id = 'cae3b3ec-b355-4509-bd4e-0f7da8cb2858'
ORDER BY embedding <=> '[embedding_vector]'
LIMIT 5;
```

---

## Expected Deliverables

### 1. Deep Dive Notebook
**File:** `tests/fm_038/FM_038_Deep_Dive_Notebook.ipynb`

**Features:**
- 35+ cells for granular analysis
- Production log parsing and visualization
- Function-level tracking
- Agent state visualization
- RAG operation breakdown
- Performance waterfall charts
- Error propagation tracking

### 2. Usage Guide
**File:** `tests/fm_038/FM_038_DEEP_DIVE_USAGE_GUIDE.md`

**Contents:**
- How to fetch production logs
- How to run locally with instrumentation
- How to analyze specific operations
- How to identify bottlenecks
- How to debug specific issues

### 3. Analysis Template
**File:** `tests/fm_038/FM_038_ANALYSIS_TEMPLATE.md`

**Contents:**
- Template for documenting findings
- Checklist for root cause analysis
- Format for corrective actions
- Structure for FRACAS report

---

## Success Criteria

### Must Show
- ✅ Complete execution flow from request to response
- ✅ Every agent handoff with state
- ✅ Every tool call with inputs/outputs
- ✅ Every RAG operation step
- ✅ Every database query with results
- ✅ Performance timing at each step
- ✅ Error location and propagation

### Must Identify
- ✅ Exact point where zero chunks occur
- ✅ Why embeddings fail (if they do)
- ✅ Why database returns no results (if it does)
- ✅ Performance bottlenecks
- ✅ Root cause of issue

### Must Enable
- ✅ Step-by-step debugging
- ✅ Reproduce issue locally
- ✅ Test fixes interactively
- ✅ Validate corrections

---

## Implementation Priority

### Phase 2B-1: Production Log Analysis (Start Here) ⭐
**Why:** Fastest way to see internal flow without code changes
**Approach:** Fetch and parse existing production logs
**Timeline:** 2-3 hours

### Phase 2B-2: Enhanced Instrumentation
**Why:** Add missing checkpoints if logs insufficient
**Approach:** Add detailed logging to key functions
**Timeline:** 4-6 hours

### Phase 2B-3: Local Testing Environment
**Why:** Test fixes without deploying to production
**Approach:** Run system locally with full instrumentation
**Timeline:** 6-8 hours

---

## Next Steps

1. **Create Phase 2B Prompt** - Detailed prompt for agent
2. **Build Deep Dive Notebook** - Implement production log analysis
3. **Run Analysis** - Execute notebook on recent operations
4. **Document Findings** - Create comprehensive analysis
5. **Proceed to Phase 3** - Use findings for corrective actions

---

**Document Version:** 1.0  
**Created:** 2025-10-09  
**Status:** Ready for Implementation  
**Supersedes:** Phase 2 high-level notebook  
**Next:** Create Phase 2B implementation prompt

