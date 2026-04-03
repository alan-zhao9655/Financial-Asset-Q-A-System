# Evaluation Framework

Four evaluation scripts covering different layers of the system. Each can be run independently.

```
evaluation/
  test_routing.py          Routing accuracy — does the understanding agent classify correctly?
  test_retrieval.py        RAG retrieval quality — Hit@1, Hit@5, MRR, reranker lift
  test_market_accuracy.py  Data layer sanity — structural integrity + math consistency
  test_faithfulness.py     Answer faithfulness — Haiku judges whether Sonnet hallucinated numbers
  data/
    routing_labels.json    40 labeled queries (market / comparison / knowledge / clarify)
    retrieval_labels.json  25 questions with expected source documents
```

All scripts must be run from `financial-qa/backend/` so backend imports resolve:

```bash
cd financial-qa/backend
```

---

## test_routing.py

**What it measures:** Does the understanding agent route each query to the correct handler?

**How it works:**
- Loads 40 labeled queries from `data/routing_labels.json`
- Calls `handle_chat()` with an empty history
- Mocks all downstream agents (no actual market/RAG calls)
- Compares predicted `query_type` against ground-truth label
- Prints per-category accuracy + confusion matrix + ticker accuracy

**Output metrics:**
- Overall accuracy (correct routes / total)
- Per-category accuracy (market / comparison / knowledge / clarify)
- Ticker accuracy (was the right ticker extracted?)
- Confusion matrix
- List of failed cases

**Requires:** `ANTHROPIC_API_KEY` (makes real Haiku/Sonnet calls for routing)

```bash
../../.venv/bin/python ../evaluation/test_routing.py
```

---

## test_retrieval.py

**What it measures:** Does the RAG pipeline retrieve the right documents?

**How it works:**
- Loads 25 questions from `data/retrieval_labels.json`, each with expected source documents
- Runs full two-stage retrieval: FAISS + bge-reranker-v2-m3
- Also runs FAISS-only retrieval to measure how much the reranker helps
- Computes Hit@1, Hit@5, MRR, and reranker lift

**Output metrics:**
- Hit@1: top result from expected source?
- Hit@5: any of top-5 from expected source?
- MRR: mean reciprocal rank
- Reranker lift: % of queries where reranking improved the rank
- Score calibration: avg top-1 rerank score for hits vs misses

**Requires:** No API key. Needs the RAG index built (`python -m rag.indexer`).

```bash
../../.venv/bin/python ../evaluation/test_retrieval.py
```

---

## test_market_accuracy.py

**What it measures:** Is the fetched market data structurally sound and mathematically consistent?

**How it works:**
- Fetches live data for 5 test tickers: AAPL, MSFT, TSLA, BABA, SPY
- Checks StockData structural integrity (non-empty history, non-null prices)
- Checks OHLCV candle sanity (high >= low, high >= open/close, etc.)
- Cross-validates computed metrics against raw data (day_change_pct, pct_from_52w_high)
- Checks quarterly earnings format and ordering

**Requires:** No API key. Uses yfinance directly.

```bash
../../.venv/bin/python ../evaluation/test_market_accuracy.py
```

---

## test_faithfulness.py

**What it measures:** Do market agent answers faithfully report only numbers from the data block?

**How it works:**
- Runs 5 test cases (ticker + question) through the full market agent pipeline
- Captures the exact data block sent to Sonnet
- Captures Sonnet's answer
- Uses Claude Haiku as an independent judge to check for hallucinated numbers
- Also checks structural integrity (required sections present)

**Output metrics:**
- Structural pass rate (all 3 sections present and non-empty)
- Faithfulness pass rate (Haiku found no hallucinated numbers)
- Per-case detail on any failures

**Requires:** `ANTHROPIC_API_KEY` (both Sonnet for answer generation and Haiku for judging)

```bash
../../.venv/bin/python ../evaluation/test_faithfulness.py
```

---

## Interpreting Results

| Metric | Target | Notes |
|--------|--------|-------|
| Routing accuracy | ≥ 90% | Failures on "explain why BABA crashed" style queries are expected edge cases |
| Ticker accuracy | ≥ 85% | Company name → ticker resolution may fail for less-known companies |
| Hit@5 | ≥ 80% | Some questions span multiple articles — missing one expected source isn't always wrong |
| Hit@1 | ≥ 60% | The first result being exactly right is a high bar |
| MRR | ≥ 0.65 | Higher is better; 1.0 = always ranked first |
| Faithfulness | ≥ 90% | LLM-as-judge can produce false positives on rounded numbers |

Reranker lift should be positive for most queries — if it's near 0%, the reranker isn't
helping and you may want to investigate model loading or threshold settings.
