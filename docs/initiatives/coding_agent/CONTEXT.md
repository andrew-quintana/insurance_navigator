You don't need a novella—just a small, opinionated **"docs contract"** that enforces adjacent-first scoping and dated citations. Below is a drop-in package: filenames, exact contents, and a scaffold script. Paste these into your repo and you've "prescribed" the organization to Cursor and Claude Code.

**⚠️ Important for Tools:** When Cursor or Claude Code need the current date (for updating adjacency.json, inserting yyyy-mm-dd citations, etc.), always run `date +%Y-%m-%d` to get the actual system date. Do not guess or rely on the model's internal understanding of the current date.

# **0) What you're creating**

- A single source of truth for structure: DOCS_[POLICY.md](http://POLICY.md)
- Tool-specific instructions: .cursor/rules.mdc and CLAUDE_CODE_SYSTEM_[PROMPT.md](http://PROMPT.md)
- Lightweight templates: /docs/meta/templates/*
- A minimal seed index + config: ADJACENT_[INDEX.md](http://INDEX.md), adjacency.json, search_config.json
- A one-command scaffolder for new initiatives: scripts/scaffold_[initiative.sh](http://initiative.sh)
- A guard checklist the tools must satisfy: DOCS_READINESS_[CHECKLIST.md](http://CHECKLIST.md)

---

# **1) Repo root docs**

## **/docs/[README.md](http://README.md)**

```markdown
# Documentation Contract

This repository standardizes initiative docs so tools (Cursor, Claude Code) can reliably discover adjacent systems and stay within context budgets.

**Hierarchy**
/docs/

	/initiatives/           # initiative serials (CONTEXTxxx, PRDxxx, RFCxxx, TODOxxx)

	/knowledge/             # cross-initiative knowledge: impl notes, test summaries, tech debt, change logs

	/summaries/rollups/     # 200–400 word per-component rollups

	/meta/                  # templates, indices, adjacency graph, search config

**Principles**
1. Adjacent-first: PRDs/RFCs/TODOs must cite the freshest adjacent rollups + interfaces.
2. Pin contracts: RFCs must include verbatim interface signatures for all integrations.
3. Budgeted context: Prefer rollups; only include code for interface surfaces.

## Isolation Exception
If an initiative is truly isolated, set in [CONTEXTXXX.md](http://CONTEXTXXX.md):

> Isolation: true  
> Isolation_Justification: {1–2 sentences}

CI will skip adjacency freshness & citation checks when `Isolation: true`.
```

## **/docs/DOCS_[POLICY.md](http://POLICY.md)**

```markdown
# Docs Policy (Non-Negotiable)

1) **Required files per initiative** (same serial XXX):
   - docs/initiatives/[CONTEXTXXX.md](http://CONTEXTXXX.md)
   - docs/initiatives/[PRDXXX.md](http://PRDXXX.md)
   - docs/initiatives/[RFCXXX.md](http://RFCXXX.md)
   - docs/initiatives/[TODOXXX.md](http://TODOXXX.md)

2) **Adjacent-first rule**
   - [CONTEXTXXX.md](http://CONTEXTXXX.md) must list 3–7 adjacent components with links to:
     - /summaries/rollups/{component}_[rollup.md](http://rollup.md) (preferred)
     - /knowledge/IMPL_NOTES/{component}/[IMPL.md](http://IMPL.md)
     - /knowledge/TEST_SUMMARIES/{component}/[TESTS.md](http://TESTS.md)
     - /knowledge/TECH_DEBT/{component}/[DEBT.md](http://DEBT.md)

3) **Freshness**
   - If a component's `updated` in `docs/meta/adjacency.json` > 90 days, use its rollup only; do not trust raw notes.

4) **Token budget**
   - Max 20k tokens when drafting PRD/RFC/TODO.
   - Allocation guideline: 40% CONTEXT, 40% rollups, 20% code/test snippets.
   - Overflow → keep interface signatures, drop narrative first.

5) **Readiness gates (must pass before coding)**
   - /docs/knowledge/ADJACENT_[INDEX.md](http://INDEX.md) entry exists for each adjacent component (with last updated date).
   - [RFCXXX.md](http://RFCXXX.md) includes verbatim interface contracts for all integrations.
   - [TODOXXX.md](http://TODOXXX.md) includes "Phase 0 — Context Harvest".
```

## **/docs/DOCS_READINESS_[CHECKLIST.md](http://CHECKLIST.md)**

```markdown
# Docs Readiness Checklist (Gate)

- [ ] CONTEXT lists 3–7 adjacents with rollups + notes + tests + debt
- [ ] All listed adjacents appear in ADJACENT_INDEX with dates
- [ ] adjacency.json has up-to-date `code_roots` and `interfaces`
- [ ] RFC pins verbatim interfaces for all adjacents
- [ ] TODO Phase 0 harvest tasks present and blockers set
- [ ] Token budget noted in CONTEXT (<=20k)
- [ ] PRD/RFC include *dated* citations to ADJACENT_INDEX (yyyy-mm-dd)
- [ ] Isolation flag evaluated (Isolation: true requires justification)
```

---

# **2) Tool-specific prescriptions**

## **/.cursor/rules.mdc**

```
version: 1
policies:
  - name: "Adjacent-First Context Policy"
    description: "Mine adjacent components before drafting PRD/RFC/TODO."
    when:
      file_globs: ["docs/initiatives/*"]
    require:
      - step: "Load indices"
        action: "read"
        paths: ["docs/meta/adjacency.json", "docs/knowledge/ADJACENT_[INDEX.md](http://INDEX.md)"]
      - step: "Load adjacents from CONTEXT"
        action: "read-linked-rollups"
        from: "docs/initiatives/CONTEXT*.md"
        prefer_rollups: true
      - step: "Enforce token budget"
        action: "limit"
        token_budget:
          total: 20000
          allocation: { CONTEXT: 0.40, ROLLUPS: 0.40, CODE_SNIPPETS: 0.20 }
        overflow_strategy: "keep_interfaces_only"
guardrails:
  - name: "NoMegadumps"
    rule: "Reject >400 lines raw code in context unless explicitly requested."
  - name: "CiteAdjacency"
    rule: "PRD/RFC must cite ADJACENT_INDEX rows with dates."
  - name: "Skip-Checks-When-Isolated"
	  rule: "If [CONTEXTXXX.md](http://CONTEXTXXX.md) has 'Isolation: true', allow drafting without adjacency freshness enforcement."
	- name: "Use-System-Date"
    rule: "Always use `date +%Y-%m-%d` command to get current date instead of guessing."
commands:
  - name: "context:interfaces"
    run: |
      jq -r '.components[].code_roots[]' docs/meta/adjacency.json | \
      xargs -I{} rg -n --glob '{}**/*.{ts,tsx,py,go}' -e 'export interface|export type|def [a-zA-Z0-9_]+\(|class [A-Z]' | head -n 300
```

## **/docs/meta/CLAUDE_CODE_SYSTEM_[PROMPT.md](http://PROMPT.md)**

```markdown
You are drafting PRD/RFC/TODO for initiative XXX.

Before writing:
1) Load docs/initiatives/[CONTEXTXXX.md](http://CONTEXTXXX.md), docs/knowledge/ADJACENT_[INDEX.md](http://INDEX.md), docs/meta/adjacency.json.
2) For each adjacent in [CONTEXTXXX.md](http://CONTEXTXXX.md), load /summaries/rollups/{component}_[rollup.md](http://rollup.md); only if missing details, consult IMPL/TESTS/DEBT.
3) Keep total input under 20k tokens (≈40% CONTEXT, 40% rollups, 20% precise signatures/tests). If overflow, keep interface signatures and drop narrative.
4) PRD must include "Adjacent Systems Considered" with citations + last-updated dates.
5) RFC must pin verbatim interface signatures for all integrations.
6) TODO must include "Phase 0 — Context Harvest" and block implementation until complete.
7) If any ADJACENT_INDEX entry is stale (>90d), request a rollup refresh in the output's "Risks / Next Actions".

**IMPORTANT - Date Handling:**
When you need the current date (for updating adjacency.json, inserting dated citations, etc.), always run `date +%Y-%m-%d` to get the actual system date. Do not guess or use your internal understanding of the current date, as models are unreliable about this.
```

---

# **3) Lightweight templates**

## **/docs/meta/templates/[CONTEXT.md](http://CONTEXT.md)**

```markdown
# CONTEXT XXX — {InitiativeName}

## Objective
{Single paragraph: why now, success criteria}

## Scope
- In: …
- Out: …

## Adjacent & Integrating Components
{List 3–7}
- [{Comp} rollup](/docs/summaries/rollups/{Comp}_[rollup.md](http://rollup.md))
- [{Comp} IMPL](/docs/knowledge/IMPL_NOTES/{Comp}/[IMPL.md](http://IMPL.md))
- [{Comp} TESTS](/docs/knowledge/TEST_SUMMARIES/{Comp}/[TESTS.md](http://TESTS.md))
- [{Comp} DEBT](/docs/knowledge/TECH_DEBT/{Comp}/[DEBT.md](http://DEBT.md))

## Interface Contracts to Preserve (verbatim if possible)
- {Signature}
- {Signature}

## Risks & Constraints from Adjacent Systems
- …

## Context Budget
- Max: 20k tokens; 40/40/20 (context/rollups/snippets); overflow → keep signatures.

## Evidence Links
- …

## Deliverables
- [PRDXXX.md](http://PRDXXX.md), [RFCXXX.md](http://RFCXXX.md), [TODOXXX.md](http://TODOXXX.md)

## Isolation
Isolation: false
Isolation_Justification: 
```

## **/docs/meta/templates/[PRD.md](http://PRD.md)**

```markdown
# PRD XXX — {InitiativeName}

## Problem & Goals
…

## Adjacent Systems Considered (with citations + dates)
- {Comp} — last_updated: 2025-08-20 — [rollup] [impl] [tests] [debt]
- Impact on design choices: …

## User Stories & Acceptance Criteria
…

## Metrics / Guardrails
- Backward-compat with {interfaces}, error budget, integration test pass rate.

## Risks / Open Questions
…
```

## **/docs/meta/templates/[RFC.md](http://RFC.md)**

```markdown
# RFC XXX — {InitiativeName}

## Design Overview
…

## Interface Contracts (verbatim)
```