"""Bounded LangGraph workflow, not an autonomous general-purpose banking agent."""

import re
import time
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from bankops.config import Settings
from bankops.database import seed_database
from bankops.guardrails import refusal_reason
from bankops.models import AskRequest, AskResponse
from bankops.providers import generate
from bankops.retrieval import PolicyIndex
from bankops.tools import NoDataError, TreasuryTools


class State(TypedDict, total=False):
    request: AskRequest
    task: str
    reason: str
    status: str
    answer: str
    sources: list
    data: dict
    narrative: str | None
    warnings: list
    trace: list


def route(question: str) -> str:
    q = question.lower()
    if re.search(r"stress|what.if|стресс|\d+\s*%", q):
        return "stress"
    policy = bool(
        re.search(
            r"policy|policies|required|buffer|floor|escalat|буфер|правил|порог|лимит|регламент", q
        )
    )
    if re.search(r"exposure|concentration|counterpart|контрагент|концентрац", q) and not policy:
        return "exposure"
    if re.search(r"forecast|project|прогноз", q):
        return "forecast"
    if policy:
        return "policy"
    if re.search(r"liquidity|cash|ликвид|остаток", q):
        return "liquidity"
    return "policy"


class BankOpsAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = settings.runtime / "treasury.sqlite"
        if not self.database.exists():
            seed_database(settings.root, self.database)
        self.tools = TreasuryTools(self.database)
        self.index = PolicyIndex(settings.root, settings.retriever)
        graph = StateGraph(State)
        for name in ("guard", "plan", "execute", "retrieve", "compose", "narrate"):
            graph.add_node(name, getattr(self, name))
        graph.add_edge(START, "guard")
        graph.add_conditional_edges(
            "guard", lambda s: "end" if s.get("reason") else "plan", {"end": END, "plan": "plan"}
        )
        graph.add_edge("plan", "execute")
        graph.add_conditional_edges(
            "execute",
            lambda s: "end" if s.get("reason") else "retrieve",
            {"end": END, "retrieve": "retrieve"},
        )
        graph.add_edge("retrieve", "compose")
        graph.add_conditional_edges(
            "compose",
            lambda s: "narrate" if s["status"] == "answered" else "end",
            {"narrate": "narrate", "end": END},
        )
        graph.add_edge("narrate", END)
        self.graph = graph.compile()

    def guard(self, state: State):
        req = state["request"]
        reason = refusal_reason(req.question)
        explicit_dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", req.question)
        if any(d != req.as_of.isoformat() for d in explicit_dates):
            reason = "Question date differs from as_of; set the date control explicitly"
        return {
            "reason": reason or "",
            "status": "refused" if reason else "answered",
            "answer": reason or "",
            "trace": [{"node": "guard", "passed": not bool(reason)}],
        }

    def plan(self, state: State):
        req = state["request"]
        task = route(req.question) if req.task == "auto" else req.task
        return {
            "task": task,
            "trace": state["trace"]
            + [
                {
                    "node": "plan",
                    "task": task,
                    "planner": "bounded_rules",
                    "as_of": req.as_of.isoformat(),
                    "horizon_days": req.horizon_days,
                }
            ],
        }

    def execute(self, state: State):
        req, task = state["request"], state["task"]
        stress = req.stress_pct
        if task == "stress":
            if re.search(
                r"inflows?|поступлен|decreas|drop|reduc|сниз|уменьш|[-−]\s*\d+\s*%",
                req.question,
                re.I,
            ):
                reason = "Supported stress scenario: increase scheduled outflows only."
                return {"reason": reason, "status": "insufficient_evidence", "answer": reason}
            percentages = re.findall(r"(\d+(?:\.\d+)?)\s*%", req.question)
            if stress is None:
                if (
                    len(percentages) != 1
                    or not percentages[0].isdigit()
                    or int(percentages[0]) > 100
                ):
                    reason = "Specify one integer outflow stress from 0 to 100 percent using stress_pct or %."
                    return {"reason": reason, "status": "insufficient_evidence", "answer": reason}
                stress = int(percentages[0])
            elif percentages and any(float(p) != stress for p in percentages):
                reason = "Question percentage differs from stress_pct; make them match."
                return {"reason": reason, "status": "insufficient_evidence", "answer": reason}
        try:
            if task == "policy":
                data = {"metrics": {}, "rows": [], "sql": []}
            elif task == "exposure":
                data = self.tools.exposure(req.as_of)
            else:
                data = self.tools.snapshot(req.as_of, req.horizon_days, stress or 0)
        except NoDataError:
            reason = "No synthetic snapshot for this date. Choose 2026-10-01 through 2026-10-30."
            return {
                "reason": reason,
                "status": "insufficient_evidence",
                "answer": reason,
                "trace": state["trace"] + [{"node": "execute", "result": "missing_snapshot"}],
            }
        return {
            "data": data,
            "trace": state["trace"] + [{"node": "execute", "tool": task, "queries": data["sql"]}],
        }

    def retrieve(self, state: State):
        req, task = state["request"], state["task"]
        canonical = {
            "liquidity": "liquidity buffer cash minimum escalation",
            "forecast": "liquidity buffer cashflow forecast",
            "stress": "liquidity buffer outflow stress",
            "exposure": "counterparty concentration exposure limit",
        }
        query = canonical.get(task, req.question)
        sources = self.index.search(query, req.as_of, k=3)
        if task != "policy":
            key = "max_share_pct" if task == "exposure" else "buffer_rub"
            # Only the policy section with the corresponding machine-readable rule
            # can support a decision. Extra hits remain explanatory sources.
            sources.sort(key=lambda s: key not in self.index.rules[s.id])
        return {
            "sources": sources,
            "trace": state["trace"]
            + [
                {
                    "node": "retrieve",
                    "mode": self.settings.retriever,
                    "source_ids": [s.id for s in sources],
                    "temporal_filter": req.as_of.isoformat(),
                }
            ],
        }

    def compose(self, state: State):
        sources, task = state["sources"], state["task"]
        data = state["data"]
        m = dict(data["metrics"])
        if not sources:
            return {
                "status": "insufficient_evidence",
                "answer": "No relevant, effective policy found.",
                "trace": state["trace"] + [{"node": "compose", "result": "abstained"}],
            }
        source = sources[0]
        rule = self.index.rules[source.id]
        ru = state["request"].language == "ru"
        if task == "policy":
            # Exact excerpts: no claim that retrieval alone answers every clause.
            answer = "\n\n".join(f"[{s.id}] {s.text}" for s in sources)
        elif task == "exposure" and "max_share_pct" in rule:
            limit = rule["max_share_pct"]
            breached = m["largest_share_pct_exact"] > limit
            m.update({"limit_pct": limit, "breached": breached})
            answer = (
                f"Крупнейший контрагент: {m['largest_counterparty']}. Доля: {m['largest_share_pct']}%. "
                f"Лимит: {limit}%. Превышение: {'да' if breached else 'нет'}. [{source.id}]"
                if ru
                else f"Largest counterparty: {m['largest_counterparty']}; share {m['largest_share_pct']}%. "
                f"Policy maximum: {limit}%. Breach: {'yes' if breached else 'no'}. [{source.id}]"
            )
        elif "buffer_rub" in rule and task != "exposure":
            buffer = rule["buffer_rub"]
            breaches = [r["date"] for r in data["rows"] if r["closing_cash_rub"] < buffer]
            m.update(
                {
                    "buffer_rub": buffer,
                    "breached": bool(breaches),
                    "first_breach_date": breaches[0] if breaches else None,
                }
            )
            answer = (
                f"На {m['as_of']} начальный остаток: {m['opening_cash_rub']:,.2f} RUB. "
                f"Срок: {m['horizon_days']} дн.; рост выплат: {m['stress_pct']}%. "
                f"Минимум: {m['minimum_cash_rub']:,.2f} RUB. Буфер: {buffer:,.2f} RUB. "
                f"Первое нарушение: {m['first_breach_date'] or 'нет'}. [{source.id}]"
                if ru
                else f"As of {m['as_of']}, opening cash is {m['opening_cash_rub']:,.2f} RUB. "
                f"Over {m['horizon_days']} days with outflows increased by {m['stress_pct']}%, "
                f"minimum closing cash is {m['minimum_cash_rub']:,.2f} RUB. "
                f"Required buffer: {buffer:,.2f} RUB. "
                f"First breach: {m['first_breach_date'] or 'none'}. [{source.id}]"
            )
            if breaches:
                answer += (
                    " Нужна проверка казначея. Переводы не выполняются."
                    if ru
                    else " Escalate to the treasury supervisor for review; no transaction is executed."
                )
        else:
            return {
                "status": "insufficient_evidence",
                "answer": "Required policy rule is unavailable.",
            }
        return {
            "answer": answer,
            "status": "answered",
            "data": {**data, "metrics": m},
            "trace": state["trace"] + [{"node": "compose", "result": "evidence_attached"}],
        }

    def narrate(self, state: State):
        req = state["request"]
        narrative, warnings = generate(
            self.settings.provider, req.question, state["answer"], state["sources"], req.language
        )
        return {
            "narrative": narrative,
            "warnings": warnings,
            "trace": state["trace"]
            + [
                {
                    "node": "narrate",
                    "provider": self.settings.provider,
                    "generated": narrative is not None,
                }
            ],
        }

    def ask(self, request: AskRequest) -> AskResponse:
        started = time.perf_counter()
        state = self.graph.invoke({"request": request}, config={"recursion_limit": 12})
        data = state.get("data", {})
        return AskResponse(
            request_id=str(uuid.uuid4()),
            task=state.get("task", "guard"),
            status=state["status"],
            answer=state["answer"],
            narrative=state.get("narrative"),
            provider=self.settings.provider,
            retriever=self.settings.retriever,
            metrics=data.get("metrics", {}),
            rows=data.get("rows", []),
            sources=state.get("sources", []),
            trace=state["trace"],
            warnings=state.get("warnings", []),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
