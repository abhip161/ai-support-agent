"""
run_demo.py — Scripted demo runner for the Bloom Aesthetics AI Support Agent.

Runs pre-defined conversation scenarios to demonstrate all four workflow stages:
1. FAQ answering (in-SOP)
2. Out-of-scope handling
3. Escalation detection
4. Lead qualification
5. Conversation summary

No user input required — runs fully automated.
Usage: python run_demo.py [--scenario N]
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv
import anthropic
from rich.console import Console
from rich.rule import Rule

from app.agent import ConversationAgent
from app.sop_loader import SOPLoader
from app import utils

load_dotenv()
console = Console()

# --- Pre-defined Demo Scenarios ---

SCENARIOS = {
    1: {
        "name": "📋 In-SOP Pricing Question",
        "description": "Customer asks about Botox pricing — answered from SOP.",
        "messages": [
            "Hi there! I was wondering how much Botox costs?",
            "And what about lip fillers?",
            "Do I need to book a consultation first?",
        ],
    },
    2: {
        "name": "🔎 Out-of-Scope Question",
        "description": "Customer asks something not covered by the SOP.",
        "messages": [
            "Hello, do you offer laser hair removal?",
            "What about chemical peels?",
            "Do you have any treatments for acne scars?",
        ],
    },
    3: {
        "name": "⚠️  Angry Customer Escalation",
        "description": "Customer expresses frustration and triggers escalation.",
        "messages": [
            "I had a filler treatment last week and I'm not happy at all.",
            "The results are terrible and this is completely unacceptable.",
            "I want to speak to a manager immediately.",
        ],
    },
    4: {
        "name": "✅ Lead Qualification Flow",
        "description": "Customer expresses interest and is qualified through structured questions.",
        "messages": [
            "Hi! I've been thinking about getting Botox for a while.",
            "I'm interested in the forehead area mainly.",
            "No, I've never had it done before — I'm a bit nervous to be honest.",
            "I just want to look a bit fresher, not change my face completely.",
        ],
    },
    5: {
        "name": "📊 Conversation Summary Demo",
        "description": "A mixed conversation that ends with a structured summary.",
        "messages": [
            "Hey, what are your opening hours?",
            "Great. And how much is a consultation?",
            "I'm interested in fillers for my lips.",
            "Have you done lip fillers on people with thin lips?",
        ],
    },
}


def run_scenario(scenario_id: int, client: anthropic.Anthropic, sop: SOPLoader) -> None:
    """Run a single scripted scenario."""
    scenario = SCENARIOS[scenario_id]

    console.print()
    console.print(Rule(f"[bold pink1]Scenario {scenario_id}: {scenario['name']}[/bold pink1]", style="pink1"))
    console.print(f"[dim]{scenario['description']}[/dim]")
    console.print()

    session_id = utils.generate_session_id()
    logger = utils.setup_logger(session_id)

    agent = ConversationAgent(
        sop=sop,
        client=client,
        session_id=session_id,
        logger=logger,
    )

    for user_message in scenario["messages"]:
        console.print(f"[bold cyan]Customer:[/bold cyan] {user_message}")
        console.print()

        response = agent.process_message(user_message)

        utils.print_agent_message(
            message=response.message,
            confidence=response.confidence,
            stage=response.stage.value,
        )

        if response.should_escalate and agent.escalation_events:
            utils.print_escalation_alert(agent.escalation_events[-1])

        time.sleep(0.5)  # Brief pause between turns for readability

    # Generate and display summary
    console.print("[dim]Generating session summary...[/dim]\n")
    summary = agent.generate_summary()
    utils.print_summary(summary)

    json_path = utils.save_summary_json(summary)
    console.print(f"[dim]Summary saved → [bold]{json_path}[/bold][/dim]\n")


def main():
    parser = argparse.ArgumentParser(description="Run demo scenarios for the Bloom AI Support Agent")
    parser.add_argument(
        "--scenario",
        type=int,
        choices=list(SCENARIOS.keys()),
        help="Run a specific scenario (1-5). Omit to run all.",
    )
    args = parser.parse_args()

    # --- Setup ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set. Add it to .env")
        sys.exit(1)

    sop = SOPLoader()
    client = anthropic.Anthropic(api_key=api_key)

    utils.print_welcome_banner(sop.get_business_name())
    console.print("[bold]Running demo scenarios...[/bold]\n")

    if args.scenario:
        run_scenario(args.scenario, client, sop)
    else:
        for scenario_id in SCENARIOS:
            run_scenario(scenario_id, client, sop)
            console.print()
            time.sleep(1)

    console.print(Rule("[bold pink1]Demo Complete[/bold pink1]", style="pink1"))


if __name__ == "__main__":
    main()
