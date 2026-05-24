# Prompt Design Document

**Project:** Bloom Aesthetics Clinic — AI Customer Support Agent  
**Author:** AI Engineering Internship Assignment  
**Model:** Claude Sonnet (claude-sonnet-4-20250514)

---

## 1. Full System Prompt

```
You are Bloom, a friendly and professional AI customer support assistant for Bloom Aesthetics Clinic.

Your role is to help customers with their enquiries in a warm, professional, and trustworthy manner — the way a knowledgeable receptionist would.

=== YOUR SOP (ONLY SOURCE OF TRUTH) ===
[SOP injected here at runtime from data/sop.json]
...
=== END OF SOP ===
CRITICAL: You must ONLY answer from the above SOP data.
If a customer asks something not covered above, do NOT guess.
Instead, acknowledge the gap and escalate to a human agent.
```

> The full prompt is dynamically constructed in `app/prompts.py:build_system_prompt()`. The SOP block is injected at runtime, meaning prompt changes don't require code changes — only the SOP data file.

---

## 2. Why Each Instruction Exists

### Persona: "You are Bloom, a friendly receptionist"
**Reasoning:** Giving the AI a name and a concrete human analogy (receptionist) sets a strong, consistent tone anchor. "Bloom" aligns with the clinic brand. A named persona is harder to jailbreak than an unnamed assistant because the model identifies with the role.

### "Warm, professional, and trustworthy manner"
**Reasoning:** SMB customers are often apprehensive (especially in aesthetics — it involves their appearance and potential medical risk). Warmth reduces anxiety; professionalism builds trust; trustworthy reminds the model not to oversell or guess.

### SOP Injection as a Block (not summarised)
**Reasoning:** The full SOP is injected verbatim rather than summarised. This is intentional:
- Summarisation risks losing nuances (e.g. "from £200" vs "£200")
- Verbatim injection leaves no room for the model to fill gaps with assumptions
- The block has a clear start (`=== SOP: ... ===`) and end (`=== END OF SOP ===`) marker so the model knows exactly where its truth boundary is

### "CRITICAL: You must ONLY answer from the above SOP data"
**Reasoning:** The word CRITICAL in caps functions as a strong instruction signal in LLMs. The explicit repetition of the boundary ("above SOP data") reduces the chance of the model confabulating.

### British English instruction
**Reasoning:** Bloom Aesthetics is a UK clinic. Using British spelling (colour, organisation, centre) avoids subtle trust erosion from Americanisms. Customers notice when "color" appears in a UK clinic's comms.

---

## 3. Hallucination Prevention Strategy

### Layer 1: Explicit SOP Boundary
The system prompt states three times (in different phrasings) that the model must only answer from the SOP:
1. "Your SOP (ONLY SOURCE OF TRUTH)"
2. "CRITICAL: You must ONLY answer from the above SOP data"
3. "If a customer asks something not covered above, do NOT guess"

Repetition with different wording is a prompt engineering technique to reinforce constraints across paraphrases.

### Layer 2: Confidence Scoring
Every AI response includes `[CONFIDENCE: X.XX]`. The model is instructed to score its own certainty about whether the answer comes from the SOP. Responses with confidence < 0.60 trigger automatic escalation — a safety net that catches hallucinations the rule-based layer misses.

This works because LLMs are reasonably well-calibrated in their uncertainty. When forced to express confidence, they often reveal when they're extrapolating.

### Layer 3: Explicit Failure Mode
The model is told exactly what to say when it doesn't know: `"I don't have that information to hand — let me get one of our team to help you with that."` This eliminates the need for the model to improvise a graceful refusal, which reduces the risk of it trying to help anyway.

### Layer 4: Rule-Based Pre-Scan (Code Layer)
`escalation.py:check_user_input_for_escalation()` scans user input for known sensitive keywords (medical terms, complaint language) **before** the AI responds. This handles obvious cases deterministically, without relying on AI judgement.

### Layer 5: SOP Gap Tracking
Any response with confidence < 0.65 is logged as a SOP gap and surfaced in the end-of-session summary. This creates an improvement loop — human agents can review what the AI couldn't answer and update the SOP.

---

## 4. Confidence-Based Escalation Design

### Why Confidence Scoring?
LLM hallucinations rarely come with a warning. By forcing the model to output a confidence score, we create a parseable signal that the code can act on programmatically.

### Threshold: 0.60
Set through experimentation and reasoning:
- Above 0.90: Model is certain — fully SOP-grounded answer
- 0.70–0.90: Minor uncertainty — still serve, no escalation
- 0.60–0.70: Partial gap — serve but flag
- Below 0.60: High hallucination risk — escalate

This threshold is exposed as a constant (`CONFIDENCE_THRESHOLD = 0.60` in `escalation.py`) for easy tuning.

### Signal Parsing
`parse_ai_response_signals()` uses regex to extract:
- `[CONFIDENCE: X.XX]` — confidence score
- `[ESCALATE: reason]` — explicit escalation flag
- `[QUAL: ...]` — qualification data

After parsing, all signal markers are stripped from the customer-facing message. This means the model can "think out loud" in a structured way without the customer seeing internal signals.

### Dual Escalation Mechanism
```
User message → Rule-based pre-scan → API call → AI response parsing
                       ↓                               ↓
              Keyword match found?          [ESCALATE] or low confidence?
                       ↓                               ↓
                 Escalate now              Escalate + strip markers from message
```

The two-layer approach ensures:
- Obvious triggers (angry keywords) are caught fast and cheaply
- Subtle misalignments (model uncertainty) are caught via AI self-assessment

---

## 5. Tone and Persona Reasoning

### Target Persona: Friendly Clinic Receptionist
**Why this framing?** A clinic receptionist is:
- Warm and approachable (patients are often anxious)
- Knowledgeable but not clinical (not a doctor)
- Boundary-aware (knows when to refer to a clinician)
- Professional without being robotic

This maps precisely to what the AI should do.

### British English
UK SMB customers expect UK spelling. Even minor Americanisms erode trust subtly. The instruction to use British spellings is a small prompt element with outsized brand alignment value.

### "Never argue with customers"
Aesthetics is a trust-sensitive category. Even if a customer is wrong, the AI defending itself would damage the brand. The instruction to de-escalate rather than correct is intentional and consistent with best practices in customer service.

### "Never discuss competitor businesses"
Prevents the AI from making comparative claims that could be inaccurate or create legal risk.

### "Never give medical advice"
Aesthetics treatments have real medical implications. The AI is explicitly prohibited from commenting on medical suitability, side effects, or health interactions. This is a hard safety guardrail, not a soft preference.

---

## 6. Guardrails

| Guardrail | Implementation | Reason |
|---|---|---|
| SOP-only answers | System prompt + confidence scoring | Prevent hallucination |
| No medical advice | System prompt instruction | Safety + legal risk |
| No pricing negotiation | Rule-based keyword + AI instruction | Protect business |
| Angry customer → handoff | Keyword scanner + AI sentiment | Brand protection |
| Post-treatment concern → handoff | Rule-based keyword | Patient safety |
| Max 2 unanswered → handoff | Counter in agent.py | SOP completeness signal |
| No competitor mention | System prompt instruction | Legal + brand |

---

## 7. Failure Handling

### API Failure
If the Claude API call fails (timeout, rate limit, 5xx error), the agent falls back to a safe default message:
```
"I'm sorry, I'm having a technical issue right now. Please contact us directly via WhatsApp..."
```
This response includes `[CONFIDENCE: 0.00][ESCALATE: low_confidence]` so it's logged and triggers escalation automatically.

### JSON Parse Failure (Summary)
If the summary generation returns malformed JSON, `summary.py` catches the exception and returns a safe fallback summary with a manual review flag.

### Missing SOP File
`sop_loader.py` raises a `FileNotFoundError` with a clear message. `main.py` catches this and exits with a helpful error. The app never silently fails with a missing SOP.

### Empty/Null Responses
All response strings are validated before being returned to the user. Empty strings fall through to a safe default.

---

## 8. Tradeoffs and Design Decisions

### Tradeoff 1: Verbatim SOP vs Semantic Retrieval
**Decision:** Verbatim injection into the prompt  
**Alternative:** RAG (Retrieval-Augmented Generation) — vector search over SOP chunks  
**Why verbatim?** The SOP is small (~500 tokens). RAG adds latency, infrastructure complexity, and retrieval errors for no benefit at this scale. If the SOP grows to 50+ pages, RAG becomes necessary.

### Tradeoff 2: Rule-Based vs LLM-Only Escalation
**Decision:** Two-layer (rule-based + LLM signal)  
**Alternative:** LLM-only sentiment detection  
**Why dual?** Rule-based catches obvious triggers deterministically and cheaply (no API call). LLM catches nuanced cases the rules miss. Combining both is safer than either alone.

### Tradeoff 3: Structured Signal Markers in Response
**Decision:** `[CONFIDENCE: X]`, `[ESCALATE: Y]`, `[QUAL: Z]` embedded in AI response  
**Alternative:** Parallel API call for classification; tool use / function calling  
**Why markers?** Simpler to implement, no extra API calls, no latency overhead. The tradeoff is that a very long or poorly formatted response might clip the markers — mitigated by keeping responses concise and parsing with tolerant regex.

### Tradeoff 4: Single-Turn vs Multi-Turn Context
**Decision:** Full conversation history passed on every turn  
**Alternative:** Summarised context to save tokens  
**Why full history?** At SMB scale, conversations are short (5–15 turns). The accuracy benefit of full context outweighs the modest token cost. This ensures the qualification logic and sentiment analysis always have complete context.

---

## 9. Prompt Engineering Principles Applied

| Principle | Application |
|---|---|
| **Role prompting** | "You are Bloom, a friendly receptionist" |
| **Constraint repetition** | SOP boundary stated 3× in different phrasings |
| **Explicit failure mode** | Exact phrasing provided for "I don't know" responses |
| **Structured output** | `[CONFIDENCE]`, `[ESCALATE]`, `[QUAL]` markers |
| **In-context data** | Full SOP injected verbatim (not summarised) |
| **Stage awareness** | Current stage injected into each turn's context |
| **Positive + negative** | "Always maintain warm tone" + "Never argue with customers" |
| **Tone anchoring** | British English, named persona, persona analogy |
| **Threshold-based safety** | Confidence < 0.60 → escalate |
| **Graceful degradation** | Clear fallback messages for every failure mode |
