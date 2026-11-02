from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Task = Literal["auto", "liquidity", "forecast", "exposure", "stress", "policy"]


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=2000)
    task: Task = "auto"
    as_of: date = date(2026, 10, 30)
    horizon_days: int = Field(default=7, ge=1, le=30)
    stress_pct: int | None = Field(default=None, ge=0, le=100)
    language: Literal["en", "ru"] = "en"

    @field_validator("question")
    @classmethod
    def strip_question(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Question is too short")
        return value


class Source(BaseModel):
    id: str
    title: str
    effective_from: date
    effective_to: date | None = None
    text: str
    score: float = 0.0


class AskResponse(BaseModel):
    request_id: str
    task: str
    status: Literal["answered", "refused", "insufficient_evidence"]
    answer: str
    narrative: str | None = None
    provider: str
    retriever: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    elapsed_ms: float
