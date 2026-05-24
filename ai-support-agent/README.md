# 🌸 Bloom Aesthetics — AI Customer Support Agent

A production-style Python AI workflow that handles inbound customer conversations for **Bloom Aesthetics Clinic** across four stages: FAQ answering, lead qualification, escalation detection, and conversation summarisation.

Built with the **Anthropic Claude API**, `pydantic`, `rich`, and clean modular architecture.

---

## Architecture

```
Customer Message
       │
       ▼
┌─────────────────────┐
│  Rule-Based         │  ← Fast keyword scan (no API call)
│  Escalation Check   │    Catches: complaints, angry words, medical keywords
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude API Call    │  ← Full conversation history + SOP in system prompt
│  (claude-sonnet)    │    Returns: response + [CONFIDENCE] + [ESCALATE] + [QUAL]
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Signal Parser      │  ← Extracts structured markers from AI response
│  (escalation.py)    │    Strips markers before showing to customer
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
Escalated?    Continue?
    │             │
    ▼             ▼
Handoff      Next turn
Message      (loop back)
    │
    └──────────────────► End of session → Summary Generator
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `app/main.py` | CLI loop, user I/O, session orchestration |
| `app/agent.py` | Conversation state, API calls, stage management |
| `app/prompts.py` | All prompt templates and system prompt builder |
| `app/sop_loader.py` | Parse SOP JSON → formatted prompt block |
| `app/escalation.py` | Rule-based scanner + AI signal parser |
| `app/qualification.py` | Qualification data tracker |
| `app/summary.py` | End-of-session summary generator |
| `app/models.py` | Pydantic data models |
| `app/utils.py` | Rich CLI formatting, logging, JSON export |

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/ai-support-agent
cd ai-support-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run the interactive chat

```bash
python -m app.main
```

### 4. Run automated demo scenarios

```bash
# Run all 5 demo scenarios
python run_demo.py

# Run a specific scenario
python run_demo.py --scenario 3
```

---

## How to Run

### Interactive Mode (`python -m app.main`)
- Type your message and press Enter
- Type `quit`, `exit`, or `done` to end the session
- A structured summary is generated at the end
- All logs saved to `logs/` directory

### Demo Mode (`python run_demo.py`)
- Runs 5 scripted scenarios without user input
- Each scenario demonstrates a different workflow stage
- Summaries saved as JSON in `logs/`

---

## Example Conversations

### FAQ — Pricing Question
```
You: How much does Botox cost?
Bloom: Botox starts from £200 per area. The exact cost depends on how many areas 
       you'd like treated. We recommend a free consultation for a personalised quote!
       You can book via WhatsApp or our website.
[Stage: faq] [Confidence: 97%]
```

### Escalation — Complaint
```
You: I'm not happy with my treatment at all.
Bloom: I'm really sorry to hear that — that's not the experience we want for you at all...
[Stage: escalated] [Confidence: 80%]

⚠ ESCALATION TRIGGERED
Reason: complaint | Details: Keyword match: 'not happy'
```

### Out-of-Scope
```
You: Do you offer laser hair removal?
Bloom: I'm afraid I don't have that in our current service menu. I don't want to give 
       you incorrect information — please reach out to our team directly via WhatsApp.
[Stage: faq] [Confidence: 45%]
```

---

## Escalation Logic

Escalation is triggered by **two independent layers**:

### Layer 1: Rule-Based Pre-Scan (before API call)
Fast keyword matching against known triggers:
- **Complaint:** "not happy", "terrible", "unacceptable", "complaint"
- **Medical:** "side effect", "allergic", "medication", "pregnant"
- **Pricing negotiation:** "discount", "cheaper", "negotiate"
- **Anger:** "furious", "outraged", "scam", "fraud"
- **Human request:** "speak to a human", "manager", "supervisor"
- **Post-treatment:** "since my botox", "reaction after", "looks wrong"

### Layer 2: AI Signal Parsing (after API call)
The AI embeds `[ESCALATE: reason]` and `[CONFIDENCE: X.XX]` in every response.
- Confidence < 0.60 → auto-escalate with `low_confidence`
- `[ESCALATE: reason]` → escalate with AI-provided reason

### Auto-Escalation
- More than 2 unanswered questions in one session → auto-escalate

### Handoff Message
A warm, empathetic handoff message is delivered based on the escalation reason. The AI never abruptly drops the conversation.

---

## Conversation Stages

```
faq → qualification → escalated
              ↓
           summary → complete
```

| Stage | Description |
|---|---|
| `faq` | Answering customer questions from SOP |
| `qualification` | Collecting lead information (service interest, prior experience, goals) |
| `escalated` | Human handoff triggered — AI delivers handoff message |
| `summary` | Generating end-of-session structured summary |
| `complete` | Session finished |

---

## Logs and Summaries

Every session generates:
- **Log file:** `logs/{session_id}.log` — full timestamped conversation log
- **Summary JSON:** `logs/{session_id}_summary.json` — structured session summary

### Example Summary JSON
```json
{
  "session_id": "session_20250101_143022_a1b2c3d4",
  "customer_intent": "Enquired about lip filler pricing and suitability",
  "stage_reached": "qualification",
  "key_details_collected": {
    "interested_service": "Lip fillers",
    "has_had_treatment_before": false
  },
  "escalation_events": [],
  "sop_gaps": ["Customer asked about case studies for thin lips — not in SOP"],
  "recommended_next_action": "Book free consultation. Flag thin lips concern for practitioner.",
  "total_turns": 4,
  "unanswered_question_count": 1
}
```

---

## Known Limitations

1. **No persistent storage** — conversation history lives in memory only. Sessions are independent.
2. **Single-threaded** — designed for one conversation at a time (CLI). A production system would use async + session management.
3. **English only** — no multilingual support.
4. **SOP coverage** — the AI can only be as good as the SOP data. If the SOP has gaps, the AI will escalate.
5. **Confidence calibration** — the model's self-reported confidence is a proxy, not a ground truth measure.
6. **No WhatsApp/web integration** — CLI only. Would need a messaging API adapter for production.

---

## Future Improvements

- [ ] **WhatsApp integration** via Twilio or Meta Cloud API
- [ ] **RAG-based SOP retrieval** for large SOPs (50+ pages)
- [ ] **Async session management** for concurrent conversations
- [ ] **Human-in-the-loop dashboard** for reviewing escalations
- [ ] **A/B testing framework** for prompt variants
- [ ] **Sentiment trend analysis** across sessions
- [ ] **SOP gap analytics** — aggregate which questions aren't covered
- [ ] **Webhook support** for CRM integration (push qualified leads to HubSpot/Salesforce)
- [ ] **Voice support** via text-to-speech for phone calls
- [ ] **Multi-language** support

---

## Dependencies

```
anthropic>=0.40.0      # Anthropic Claude API client
python-dotenv>=1.0.0   # Environment variable loading
pydantic>=2.0.0        # Data validation and models
rich>=13.0.0           # Beautiful CLI output
```

---

## Project Structure

```
ai-support-agent/
├── app/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── agent.py          # Core conversation orchestrator
│   ├── prompts.py        # All prompt templates
│   ├── sop_loader.py     # SOP JSON parser
│   ├── escalation.py     # Escalation detection
│   ├── qualification.py  # Lead qualification tracker
│   ├── summary.py        # Session summary generator
│   ├── models.py         # Pydantic data models
│   └── utils.py          # Rich CLI + logging helpers
├── data/
│   └── sop.json          # SOP source of truth
├── test_transcripts/
│   ├── in_scope.md
│   ├── out_of_scope.md
│   ├── escalation.md
│   ├── qualification.md
│   └── summary.md
├── logs/                 # Auto-generated session logs
├── .env.example
├── requirements.txt
├── README.md
├── prompt_design.md
└── run_demo.py
```
