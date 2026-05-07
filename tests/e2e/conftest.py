import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from playwright.sync_api import Page

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "methodic" / "static"
GOLDEN_SSE = Path(__file__).resolve().parent / "fixtures" / "sse_golden_run.txt"


@pytest.fixture(scope="session")
def demo_server():
    handler = partial(SimpleHTTPRequestHandler, directory=str(STATIC_DIR))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "tests/e2e/videos/",
        "viewport": {"width": 1280, "height": 800},
    }


@pytest.fixture
def demo_page(page: Page, demo_server: str):
    sse_bytes = GOLDEN_SSE.read_bytes()

    def handle_stream(route):
        route.fulfill(
            status=200,
            headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
            body=sse_bytes,
        )

    page.route("**/api/stream", handle_stream)
    page.goto(f"{demo_server}/demo.html")
    return page


@pytest.fixture
def error_page(page: Page, demo_server: str):
    error_sse = b'data: {"author": "error", "text": "Model quota exceeded", "state_delta": {}}\n\ndata: {"author": "system", "text": "Stream complete.", "state_delta": {}}\n\n'

    def handle_error(route):
        route.fulfill(
            status=200,
            headers={"Content-Type": "text/event-stream"},
            body=error_sse,
        )

    page.route("**/api/stream", handle_error)
    page.goto(f"{demo_server}/demo.html")
    return page


@pytest.fixture
def live_page(page: Page):
    import subprocess
    token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token"], text=True
    ).strip()
    page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
    page.goto("https://methodic-2030382823.us-central1.run.app/static/demo.html")
    return page
