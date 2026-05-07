#!/usr/bin/env python3
"""Record a demo video of the Methodic UI using Playwright.

Usage:
    python3 scripts/record_demo.py              # live Cloud Run
    python3 scripts/record_demo.py --mock       # local mock (no auth needed)

Outputs:
    demo_output/demo.webm          — full video
    demo_output/01_idle.png        — empty state
    demo_output/02_running.png     — mid-interview
    demo_output/03_guardrail.png   — guardrail probe highlight
    demo_output/04_complete.png    — final coverage
"""

import argparse
import subprocess
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "methodic" / "static"
GOLDEN_SSE = ROOT / "tests" / "e2e" / "fixtures" / "sse_golden_run.txt"
OUTPUT_DIR = ROOT / "demo_output"
CLOUD_RUN_URL = "https://methodic-2030382823.us-central1.run.app"


def start_local_server():
    handler = partial(SimpleHTTPRequestHandler, directory=str(STATIC_DIR))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}", server


def main():
    parser = argparse.ArgumentParser(description="Record Methodic demo video")
    parser.add_argument("--mock", action="store_true", help="Use mock SSE fixture instead of live Cloud Run")
    parser.add_argument("--headed", action="store_true", help="Show browser window during recording")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        server = None
        if args.mock:
            base_url, server = start_local_server()
            sse_bytes = GOLDEN_SSE.read_bytes()
            page.route("**/api/stream", lambda route: route.fulfill(
                status=200,
                headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
                body=sse_bytes,
            ))
            page.goto(f"{base_url}/demo.html")
        else:
            token = subprocess.check_output(
                ["gcloud", "auth", "print-identity-token"], text=True
            ).strip()
            context.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            page.goto(f"{CLOUD_RUN_URL}/static/demo.html")

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUTPUT_DIR / "01_idle.png"))
        print("📸 01_idle.png — empty state captured")

        page.locator("#run-btn").click()
        page.wait_for_timeout(500)

        if args.mock:
            page.wait_for_function(
                'document.querySelectorAll(".conv-event").length >= 3',
                timeout=10_000,
            )
            page.wait_for_timeout(300)
        else:
            page.wait_for_function(
                'document.querySelectorAll(".conv-event").length >= 4',
                timeout=60_000,
            )
            page.wait_for_timeout(2000)

        page.screenshot(path=str(OUTPUT_DIR / "02_running.png"))
        print("📸 02_running.png — mid-interview captured")

        try:
            page.wait_for_function(
                'document.querySelector(".conv-event.guardrail") !== null',
                timeout=30_000 if not args.mock else 5_000,
            )
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUTPUT_DIR / "03_guardrail.png"))
            print("📸 03_guardrail.png — guardrail highlight captured")
        except Exception:
            print("⚠️  No guardrail event detected, skipping 03_guardrail.png")

        page.wait_for_function(
            'document.getElementById("status-badge").textContent === "complete"',
            timeout=120_000 if not args.mock else 10_000,
        )
        page.wait_for_timeout(1000)
        page.screenshot(path=str(OUTPUT_DIR / "04_complete.png"))
        print("📸 04_complete.png — final coverage captured")

        page.wait_for_timeout(2000)

        context.close()
        browser.close()
        if server:
            server.shutdown()

    video_files = list(OUTPUT_DIR.glob("*.webm"))
    if video_files:
        latest = max(video_files, key=lambda f: f.stat().st_mtime)
        target = OUTPUT_DIR / "demo.webm"
        if latest != target:
            latest.rename(target)
        print(f"\n🎬 Video saved: {target}")
        print(f"   Screenshots: {OUTPUT_DIR}/01_idle.png .. 04_complete.png")
    else:
        print("\n⚠️  No video file found")


if __name__ == "__main__":
    main()
