"""
main.py — CLI entry point for the Bloom Aesthetics AI Support Agent.

Orchestrates the conversation loop using the ConversationAgent.
Handles user input, displays rich-formatted output, and generates
the end-of-session summary.
"""

import os
import sys
from dotenv import load_dotenv
import anthropic
from rich.console import Console

from app.agent import ConversationAgent
from app.sop_loader import SOPLoader
from app import utils

# Load environment variables from .env
load_dotenv()

console = Console()


def main():
    """Run the interactive CLI conversation loop."""

    # --- Initialisation ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found in environment.")
        console.print("Please copy [bold].env.example[/bold] to [bold].env[/bold] and add your API key.")
        sys.exit(1)

    # Load SOP
    try:
        sop = SOPLoader()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    # Generate session ID and set up logger
    session_id = utils.generate_session_id()
    logger = utils.setup_logger(session_id)
    logger.info(f"New session started: {session_id}")

    # Initialise Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Initialise agent
    agent = ConversationAgent(
        sop=sop,
        client=client,
        session_id=session_id,
        logger=logger,
    )

    # --- Welcome ---
    utils.print_welcome_banner(sop.get_business_name())

    # --- Conversation Loop ---
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session interrupted.[/dim]")
            break

        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ("quit", "exit", "bye", "done"):
            console.print()
            console.print("[dim]Ending session and generating summary...[/dim]\n")
            break

        # Process message
        utils.print_user_message(user_input)

        response = agent.process_message(user_input)

        # Display response
        utils.print_agent_message(
            message=response.message,
            confidence=response.confidence,
            stage=response.stage.value,
        )

        # Show escalation alert if triggered
        if response.should_escalate and agent.escalation_events:
            latest_event = agent.escalation_events[-1]
            utils.print_escalation_alert(latest_event)
            logger.warning(f"Escalation displayed: {latest_event.reason.value}")

            # After escalation, ask if they want to continue or end
            console.print("[dim]The conversation has been escalated. Type [bold]quit[/bold] to end and see the summary, or continue chatting.[/dim]\n")

    # --- End of Session: Generate Summary ---
    if agent.turn_count > 0:
        summary = agent.generate_summary()
        utils.print_summary(summary)

        # Save JSON summary
        json_path = utils.save_summary_json(summary)
        console.print(f"\n[dim]Summary saved to: [bold]{json_path}[/bold][/dim]")
        logger.info(f"Session complete. Summary saved to {json_path}")
    else:
        console.print("[dim]No messages exchanged. Goodbye![/dim]")


if __name__ == "__main__":
    main()
