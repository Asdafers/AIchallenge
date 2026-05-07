"""E2E browser tests for interactive interview UI."""

import json
from pathlib import Path

from playwright.sync_api import Page, expect

INTERACTIVE_SSE = Path(__file__).resolve().parent / "fixtures" / "sse_interactive_run.txt"


def _route_interactive_api(page: Page, sse_bytes: bytes):
    page.route("**/api/interactive/start", lambda r: r.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "session_id": "INT-test",
            "stream_url": "/api/interactive/INT-test/stream",
            "title": "Q1 2026 Lost Deal Analysis",
            "persona_hint": "VP of Engineering at a mid-market SaaS company.",
        }),
    ))
    page.route("**/api/interactive/*/stream", lambda r: r.fulfill(
        status=200,
        headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
        body=sse_bytes,
    ))
    page.route("**/api/interactive/*/respond", lambda r: r.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body='{"status":"ok"}',
    ))


def _start_and_wait_for_app(page: Page, demo_server: str):
    sse_bytes = INTERACTIVE_SSE.read_bytes()
    _route_interactive_api(page, sse_bytes)
    page.goto(f"{demo_server}/interactive.html")

    page.locator(".preset-card").first.click()
    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    return page


def test_config_screen_loads(page: Page, demo_server: str):
    page.goto(f"{demo_server}/interactive.html")
    expect(page.locator("#config-screen")).to_be_visible()
    expect(page.locator("#start-btn")).to_be_visible()
    preset_cards = page.locator(".preset-card")
    assert preset_cards.count() == 3


def test_preset_selection_highlights(page: Page, demo_server: str):
    page.goto(f"{demo_server}/interactive.html")
    first_card = page.locator(".preset-card").first
    first_card.click()
    assert "selected" in (first_card.get_attribute("class") or "")


def test_config_to_app_transition(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#config-screen")).to_be_hidden()
    expect(page.locator("#app")).to_be_visible()


def test_persona_hint_displayed(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    system_msg = page.locator(".system-msg")
    expect(system_msg.first).to_contain_text("VP of Engineering")


def test_methodology_json_renders_verdict(page: Page, demo_server: str):
    """Regression: methodology reviewer JSON should render as verdict, not raw JSON."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    agentic_card = page.locator(".agentic-card.methodology")
    expect(agentic_card.first).to_be_visible(timeout=5_000)

    card_text = agentic_card.first.locator(".agentic-text").text_content() or ""
    assert "Verdict: APPROVED" in card_text, f"Expected 'Verdict: APPROVED' but got: {card_text}"
    assert not card_text.startswith("{"), f"Raw JSON leaked into agentic card: {card_text}"


def test_interviewer_bubble_appears(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    agent_bubble = page.locator(".bubble.agent")
    expect(agent_bubble.first).to_be_visible(timeout=10_000)
    expect(agent_bubble.first).to_contain_text("purchasing decision")


def test_input_enabled_on_input_requested(page: Page, demo_server: str):
    """When input_requested delta arrives, enableInput() fires synchronously."""
    sse_bytes = INTERACTIVE_SSE.read_bytes()
    _route_interactive_api(page, sse_bytes)
    page.goto(f"{demo_server}/interactive.html")

    page.locator(".preset-card").first.click()

    page.evaluate("""() => {
        window.__inputWasEnabled = false;
        const poll = setInterval(() => {
            const el = document.getElementById('user-input');
            if (!el) return;
            clearInterval(poll);
            const desc = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'disabled'
            );
            Object.defineProperty(el, 'disabled', {
                get() { return desc.get.call(this); },
                set(v) {
                    if (v === false) window.__inputWasEnabled = true;
                    desc.set.call(this, v);
                },
                configurable: true,
            });
        }, 5);
    }""")

    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    was_enabled = page.evaluate("window.__inputWasEnabled")
    assert was_enabled, "Input was never enabled during the stream"


def test_send_message_creates_participant_bubble(page: Page, demo_server: str):
    """Typing and sending a message should create a right-side participant bubble."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    page.evaluate("""() => {
        document.getElementById('results-overlay').classList.add('hidden');
        document.getElementById('user-input').disabled = false;
        document.getElementById('send-btn').disabled = false;
    }""")

    existing_count = page.locator(".bubble.participant").count()

    page.locator("#user-input").fill("It was about price.")
    page.locator("#send-btn").click()

    participant_bubbles = page.locator(".bubble.participant")
    expect(participant_bubbles.nth(existing_count)).to_be_visible(timeout=5_000)
    expect(participant_bubbles.nth(existing_count)).to_contain_text("It was about price.")


def test_results_overlay_on_complete(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    results = page.locator("#results-overlay")
    expect(results).to_be_visible(timeout=5_000)
    expect(results).to_contain_text("Interview Complete")

    stat_cards = results.locator(".stat-card")
    assert stat_cards.count() >= 3, f"Expected at least 3 stat cards, got {stat_cards.count()}"


def test_coverage_updates_during_stream(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    high_cards = page.locator(".insight-card.covered_high_confidence")
    assert high_cards.count() >= 1, "Expected at least one high-confidence insight card"


def test_phase_progress_rendered(page: Page, demo_server: str):
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    phase_items = page.locator("#phase-list .phase-item")
    assert phase_items.count() >= 2, f"Expected at least 2 phase items, got {phase_items.count()}"
