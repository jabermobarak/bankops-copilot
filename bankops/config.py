import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    runtime: Path = ROOT / "runtime"
    provider: str = "extractive"
    retriever: str = "lexical"
    api_key: str = ""

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env", override=False)
        provider = os.getenv("BANKOPS_PROVIDER", "extractive")
        retriever = os.getenv("BANKOPS_RETRIEVER", "lexical")
        if provider not in {"extractive", "gigachat", "openai_compatible"}:
            raise ValueError("Unknown BANKOPS_PROVIDER")
        if retriever not in {"lexical", "semantic"}:
            raise ValueError("Unknown BANKOPS_RETRIEVER")
        return cls(
            runtime=Path(os.getenv("BANKOPS_RUNTIME", str(ROOT / "runtime"))).resolve(),
            provider=provider,
            retriever=retriever,
            api_key=os.getenv("BANKOPS_API_KEY", ""),
        )
