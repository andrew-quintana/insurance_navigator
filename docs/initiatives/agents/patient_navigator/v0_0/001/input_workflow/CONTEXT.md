# CONTEXT.md

## Feature Overview
We are building an **Input Processing Workflow** for an agentic AI system that accepts both voice and text input from users, with the goal of translating non-English inputs to English, cleaning/sanitizing them, and then passing the processed result into the core multi-agent workflow.

## Problem Statement
Users may speak or type in various languages, and often in ambiguous or informal ways. We need a lightweight, latency-sensitive mechanism to:
- Accept input (via microphone or text field)
- Auto-detect the language
- Translate to English using ElevenLabs or equivalent
- Apply sanitization logic to disambiguate references, resolve coreference, and clarify user intent
- Pass this cleaned input to downstream agents

## Goals
- Allow users to interact naturally in any supported language
- Provide a clean, structured English prompt to the backend agent
- Achieve low latency (~<5s end-to-end) to preserve responsiveness
- Rely on out-of-the-box ElevenLabs translation where possible
- Optimize for simplicity, MVP-level design

## Non-Goals
- No advanced personalization or fine-tuning of translation models
- No integrated security/throttling features yet (may come in a future config manager)
- Not building a full UX/UI beyond CLI testing during MVP
- No persistence/logging/telemetry at this stage

## Stakeholders
- **Product Owner**: Andrew (self), driving design and testing
- **Developer**: GPT-based coding assistant
- **Test Interface**: CLI via MacBook microphone
- **Future User**: End users with varied languages and input styles (later milestone)

## Functional Requirements
- Voice input captured from system microphone (initially via CLI)
- Text input supported as alternative
- Language detection and translation to English (using ElevenLabs v3 or fallback to Flash v2.5 for cost)
- Basic intent-sanitization pass
- Pass structured output to next agent
- Model switching logic based on language (for cost optimization)

## Non-Functional Requirements
- ~<5s total latency per interaction
- MVP must be deployable on Vercel/Render setup with minimal cost
- Workflow should have reliable fallback behavior if translation fails

## Constraints
- Time: MVP must be built in a few hours (lean, testable version)
- Cost: Free-tier ElevenLabs or similar tools only
- Tech: CLI testing only for now; browser or production-ready integration is out-of-scope

## Milestones & Review Criteria
- **Phase 1**: Build and test basic multilingual input → translation → sanitization → output path via CLI. (No fallback handling yet.)
- **Phase 2**: Add fallback routing and error messaging for cases when translation or processing fails.
- **Review Criteria**:
  - Functionality matches user scenarios
  - CLI tests demonstrate successful round-trips
  - Output is reliably clean, English-only, and structurally consistent

## Edge Cases
- Unsupported or ambiguous languages
- Mixed-language utterances
- Long or rambling voice input that exceeds model limits
- Silent or invalid mic input
- Input that fails translation (garbled, too short, unrecognized dialect)

## Integration Points
- ElevenLabs for translation
- Future integration with chat orchestration workflow
- Optional fallback agent for low-confidence sanitization

## Open Questions
- What threshold should trigger fallback routing? Let's enable 2 retries of rephrasing before 
- Should sanitization rephrase in the user's voice or prioritize formal clarity?
- What’s the boundary between clarification and intent re-writing?