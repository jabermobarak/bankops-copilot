"""Three reproducible investigations without starting a web server."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bankops.agent import BankOpsAgent  # noqa: E402
from bankops.config import Settings  # noqa: E402
from bankops.models import AskRequest  # noqa: E402

if __name__ == "__main__":
    agent = BankOpsAgent(Settings.from_env())
    for question in [
        "Show liquidity",
        "What if outflows increase by 20%?",
        "Show counterparty exposure",
    ]:
        result = agent.ask(AskRequest(question=question))
        print(question)
        print(result.answer)
        print(json.dumps(result.metrics, indent=2, ensure_ascii=False))
