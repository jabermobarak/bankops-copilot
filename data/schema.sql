CREATE TABLE balances (
    as_of TEXT NOT NULL,
    desk TEXT NOT NULL,
    cash_minor INTEGER NOT NULL CHECK(cash_minor >= 0),
    PRIMARY KEY(as_of, desk)
);
CREATE TABLE cashflows (
    id TEXT PRIMARY KEY,
    as_of TEXT NOT NULL,
    due_date TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('in', 'out')),
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    counterparty TEXT NOT NULL,
    category TEXT NOT NULL
);
CREATE TABLE exposures (
    as_of TEXT NOT NULL,
    counterparty TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK(amount_minor >= 0),
    PRIMARY KEY(as_of, counterparty)
);
