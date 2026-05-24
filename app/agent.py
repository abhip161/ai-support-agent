"""
agent.py — Core AI agent orchestration.

The ConversationAgent class manages:
- Conversation history
- API calls to Claude
- Stage transitions (FAQ → Qualification → Escalated → Summary)
- Escalation detection (rule-based + AI-signal)
- Qualification data accumulation
- SOP gap tracking
"""

import anthropic
from typing import Optional

from app.models import (
    ConversationStage,
    EscalationEvent,
    EscalationReason,
    AgentResponse,
)
from app.sop_loader import SOPLoader
from app.prompts import build_system_prompt, build_escalation_handoff_message
from app.escalation import (
    check_user_input_for_escalation,
    parse_ai_response_signals,
    parse_qualification_data,
)
from app.qualification import QualificationTracker
from app.summary import SummaryGenerator
from app.models import ConversationSummary
from app import utils

import logging


# Maximum unanswered questions before auto-escalation
MAX_UNANSWERED_QUESTIONS = 2


class ConversationAgent:
    """
    Orchestrates the full customer support conversation lifecycle.

    Responsibilities:
    - Maintain conversation history
    - Call Claude API for each response
    - Parse AI signals ([CONFIDENCE], [ESCALATE], [QUAL])
    - Manage stage transitions
    - Track escalation events and SOP gaps
    - Generate end-of-session summary
    """

    def __init__(
        self,
        sop: SOPLoader,
        client: anthropic.Anthropic,
        session_id: str,
        logger: Optional[logging.Logger] = None,
    ):
        self.sop = sop
        self.client = client
        self.session_id = session_id
        self.logger = logger or logging.getLogger(__name__)

        # Build system prompt once
        self.system_prompt = build_system_prompt(sop)

        # Conversation state
        self.history: list[dict] = []  # [{role, content}]
        self.stage = ConversationStage.FAQ
        self.turn_count = 0

        # Tracking
        self.escalation_events: list[EscalationEvent] = []
        self.sop_gaps: list[str] = []
        self.unanswered_count = 0
        self.has_escalated = False

        # Qualification
        self.qual_tracker = QualificationTracker()

        # Summary generator
        self.summary_generator = SummaryGenerator(client)

        self.logger.info(f"Agent initialised for session {session_id}")

    def process_message(self, user_message: str) -> AgentResponse:
        """
        Process a single user message and return the agent's response.

        Flow:
        1. Rule-based pre-scan for escalation triggers
        2. Add message to history
        3. Call Claude API
        4. Parse signals from AI response
        5. Update state
        6. Return AgentResponse
        """
        self.turn_count += 1
        self.logger.info(f"Turn {self.turn_count} | User: {user_message[:100]}")

        # Step 1: Pre-scan for escalation triggers (fast, before API call)
        pre_escalation = check_user_input_for_escalation(user_message)
        if pre_escalation and not self.has_escalated:
            self.logger.warning(f"Pre-scan escalation: {pre_escalation.reason}")
            self.escalation_events.append(pre_escalation)
            self._transition_to_escalated()

        # Step 2: Add user message to history
        self.history.append({"role": "user", "content": user_message})

        # Step 3: Build context-aware prompt and call Claude
        raw_response = self._call_claude()
        self.logger.debug(f"Raw AI response: {raw_response[:200]}")

        # Step 4: Parse signals
        ai_escalation, confidence, clean_message = parse_ai_response_signals(raw_response)
        qual_data = parse_qualification_data(raw_response)

        # Add AI response to history (with signals stripped for cleanliness)
        self.history.append({"role": "assistant", "content": clean_message})

        # Step 5: Process AI-flagged escalation
        if ai_escalation and not self.has_escalated:
            self.logger.warning(f"AI-flagged escalation: {ai_escalation.reason}")
            self.escalation_events.append(ai_escalation)
            self._transition_to_escalated()

        # Track SOP gaps (low confidence responses = gap)
        if confidence < 0.65:
            gap = f"Turn {self.turn_count}: '{user_message[:60]}...'" if len(user_message) > 60 else f"Turn {self.turn_count}: '{user_message}'"
            self.sop_gaps.append(gap)
            self.unanswered_count += 1
            self.logger.info(f"SOP gap recorded. Total unanswered: {self.unanswered_count}")

        # Auto-escalate if too many unanswered questions
        if self.unanswered_count > MAX_UNANSWERED_QUESTIONS and not self.has_escalated:
            event = EscalationEvent(
                reason=EscalationReason.TOO_MANY_UNANSWERED,
                confidence=1.0,
                triggered_by=user_message,
                details=f"{self.unanswered_count} questions could not be answered from SOP",
            )
            self.escalation_events.append(event)
            self._transition_to_escalated()
            self.logger.warning("Auto-escalation: too many unanswered questions")

        # Merge qualification data
        if qual_data:
            self.qual_tracker.merge(qual_data)
            self.logger.info(f"Qualification updated: {qual_data}")

        # Transition to qualification stage after FAQ stage (if not escalated)
        if (
            self.stage == ConversationStage.FAQ
            and not self.has_escalated
            and self.turn_count >= 2
        ):
            self.stage = ConversationStage.QUALIFICATION

        # Build the final response message
        if self.has_escalated and len(self.escalation_events) > 0:
            final_message = build_escalation_handoff_message(
                reason=self.escalation_events[-1].reason.value,
                business_name=self.sop.get_business_name(),
            )
            # Only send the handoff message once
            if self.history[-1]["content"] != final_message:
                self.history.append({"role": "assistant", "content": final_message})
                clean_message = final_message

        return AgentResponse(
            message=clean_message,
            confidence=confidence,
            stage=self.stage,
            should_escalate=self.has_escalated,
            escalation_reason=(
                self.escalation_events[-1].reason if self.escalation_events else None
            ),
            qualification_data_updated=self.qual_tracker.data,
        )

    def generate_summary(self) -> ConversationSummary:
        """Generate and return the end-of-session summary."""
        self.stage = ConversationStage.SUMMARY
        self.logger.info("Generating session summary")

        summary = self.summary_generator.generate(
            session_id=self.session_id,
            conversation_history=self.history,
            qualification_data=self.qual_tracker.as_dict(),
            escalation_events=self.escalation_events,
            sop_gaps=self.sop_gaps,
            stage=self.stage,
            total_turns=self.turn_count,
            unanswered_count=self.unanswered_count,
        )

        self.stage = ConversationStage.COMPLETE
        return summary

    def _call_claude(self) -> str:
        """
        Make the Claude API call with retry-safe logic.
        Returns the raw text response including signal markers.
        """
        # Inject current stage context
        context_note = f"\n\n[Current conversation stage: {self.stage.value} | Turn: {self.turn_count}]"

        # Build messages — inject context note into last user message
        messages = self.history[:-1] + [{
            "role": "user",
            "content": self.history[-1]["content"] + context_note,
        }]

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=self.system_prompt,
                messages=messages,
            )
            return response.content[0].text

        except anthropic.APIStatusError as e:
            self.logger.error(f"Claude API error: {e}")
            return (
                "I'm sorry, I'm having a technical issue right now. "
                "Please contact us directly via WhatsApp and our team will help you straight away. "
                "[CONFIDENCE: 0.00][ESCALATE: low_confidence]"
            )

    def _transition_to_escalated(self) -> None:
        """Mark the conversation as escalated."""
        if not self.has_escalated:
            self.has_escalated = True
            self.stage = ConversationStage.ESCALATED
            self.logger.info(f"Conversation escalated at turn {self.turn_count}")
