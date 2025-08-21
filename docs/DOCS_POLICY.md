# Docs Policy (Non-Negotiable)

1) **Required files per initiative** (same serial XXX):
   - docs/initiatives/CONTEXTXXX.md
   - docs/initiatives/PRDXXX.md
   - docs/initiatives/RFCXXX.md
   - docs/initiatives/TODOXXX.md

2) **Adjacent-first rule**
   - CONTEXTXXX.md must list 3–7 adjacent components with links to:
     - /summaries/rollups/{component}_rollup.md (preferred)
     - /knowledge/IMPL_NOTES/{component}/IMPL.md
     - /knowledge/TEST_SUMMARIES/{component}/TESTS.md
     - /knowledge/TECH_DEBT/{component}/DEBT.md

3) **Freshness**
   - If a component's `updated` in `docs/meta/adjacency.json` > 90 days, use its rollup only; do not trust raw notes.

4) **Token budget**
   - Max 20k tokens when drafting PRD/RFC/TODO.
   - Allocation guideline: 40% CONTEXT, 40% rollups, 20% code/test snippets.
   - Overflow → keep interface signatures, drop narrative first.

5) **Readiness gates (must pass before coding)**
   - /docs/knowledge/ADJACENT_INDEX.md entry exists for each adjacent component (with last updated date).
   - RFCXXX.md includes verbatim interface contracts for all integrations.
   - TODOXXX.md includes "Phase 0 — Context Harvest".