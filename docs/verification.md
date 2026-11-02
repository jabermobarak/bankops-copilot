# Delivery verification

Verified 1 November 2026 on Python 3.12 / Linux.

| Check | Result |
| --- | --- |
| Ruff lint | Passed |
| Ruff formatting | Passed |
| Automated tests | 56 passed |
| Functional regression fixture | 16 / 16 passed |
| Retrieval fixture | 16 authored queries; BM25 and hybrid lexical Hit@1 / Recall@3 = 1.0 |
| Dependency consistency | pip check passed |
| Streamlit widgets + real local HTTP API | Dashboard and stress button passed |
| GigaChat SDK configuration fields | Installed adapter inspected; credentials/timeout/TLS fields present |
| Compatible-provider HTTP contract | Mocked server request/response and invalid-output fallback passed |
| Dense store | Real Qdrant, deterministic fake encoder; temporal filter passed |

Two deprecation warnings originate inside Streamlit chart handling with the installed Pandas version; the UI test passed.

Not executed: live GigaChat, a live local generative model, real E5 embeddings, Docker build/run, Windows launcher, or GitHub-hosted CI. The Windows script and deployment files are provided for use on those platforms. No claim of live provider or production validation is made.

The fixture is deliberately small and authored. Perfect retrieval scores are regression evidence only and do not establish generalization or banking readiness. See evaluation_results.json for every case and the data hash.
