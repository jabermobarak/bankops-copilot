"""Small authored regression fixture; not a held-out bank or LLM benchmark."""

import hashlib
import json
import platform
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bankops.agent import BankOpsAgent  # noqa: E402
from bankops.config import Settings  # noqa: E402
from bankops.models import AskRequest  # noqa: E402


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate(output: Path):
    with tempfile.TemporaryDirectory() as directory:
        agent = BankOpsAgent(Settings(root=ROOT, runtime=Path(directory)))
        retrieval_cases = read_lines(ROOT / "evaluation/retrieval.jsonl")
        retrieval = {}
        for method in ("bm25", "hybrid"):
            results = []
            for case in retrieval_cases:
                hits = agent.index.search(
                    case["query"], date.fromisoformat(case["as_of"]), method=method
                )
                ids = [h.id for h in hits]
                rank = ids.index(case["expected"]) + 1 if case["expected"] in ids else None
                results.append({**case, "retrieved": ids, "rank": rank})
            n = len(results)
            retrieval[method] = {
                "hit_at_1": sum(r["rank"] == 1 for r in results) / n,
                "recall_at_3": sum(r["rank"] is not None for r in results) / n,
                "mrr_at_3": sum(1 / r["rank"] if r["rank"] else 0 for r in results) / n,
                "cases": results,
            }
        tasks = []
        for case in read_lines(ROOT / "evaluation/tasks.jsonl"):
            r = agent.ask(AskRequest(**case["request"]))
            failures = []
            if r.status != case["status"]:
                failures.append(f"status expected {case['status']}, got {r.status}")
            if r.task != case["task"]:
                failures.append(f"task expected {case['task']}, got {r.task}")
            for key, expected in case.get("metrics", {}).items():
                if r.metrics.get(key) != expected:
                    failures.append(f"{key}: expected {expected}, got {r.metrics.get(key)}")
            if case.get("source") and case["source"] not in [s.id for s in r.sources]:
                failures.append("missing expected citation")
            tasks.append(
                {
                    "id": case["id"],
                    "passed": not failures,
                    "failures": failures,
                    "elapsed_ms": r.elapsed_ms,
                }
            )
        data_hash = hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((ROOT / "data").rglob("*")) if p.is_file())
        ).hexdigest()
        report = {
            "created_utc": datetime.now(UTC).isoformat(),
            "python": platform.python_version(),
            "provider": "extractive",
            "retriever": "lexical",
            "data_sha256": data_hash,
            "scope": "Authored synthetic regression fixture; no live LLM, bank data or held-out benchmark",
            "retrieval_queries": len(retrieval_cases),
            "retrieval": retrieval,
            "tasks_passed": sum(t["passed"] for t in tasks),
            "tasks_total": len(tasks),
            "tasks": tasks,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(f"Tasks: {report['tasks_passed']}/{len(tasks)}")
        for method, result in retrieval.items():
            print(
                f"{method}: Hit@1={result['hit_at_1']:.3f}; Recall@3={result['recall_at_3']:.3f}; MRR@3={result['mrr_at_3']:.3f}"
            )
        print(f"Report: {output}")
        return report["tasks_passed"] == len(tasks) and retrieval["hybrid"]["recall_at_3"] >= 0.8


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/evaluation_results.json"
    raise SystemExit(0 if evaluate(output) else 1)
