# Sber AI engineering: research and project mapping

Checked **1 November 2026**. This is a targeted sample of public vacancies, not a comprehensive hiring survey.
An employer's advertised stack does not reveal its private implementation. BankOps is an independent approximation
of a relevant business problem and engineering workflow, not a reproduction of Sber software.

## Roles found

### AI инженер (Финансы)

The description concerns treasury-related AI agents and the full lifecycle from requirements to integration.
It asks for Python, backend APIs, FastAPI/Flask, LangChain/LangGraph, RAG/vector stores and familiarity with LLMs.
The body mentions at least two years of relevant experience; the HH listing uses the 3–6 years category.

- [Employer vacancy on HH](https://hh.ru/vacancy/138781067)
- [HH search confirmation](https://hh.ru/vacancies/data-science-engineer)
- [Accessible description mirror](https://h.careers/job/37369d6b-266d-43f4-9680-717e654e4a5f)

Evidence status: HH search exposed the employer/title and experience category; the direct detail page could
not be fetched. Detailed requirements were read from the mirror. Confirm availability before applying.

### AI Agents Developer, Центр ИИ «Сервисы»

The employer's HH search listing places this role in the 1–3 years category. Visible requirements include
Python, LangChain/LangGraph, PyTorch, Transformers and SQL. Responsibilities include agent development and
RAG; model adaptation and cross-encoders appear among relevant additional capabilities in the search excerpts.

- [Employer vacancy on HH](https://hh.ru/vacancy/138383543)
- [HH listing/search evidence](https://hh.ru/vacancies/agent-pensionnogo-strahovaniya?page=2)

Evidence status: searchable employer listing; direct vacancy detail fetch was unavailable. The search URL's
title is unrelated because HH's broad search results also contain these AI roles; check the actual role title.

### ML/NLP Engineer, LLM / AI agents / RAG

The accessible Sber listing describes an assistant for Sberbank Online. Work includes agents, RAG, NLP,
model adaptation, quality evaluation and collaboration on deployment. The role asks for several years
of ML experience and lists Python ML/NLP libraries alongside agent frameworks.

- [Accessible employer listing on getmatch](https://getmatch.ru/vacancies/34371-ml-nlp-engineer-llm-ai-agenty-rag)

### Official Sber Finance engineering recruitment event

Sber's own page describes finance systems covering treasury and risk, with Python, FastAPI, SQL, Docker,
Kubernetes and CI tooling. It explicitly connects RAG/agentic LLM integration with business calculations
and asks for code review, static analysis and tests. This is a **historical 8 August 2026 event**, not proof
that its Senior/Lead vacancy is open now.

- [Official Finance engineering page](https://developers.sber.ru/kak-v-sbere/one-day-offer/python_august_2026)

Some indexed Sber vacancy URLs redirected to the general careers page when opened. Their cached snippets
were not treated as confirmation that a specific vacancy remains open.

## Why this project

The practical overlap is an assistant that combines a business calculation, database access, document
retrieval, an LLM interface, testable behavior and a service boundary. A treasury workflow is especially
relevant to the Finance role. The decision to build BankOps is our inference from these public requirements.

| Advertised capability | Concrete code / artifact | Scope |
| --- | --- | --- |
| Python backend, API | `bankops/api.py`, Pydantic schemas | Implemented and HTTP-tested |
| LangGraph orchestration | `bankops/agent.py` | Fixed graph, rule-based routing |
| SQL integration | `bankops/tools.py`, `database.py` | Read-only SQLite; no bank integration |
| RAG and source grounding | `retrieval.py`, dated policies | Lexical hybrid runs by default |
| Embeddings / vector store | E5 + Qdrant adapter | Optional; Qdrant tested with fake encoder |
| GigaChat integration | `providers.py`, `.env.example` | SDK adapter; no live credentialed call |
| Quality evaluation | `tests/`, `evaluation/`, JSON report | Synthetic functional/retrieval fixtures |
| Deployment practices | Dockerfile, Compose, CI | CI config included; Docker unexecuted here |
| Observability | Request IDs, JSON audit events, `/metrics` | Local process counters, no distributed tracing |
| ML research / LoRA / distributed training | Not represented | Must be learned/demonstrated separately |

This project can demonstrate relevant engineering choices. It does not confer commercial experience or
cover every requirement in research-oriented vacancies. At interview, describe it as an independent portfolio
project and explain its calculations, boundaries, failure cases and verification.
