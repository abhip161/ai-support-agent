"""
escalation.py — Escalation detection logic.

Two-layer detection:
1. Rule-based: keyword/pattern scanning on user input (fast, deterministic)
2. AI-signal based: parsing [ESCALATE: reason] and [CONFIDENCE: X] from AI output

This dual approach ensures we never miss an escalation that the AI flags,
and adds a safety net for obvious cases before the AI even responds.
"""

import re
from typing import Optional, Tuple
from app.models import EscalationReason, EscalationEvent


# --- Rule-Based Keyword Triggers ---

ESCALATION_KEYWORD_MAP: dict[EscalationReason, list[str]] = {
    EscalationReason.COMPLAINT: [
        "complaint", "complain", "terrible", "awful", "disgusting",
        "unacceptable", "rubbish", "useless", "awful", "horrible",
        "bad experience", "not happy", "very disappointed",
    ],
    EscalationReason.MEDICAL_QUESTION: [
        "side effect", "allergic", "allergy", "reaction", "swelling",
        "bruising", "infection", "pain", "symptom", "medical condition",
        "medication", "pregnant", "breastfeeding", "blood thinner",
        "health condition", "epilepsy", "diabetes", "autoimmune",
    ],
    EscalationReason.PRICING_NEGOTIATION: [
        "can you do it cheaper", "discount", "deal", "negotiate",
        "lower the price", "reduce the cost", "best price",
        "better price", "match the price", "cheaper than",
    ],
    EscalationReason.ANGRY_SENTIMENT: [
        "furious", "outraged", "livid", "disgusted", "fed up",
        "sick of", "ridiculous", "joke", "scam", "fraud", "liar",
        "useless", "waste of time", "appalling", "shocking",
    ],
    EscalationReason.EXPLICIT_HUMAN_REQUEST: [
        "speak to a human", "speak to a person", "talk to someone",
        "human agent", "real person", "manager", "supervisor",
        "speak to staff", "contact a person",
    ],
    EscalationReason.POST_TREATMENT_CONCERN: [
        "after my treatment", "post treatment", "since the botox",
        "since the filler", "swollen after", "reaction after",
        "not healing", "looks wrong", "gone wrong",
    ],
}

# Confidence threshold below which we escalate
CONFIDENCE_THRESHOLD = 0.60


def check_user_input_for_escalation(user_message: str) -> Optional[EscalationEvent]:
    """
    Rule-based pre-scan of user input.
    Returns an EscalationEvent if a trigger is found, else None.
    Fast path — runs before AI call.
    """
    msg_lower = user_message.lower()

    for reason, keywords in ESCALATION_KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in msg_lower:
                return EscalationEvent(
                    reason=reason,
                    confidence=0.85,  # Rule-based has high confidence
                    triggered_by=user_message,
                    details=f"Keyword match: '{keyword}'",
                )
    return None


def parse_ai_response_signals(ai_response: str) -> Tuple[Optional[EscalationEvent], float, str]:
    """
    Parse the AI's response for:
    1. [ESCALATE: reason] — explicit escalation flag
    2. [CONFIDENCE: X.XX] — confidence score
    3. [QUAL: ...] — qualification data markers

    Returns:
        (escalation_event or None, confidence_score, clean_message)
    """
    escalation_event = None
    confidence = 1.0
    triggered_by_str = ai_response[:100]  # Capture context

    # Parse [ESCALATE: reason]
    escalate_match = re.search(r'\[ESCALATE:\s*([^\]]+)\]', ai_response, re.IGNORECASE)
    if escalate_match:
        raw_reason = escalate_match.group(1).strip().lower().replace(" ", "_")
        try:
            reason_enum = EscalationReason(raw_reason)
        except ValueError:
            reason_enum = EscalationReason.OUT_OF_SCOPE  # Fallback
        escalation_event = EscalationEvent(
            reason=reason_enum,
            confidence=0.90,
            triggered_by=triggered_by_str,
            details=f"AI self-flagged escalation: {raw_reason}",
        )

    # Parse [CONFIDENCE: X.XX]
    conf_match = re.search(r'\[CONFIDENCE:\s*([\d.]+)\]', ai_response, re.IGNORECASE)
    if conf_match:
        try:
            confidence = float(conf_match.group(1))
        except ValueError:
            confidence = 1.0

    # Low confidence triggers escalation (if not already escalated)
    if confidence < CONFIDENCE_THRESHOLD and escalation_event is None:
        escalation_event = EscalationEvent(
            reason=EscalationReason.LOW_CONFIDENCE,
            confidence=1.0 - confidence,
            triggered_by=triggered_by_str,
            details=f"AI confidence score {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}",
        )

    # Strip all signal markers from the message shown to the customer
    clean_message = re.sub(r'\[CONFIDENCE:\s*[\d.]+\]', '', ai_response)
    clean_message = re.sub(r'\[ESCALATE:\s*[^\]]+\]', '', clean_message)
    clean_message = re.sub(r'\[QUAL:\s*[^\]]+\]', '', clean_message)
    clean_message = clean_message.strip()

    return escalation_event, confidence, clean_message


def parse_qualification_data(ai_response: str) -> dict:
    """
    Extract [QUAL: service=X | prior_treatment=yes/no | goal=X] from AI response.
    Returns a dict of parsed qualification data, or empty dict if not present.
    """
    qual_match = re.search(r'\[QUAL:\s*([^\]]+)\]', ai_response, re.IGNORECASE)
    if not qual_match:
        return {}

    raw = qual_match.group(1)
    result = {}

    for part in raw.split("|"):
        part = part.strip()
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()

    return result
