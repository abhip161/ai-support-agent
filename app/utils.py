"""
utils.py — Shared utility functions for the AI support agent.

Includes:
- Session ID generation
- Logging helpers
- JSON formatting
- Rich console helpers
"""

import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from app.models import ConversationSummary, EscalationEvent


console = Console()


def generate_session_id() -> str:
    """Generate a unique session ID for this conversation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{short_uuid}"


def setup_logger(session_id: str, log_dir: str = "logs") -> logging.Logger:
    """
    Set up a file-based logger for this session.
    Logs are written to logs/{session_id}.log
    """
    Path(log_dir).mkdir(exist_ok=True)
    log_path = Path(log_dir) / f"{session_id}.log"

    logger = logging.getLogger(session_id)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def print_welcome_banner(business_name: str) -> None:
    """Print a styled welcome banner to the console."""
    console.print()
    console.print(Panel(
        f"[bold pink1]🌸 {business_name} — AI Support Assistant[/bold pink1]\n"
        "[dim]Type your message and press Enter. Type [bold]quit[/bold] or [bold]exit[/bold] to end the session.[/dim]",
        border_style="pink1",
        padding=(1, 2),
    ))
    console.print()


def print_user_message(message: str) -> None:
    """Print the user's message with styling."""
    console.print(f"[bold cyan]You:[/bold cyan] {message}")
    console.print()


def print_agent_message(message: str, confidence: float, stage: str) -> None:
    """Print the agent's response with confidence indicator."""
    conf_color = _confidence_color(confidence)
    stage_label = f"[dim][Stage: {stage}][/dim]"
    conf_label = f"[{conf_color}][Confidence: {confidence:.0%}][/{conf_color}]"

    console.print(f"[bold pink1]Bloom:[/bold pink1] {message}")
    console.print(f"  {stage_label}  {conf_label}")
    console.print()


def print_escalation_alert(event: EscalationEvent) -> None:
    """Print a highlighted escalation alert box."""
    console.print(Panel(
        f"[bold red]⚠ ESCALATION TRIGGERED[/bold red]\n"
        f"Reason: [yellow]{event.reason.value}[/yellow]\n"
        f"Details: {event.details or 'N/A'}\n"
        f"Confidence: {event.confidence:.0%}",
        border_style="red",
        title="[bold red]Human Handoff Required[/bold red]",
        padding=(0, 1),
    ))
    console.print()


def print_summary(summary: ConversationSummary) -> None:
    """Print the end-of-session summary as a rich formatted panel."""
    console.rule("[bold pink1]Session Summary[/bold pink1]")

    # Main summary table
    table = Table(box=box.ROUNDED, border_style="pink1", show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold dim", width=28)
    table.add_column("Value")

    table.add_row("Session ID", summary.session_id)
    table.add_row("Customer Intent", summary.customer_intent)
    table.add_row("Stage Reached", summary.stage_reached.value)
    table.add_row("Total Turns", str(summary.total_turns))
    table.add_row("Unanswered Questions", str(summary.unanswered_question_count))
    table.add_row("Recommended Next Action", summary.recommended_next_action)

    console.print(table)

    # Qualification data
    if summary.qualification_data:
        qual_dict = summary.qualification_data.model_dump(exclude_none=True)
        if qual_dict:
            console.print("\n[bold]Qualification Data Collected:[/bold]")
            for k, v in qual_dict.items():
                console.print(f"  • {k}: [cyan]{v}[/cyan]")

    # Escalation events
    if summary.escalation_events:
        console.print("\n[bold red]Escalation Events:[/bold red]")
        for ev in summary.escalation_events:
            console.print(f"  • {ev.reason.value}: {ev.details or 'N/A'}")

    # SOP gaps
    if summary.sop_gaps:
        console.print("\n[bold yellow]SOP Gaps (questions not in SOP):[/bold yellow]")
        for gap in summary.sop_gaps:
            console.print(f"  • {gap}")

    console.rule()


def save_summary_json(summary: ConversationSummary, output_dir: str = "logs") -> str:
    """
    Save the conversation summary as a JSON file.
    Returns the file path.
    """
    Path(output_dir).mkdir(exist_ok=True)
    output_path = Path(output_dir) / f"{summary.session_id}_summary.json"

    # Convert to JSON-serializable dict
    summary_dict = json.loads(summary.model_dump_json())

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2, default=str)

    return str(output_path)


def _confidence_color(confidence: float) -> str:
    """Return a Rich color name based on confidence level."""
    if confidence >= 0.85:
        return "green"
    elif confidence >= 0.65:
        return "yellow"
    else:
        return "red"
