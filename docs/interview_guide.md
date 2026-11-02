# Explain and demonstrate BankOps

## A clear explanation

“I built a treasury-analysis assistant that combines read-only SQL calculations with effective-date policy
retrieval. A LangGraph workflow validates the request, chooses a bounded tool, calculates a scenario and
attaches supporting policy excerpts. An optional GigaChat adapter adds a separate explanation. The browser
interface exposes the data and execution trace so the result can be checked.”

The project is independent, uses synthetic data, and was developed with AI assistance. Before presenting
it, run the code and understand every step you describe. Do not describe it as work completed at Sber.

## Five-minute demonstration

1. Start with `start_windows.bat` or `python scripts/run.py`. Open localhost:8501.
2. Explain the default date, 2026-10-30, and seven-day horizon. The cash schedule has ₽26m opening cash.
3. Click the 20% outflow stress example. The result has ₽5.8m minimum cash and first breach on 2026-11-03.
4. Open Figures, Policy evidence and Execution trace. Explain the calculation and `liquidity-v2` source.
5. Show counterparty exposure: 40% for Synthetic Alpha against a fictional 25% limit.
6. Ask for a transfer: the workflow refuses before reading the database.
7. Show tests and the saved evaluation report. Explain the limits of the tiny authored benchmark.

## Questions to prepare for

**Why not let the LLM write SQL?**

For these fixed business tasks, parameterized named tools are easier to verify. The database also opens
read-only. This removes arbitrary SQL generation from the execution path. It limits flexibility, deliberately.

**Why use LangGraph for a small workflow?**

It makes state, branches and termination explicit and provides a place to extend routing or approval
steps later. A plain Python orchestrator would also work; the graph is not evidence of agent intelligence.

**Why separate calculations from the LLM explanation?**

The authoritative figures come from deterministic arithmetic, not generated prose. If an LLM is unavailable
or violates the response contract, the checked calculation remains available. Narrative citation and number
checks are limited: they do not prove that the explanation follows logically from the evidence.

**What does RAG mean here?**

Retrieve the relevant policy sections and attach them to the answer and optional generation context.
The shipped default is lexical hybrid search, BM25 plus character TF-IDF. E5/Qdrant is an optional semantic
path, not the algorithm used for the committed benchmark. Each file is already a short section.

**What is the financial calculation?**

For each future day: closing cash = previous closing cash + scheduled inflows − scheduled outflows.
For stress, multiply daily outflows by 1 + stress percentage / 100, rounding to kopecks before accumulation.
Check every closing balance against the effective liquidity buffer. This is a schedule projection, not ML.

**How do you avoid stale policy answers?**

Filter documents by effective-from/effective-to dates before ranking. The old ₽8m policy expires on
2026-09-30; the ₽10m version begins on 2026-10-01. The metadata stores the machine-readable threshold,
and a test checks that the visible policy contains that value. Arbitrary policy edits still require review.

**What did you evaluate?**

Hand-calculated scenario fixtures, arithmetic invariants, API/guard behavior and retrieval source IDs.
The saved report contains 16 functional cases and 16 authored retrieval queries. Both lexical methods
score perfectly on that fixture, which means it cannot establish a quality advantage for hybrid search.
There is no held-out dataset or live LLM evaluation.

**What would change for production?**

Start with the actual data contract and business owners. Add authenticated user identity, role/tenant
filters, reviewed ingestion/versioning, immutable audits, robust data validation, distributed observability,
load tests and a realistic held-out evaluation with human review. Move storage to a managed database and
vector service as warranted. Measure quality, latency, cost and failure rates before rollout.

## A concrete extension to implement yourself

Add a new liquidity policy version effective on a future date with a ₽12m buffer. Add a boundary test,
then demonstrate that historical queries still retrieve the earlier version. This is a small change that
requires understanding the data, effective dates, retrieval and decision logic.
