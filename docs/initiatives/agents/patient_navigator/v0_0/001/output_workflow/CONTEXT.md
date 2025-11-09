# CONTEXT.md

## 📌 Core Product Context

This feature is an **output communication agent workflow** in the Insurance Navigator chat agent pipeline. Its purpose is to **consolidate information from upstream agent workflows** and present it to users in a warm, emotionally aware, and informative manner.

The workflow receives **structured data and insights** from various specialized agent workflows (benefits analysis, eligibility checks, form assistance, etc.) and transforms this information into cohesive, user-friendly responses that are appropriately toned for the sensitivity of the content.

---

## 🧭 Intended Behavior

- **Consolidate**: Aggregate outputs from multiple upstream agent workflows into coherent responses.
- **Humanize**: Apply warm, empathetic communication style appropriate to insurance/healthcare context.
- **Contextualize**: Present information in clear, actionable formats that users can easily understand.
- **Adapt Tone**: Adjust emotional sensitivity based on content type (e.g., claim denials vs. benefit explanations).

---

## 🎨 Communication Principles

- **Warmth**: Use friendly, supportive language that acknowledges user stress around insurance matters.
- **Clarity**: Break down complex insurance concepts into digestible explanations.
- **Empathy**: Recognize emotional weight of healthcare/insurance decisions and respond appropriately.
- **Actionability**: Always include clear next steps or guidance where applicable.

---

## 🎯 Design Considerations

### Content Types
- **Benefits explanations**: Clear breakdown of coverage details with examples
- **Eligibility results**: Supportive messaging around coverage status
- **Form assistance**: Step-by-step guidance with encouraging tone
- **Claim guidance**: Sensitive handling of potentially stressful situations

### Tone Adaptation
- **Sensitive topics** (denials, limitations): Extra empathy, clear explanations, alternative options
- **Routine information** (general benefits): Friendly, informative, straightforward
- **Complex procedures**: Patient, step-by-step, reassuring

### Integration Points
- Receives structured data from upstream agent workflows
- Has access to:
  - User context and preferences
  - Content sensitivity indicators
  - Communication style guidelines
- Outputs to:
  - Final user interface
  - Conversation history/context

---

## ❓ Open Questions

- How should tone adaptation be configured (rule-based vs. learned)?
- What level of personalization should be applied based on user interaction history?
- How do we maintain consistency across different types of insurance content?
- Should we support multiple communication styles (professional, casual, etc.)?

---

## 🏗️ Workflow Architecture

- **Modular design**: Easy to extend with additional communication styles or content types
- **Agent-based**: Core communication logic wrapped in extensible workflow pattern
- **Configurable**: Tone and style parameters easily adjustable without code changes

---

## MVP Scope

- Basic communication agent with warm, empathetic tone
- Consolidation of simple structured inputs into user-friendly responses
- Workflow wrapper for future extensibility
- Basic tone adaptation for sensitive vs. routine content

---

## 🔮 Future Considerations (Out of Scope)

While the current scope focuses purely on communication enhancement, future phases may consider:
- **Content validation**: Ensuring outputs remain grounded in user data
- **Security enforcement**: Preventing data leakage or unauthorized information disclosure
- **Risk assessment**: Evaluating content appropriateness before user delivery
- **Compliance monitoring**: HIPAA and PHI compliance validation

---

**Next step: move into "Goals and Non-goals." Prompt me when ready.**