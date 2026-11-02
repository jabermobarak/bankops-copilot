"""Start API + browser UI from the same interpreter, on Windows/macOS/Linux."""

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    processes = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    try:
        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "bankops.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=ROOT,
            env=env,
        )
        processes.append(api)
        ready = False
        for _ in range(100):
            if api.poll() is not None:
                raise RuntimeError("API stopped during startup; see terminal output above")
            try:
                with httpx.Client(timeout=1, trust_env=False) as client:
                    ready = client.get("http://127.0.0.1:8000/health").status_code == 200
                if ready:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        if not ready:
            raise RuntimeError("API startup timed out")
        ui = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                "8501",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=ROOT,
            env=env,
        )
        processes.append(ui)
        print("Open http://localhost:8501 — API docs: http://localhost:8000/docs", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()


if __name__ == "__main__":
    main()
