# 🚣️ Product Roadmap: Strategy Evaluation & Validation System (Web-First MVP)

---

## ✅ **MVP Phase: Simplified MCP + Strategy Creation + Regulatory Check + Lightweight Memory**

### 🌟 Goal:

Enable real-time creation and validation of healthcare access strategies based on user plan constraints — no database, no memory, minimal agents. This represents one self-contained workflow within a larger agentic system.

### ✅ Key Capabilities:

Includes optional lightweight memory for storing and reusing strategies across sessions.

| Component            | Description                                                                                                                                                                                                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StrategyMCP`        | Takes plan-specific constraints (copay, deductible, network access) already extracted and stored as metadata in a table, and uses them to form targeted web search queries and to retrieve relevant strategies from memory using a RAG-style plugin. |
| `StrategyCreator`    | Agent that uses retrieved context to propose strategies optimizing for speed, cost, or quality.                                                                                                                                                      |
| `RegulatoryAgent`    | ReAct agent that uses RAG and live web access to validate strategies against legality, feasibility, and ethical guidelines.                                                                                                                          |
| `StrategyMemoryLite` | Stores strategy text, scores (LLM + optional manual), constraints, and validation outcome in both a metadata table and a vector store — supports reuse, filtering, and semantic retrieval during evaluation.                                         |

---

## 🔄 **Phase 2: Modular Orchestration & Light Memory**

### 🌟 Goal:

Decompose agent roles into a **LangGraph or ReAct pipeline** and introduce **light in-memory caching** for reuse.

| Component                    | Description                                                            |
| ---------------------------- | ---------------------------------------------------------------------- |
| `LangGraph Orchestrator`     | Nodes for: Query → Retrieve → Extract → Evaluate → Validate            |
| `EvalTraceViewer`            | Logs full prompt/reasoning chain for each strategy                     |
| `In-Memory Strategy Cache`   | Holds previous results in session (e.g. using `Chroma` or in-RAM dict) |
| `Evaluation Template Schema` | Standard format for strategy evaluation (cost, speed, quality, flags)  |
| `Basic Reranker`             | Orders strategies by match to user's chosen priority                   |

---

## 🧠 **Phase 3: Personalization + Strategy Memory**

### 🌟 Goal:

Introduce persistent memory of validated strategies and allow personalized retrieval and generation.

| Component             | Description                                                             |
| --------------------- | ----------------------------------------------------------------------- |
| `StrategyMemory (DB)` | Stores evaluated strategies + validation trace                          |
| `StrategyMatcher`     | Retrieves past strategies relevant to user’s insurance plan, priorities |
| `FallbackGenerator`   | LLM can simulate novel strategies if retrieval fails                    |
| `Search Explainer`    | Shows how queries were formed from insurance constraints                |

---

## 🔒 **Phase 4: Validation Feedback Loops + Reliability Controls**

### 🌟 Goal:

Add feedback-driven refinement, hallucination checks, and human-in-the-loop controls.

| Component                     | Description                                                      |
| ----------------------------- | ---------------------------------------------------------------- |
| `Validation Confidence Agent` | Flags uncertain or unverifiable claims                           |
| `Human-in-the-Loop Reviewer`  | Admin interface to approve/reject evals                          |
| `Auto-Revision Agent`         | Revises flagged strategies to improve feasibility or correctness |
| `Performance Tracker`         | Logs success/failure rates of strategies across contexts         |
