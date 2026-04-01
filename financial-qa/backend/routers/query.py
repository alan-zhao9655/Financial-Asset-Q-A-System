from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.market_agent import handle_market_query

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    ticker: str


class QueryResponse(BaseModel):
    answer: str
    query_type: str
    ticker: str


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    # This endpoint requires a ticker, so it is always a market query.
    # Classification happens inside the understanding agent on the /api/chat path.
    answer = await handle_market_query(req.question, req.ticker)
    return QueryResponse(answer=answer, query_type="market", ticker=req.ticker)
