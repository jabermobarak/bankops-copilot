"""Regenerate the committed synthetic fixture. No real customers or Sber data."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(name, columns, rows):
    with (ROOT / "data" / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    rng = random.Random(42)
    balances, flows, exposures = [], [], []
    for n in range(30):
        as_of = date(2026, 10, 1) + timedelta(days=n)
        for desk, rub in [("Corporate", 12_000_000), ("Retail", 8_000_000), ("Markets", 6_000_000)]:
            cash = rub if n == 29 else rub + rng.randint(-10, 10) * 100_000
            balances.append((as_of, desk, cash * 100))
        for day in range(1, 31):
            due = as_of + timedelta(days=day)
            for direction, latest in [
                ("in", [5, 3, 4, 2, 6, 4, 5]),
                ("out", [4, 9, 5, 10, 3, 4, 6]),
            ]:
                amount = (
                    latest[day - 1] * 1_000_000
                    if n == 29 and day <= 7
                    else rng.randint(2, 6) * 1_000_000
                )
                flows.append(
                    (
                        f"CF-{n:02}-{day:02}-{direction}",
                        as_of,
                        due,
                        direction,
                        amount * 100,
                        "Synthetic Company " + ("A" if day % 2 else "B"),
                        "Receivable" if direction == "in" else "Payable",
                    )
                )
        for name, millions in [
            ("Synthetic Alpha", 40),
            ("Synthetic Beta", 25),
            ("Synthetic Gamma", 20),
            ("Synthetic Delta", 15),
        ]:
            exposures.append((as_of, name, millions * 1_000_000 * 100))
    write("balances.csv", ["as_of", "desk", "cash_minor"], balances)
    write(
        "cashflows.csv",
        ["id", "as_of", "due_date", "direction", "amount_minor", "counterparty", "category"],
        flows,
    )
    write("exposures.csv", ["as_of", "counterparty", "amount_minor"], exposures)
    print(f"Created {len(balances)} balances, {len(flows)} cashflows, {len(exposures)} exposures.")


if __name__ == "__main__":
    main()
