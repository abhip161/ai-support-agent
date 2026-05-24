"""
qualification.py — Lead qualification state management.

Tracks which qualification questions have been asked and answered,
and merges AI-extracted data into the running QualificationData model.
"""

from app.models import QualificationData


class QualificationTracker:
    """
    Manages the state of the lead qualification flow.
    Merges incremental data from each AI turn into a single QualificationData object.
    """

    def __init__(self):
        self.data = QualificationData()
        self.questions_asked: list[str] = []
        self.is_complete = False

    def merge(self, parsed_qual: dict) -> None:
        """
        Merge parsed qualification data from an AI response into the tracker.

        Args:
            parsed_qual: Dict from escalation.parse_qualification_data()
        """
        if not parsed_qual:
            return

        if "service" in parsed_qual and parsed_qual["service"] not in ("X", "unknown", ""):
            self.data.interested_service = parsed_qual["service"]

        if "prior_treatment" in parsed_qual:
            val = parsed_qual["prior_treatment"].lower()
            if val == "yes":
                self.data.has_had_treatment_before = True
            elif val == "no":
                self.data.has_had_treatment_before = False

        if "goal" in parsed_qual and parsed_qual["goal"] not in ("X", "unknown", ""):
            self.data.additional_notes = parsed_qual["goal"]

    def as_dict(self) -> dict:
        """Return qualification data as a plain dict (for summary generation)."""
        return {
            k: v
            for k, v in self.data.model_dump().items()
            if v is not None
        }

    def has_enough_data(self) -> bool:
        """
        Returns True if we have collected enough to qualify the lead.
        Minimum: we know what service they're interested in.
        """
        return self.data.interested_service is not None
