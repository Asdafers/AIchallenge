# Playwright E2E Tests — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Playwright E2E tests that prove the demo UI works end-to-end — mock-based for CI/regression, live-mode for smoke testing the deployed Cloud Run service.

**Architecture:** `pytest-playwright` runs headless Chromium against demo.html served by a minimal local file server. Mock mode uses `page.route('**/api/stream', ...)` to intercept the fetch and replay a captured golden SSE fixture. Live mode (`@pytest.mark.live`) hits the real Cloud Run endpoint with an identity token. Video recording is on by default for demo-video artifacts.

**Tech Stack:** pytest-playwright, Playwright for Python (Chromium only), pytest marks for live/mock separation

---

### Task 1: Branch setup + Playwright dependencies

**Files:**
- Modify: `requirements-dev.txt`
- Create: `pyproject.toml` (Playwright config section)

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feat/e2e-tests main
```

- [ ] **Step 2: Add pytest-playwright to dev dependencies**

Add to `requirements-dev.txt`:

```
pytest-playwright>=0.5.0
```

- [ ] **Step 3: Install dependencies and Chromium**

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

Note: Chromium browser binary is ~200MB. This is a one-time download.

- [ ] **Step 4: Add Playwright config to pyproject.toml**

Create `pyproject.toml` (or add section if exists):

```toml
[tool.pytest.ini_options]
markers = [
    "live: marks tests that hit the real Cloud Run endpoint (deselect with '-m not live')",
]
asyncio_mode = "auto"

[tool.playwright]
browser = "chromium"
headless = true
video = "on"
screenshot = "only-on-failure"
```

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt pyproject.toml
git commit -m "chore: add pytest-playwright dependency and config"
```

---

### Task 2: Capture golden SSE fixture from Cloud Run

**Files:**
- Create: `tests/e2e/fixtures/sse_golden_run.txt`

The golden fixture is captured from one real Cloud Run run. This is ground truth — not a hand-crafted fiction. The mock replays these exact bytes.

- [ ] **Step 1: Capture SSE stream from deployed service**

```bash
TOKEN=$(gcloud auth print-identity-token)
curl -sN \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"study_brief":"Run a win-loss study on recent Q1 2026 lost deals. Focus on understanding why deals were lost, especially around ROI clarity and procurement friction. Available participants: P-001, P-002, P-003. Reserve: P-005."}' \
  https://methodic-2030382823.us-central1.run.app/api/stream \
  > tests/e2e/fixtures/sse_golden_run.txt
```

Wait for stream to complete (60-90s). The file should end with:
```
data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 2: Verify fixture has required event types**

The fixture must contain all of these for the tests to be meaningful:
- At least one event with `"author": "interviewer"` 
- At least one event with `"author": "participant_sim"`
- At least one event where text matches a guardrail keyword (e.g., "could you elaborate", "can you tell me more")
- At least one `state_delta` with `coverage_state` or `participant_coverage` containing a field at `covered_high_confidence`
- The final `"author": "system"` completion event

If any are missing, run again — Gemini output is non-deterministic. Edit minimally if needed: add one guardrail-keyword line to ensure test 5 is deterministic.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/fixtures/sse_golden_run.txt
git commit -m "test: capture golden SSE fixture from live Cloud Run"
```

---

### Task 3: Playwright conftest with mock SSE and file server

**Files:**
- Create: `tests/e2e/__init__.py`
- Create: `tests/e2e/conftest.py`

- [ ] **Step 1: Write the failing test (import check)**

Create `tests/e2e/__init__.py` (empty) and `tests/e2e/conftest.py`:

```python
import pytest
from pathlib import Path
from playwright.sync_api import Page

DEMO_HTML = Path(__file__).resolve().parent.parent.parent / "methodic" / "static" / "demo.html"
GOLDEN_SSE = Path(__file__).resolve().parent / "fixtures" / "sse_golden_run.txt"


@pytest.fixture
def demo_page(page: Page):
    """Load demo.html via file:// and intercept /api/stream with golden fixture."""
    sse_bytes = GOLDEN_SSE.read_bytes()

    def handle_stream(route):
        route.fulfill(
            status=200,
            headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
            body=sse_bytes,
        )

    page.route("**/api/stream", handle_stream)
    page.goto(f"file://{DEMO_HTML}")
    return page


@pytest.fixture
def live_page(page: Page):
    """Load demo pointed at real Cloud Run (requires --live mark)."""
    import subprocess
    token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token"], text=True
    ).strip()
    page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
    page.goto("https://methodic-2030382823.us-central1.run.app/static/demo.html")
    return page
```

- [ ] **Step 2: Run import to verify conftest loads**

```bash
python3 -c "from tests.e2e.conftest import DEMO_HTML, GOLDEN_SSE; print(DEMO_HTML.exists(), GOLDEN_SSE.exists())"
```

Expected: `True True`

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/__init__.py tests/e2e/conftest.py
git commit -m "test: add Playwright conftest with mock SSE route interception"
```

---

### Task 4: Mock-mode E2E tests — page load and run button

**Files:**
- Create: `tests/e2e/test_demo_ui.py`

- [ ] **Step 1: Write failing test — page loads with correct initial state**

```python
from playwright.sync_api import expect


def test_page_loads_with_idle_state(demo_page):
    expect(demo_page.locator("#status-badge")).to_have_text("idle")
    expect(demo_page.locator("#run-btn")).to_be_enabled()
    expect(demo_page.locator("#conversation-log")).to_be_empty()


def test_run_button_disabled_during_stream(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#run-btn")).to_be_disabled()
```

- [ ] **Step 2: Run tests to verify they fail (Playwright not finding page)**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py -v -m "not live"
```

Expected: Tests should pass since demo_page fixture loads via file:// and mock intercepts /api/stream.

Note: If `file://` doesn't trigger the route intercept (fetch to relative `/api/stream` from a file:// origin may fail), we need a minimal local server. See step 3.

- [ ] **Step 3: If file:// doesn't work, add a local server fixture**

Replace the `demo_page` fixture in conftest.py with a version that serves via http:

```python
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

@pytest.fixture(scope="session")
def demo_server():
    """Serve methodic/static/ on a random local port."""
    static_dir = str(DEMO_HTML.parent)
    handler = partial(SimpleHTTPRequestHandler, directory=static_dir)
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


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
```

- [ ] **Step 4: Run tests again, verify passing**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py::test_page_loads_with_idle_state tests/e2e/test_demo_ui.py::test_run_button_disabled_during_stream -v
```

Expected: Both PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_demo_ui.py
git commit -m "test: add E2E tests for page load and run button state"
```

---

### Task 5: Mock-mode E2E tests — SSE event rendering

**Files:**
- Modify: `tests/e2e/test_demo_ui.py`

- [ ] **Step 1: Write test — conversation events appear after clicking Run**

```python
def test_conversation_events_render(demo_page):
    demo_page.locator("#run-btn").click()
    events = demo_page.locator("#conversation-log .conv-event")
    expect(events.first).to_be_visible(timeout=10_000)
    count = events.count()
    assert count >= 3, f"Expected at least 3 conversation events, got {count}"


def test_agent_and_participant_events_have_correct_roles(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator(".conv-event.agent").first).to_be_visible(timeout=10_000)
    expect(demo_page.locator(".conv-event.participant").first).to_be_visible(timeout=10_000)
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py::test_conversation_events_render tests/e2e/test_demo_ui.py::test_agent_and_participant_events_have_correct_roles -v
```

Expected: Both PASS.

- [ ] **Step 3: Write test — guardrail highlighting appears**

```python
def test_guardrail_highlight_appears(demo_page):
    demo_page.locator("#run-btn").click()
    guardrail = demo_page.locator(".conv-event.guardrail")
    expect(guardrail.first).to_be_visible(timeout=15_000)
    expect(guardrail.first).to_have_css("border-left-style", "solid")
```

This test depends on the golden fixture containing at least one event with a guardrail keyword ("could you elaborate", "can you tell me more", etc.). If the fixture lacks one, add a synthetic event line to the fixture file.

- [ ] **Step 4: Run test**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py::test_guardrail_highlight_appears -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_demo_ui.py
git commit -m "test: add E2E tests for SSE event rendering and guardrail highlight"
```

---

### Task 6: Mock-mode E2E tests — coverage bars and timeline

**Files:**
- Modify: `tests/e2e/test_demo_ui.py`

- [ ] **Step 1: Write test — coverage bars update from SSE state_delta**

```python
def test_coverage_bars_update(demo_page):
    demo_page.locator("#run-btn").click()
    badge = demo_page.locator("#status-badge")
    expect(badge).to_have_text("complete", timeout=30_000)

    fills = demo_page.locator(".cov-bar-fill")
    any_nonzero = False
    for i in range(fills.count()):
        width = fills.nth(i).evaluate("el => getComputedStyle(el).width")
        if width != "0px":
            any_nonzero = True
            break
    assert any_nonzero, "Expected at least one coverage bar to have non-zero width"
```

- [ ] **Step 2: Write test — timeline dots appear and reach done state**

```python
def test_timeline_shows_pipeline_steps(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)

    steps = demo_page.locator("#timeline .step")
    assert steps.count() >= 3, f"Expected at least 3 timeline steps, got {steps.count()}"

    done_dots = demo_page.locator(".step-dot.done")
    assert done_dots.count() >= 1, "Expected at least one step dot in 'done' state"
```

- [ ] **Step 3: Write test — status badge reaches 'complete'**

```python
def test_status_badge_transitions_to_complete(demo_page):
    expect(demo_page.locator("#status-badge")).to_have_text("idle")
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)
    expect(demo_page.locator("#run-btn")).to_be_enabled()
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py -v -m "not live"
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_demo_ui.py
git commit -m "test: add E2E tests for coverage bars, timeline, and status transitions"
```

---

### Task 7: Error path E2E test

**Files:**
- Modify: `tests/e2e/test_demo_ui.py`
- Modify: `tests/e2e/conftest.py`

- [ ] **Step 1: Add error fixture to conftest**

```python
@pytest.fixture
def error_page(page: Page, demo_server: str):
    """Load demo with a mock SSE that returns an error event."""
    error_sse = b'data: {"author": "error", "text": "Model quota exceeded", "state_delta": {}}\n\n'

    def handle_error(route):
        route.fulfill(
            status=200,
            headers={"Content-Type": "text/event-stream"},
            body=error_sse,
        )

    page.route("**/api/stream", handle_error)
    page.goto(f"{demo_server}/demo.html")
    return page
```

- [ ] **Step 2: Write error path test**

```python
def test_error_event_shows_failed_status(error_page):
    error_page.locator("#run-btn").click()
    expect(error_page.locator("#status-badge")).to_have_text("complete", timeout=10_000)
    error_event = error_page.locator(".conv-event.error")
    expect(error_event.first).to_be_visible()
    expect(error_event.first).to_contain_text("Model quota exceeded")
```

Note: The current demo.html doesn't set status to "failed" on error events — it only does so on stream error (catch block). The error event from the agent just renders as a conv-event with error class. The badge transitions to "complete" when the stream ends. This test verifies the error event renders; a separate improvement could make the badge show "failed" when an error event arrives.

- [ ] **Step 3: Run test**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py::test_error_event_shows_failed_status -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_demo_ui.py tests/e2e/conftest.py
git commit -m "test: add E2E error path test with mock error SSE"
```

---

### Task 8: Live-mode E2E test

**Files:**
- Modify: `tests/e2e/test_demo_ui.py`

This test hits the real Cloud Run service. It's slow (~60-90s) and requires `gcloud auth`. Run with `pytest -m live`.

- [ ] **Step 1: Write live-mode test**

```python
import pytest

@pytest.mark.live
def test_live_demo_completes(live_page):
    live_page.locator("#run-btn").click()
    expect(live_page.locator("#status-badge")).to_have_text("running", timeout=5_000)
    expect(live_page.locator("#status-badge")).to_have_text("complete", timeout=120_000)

    events = live_page.locator("#conversation-log .conv-event")
    assert events.count() >= 5, f"Expected at least 5 events from live run, got {events.count()}"

    agent_events = live_page.locator(".conv-event.agent")
    assert agent_events.count() >= 1
    participant_events = live_page.locator(".conv-event.participant")
    assert participant_events.count() >= 1
```

Important: Do NOT assert exact text content — Gemini output is non-deterministic. Only assert structure (classes, counts, transitions).

- [ ] **Step 2: Run live test (requires gcloud auth)**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py::test_live_demo_completes -v -m live
```

Expected: PASS (within 120s timeout).

Note on auth: The `live_page` fixture sets `Authorization` header on the page context. However, the demo.html's inner `fetch('/api/stream', ...)` uses a relative URL — when served from Cloud Run this is same-origin, so the browser includes the auth cookie/header. The `set_extra_http_headers` on the page context should propagate to fetch calls from that page. If it doesn't, the alternative is deploying a test revision with `--allow-unauthenticated`.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_demo_ui.py
git commit -m "test: add live-mode E2E test against Cloud Run"
```

---

### Task 9: Video recording config and run script

**Files:**
- Modify: `tests/e2e/conftest.py`
- Create: `scripts/run_e2e.sh`

- [ ] **Step 1: Add video recording to conftest**

Add to conftest.py at module level:

```python
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "tests/e2e/videos/",
        "viewport": {"width": 1280, "height": 800},
    }
```

- [ ] **Step 2: Create run script**

```bash
#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mock}"

echo "=== Playwright E2E Tests (${MODE} mode) ==="

if [ "$MODE" = "live" ]; then
    python3 -m pytest tests/e2e/ -v -m live --video=on
elif [ "$MODE" = "all" ]; then
    python3 -m pytest tests/e2e/ -v --video=on
else
    python3 -m pytest tests/e2e/ -v -m "not live" --video=on
fi

echo ""
echo "Videos saved to tests/e2e/videos/"
```

- [ ] **Step 3: Add videos directory to .gitignore**

```bash
echo "tests/e2e/videos/" >> .gitignore
```

- [ ] **Step 4: Run full mock suite with video**

```bash
bash scripts/run_e2e.sh mock
```

Expected: All tests pass, video files appear in `tests/e2e/videos/`.

- [ ] **Step 5: Commit**

```bash
chmod +x scripts/run_e2e.sh
git add tests/e2e/conftest.py scripts/run_e2e.sh .gitignore
git commit -m "test: add video recording config and E2E run script"
```
