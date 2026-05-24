"""
summary.py — Generates structured end-of-session conversation summaries.

Calls the Claude API with the full conversation history to produce
a clean JSON summary that human agents can act on immediately.
"""

import json
import anthropic
from app.models import ConversationSummary, ConversationStage, QualificationData, EscalationEvent
from app.prompts import build_summary_prompt


class SummaryGenerator:
    """Generates a structured JSON summary of the completed conversation."""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def generate(
        self,
        session_id: str,
        conversation_history: list[dict],
        qualification_data: dict,
        escalation_events: list[EscalationEvent],
        sop_gaps: list[str],
        stage: ConversationStage,
        total_turns: int,
        unanswered_count: int,
    ) -> ConversationSummary:
        """
        Use Claude to generate a structured summary of the conversation.

        Args:
            session_id: Unique identifier for this conversation
            conversation_history: Full message history (role + content)
            qualification_data: Collected qualification answers
            escalation_events: All escalation events that occurred
            sop_gaps: Questions the SOP couldn't answer
            stage: Final stage the conversation reached
            total_turns: Number of turns
            unanswered_count: How many questions were unanswered

        Returns:
            ConversationSummary pydantic object
        """
        prompt = build_summary_prompt(conversation_history, qualification_data, sop_gaps)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text.strip()

            # Strip markdown fences if present
            if raw_text.startswith("```"):
                raw_text = "\n".join(raw_text.split("\n")[1:])
            if raw_text.endswith("```"):
                raw_text = "\n".join(raw_text.split("\n")[:-1])

            summary_dict = json.loads(raw_text)

        except (json.JSONDecodeError, Exception) as e:
            # Graceful fallback if parsing fails
            summary_dict = {
                "customer_intent": "Could not parse summary (JSON error)",
                "sentiment": "unknown",
                "key_details_collected": {},
                "escalation_events": [],
                "sop_gaps": sop_gaps,
                "recommended_next_action": "Review conversation transcript manually",
                "outcome": "incomplete",
            }

        # Build the Pydantic model
        qual_model = QualificationData(**{
            k: v for k, v in qualification_data.items()
            if k in QualificationData.model_fields
        }) if qualification_data else QualificationData()

        return ConversationSummary(
            session_id=session_id,
            customer_intent=summary_dict.get("customer_intent", "Unknown"),
            stage_reached=stage,
            key_details_collected=summary_dict.get("key_details_collected", {}),
            qualification_data=qual_model,
            escalation_events=escalation_events,
            sop_gaps=summary_dict.get("sop_gaps", sop_gaps),
            recommended_next_action=summary_dict.get("recommended_next_action", "Follow up required"),
            total_turns=total_turns,
            unanswered_question_count=unanswered_count,
        )
