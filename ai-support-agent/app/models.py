"""
models.py — Pydantic data models for the AI support agent.

Defines all structured data contracts used across the system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class EscalationReason(str, Enum):
    """Enum of all possible escalation reasons."""
    COMPLAINT = "complaint"
    MEDICAL_QUESTION = "medical_question"
    PRICING_NEGOTIATION = "pricing_negotiation"
    TOO_MANY_UNANSWERED = "too_many_unanswered_questions"
    ANGRY_SENTIMENT = "angry_sentiment"
    EXPLICIT_HUMAN_REQUEST = "explicit_human_request"
    LOW_CONFIDENCE = "low_confidence"
    OUT_OF_SCOPE = "out_of_scope"
    POST_TREATMENT_CONCERN = "post_treatment_concern"


class ConversationStage(str, Enum):
    """Tracks the current stage of the conversation flow."""
    FAQ = "faq"
    QUALIFICATION = "qualification"
    ESCALATED = "escalated"
    SUMMARY = "summary"
    COMPLETE = "complete"


class Message(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str


class QualificationData(BaseModel):
    """Stores lead qualification answers."""
    interested_service: Optional[str] = None
    has_had_treatment_before: Optional[bool] = None
    has_had_consultation: Optional[bool] = None
    preferred_contact_method: Optional[str] = None
    any_medical_conditions_declared: Optional[bool] = None
    additional_notes: Optional[str] = None


class EscalationEvent(BaseModel):
    """Represents a detected escalation event."""
    reason: EscalationReason
    confidence: float = Field(ge=0.0, le=1.0)
    triggered_by: str  # The user message that caused it
    details: Optional[str] = None


class ConversationSummary(BaseModel):
    """Structured end-of-session summary."""
    session_id: str
    customer_intent: str
    stage_reached: ConversationStage
    key_details_collected: dict
    qualification_data: QualificationData
    escalation_events: List[EscalationEvent]
    sop_gaps: List[str]  # Questions the SOP couldn't answer
    recommended_next_action: str
    total_turns: int
    unanswered_question_count: int


class AgentResponse(BaseModel):
    """The agent's structured response for each turn."""
    message: str
    confidence: float = Field(ge=0.0, le=1.0, description="How confident the agent is in this response")
    stage: ConversationStage
    should_escalate: bool
    escalation_reason: Optional[EscalationReason] = None
    qualification_data_updated: Optional[QualificationData] = None
