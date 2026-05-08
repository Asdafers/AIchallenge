"""Scenario-based e2e tests for interactive interview UI."""

import json
from pathlib import Path

from playwright.sync_api import Page, expect

FIXTURES = Path(__file__).resolve().parent / "fixtures"

MOCK_RESULTS = json.dumps({
    "participant_responses": {"P-INTERACTIVE": {"primary_loss_reason": "unclear_roi"}},
    "coverage_state": {"primary_loss_reason": "covered_high_confidence"},
})


def _route_and_start(page: Page, demo_server: str, fixture_name: str):
    sse_bytes = (FIXTURES / fixture_name).read_bytes()

    page.route("**/api/interactive/start", lambda r: r.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "session_id": "INT-test",
            "stream_url": "/api/interactive/INT-test/stream",
            "title": "Test Study",
            "persona_hint": "Test persona.",
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
    page.route("**/api/interactive/*/results", lambda r: r.fulfill(
        status=200,
        headers={"Content-Type": "application/json"},
        body=MOCK_RESULTS,
    ))

    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    return page


# ─── Perfect Coverage Scenario ──────────────────────────────────────

def test_perfect_all_fields_high(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    high_badges = page.locator("#results-overlay .coverage-badge.high")
    assert high_badges.count() == 8, f"Expected 8 HIGH badges in results, got {high_badges.count()}"


def test_perfect_no_missing_fields(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    miss_badges = page.locator("#results-overlay .coverage-badge.miss")
    assert miss_badges.count() == 0, f"Expected 0 MISSING badges in results, got {miss_badges.count()}"


def test_perfect_turn_count(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    results = page.locator("#results-overlay")
    expect(results).to_contain_text("9")


# ─── Partial Coverage Scenario ──────────────────────────────────────

def test_partial_mixed_coverage(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_partial.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    high_badges = page.locator("#results-overlay .coverage-badge.high")
    assert high_badges.count() == 4, f"Expected 4 HIGH badges, got {high_badges.count()}"

    miss_badges = page.locator("#results-overlay .coverage-badge.miss")
    assert miss_badges.count() == 2, f"Expected 2 MISSING badges, got {miss_badges.count()}"


def test_partial_low_confidence_count(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_partial.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    low_badges = page.locator("#results-overlay .coverage-badge.low")
    assert low_badges.count() == 2, f"Expected 2 LOW badges, got {low_badges.count()}"


# ─── Error Scenario ─────────────────────────────────────────────────

def test_error_shows_error_bubble(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_error.txt")

    error_bubble = page.locator(".bubble.error")
    expect(error_bubble.first).to_be_visible(timeout=10_000)
    expect(error_bubble.first).to_contain_text("Model quota exceeded")


def test_error_status_badge_shows_failed(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_error.txt")
    expect(page.locator("#status-badge")).to_have_text("failed", timeout=10_000)


def test_error_partial_coverage_preserved(page: Page, demo_server: str):
    """Even after error, coverage data from before the error should be visible in sidebar."""
    _route_and_start(page, demo_server, "sse_scenario_error.txt")
    expect(page.locator("#status-badge")).to_have_text("failed", timeout=10_000)

    insight_cards = page.locator(".insight-card")
    assert insight_cards.count() >= 1, "Expected insight cards even after error"


def test_error_results_overlay_shows(page: Page, demo_server: str):
    """Error path should still show results overlay (handleEvent calls showResults on error)."""
    _route_and_start(page, demo_server, "sse_scenario_error.txt")
    expect(page.locator("#status-badge")).to_have_text("failed", timeout=10_000)

    results = page.locator("#results-overlay")
    expect(results).to_be_visible(timeout=5_000)


# ─── Edge Case Scenario ─────────────────────────────────────────────

def test_edge_methodology_revision_then_approval(page: Page, demo_server: str):
    """Both methodology_reviewer and methodology author aliases produce methodology cards."""
    _route_and_start(page, demo_server, "sse_scenario_edge.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    agentic_cards = page.locator(".agentic-card.methodology")
    assert agentic_cards.count() == 2, f"Expected exactly 2 methodology cards, got {agentic_cards.count()}"

    first_text = agentic_cards.nth(0).locator(".agentic-text").text_content() or ""
    assert "REVISE_REQUIRED" in first_text, f"Expected REVISE_REQUIRED in first card: {first_text}"

    second_text = agentic_cards.nth(1).locator(".agentic-text").text_content() or ""
    assert "APPROVED" in second_text, f"Expected APPROVED in second card: {second_text}"


def test_edge_ambiguous_field_shown(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_edge.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    ambig_badges = page.locator("#results-overlay .coverage-badge.ambig")
    assert ambig_badges.count() >= 1, f"Expected at least 1 AMBIG badge in results"
