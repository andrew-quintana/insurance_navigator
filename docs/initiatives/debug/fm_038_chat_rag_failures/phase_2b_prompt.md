# Phase 2B Prompt: Deep Dive Internal Flow Analysis Notebook

**Phase:** 2B - Internal Flow Deep Dive  
**Objective:** Create notebook for granular internal system analysis  
**Status:** 🔴 **Ready for Implementation**  
**Priority:** P0 - Critical for identifying root cause

---

## Context

The Phase 2 notebook was too high-level, only testing from the client side (API requests/responses). We need a **deep dive into internal execution flow** to understand:

1. Agent-to-agent handoffs
2. Tool execution (especially RAG tool)
3. Function-level performance
4. Database operations
5. Embedding generation process
6. Where exactly the zero-chunk issue occurs

---

## Your Task

Create a Jupyter notebook that provides **granular analysis of internal system execution** by parsing production logs and reconstructing the complete execution flow.

---

## Notebook Structure

### Part 1: Setup and Log Fetching (Cells 1-5)

#### Cell 1: Overview (Markdown)
- Explain this is internal flow analysis
- List what we'll investigate
- Prerequisites

#### Cell 2: Imports and Setup (Python)
```python
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from IPython.display import display, HTML, Markdown
import re
from collections import defaultdict
```

#### Cell 3: Log Data Structures (Python)
```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    operation_id: Optional[str]
    checkpoint: Optional[str]
    
@dataclass
class FunctionCall:
    name: str
    start_time: datetime
    end_time: Optional[datetime]
    inputs: Dict[str, Any]
    outputs: Any
    duration_ms: Optional[float]
    
@dataclass
class OperationFlow:
    operation_id: str
    start_time: datetime
    end_time: Optional[datetime]
    user_id: str
    query_text: str
    function_calls: List[FunctionCall]
    checkpoints: List[str]
    chunks_returned: int
    success: bool
    error: Optional[str]
```

#### Cell 4: Load Production Logs (Python)
Options:
- **Option A:** Load from saved log file
- **Option B:** Paste logs directly
- **Option C:** Fetch from Render API (if available)

```python
# Option A: Load from file
with open('production_logs_20251009.txt', 'r') as f:
    raw_logs = f.read()

# Option B: Paste logs directly
raw_logs = """
[paste production logs here]
"""

# Parse logs into structured format
log_entries = parse_log_entries(raw_logs)
display(Markdown(f"### ✅ Loaded {len(log_entries)} log entries"))
```

#### Cell 5: Identify Operations (Python)
```python
# Find all RAG operations in logs
operations = {}
for entry in log_entries:
    if "RAG Operation Started" in entry.message:
        operation_id = extract_operation_id(entry.message)
        operations[operation_id] = OperationFlow(
            operation_id=operation_id,
            start_time=entry.timestamp,
            # ... extract other fields
        )

display(Markdown(f"### 🔍 Found {len(operations)} RAG operations"))
display_operations_table(operations)
```

---

### Part 2: Operation Selection and Flow Reconstruction (Cells 6-10)

#### Cell 6: Select Operation to Analyze (Python)
```python
# Select specific operation (or most recent failure)
selected_operation_id = "f287de61-81be-4e4d-99a1-486e29849b1f"  # Modify as needed

# Or select most recent zero-chunk operation
# selected_operation_id = find_zero_chunk_operations(operations)[0]

operation = operations[selected_operation_id]
display_operation_summary(operation)
```

#### Cell 7: Extract Function Calls (Python)
```python
# Parse logs to extract all function calls for this operation
function_calls = extract_function_calls(log_entries, selected_operation_id)

display(Markdown(f"### 📞 Found {len(function_calls)} function calls"))
display_function_timeline(function_calls)
```

#### Cell 8: Extract Checkpoints (Python)
```python
# Extract CHECKPOINT A-H logs
checkpoints = extract_checkpoints(log_entries, selected_operation_id)

display(Markdown("### 🛤️ Checkpoint Progress"))
for checkpoint in checkpoints:
    display(Markdown(f"- **{checkpoint.name}**: {checkpoint.message} (t+{checkpoint.elapsed_ms}ms)"))
```

#### Cell 9: Reconstruct Execution Flow (Python)
```python
# Build complete execution timeline
flow = reconstruct_flow(operation, function_calls, checkpoints)

display(Markdown("### 🔄 Complete Execution Flow"))
display_flow_diagram(flow)
```

#### Cell 10: Flow Summary Visualization (Python)
```python
# Create Gantt-style timeline
fig, ax = plt.subplots(figsize=(15, 8))
plot_execution_timeline(ax, flow)
plt.title(f"Execution Timeline: {selected_operation_id}")
plt.show()
```

---

### Part 3: Request Processing Analysis (Cells 11-15)

#### Cell 11: Request Entry Analysis (Python)
```python
display(Markdown("### 📨 Request Processing"))

# Find request entry logs
request_logs = find_logs_matching(log_entries, selected_operation_id, pattern="chat request")

display_log_entries(request_logs)
```

#### Cell 12: Agent Selection (Python)
```python
display(Markdown("### 🤖 Agent Selection"))

# Find agent selection logs
agent_logs = find_logs_matching(log_entries, selected_operation_id, pattern="agent|navigator")

# Visualize agent selection
display(HTML(f"""
<div style="padding: 15px; background: #e3f2fd; border-radius: 5px;">
    <h4>Agent: Patient Navigator</h4>
    <p>Selected based on: {extract_selection_reason(agent_logs)}</p>
</div>
"""))
```

#### Cell 13: User Context Loading (Python)
```python
display(Markdown("### 👤 User Context"))

# Extract user context information
user_context = extract_user_context(log_entries, operation.user_id)

display(HTML(f"""
<table>
    <tr><td><strong>User ID:</strong></td><td>{operation.user_id}</td></tr>
    <tr><td><strong>Documents:</strong></td><td>{user_context.get('documents', 'N/A')}</td></tr>
    <tr><td><strong>Chunks Available:</strong></td><td>{user_context.get('chunks', 'N/A')}</td></tr>
</table>
"""))
```

#### Cell 14: Tool Planning (Python)
```python
display(Markdown("### 🛠️ Tool Planning"))

# Find tool selection logs
tool_logs = find_logs_matching(log_entries, selected_operation_id, pattern="tool")

display(Markdown("**Tools Considered:**"))
for tool in extract_tools(tool_logs):
    display(Markdown(f"- {tool.name}: {tool.reason}"))
```

#### Cell 15: Tool Invocation Summary (Python)
```python
display(Markdown("### ⚡ Tool Invocation"))

# Extract tool calls
tool_calls = extract_tool_calls(function_calls)

for tool_call in tool_calls:
    display(HTML(f"""
    <div style="padding: 10px; background: #fff3cd; border-radius: 5px; margin: 10px 0;">
        <strong>Tool:</strong> {tool_call.name}<br>
        <strong>Duration:</strong> {tool_call.duration_ms:.2f}ms<br>
        <strong>Status:</strong> {tool_call.status}
    </div>
    """))
```

---

### Part 4: RAG Tool Deep Dive (Cells 16-30)

#### Cell 16: RAG Tool Entry (Python)
```python
display(Markdown("### 🔍 RAG Tool: retrieve_chunks_from_text()"))

# Find RAG entry point
rag_entry = find_function_entry(function_calls, "retrieve_chunks_from_text")

display(HTML(f"""
<div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff;">
    <h4>Function Entry</h4>
    <pre>
retrieve_chunks_from_text(
    user_id="{rag_entry.inputs['user_id']}",
    query_text="{rag_entry.inputs['query_text'][:100]}...",
    similarity_threshold={rag_entry.inputs.get('similarity_threshold', 0.5)}
)
    </pre>
</div>
"""))
```

#### Cell 17: Pre-Embedding Checkpoint (Python)
```python
display(Markdown("### 🎯 PRE-EMBEDDING Checkpoint"))

# Find PRE-EMBEDDING logs
pre_embedding = find_logs_matching(log_entries, selected_operation_id, pattern="PRE-EMBEDDING")

if pre_embedding:
    display(Markdown("✅ **PRE-EMBEDDING checkpoint reached**"))
    display_log_entries(pre_embedding)
else:
    display(Markdown("❌ **PRE-EMBEDDING checkpoint NOT found** - function may not have reached embedding generation"))
```

#### Cell 18: Embedding Generation Analysis (Python)
```python
display(Markdown("### 🧠 Embedding Generation: _generate_embedding()"))

# Find embedding generation logs
embedding_logs = find_logs_matching(log_entries, selected_operation_id, pattern="embedding|_generate_embedding")

# Check if function was called
if embedding_logs:
    display(Markdown("✅ **Embedding generation attempted**"))
    
    # Extract details
    embedding_call = find_function_entry(function_calls, "_generate_embedding")
    if embedding_call:
        display(HTML(f"""
        <table>
            <tr><td><strong>Text Length:</strong></td><td>{embedding_call.inputs.get('text_length', 'N/A')}</td></tr>
            <tr><td><strong>Duration:</strong></td><td>{embedding_call.duration_ms:.2f}ms</td></tr>
            <tr><td><strong>Status:</strong></td><td>{embedding_call.status}</td></tr>
        </table>
        """))
else:
    display(Markdown("❌ **Embedding generation NOT attempted** - function may have exited early"))
```

#### Cell 19: Threading Analysis (Python)
```python
display(Markdown("### 🧵 Threading Wrapper Analysis"))

# Look for threading-related logs
threading_logs = find_logs_matching(log_entries, selected_operation_id, pattern="thread|executor")

if threading_logs:
    display(Markdown("**Threading Activity:**"))
    for log in threading_logs:
        display(Markdown(f"- `{log.message}`"))
    
    # Analyze if threading caused issues
    analyze_threading_issues(threading_logs)
else:
    display(Markdown("⚠️ No threading logs found"))
```

#### Cell 20: OpenAI API Call Analysis (Python)
```python
display(Markdown("### 🌐 OpenAI API Call"))

# Find OpenAI API logs
openai_logs = find_logs_matching(log_entries, selected_operation_id, pattern="openai|api|embedding|text-embedding")

if openai_logs:
    display(Markdown("✅ **OpenAI API called**"))
    
    # Extract request/response
    api_call = extract_api_call(openai_logs)
    display(HTML(f"""
    <div style="padding: 15px; background: #d4edda; border-radius: 5px;">
        <h4>API Call Details</h4>
        <table>
            <tr><td><strong>Model:</strong></td><td>{api_call.get('model', 'N/A')}</td></tr>
            <tr><td><strong>Request Time:</strong></td><td>{api_call.get('request_time', 'N/A')}</td></tr>
            <tr><td><strong>Response Time:</strong></td><td>{api_call.get('response_time', 'N/A')}</td></tr>
            <tr><td><strong>Duration:</strong></td><td>{api_call.get('duration_ms', 'N/A')}ms</td></tr>
            <tr><td><strong>Status:</strong></td><td>{api_call.get('status', 'N/A')}</td></tr>
        </table>
    </div>
    """))
else:
    display(Markdown("❌ **OpenAI API NOT called** - This is likely the issue!"))
```

#### Cell 21: POST-Embedding Checkpoint (Python)
```python
display(Markdown("### 🎯 POST-EMBEDDING Checkpoint"))

# Find POST-EMBEDDING logs
post_embedding = find_logs_matching(log_entries, selected_operation_id, pattern="POST-EMBEDDING")

if post_embedding:
    display(Markdown("✅ **POST-EMBEDDING checkpoint reached**"))
    display_log_entries(post_embedding)
else:
    display(Markdown("❌ **POST-EMBEDDING checkpoint NOT found** - embedding generation may have failed"))
```

#### Cell 22: Embedding Validation (Python)
```python
display(Markdown("### ✓ Embedding Validation"))

# Extract embedding if available
embedding_data = extract_embedding_from_logs(embedding_logs)

if embedding_data:
    display(HTML(f"""
    <table>
        <tr><td><strong>Dimensions:</strong></td><td>{len(embedding_data)} (should be 1536)</td></tr>
        <tr><td><strong>Type:</strong></td><td>{type(embedding_data).__name__}</td></tr>
        <tr><td><strong>Valid:</strong></td><td>{'✅ Yes' if len(embedding_data) == 1536 else '❌ No'}</td></tr>
        <tr><td><strong>Sample Values:</strong></td><td>{embedding_data[:5]}...</td></tr>
    </table>
    """))
else:
    display(Markdown("❌ **No embedding data found in logs**"))
```

#### Cell 23: Database Query Preparation (Python)
```python
display(Markdown("### 🗄️ Database Query: retrieve_chunks()"))

# Find database query logs
db_logs = find_logs_matching(log_entries, selected_operation_id, pattern="retrieve_chunks|database|query")

if db_logs:
    display(Markdown("✅ **Database query attempted**"))
    display_log_entries(db_logs)
else:
    display(Markdown("❌ **Database query NOT attempted** - embedding generation likely failed"))
```

#### Cell 24: SQL Execution Analysis (Python)
```python
display(Markdown("### 📊 SQL Execution"))

# Extract SQL query if logged
sql_query = extract_sql_from_logs(db_logs)

if sql_query:
    display(Markdown("**Executed SQL:**"))
    display(HTML(f"<pre style='background: #f8f9fa; padding: 10px;'>{sql_query}</pre>"))
    
    # Extract parameters
    params = extract_sql_params(db_logs)
    display(Markdown("**Parameters:**"))
    for key, value in params.items():
        display(Markdown(f"- `{key}`: {value}"))
else:
    display(Markdown("⚠️ SQL query not logged"))
```

#### Cell 25: Vector Similarity Analysis (Python)
```python
display(Markdown("### 🎯 Vector Similarity Calculation"))

# Find similarity calculation logs
similarity_logs = find_logs_matching(log_entries, selected_operation_id, pattern="similarity|distance|<=>")

if similarity_logs:
    display(Markdown("**Similarity Operation:**"))
    display_log_entries(similarity_logs)
    
    # Extract similarity scores if available
    scores = extract_similarity_scores(similarity_logs)
    if scores:
        plot_similarity_distribution(scores)
else:
    display(Markdown("⚠️ No similarity calculation logs found"))
```

#### Cell 26: Database Results (Python)
```python
display(Markdown("### 📥 Database Query Results"))

# Extract query results
db_results = extract_db_results(db_logs)

if db_results is not None:
    display(HTML(f"""
    <div style="padding: 15px; {'background: #d4edda' if db_results > 0 else 'background: #f8d7da'}; border-radius: 5px;">
        <h4>Query Results</h4>
        <p><strong>Rows Returned:</strong> {db_results}</p>
    </div>
    """))
    
    if db_results == 0:
        display(Markdown("**⚠️ Zero rows returned from database!**"))
        display(Markdown("Possible reasons:"))
        display(Markdown("- No chunks in database for this user"))
        display(Markdown("- No chunks have embeddings"))
        display(Markdown("- Similarity scores all below threshold"))
        display(Markdown("- SQL query error"))
else:
    display(Markdown("❌ Cannot determine query results from logs"))
```

#### Cell 27: Threshold Filtering (Python)
```python
display(Markdown("### 🔬 Similarity Threshold Filtering"))

# Analyze threshold application
threshold = operation.similarity_threshold or 0.5

display(HTML(f"""
<table>
    <tr><td><strong>Threshold:</strong></td><td>{threshold}</td></tr>
    <tr><td><strong>Chunks Before Filter:</strong></td><td>{extract_chunks_before_filter(db_logs)}</td></tr>
    <tr><td><strong>Chunks After Filter:</strong></td><td>{operation.chunks_returned}</td></tr>
</table>
"""))

# If threshold filtering is the issue
if extract_chunks_before_filter(db_logs) > 0 and operation.chunks_returned == 0:
    display(Markdown("**⚠️ ISSUE IDENTIFIED: Chunks exist but filtered out by threshold!**"))
```

#### Cell 28: Chunk Processing (Python)
```python
display(Markdown("### 📦 Chunk Processing"))

# Find chunk processing logs
chunk_logs = find_logs_matching(log_entries, selected_operation_id, pattern="chunk|format")

if operation.chunks_returned > 0:
    display(Markdown(f"✅ **{operation.chunks_returned} chunks processed successfully**"))
    display_log_entries(chunk_logs)
else:
    display(Markdown("❌ **No chunks to process** - zero chunks returned"))
```

#### Cell 29: RAG Tool Exit (Python)
```python
display(Markdown("### 🚪 RAG Tool Exit"))

# Find function exit
rag_exit = find_function_exit(function_calls, "retrieve_chunks_from_text")

if rag_exit:
    display(HTML(f"""
    <div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff;">
        <h4>Function Exit</h4>
        <table>
            <tr><td><strong>Duration:</strong></td><td>{rag_exit.duration_ms:.2f}ms</td></tr>
            <tr><td><strong>Chunks Returned:</strong></td><td>{rag_exit.outputs.get('chunks', 0)}</td></tr>
            <tr><td><strong>Status:</strong></td><td>{rag_exit.status}</td></tr>
        </table>
    </div>
    """))
```

#### Cell 30: RAG Operation Complete (Python)
```python
display(Markdown("### ✅ RAG Operation Complete"))

# Find operation completion log
completion = find_logs_matching(log_entries, selected_operation_id, pattern="RAG Operation SUCCESS|RAG Operation FAILED")

if completion:
    display_log_entries(completion)
else:
    display(Markdown("⚠️ No completion log found"))
```

---

### Part 5: Visualization and Analysis (Cells 31-36)

#### Cell 31: Complete Flow Waterfall (Python)
```python
display(Markdown("### 📊 Complete Flow Waterfall Chart"))

# Create waterfall chart showing all steps
fig, ax = plt.subplots(figsize=(15, 10))
plot_waterfall_chart(ax, flow)
plt.title("Complete Execution Waterfall")
plt.show()
```

#### Cell 32: Performance Bottleneck Analysis (Python)
```python
display(Markdown("### ⚡ Performance Bottleneck Analysis"))

# Identify slowest operations
bottlenecks = identify_bottlenecks(function_calls)

display(Markdown("**Top 5 Slowest Operations:**"))
for i, bottleneck in enumerate(bottlenecks[:5], 1):
    display(Markdown(f"{i}. **{bottleneck.name}**: {bottleneck.duration_ms:.2f}ms ({bottleneck.percentage:.1f}% of total)"))

# Visualize
plot_bottleneck_chart(bottlenecks)
```

#### Cell 33: Agent State Transitions (Python)
```python
display(Markdown("### 🔄 Agent State Transitions"))

# Extract agent state changes
state_transitions = extract_agent_states(log_entries, selected_operation_id)

# Create state diagram
plot_state_diagram(state_transitions)
```

#### Cell 34: Error Propagation Analysis (Python)
```python
display(Markdown("### ❌ Error Propagation Analysis"))

# Find all errors
errors = find_logs_matching(log_entries, selected_operation_id, level="ERROR")

if errors:
    display(Markdown(f"**Found {len(errors)} error(s):**"))
    for error in errors:
        display(HTML(f"""
        <div style="padding: 10px; background: #f8d7da; border-radius: 5px; margin: 10px 0;">
            <strong>{error.timestamp}:</strong> {error.message}
        </div>
        """))
        
    # Trace error propagation
    trace_error_propagation(errors, flow)
else:
    display(Markdown("✅ No errors found in logs"))
```

#### Cell 35: Root Cause Analysis (Python)
```python
display(Markdown("### 🎯 Root Cause Analysis"))

# Analyze the complete flow to identify root cause
root_cause = analyze_root_cause(operation, flow, function_calls, checkpoints)

display(HTML(f"""
<div style="padding: 20px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 5px;">
    <h3>Identified Root Cause</h3>
    <p><strong>Issue:</strong> {root_cause.issue}</p>
    <p><strong>Location:</strong> {root_cause.location}</p>
    <p><strong>Evidence:</strong></p>
    <ul>
    {"".join(f"<li>{evidence}</li>" for evidence in root_cause.evidence)}
    </ul>
    <p><strong>Recommended Action:</strong> {root_cause.action}</p>
</div>
"""))
```

#### Cell 36: Comparison with Successful Operations (Python)
```python
display(Markdown("### 🔍 Comparison: Failed vs Successful Operations"))

# If there are successful operations, compare
successful_ops = [op for op in operations.values() if op.success and op.chunks_returned > 0]

if successful_ops:
    # Compare execution patterns
    comparison = compare_operations(operation, successful_ops[0])
    display_comparison_table(comparison)
else:
    display(Markdown("⚠️ No successful operations found for comparison"))
```

---

## Key Analysis Points

For each cell, ensure you:

1. **Show exactly what happened** - Don't assume, parse actual logs
2. **Identify gaps** - If expected logs are missing, flag it
3. **Measure timing** - Track duration of each step
4. **Validate data** - Check if inputs/outputs are correct
5. **Highlight issues** - Use color coding for problems

---

## Expected Outcome

By the end of the notebook, we should know:

- ✅ Exact point where issue occurs
- ✅ Whether embeddings are generated
- ✅ Whether database is queried
- ✅ Why zero chunks are returned
- ✅ Performance bottlenecks
- ✅ Root cause of issue
- ✅ Recommended fix

---

## Implementation Notes

### Log Parsing Functions

You'll need to implement these helper functions:

```python
def parse_log_entries(raw_logs: str) -> List[LogEntry]:
    """Parse raw logs into structured entries"""
    
def extract_operation_id(message: str) -> str:
    """Extract operation ID from log message"""
    
def find_logs_matching(entries: List[LogEntry], operation_id: str, pattern: str) -> List[LogEntry]:
    """Find logs matching a pattern for specific operation"""
    
def extract_function_calls(entries: List[LogEntry], operation_id: str) -> List[FunctionCall]:
    """Extract function calls from logs"""
    
def reconstruct_flow(operation, function_calls, checkpoints) -> OperationFlow:
    """Reconstruct complete execution flow"""
```

### Visualization Functions

```python
def plot_waterfall_chart(ax, flow):
    """Create waterfall chart of execution timeline"""
    
def plot_bottleneck_chart(bottlenecks):
    """Create bar chart of performance bottlenecks"""
    
def plot_state_diagram(state_transitions):
    """Create agent state transition diagram"""
    
def display_flow_diagram(flow):
    """Display ASCII or graphical flow diagram"""
```

---

## Success Criteria

Your notebook is successful if:

- ✅ Can load and parse production logs
- ✅ Can reconstruct complete execution flow
- ✅ Shows every major step with timing
- ✅ Identifies exact failure point
- ✅ Provides clear root cause analysis
- ✅ Recommends specific fixes
- ✅ Visualizations are clear and helpful

---

## References

- **Scope:** `docs/initiatives/debug/fm_038_chat_rag_failures/phase_2b_deep_dive_scope.md`
- **Phase 1 Script:** `tests/fm_038/chat_flow_investigation.py`
- **Agent Handoff:** `tests/fm_038/FM_038_AGENT_HANDOFF.md`
- **RAG Core:** `agents/tooling/rag/core.py`

---

**Next Steps After Completion:**
1. Run notebook on recent failed operations
2. Document findings in Phase 3 analysis
3. Create FRACAS report with root cause
4. Implement corrective actions

---

**Phase:** 2B - Deep Dive Internal Flow Analysis  
**Status:** Ready for Implementation  
**Expected Time:** 4-6 hours  
**Deliverable:** `tests/fm_038/FM_038_Deep_Dive_Notebook.ipynb`

