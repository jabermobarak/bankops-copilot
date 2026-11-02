"""Allowlisted tools. No endpoint executes SQL supplied by a user or an LLM.

All balances use integer kopecks. No cross-currency aggregation is performed.
The example contains RUB only; *_rub values are presentation values.
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from bankops.database import readonly

BALANCE_SQL = "SELECT SUM(cash_minor) AS cash FROM balances WHERE as_of = ?"
FLOW_SQL = """SELECT due_date,
 SUM(CASE WHEN direction='in' THEN amount_minor ELSE 0 END) AS inflow_minor,
 SUM(CASE WHEN direction='out' THEN amount_minor ELSE 0 END) AS outflow_minor
 FROM cashflows WHERE as_of = ? AND due_date > ? AND due_date <= ?
 GROUP BY due_date ORDER BY due_date"""
EXPOSURE_SQL = """SELECT counterparty, amount_minor FROM exposures
 WHERE as_of = ? ORDER BY amount_minor DESC, counterparty"""


class NoDataError(ValueError):
    pass


def rub(minor: int) -> float:
    return float(Decimal(minor) / 100)


class TreasuryTools:
    def __init__(self, path: Path):
        self.path = path

    def snapshot(self, as_of: date, horizon: int = 7, stress_pct: int = 0) -> dict:
        if not 1 <= horizon <= 30 or not 0 <= stress_pct <= 100:
            raise ValueError("Invalid tool parameters")
        end = as_of + timedelta(days=horizon)
        with readonly(self.path) as con:
            balance = con.execute(BALANCE_SQL, (as_of.isoformat(),)).fetchone()["cash"]
            if balance is None:
                raise NoDataError("No balance snapshot for requested date")
            raw = con.execute(
                FLOW_SQL, (as_of.isoformat(), as_of.isoformat(), end.isoformat())
            ).fetchall()
        by_date = {r["due_date"]: r for r in raw}
        # Coverage is explicit: all demo snapshots have a complete 30-day schedule.
        # Zero-flow days are retained so charts and first-breach dates are correct.
        closing = balance
        rows = []
        for day in range(1, horizon + 1):
            due = (as_of + timedelta(days=day)).isoformat()
            item = by_date.get(due, {"inflow_minor": 0, "outflow_minor": 0})
            inflow = item["inflow_minor"]
            outflow = int(
                (Decimal(item["outflow_minor"]) * (100 + stress_pct) / 100).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
            closing += inflow - outflow
            rows.append(
                {
                    "date": due,
                    "inflow_rub": rub(inflow),
                    "outflow_rub": rub(outflow),
                    "closing_cash_rub": rub(closing),
                }
            )
        return {
            "metrics": {
                "as_of": as_of.isoformat(),
                "currency": "RUB",
                "horizon_days": horizon,
                "opening_cash_rub": rub(balance),
                "closing_cash_rub": rub(closing),
                "minimum_cash_rub": min(row["closing_cash_rub"] for row in rows),
                "stress_pct": stress_pct,
                "inflows_rub": float(sum(Decimal(str(r["inflow_rub"])) for r in rows)),
                "outflows_rub": float(sum(Decimal(str(r["outflow_rub"])) for r in rows)),
            },
            "rows": rows,
            "sql": [
                {"template": BALANCE_SQL, "parameters": [as_of.isoformat()]},
                {
                    "template": FLOW_SQL,
                    "parameters": [as_of.isoformat(), as_of.isoformat(), end.isoformat()],
                },
            ],
        }

    def exposure(self, as_of: date) -> dict:
        with readonly(self.path) as con:
            values = con.execute(EXPOSURE_SQL, (as_of.isoformat(),)).fetchall()
        total = sum(v["amount_minor"] for v in values)
        if not total:
            raise NoDataError("No exposure snapshot for requested date")
        rows = [
            {
                "counterparty": v["counterparty"],
                "exposure_rub": rub(v["amount_minor"]),
                "share_pct": round(v["amount_minor"] * 100 / total, 2),
            }
            for v in values
        ]
        return {
            "metrics": {
                "as_of": as_of.isoformat(),
                "currency": "RUB",
                "total_exposure_rub": rub(total),
                "largest_counterparty": rows[0]["counterparty"],
                "largest_share_pct_exact": values[0]["amount_minor"] * 100 / total,
                "largest_share_pct": rows[0]["share_pct"],
            },
            "rows": rows,
            "sql": [{"template": EXPOSURE_SQL, "parameters": [as_of.isoformat()]}],
        }
