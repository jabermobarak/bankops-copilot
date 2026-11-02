import sqlite3
from datetime import date
from decimal import Decimal

import pytest

from bankops.database import readonly
from bankops.models import AskRequest
from bankops.tools import NoDataError, TreasuryTools


def test_baseline_independent_fixture(agent):
    result = agent.ask(AskRequest(question="Show liquidity"))
    assert result.metrics["opening_cash_rub"] == 26_000_000
    assert result.metrics["inflows_rub"] == 29_000_000
    assert result.metrics["outflows_rub"] == 41_000_000
    assert result.metrics["minimum_cash_rub"] == 12_000_000
    assert result.metrics["closing_cash_rub"] == 14_000_000
    assert not result.metrics["breached"]
    assert [r["closing_cash_rub"] for r in result.rows] == [
        27_000_000,
        21_000_000,
        20_000_000,
        12_000_000,
        15_000_000,
        15_000_000,
        14_000_000,
    ]


def test_stress_independent_fixture(agent):
    result = agent.ask(AskRequest(question="What if outflows increase by 20%?"))
    assert result.metrics["outflows_rub"] == 49_200_000
    assert result.metrics["minimum_cash_rub"] == 5_800_000
    assert result.metrics["first_breach_date"] == "2026-11-03"
    assert result.metrics["breached"]


@pytest.mark.parametrize("pct", [0, 1, 20, 99, 100])
def test_cash_conservation_and_monotonic_stress(agent, pct):
    result = agent.tools.snapshot(date(2026, 10, 30), 30, pct)
    cash = Decimal(str(result["metrics"]["opening_cash_rub"]))
    for row in result["rows"]:
        cash += Decimal(str(row["inflow_rub"])) - Decimal(str(row["outflow_rub"]))
        assert cash == Decimal(str(row["closing_cash_rub"]))
    baseline = agent.tools.snapshot(date(2026, 10, 30), 30, 0)
    assert all(
        r["closing_cash_rub"] <= b["closing_cash_rub"]
        for r, b in zip(result["rows"], baseline["rows"], strict=True)
    )


def test_concentration_fixture(agent):
    result = agent.ask(AskRequest(question="Show counterparty exposure"))
    assert result.metrics["largest_share_pct"] == 40
    assert result.metrics["largest_counterparty"] == "Synthetic Alpha"
    assert result.metrics["limit_pct"] == 25
    assert result.metrics["breached"]
    assert sum(r["exposure_rub"] for r in result.rows) == 100_000_000


def test_no_silent_date_fallback(agent):
    with pytest.raises(NoDataError):
        agent.tools.snapshot(date(2026, 9, 30))


def test_readonly_connection_blocks_write(agent):
    with readonly(agent.database) as con, pytest.raises(sqlite3.OperationalError):
        con.execute("DELETE FROM balances")


def test_half_up_rounding_and_empty_days(tmp_path):
    db = tmp_path / "tiny.sqlite"
    with sqlite3.connect(db) as con:
        con.executescript("""
            CREATE TABLE balances(as_of TEXT, cash_minor INTEGER);
            CREATE TABLE cashflows(as_of TEXT,due_date TEXT,direction TEXT,amount_minor INTEGER);
            INSERT INTO balances VALUES('2026-10-30', 100);
            INSERT INTO cashflows VALUES('2026-10-30','2026-10-31','out',1);
            INSERT INTO cashflows VALUES('2026-10-29','2026-10-31','out',999);
            INSERT INTO cashflows VALUES('2026-10-30','2026-10-30','out',999);
            INSERT INTO cashflows VALUES('2026-10-30','2026-11-02','out',999);
        """)
    result = TreasuryTools(db).snapshot(date(2026, 10, 30), horizon=2, stress_pct=50)
    assert result["rows"][0]["outflow_rub"] == 0.02
    assert result["rows"][1]["outflow_rub"] == 0
    assert result["metrics"]["closing_cash_rub"] == 0.98
