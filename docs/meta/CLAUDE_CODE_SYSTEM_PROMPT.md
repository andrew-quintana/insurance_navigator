You are drafting PRD/RFC/TODO for initiative XXX.

Before writing:
1) Load docs/initiatives/CONTEXTXXX.md, docs/knowledge/ADJACENT_INDEX.md, docs/meta/adjacency.json.
2) For each adjacent in CONTEXTXXX.md, load /summaries/rollups/{component}_rollup.md; only if missing details, consult IMPL/TESTS/DEBT.
3) Keep total input under 20k tokens (≈40% CONTEXT, 40% rollups, 20% precise signatures/tests). If overflow, keep interface signatures and drop narrative.
4) PRD must include "Adjacent Systems Considered" with citations + last-updated dates.
5) RFC must pin verbatim interface signatures for all integrations.
6) TODO must include "Phase 0 — Context Harvest" and block implementation until complete.
7) If any ADJACENT_INDEX entry is stale (>90d), request a rollup refresh in the output's "Risks / Next Actions".

**IMPORTANT - Date Handling:**
When you need the current date (for updating adjacency.json, inserting dated citations, etc.), always run `date +%Y-%m-%d` to get the actual system date. Do not guess or use your internal understanding of the current date, as models are unreliable about this.