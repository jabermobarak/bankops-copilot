import json
import logging
import secrets
import threading
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from bankops.agent import BankOpsAgent
from bankops.config import Settings
from bankops.models import AskRequest, AskResponse

logger = logging.getLogger("bankops.audit")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.propagate = False


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings.from_env()
    slots = threading.BoundedSemaphore(4)
    lock = threading.Lock()
    counts = {"answered": 0, "refused": 0, "insufficient_evidence": 0, "errors": 0}

    @asynccontextmanager
    async def lifespan(app):
        app.state.agent = BankOpsAgent(cfg)
        yield

    app = FastAPI(title="BankOps Copilot", version="1.0.0", lifespan=lifespan)

    def authorize(x_api_key: str | None = Header(default=None)):
        if cfg.api_key and not secrets.compare_digest(x_api_key or "", cfg.api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/health")
    def health():
        return {"status": "ok", "synthetic_data": True}

    @app.get("/v1/config", dependencies=[Depends(authorize)])
    def config():
        return {
            "provider": cfg.provider,
            "retriever": cfg.retriever,
            "snapshot_start": "2026-10-01",
            "snapshot_end": "2026-10-30",
            "read_only": True,
            "synthetic_data": True,
        }

    def run(req: AskRequest):
        if not slots.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Busy; retry shortly")
        try:
            result = app.state.agent.ask(req)
            with lock:
                counts[result.status] += 1
            # Deliberately omit prompts, SQL parameters, financial values and secrets.
            logger.info(
                json.dumps(
                    {
                        "request_id": result.request_id,
                        "task": result.task,
                        "status": result.status,
                        "elapsed_ms": result.elapsed_ms,
                        "provider": result.provider,
                    }
                )
            )
            return result
        except Exception as error:
            with lock:
                counts["errors"] += 1
            logger.error("bankops_request_failed type=%s", type(error).__name__)
            raise HTTPException(
                status_code=503, detail="Analysis unavailable; check local setup"
            ) from None
        finally:
            slots.release()

    @app.post("/v1/ask", response_model=AskResponse, dependencies=[Depends(authorize)])
    def ask(req: AskRequest):
        return run(req)

    @app.get("/v1/overview", response_model=AskResponse, dependencies=[Depends(authorize)])
    def overview(
        as_of: date = date(2026, 10, 30), horizon_days: int = Query(default=7, ge=1, le=30)
    ):
        return run(
            AskRequest(
                question="Show liquidity", task="liquidity", as_of=as_of, horizon_days=horizon_days
            )
        )

    @app.get("/metrics", response_class=PlainTextResponse, dependencies=[Depends(authorize)])
    def metrics():
        with lock:
            snapshot = dict(counts)
        return "# TYPE bankops_requests_total counter\n" + "".join(
            f'bankops_requests_total{{status="{key}"}} {value}\n' for key, value in snapshot.items()
        )

    return app


app = create_app()
