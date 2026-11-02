"""Small, transparent heuristics; these are not a general prompt-injection defense."""

import re

INJECTION = re.compile(
    r"ignore.{0,40}(instructions|rules|prompt)|system\s*prompt|"
    r"reveal.{0,30}(secret|token|key)|игнорир\w*.{0,40}(правил|инструкц)|"
    r"покажи.{0,25}(токен|пароль)",
    re.I,
)
WRITE = re.compile(
    r"\b(delete|truncate|insert|update|transfer|execute|send|pay)\b|\bdrop\s+(table|database|schema)\b|"
    r"удал\w*|перевед\w*|перевести|оплат\w*|отправ\w*",
    re.I,
)
IDENTIFIER = re.compile(r"\b(?:\d[ -]?){16}\b")


def refusal_reason(question: str) -> str | None:
    if INJECTION.search(question):
        return "Instruction override / secret extraction request"
    if WRITE.search(question):
        return "Only read-only analysis is supported"
    if IDENTIFIER.search(question):
        return "Potential payment-card identifier; use synthetic data only"
    return None
