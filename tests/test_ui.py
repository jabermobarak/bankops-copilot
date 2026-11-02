"""Exercise the actual Streamlit widgets against a real local HTTP API."""

import socket
import threading
import time

import uvicorn
from streamlit.testing.v1 import AppTest

from bankops.api import create_app
from bankops.config import ROOT


def test_dashboard_and_stress_button(settings, monkeypatch):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(create_app(settings), host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        monkeypatch.setenv("BANKOPS_API_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("BANKOPS_API_KEY", "")
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        assert not app.exception
        assert not app.error
        assert app.metric[0].value == "₽26.0m"
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state["result"]["metrics"]["closing_cash_rub"] == 5_800_000
        assert [t.label for t in app.tabs] == ["Figures", "Policy evidence", "Execution trace"]
    finally:
        server.should_exit = True
        thread.join(timeout=10)
