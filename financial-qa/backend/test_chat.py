"""
Interactive end-to-end test for the query understanding agent and classifier.

Simulates the full /api/chat flow in the terminal — no HTTP server needed.
Conversation continues until the agent is confident enough to route, then
prints the final market answer or the refined knowledge query.

Run from the backend/ directory:
    python test_chat.py
"""

import sys
import os
import asyncio
import warnings
warnings.filterwarnings("ignore", message="Timestamp.utcnow is deprecated", category=FutureWarning)

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from agents.understanding_agent import handle_chat

SUMMARIZE_THRESHOLD = 12  # mirror the value in routers/chat.py

GREETING = """
╔══════════════════════════════════════════════════════════════╗
║           Financial Asset Q&A System                        ║
║                                                              ║
║  I can help you with two things:                             ║
║  • Live market data  — prices, metrics, news for any stock  ║
║  • Financial concepts — explain terms, how things work      ║
║                                                              ║
║  You don't need to know the ticker symbol — just describe   ║
║  the company or topic and I'll figure it out.               ║
║                                                              ║
║  Type  'quit' or 'exit' to end the session.                 ║
╚══════════════════════════════════════════════════════════════╝
"""

DIVIDER = "─" * 64


def print_system(label: str, text: str):
    print(f"\n\033[96m[{label}]\033[0m {text}\n")


def print_user(text: str):
    print(f"\033[93m[YOU]\033[0m {text}")


def print_answer(answer: str, query_type: str, ticker: str | None, refined: str | None):
    print(f"\n{DIVIDER}")
    print(f"\033[92m[ROUTED → {query_type.upper()}]\033[0m", end="")
    if ticker:
        print(f"  ticker: \033[1m{ticker}\033[0m", end="")
    if refined:
        print(f"\n\033[90mrefined question: {refined}\033[0m", end="")
    print(f"\n{DIVIDER}")
    print(answer)
    print(DIVIDER)


async def maybe_summarize(
    history: list[dict],
    history_summary: str | None,
) -> tuple[list[dict], str | None]:
    """
    If history exceeds the threshold, compress the older half using Haiku
    (mirrors the /api/summarize-history endpoint logic directly).
    Returns (trimmed_history, updated_summary).
    """
    if len(history) <= SUMMARIZE_THRESHOLD:
        return history, history_summary

    # Keep the last 6 messages verbatim; compress the rest
    to_compress = history[:-6]
    recent = history[-6:]

    from dotenv import load_dotenv
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in to_compress
    )
    # Prepend any existing summary so we accumulate, not overwrite
    if history_summary:
        history_text = f"[Prior summary: {history_summary}]\n\n" + history_text

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=(
            "Summarize the following conversation concisely (3-5 sentences). "
            "Preserve: what the user is trying to find out, any companies or tickers "
            "mentioned, and what has already been clarified. Write in third person."
        ),
        messages=[{"role": "user", "content": history_text}],
    )

    new_summary = response.content[0].text.strip()
    print_system("SYSTEM", f"History compressed. Summary: {new_summary}")
    return recent, new_summary


async def run():
    print(GREETING)

    # Opening line from the system to start the conversation
    opening = (
        "Hello! What would you like to know today? "
        "You can ask about a specific stock's performance, or ask me to explain "
        "a financial concept — whatever's on your mind."
    )
    print_system("ASSISTANT", opening)

    history: list[dict] = [{"role": "assistant", "content": opening}]
    history_summary: str | None = None

    while True:
        try:
            user_input = input("\033[93mYou: \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("\nGoodbye!")
            break

        # Compress history if it's grown too long
        history, history_summary = await maybe_summarize(history, history_summary)

        print_system("SYSTEM", "Thinking…")

        result = await handle_chat(
            message=user_input,
            history=history,
            history_summary=history_summary,
        )

        # Append the exchange to history for the next turn
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": result["message"]})

        if result["type"] == "clarify":
            print_system("ASSISTANT", result["message"])

        elif result["type"] == "ready":
            print_answer(
                answer=result["message"],
                query_type=result.get("query_type", "unknown"),
                ticker=result.get("ticker"),
                refined=result.get("refined_question"),
            )

            # Ask if the user wants to start a new query
            print()
            again = input("Start a new query? [y/N]: ").strip().lower()
            if again == "y":
                history = []
                history_summary = None
                opening = "Sure! What would you like to know next?"
                print_system("ASSISTANT", opening)
                history.append({"role": "assistant", "content": opening})
            else:
                print("\nGoodbye!")
                break


if __name__ == "__main__":
    asyncio.run(run())
