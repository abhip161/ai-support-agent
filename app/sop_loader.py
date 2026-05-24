"""
sop_loader.py — Loads and formats SOP data for prompt injection.

Parses the SOP JSON and converts it into a clean, structured
text block that is embedded directly into system prompts.
"""

import json
from pathlib import Path
from typing import Optional


class SOPLoader:
    """
    Loads the SOP JSON file and exposes it in multiple formats:
    - Raw dict (for programmatic checks)
    - Formatted text block (for prompt injection)
    """

    def __init__(self, sop_path: Optional[str] = None):
        if sop_path is None:
            # Default path relative to project root
            sop_path = Path(__file__).parent.parent / "data" / "sop.json"
        self.sop_path = Path(sop_path)
        self._raw: dict = {}
        self._load()

    def _load(self) -> None:
        """Load and parse the SOP JSON file."""
        if not self.sop_path.exists():
            raise FileNotFoundError(f"SOP file not found at: {self.sop_path}")
        with open(self.sop_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)

    @property
    def raw(self) -> dict:
        """Return the raw SOP dict."""
        return self._raw

    def get_business_name(self) -> str:
        return self._raw.get("business", {}).get("name", "Unknown Business")

    def get_escalation_triggers(self) -> list[str]:
        return self._raw.get("escalation_triggers", [])

    def as_prompt_block(self) -> str:
        """
        Format the SOP as a clean text block for injection into prompts.
        This is the single source of truth the AI must operate from.
        """
        d = self._raw
        biz = d.get("business", {})
        hours = d.get("hours", {})
        services = d.get("services", [])
        booking = d.get("booking", {})
        escalation = d.get("escalation_triggers", [])

        lines = [
            f"=== SOP: {biz.get('name', 'N/A')} ===",
            f"Business Type: {biz.get('type', 'N/A')}",
            "",
            "--- OPENING HOURS ---",
        ]

        for day, time in hours.items():
            lines.append(f"  {day.capitalize()}: {time}")

        lines += ["", "--- SERVICES & PRICING ---"]
        for svc in services:
            price = svc.get("price_from", 0)
            currency = svc.get("currency", "GBP")
            unit = svc.get("unit", "")
            price_str = "Free" if price == 0 else f"From {currency_symbol(currency)}{price} {unit}"
            lines.append(f"  • {svc['name']}: {price_str}")
            lines.append(f"    Description: {svc.get('description', '')}")
            if svc.get("notes"):
                lines.append(f"    Notes: {svc['notes']}")

        lines += [
            "",
            "--- BOOKING & CANCELLATION ---",
            f"  Booking channels: {', '.join(booking.get('channels', []))}",
            f"  Cancellation policy: {booking.get('cancellation_policy', 'N/A')}",
        ]

        lines += [
            "",
            "--- ESCALATION TRIGGERS (MUST escalate if any apply) ---",
        ]
        for trigger in escalation:
            lines.append(f"  • {trigger}")

        lines += [
            "",
            "=== END OF SOP ===",
            "CRITICAL: You must ONLY answer from the above SOP data.",
            "If a customer asks something not covered above, do NOT guess.",
            "Instead, acknowledge the gap and escalate to a human agent.",
        ]

        return "\n".join(lines)


def currency_symbol(code: str) -> str:
    """Return the currency symbol for a given ISO code."""
    symbols = {"GBP": "£", "USD": "$", "EUR": "€"}
    return symbols.get(code.upper(), code)
