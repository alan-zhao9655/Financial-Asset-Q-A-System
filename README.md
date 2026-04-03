# FinQ — Financial Asset Q&A System

A full-stack conversational AI application that answers natural language questions about stocks, markets, and financial concepts.

---

## What it does

Ask anything in plain English — no need to know ticker symbols or how to phrase queries:

- **"How has Apple performed this month?"** → live price, 7-day/30-day % change, 52-week range, trend analysis, recent headlines
- **"What is dollar cost averaging?"** → Wikipedia-grounded RAG answer with cited sources
- **"Why did SVB collapse?"** → Tavily web search fallback when topic is outside the corpus
- **"Tell me about that EV company from China"** → multi-turn clarification until the query is specific enough to route

---

## Architecture

```
User message
  └── Understanding Agent (Claude Sonnet)
        ├── CLARIFY → ask one follow-up question and loop
        ├── MARKET  → Ticker Resolver → Market Agent → answer
        └── KNOWLEDGE → RAG Agent → answer

Market Agent
  ├── yfinance (TLS-Chrome impersonation via curl_cffi)
  ├── Pure-Python metrics calculator (no LLM arithmetic)
  ├── Yahoo Finance news feed
  └── Claude Sonnet (interprets pre-computed facts)

RAG Agent
  ├── FAISS + bge-m3 embeddings (1024-dim, MPS-accelerated)
  ├── bge-reranker-v2-m3 cross-encoder (top-20 → top-5)
  ├── Confidence gate: rerank_score >= 0.35 → RAG answer
  └── Below threshold → Tavily web search fallback
```
```mermaid
graph TD
    %% Styling
    classDef frontend fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef orchestrator fill:#1e1b4b,stroke:#a78bfa,stroke-width:2px,color:#fff;
    classDef engine fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff;
    classDef data fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#fff;

    %% User & UI
    User((User)) --> |"Plain English Query"| UI["React Frontend<br/>(Chat, 3D Globe, Charts)"]:::frontend

    %% Orchestrator
    UI <--> |"Clarification Loop"| Brain["Understanding Agent<br/>(Claude Sonnet)"]:::orchestrator

    %% Routing
    Brain -- "Routes Resolved Query" --> Router{ }

    %% The Three Engines
    Router -- "Live Performance" --> Market["Market Data Engine<br/>(yfinance + Pre-computed Metrics)"]:::engine
    Router -- "Compare Assets" --> Compare["Comparison Engine<br/>(Parallel Market Fetch)"]:::engine
    Router -- "Financial Concepts" --> RAG["Knowledge Retriever<br/>(FAISS + Wikipedia Corpus)"]:::engine

    %% Fallback
    RAG -- "Not in Corpus<br/>(Score < 0.35)" --> Web["Tavily Web Search<br/>(Fallback)"]:::data

    %% Generation & Return
    Market --> Synthesizer["Answer Synthesizer<br/>(Claude Sonnet)"]:::orchestrator
    Compare --> Synthesizer
    RAG -- "Confident Match" --> Synthesizer
    Web --> Synthesizer

    Synthesizer -- "Structured Text + Chart Data" --> UI
```
---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.12, uvicorn |
| LLM | Claude Sonnet 4.6 (understanding, market, RAG), Claude Haiku 4.5 (ticker resolver, summarizer) |
| Market data | yfinance 0.2.66 + curl_cffi |
| Vector search | FAISS (IndexFlatIP, ~2,087 child vectors) |
| Embeddings | BAAI/bge-m3 (1024-dim, sentence-transformers, MPS) |
| Reranker | BAAI/bge-reranker-v2-m3 (CrossEncoder, MPS) |
| Web search | Tavily (`search_depth=advanced`) |
| Frontend | React 18, Vite, Tailwind CSS |
| 3D Globe | React Three Fiber (r3f@8), drei@9, Three.js |
| Animation | Framer Motion |

---

## Project Layout

```
financial-qa/
  backend/
    main.py                    FastAPI app — CORS, warning suppression, structured logging
    agents/
      understanding_agent.py  Multi-turn intake: clarify → resolve → route (Claude Sonnet)
      market_agent.py         fetch → compute → news → Claude Sonnet
      rag_agent.py            RAG → confidence gate (0.35) → Tavily fallback → Claude Sonnet
    market/
      fetcher.py              yfinance → StockData (price, fundamentals, quarterly earnings)
      calculator.py           Pure-Python metrics → MarketMetrics
      news.py                 yfinance t.news → Yahoo Finance headlines
      web_search.py           Tavily → WebResult list (knowledge fallback only)
      ticker_resolver.py      Company name → validated ticker (Haiku + yfinance)
    rag/
      config.py               Central config: models, thresholds, chunk sizes
      build_corpus.py         Wikipedia fetcher → 50 .md files (5 financial categories)
      embedder.py             bge-m3, MPS-accelerated, lazy singleton
      chunker.py              Parent-child chunker: sections → 100-token children
      indexer.py              FAISS builder + loader, model mismatch detection
      reranker.py             bge-reranker-v2-m3, MPS, graceful fallback
      retriever.py            embed → FAISS → rerank → parent lookup
      data/documents/         50 Wikipedia .md files (committed)
    prompts/
      market_prompt.py        Structured prompt builder (3-section format)
      rag_prompt.py           RAG + web search system prompts + context formatters
    routers/
      chat.py                 POST /api/chat, POST /api/summarize-history
      query.py                POST /api/query (direct, ticker required)
    test_market.py            Data layer smoke test (no LLM)
    test_chat.py              Interactive CLI for the full conversational flow
    test_rag.py               RAG pipeline test (no API key needed)

  frontend/
    src/
      App.jsx                 Root: layout, state, landing <-> chat transition
      index.css               Global styles: animations, dark theme, scrollbar
      components/
        FinancialGlobe.jsx    R3F scene: animated GLB earth, question chips, OrbitControls
        TickerTape.jsx        Scrolling price ticker (CSS animation)
        ChatMessage.jsx       Message bubbles — user / clarify / answer
        AnswerCard.jsx        Animated section panels from ##-markdown
        InputBar.jsx          Auto-grow textarea, send button, 16px (iOS-safe)
    public/
      hologram_planet_earth_animated.glb
    vite.config.js            /api proxy + Three.js code splitting
    tailwind.config.js
    postcss.config.js
```

---

## Setup

### Prerequisites

- Python 3.12 arm64 (Homebrew: `/opt/homebrew/bin/python3`) — native Apple Silicon, required for PyTorch MPS
- Node.js 18+
- Anthropic API key
- Tavily API key (free tier: 1,000 searches/month — [tavily.com](https://tavily.com))

### 1. Clone and create the virtual environment

```bash
git clone <repo-url>
cd Financial-Asset-Q-A-System

/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate

pip install -r financial-qa/backend/requirements.txt
pip install -r financial-qa/backend/requirements-rag.txt
```

> **Why Homebrew Python?** The system Python 3.13 on macOS is an x86_64 binary running under Rosetta 2. PyTorch has no x86_64 macOS + Python 3.13 wheel, so `pip install torch` fails. Homebrew Python 3.12 is native arm64, giving you MPS GPU acceleration.

### 2. Configure environment variables

```bash
cp financial-qa/backend/.env.example financial-qa/backend/.env
# Edit .env and set:
# ANTHROPIC_API_KEY=sk-ant-...
# TAVILY_API_KEY=tvly-...
```

### 3. Build the RAG index

```bash
cd financial-qa/backend

# Fetch 50 Wikipedia articles (~90 seconds, rate-limited)
../../.venv/bin/python -m rag.build_corpus

# Build FAISS index (downloads bge-m3 ~570MB + bge-reranker ~1.1GB on first run)
../../.venv/bin/python -m rag.indexer

# Verify
../../.venv/bin/python -m rag.indexer --check
```

### 4. Start the backend

```bash
cd financial-qa/backend
../../.venv/bin/uvicorn main:app --reload --port 8000
```

### 5. Start the frontend

```bash
cd financial-qa/frontend
npm install
npm run dev   # http://localhost:5173
```

The Vite dev server proxies `/api/*` to `localhost:8000` — no CORS configuration needed during development.

---

## API Reference

### `POST /api/chat` — Conversational path

The primary entry point. Handles multi-turn clarification and returns the final answer in the same response.

```json
// Request
{
  "message": "tell me about Apple",
  "history": [],
  "history_summary": null
}

// Response — still clarifying
{ "type": "clarify", "message": "What aspect interests you — price performance, key metrics, or news?" }

// Response — ready
{
  "type": "ready",
  "message": "## Objective Data\n...",
  "query_type": "market",
  "ticker": "AAPL",
  "refined_question": "Give an overview of AAPL's recent price performance and key metrics"
}
```

**History compression:** When `len(history) > 12`, call `/api/summarize-history` with the older turns, store the returned `summary` as `history_summary`, and keep only the last 6 turns in `history`. The backend is stateless — the client owns all state.

### `POST /api/summarize-history`

```json
// Request
{ "messages": [ ...older turns... ] }

// Response
{ "summary": "The user asked about BABA's weekly performance and wanted to understand..." }
```

### `POST /api/query` — Direct path (expert users)

Ticker required. Always routes to the market agent.

```json
// Request
{ "question": "How has AAPL performed this month?", "ticker": "AAPL" }

// Response
{ "answer": "...", "query_type": "market", "ticker": "AAPL" }
```

---

## Testing

```bash
cd financial-qa/backend

# Data layer only — no API key needed
../../.venv/bin/python test_market.py

# RAG pipeline — no API key needed
../../.venv/bin/python test_rag.py

# Full conversational flow — requires ANTHROPIC_API_KEY + TAVILY_API_KEY
../../.venv/bin/python test_chat.py
```

---

## Backend Logging

The server emits structured log lines to help evaluate routing decisions:

```
12:34:01 [INFO] [ROUTE] market | ticker=AAPL | question='analyze AAPL margins'
12:34:03 [INFO] [MARKET] ticker=AAPL | company=Apple Inc. | price=213.49 | news=5 | earnings_quarters=4

12:34:01 [INFO] [ROUTE] knowledge | question='what is a P/E ratio?'
12:34:02 [INFO] [RAG] source=rag | top_score=0.872 | docs=5 | sources=['price_earnings_ratio.md', ...]

12:34:01 [INFO] [ROUTE] knowledge | question='why did SVB collapse?'
12:34:02 [INFO] [RAG] source=web_search | top_score=0.118 (below threshold 0.35)
12:34:04 [INFO] [RAG] web_search returned 5 results | urls=['https://...', ...]
```

---

## Design Decisions

**Claude never does arithmetic.** `calculator.py` computes all metrics before the LLM sees them. If a number is wrong, it's wrong in Python — not buried in a model response.

**RAG corpus is Wikipedia only.** LLM-generated corpus content would defeat the purpose of RAG — hallucinations in the corpus become "grounded facts" with citations. Wikipedia is CC BY-SA, peer-reviewed, and free via API.

**Parent-child chunking.** Small chunks (~100 tokens) are embedded for precise retrieval; large parent sections (~400 tokens) are returned to the LLM for complete context. Both without compromise.

**Confidence-gated web search.** RAG runs first (~200ms local). Only if the top rerank score is below 0.35 does Tavily activate (~1–3s, API quota). Common concept questions always use the free local corpus.

**Stateless backend.** The frontend owns `history` and `history_summary`. No server sessions = horizontally scalable, trivially testable.

**Canvas never unmounts.** The R3F Canvas stays in the tree throughout the session. Unmounting destroys the WebGL context; remounting re-initialises it, causing a flash and model reload. Instead, the container animates between two concrete pixel heights using Framer Motion.

---

## Acknowledgements

- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) and [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) — Beijing Academy of AI
- Wikipedia corpus via [Wikipedia-API](https://github.com/martin-majlis/Wikipedia-API)
- Market data via [yfinance](https://github.com/ranaroussi/yfinance)
- Web search via [Tavily](https://tavily.com)
