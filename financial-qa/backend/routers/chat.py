import os
import anthropic
from fastapi import APIRouter
from pydantic import BaseModel
from agents.understanding_agent import handle_chat

router = APIRouter()

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    history_summary: str | None = None


class ChatResponse(BaseModel):
    type: str                       # "clarify" | "ready"
    message: str                    # clarifying question OR final answer
    query_type: str | None = None   # "market" | "knowledge" — set when type=ready
    ticker: str | None = None
    refined_question: str | None = None
    context_summary: str | None = None  # updated summary if history was compressed


class SummarizeRequest(BaseModel):
    messages: list[ChatMessage]


class SummarizeResponse(BaseModel):
    summary: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_SUMMARIZE_SYSTEM = (
    "Summarize the following conversation concisely (3-5 sentences max). "
    "Preserve: what the user is trying to find out, any companies or tickers mentioned, "
    "and what has already been clarified. Write in third person (e.g. 'The user wants...')."
)

HISTORY_SUMMARIZE_THRESHOLD = 12  # messages before frontend should request compression


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    result = await handle_chat(
        message=req.message,
        history=history,
        history_summary=req.history_summary,
    )
    return ChatResponse(**result)


@router.post("/summarize-history", response_model=SummarizeResponse)
async def summarize_history(req: SummarizeRequest):
    """
    Compress older conversation turns into a single summary string.
    The frontend should call this when len(history) > HISTORY_SUMMARIZE_THRESHOLD,
    passing in the messages it wants to compress (everything except the last 6).
    The returned summary replaces those messages in future requests via history_summary.
    """
    client = _get_client()

    history_text = "\n".join(
        f"{m.role.upper()}: {m.content}" for m in req.messages
    )

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_SUMMARIZE_SYSTEM,
        messages=[{"role": "user", "content": history_text}],
    )

    return SummarizeResponse(summary=response.content[0].text.strip())
