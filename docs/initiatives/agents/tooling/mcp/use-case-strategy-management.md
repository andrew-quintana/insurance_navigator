🧭 Strategy Management with MCP

Overview

This module enables real-time and retrospective management of AI decision-making strategies via the Model Context Protocol (MCP). It provides a structured interface for storing, evolving, and evaluating strategies used by agentic AI systems, particularly in regulated or high-stakes domains like insurance, legal assistance, and benefits navigation.

⸻

Use Case

📌 Goal

Enable curators (e.g. internal staff, policy domain experts, pilot operators) to:
	•	View usage statistics for strategies applied by AI agents
	•	Edit and evolve strategies over time
	•	Track performance, feedback, and confidence signals
	•	Curate future improvements and test new versions

⸻

System Components

1. Strategy Definition (MCP Layer)

Each strategy is stored as a structured object in the MCP, containing:
	•	Unique strategy ID
	•	Target user profiles or personas
	•	RAG configuration (retrievers, documents, chunking, expansion)
	•	Action templates or prompting instructions
	•	Versioning metadata

{
  "id": "copay_reduction_v2",
  "applies_to": ["dual_eligible", "low_income"],
  "retrieval_docs": ["medicare_part_d.pdf", "ssa_form_1020.pdf"],
  "action_prompt": "Recommend copay subsidy options based on retrieved eligibility rules.",
  "version": 2,
  "created_by": "curator_admin",
  "created_at": "2025-07-01"
}


⸻

2. Strategy Log (Telemetry)

Each time a strategy is applied, the agent logs:
	•	Strategy ID
	•	User context (anonymized or ID-only)
	•	Timestamp
	•	Agent confidence
	•	Final output or recommended action
	•	Optional intermediate RAG results

{
  "user_id": "user_abc",
  "strategy_id": "copay_reduction_v2",
  "timestamp": "2025-07-24T15:21:00Z",
  "agent_confidence": 0.91,
  "output_action": "Submit SSA-1020 form"
}


⸻

3. Performance Feedback (Delayed/Curated)

As user outcomes emerge, internal curators can log:
	•	Success/failure (binary or graded)
	•	Annotated issues (retrieval gap, user mismatch, missing info)
	•	Freeform notes
	•	Suggestions for revision or forking

{
  "strategy_id": "copay_reduction_v2",
  "user_id": "user_abc",
  "reviewer": "policy_team_member_1",
  "outcome": "success",
  "notes": "User followed the suggested steps and obtained assistance.",
  "suggested_changes": "Include info on phone-based assistance programs."
}


⸻

Dashboard Features

🧩 Strategy List View

Strategy ID	Name	Usage (30d)	Avg Confidence	Success Rate	Last Modified
copay_v2	Co-pay Reduction v2	42	0.78	57%	2025-07-22

	•	Filters by tag, confidence range, review status
	•	Highlights underperforming or unreviewed strategies

⸻

🧪 Strategy Detail View
	•	View/edit JSON definition
	•	See execution logs and usage statistics
	•	Compare versions or fork existing strategy
	•	Add reviewer comments or test variants

⸻

Implementation Notes
	•	Storage via Supabase/Postgres (strategies, strategy_logs, strategy_feedback)
	•	Access controlled by Supabase Auth or Clerk (curator-only)
	•	Integrates directly with LangGraph agent logs or LangChain observability stack
	•	Optional: Use RAG fallback when no matching strategy exists, and log those for future curation

⸻

Future Extensions
	•	Version control with diffs
	•	Retrieval quality visualization (chunk coverage, document match %)
	•	Experiment framework for A/B testing strategies
	•	Auto-suggest strategy improvements via LLM feedback loop