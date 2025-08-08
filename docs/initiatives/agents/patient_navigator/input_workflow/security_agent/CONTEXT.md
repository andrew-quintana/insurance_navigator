# CONTEXT.md

## 📌 Feature Name
Security Agent – Prompt Injection Flagging (MVP)

---

## 🧭 Core Product Context

This agent is part of the **Accessa Insurance Navigator** system. It operates within the **input processing workflow**, sitting between the initial user message and the downstream agents.

**Purpose:**  
To detect prompt injection attempts in user input **before** they’re passed into sensitive system prompts or LLM contexts. This should act as a prompt injection classifier.

**Trigger:**  
Runs automatically after each user sends a message via chat UI.

**Integration Point:**  
Immediately after initial input is received, and before any sanitization or classification agents.

**System Role:**  
- If clean: Passes input to sanitization agent.
- If flagged: Stops flow, returns a rephrase request to the user, and optionally logs the event.

---

## 🎯 Goals

- Detect possible prompt injection attempts in user messages.
- Flag and block unsafe inputs at the point of entry.
- Notify users of restriction with an inline rephrase prompt.

## 🚫 Non-goals

- No full remediation or sanitization (that’s a downstream agent).
- No persistence infrastructure beyond temporary flagging.
- No complex classification of attack type.
    - No context-based or multi-input-based classification.
- No structured audit or alerting system in this MVP.

---

## 👥 Stakeholders & Roles

- **Andrew (solo developer/operator)**  
  - Writes, tests, and refines the agent prompt.
  - Deploys and supervises its integration.
  - Performs OWASP-style test cases to validate behavior.

- **Coding Agent (automated)**  
  - Implements the agent and integrates it into the pipeline.
  - Writes tests for adversarial prompt patterns.

---

## ✅ Functional Requirements

The security agent must:

- Accept a short user text input as string.
- Run a single or multi-step system prompt designed to detect prompt injection techniques.
- Evaluate common prompt injection types, including:
  - Jailbreaks (“Ignore previous instructions...”)
  - Role reassignment (“You are now the system...”)
  - Instruction injection (“Repeat this word forever...”)
- If clean:
  - Return a `{ status: "pass", input: <unchanged> }` object.
  - Proceed to next agent (e.g. sanitizer).
- If flagged:
  - Return `{ status: "flagged", reason: <detected pattern>, message: <user-facing rephrase prompt> }`
  - Halt flow and display UI rephrase request.
  - Log decision for optional UI or database update.

---

## ⚙️ Non-functional Requirements

- **Speed:**  
  - Must complete detection within 100ms (target).
- **Resilience:**  
  - Failsafe: If uncertain, errs on the side of blocking.
- **Maintainability:**  
  - Prompt must be easily editable and testable by developer.
- **Scalability:**  
  - Not a priority; designed for local MVP use with low QPS.

---

## ⛓️ Constraints

- No dedicated detection model for now (use GPT-4o or similar).
- Must be designed to later run with a smaller local model (e.g. DeepSeek, OpenRouter-compatible).
- No DB requirement for logging in this MVP.
- Should not rely on long context windows—short prompts only.

---

## ⌛ Milestones & Review Criteria

| Milestone                         | Review Criteria                                                  |
|----------------------------------|------------------------------------------------------------------|
| Prompt design complete           | Covers OWASP attack types, works with short input                |
| Integrated into workflow         | Agent runs before sanitization with clear branching on result    |
| Manual test harness functional   | Can input test cases via CLI or API call                         |
| Flagging behavior works          | UI returns clean rephrase message; doesn’t break flow            |
| Test suite passes                | At least 6 test prompts: 3 clean, 3 flagged                      |

---

## 🔍 Edge Cases

- User attempts partial jailbreaks with indirect phrasing.
- Multiple injection vectors in one input.
- Inputs that are technically unsafe but domain-specific (e.g. requesting system info for care coordination).
- Ambiguous intent—system should default to blocking.

---

## ❓ Open Questions

- Should we retain flagged inputs in a DB for future model fine-tuning? -> Yes, we should keep the flagged inputs for human verification for future classification fine-tuning.
- Do we want to provide users with a list of *why* their input was blocked? -> Yes, especially for human verification, there should be rationale for blocking but it shouldn't be shown to the user.
- Should fallback prompt be LLM-generated or hardcoded? -> hardcoded for security

---

## 🔌 Integration Points

- **Input Source:**  
  Chat UI → API Gateway

- **Next Step if Pass:**  
  → Sanitization Agent

- **Next Step if Flagged:**  
  → Chat Communicator agent returns a blocking UI prompt

---

## 📦 Output Format (Expected)

```json
{
  "status": "pass" | "flagged",
  "reason": "..." | null,
  "input": "original user text",
  "message": "rephrase request to user"
}