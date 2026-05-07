"""E2E tests for Methodic demo UI — mock SSE and live Cloud Run modes."""

import pytest
from playwright.sync_api import expect


def test_page_loads_with_idle_state(demo_page):
    expect(demo_page.locator("#status-badge")).to_have_text("idle")
    expect(demo_page.locator("#run-btn")).to_be_enabled()
    expect(demo_page.locator("#chat-messages")).to_be_empty()


def test_run_button_disabled_on_click(demo_page):
    """Button disables synchronously in the click handler."""
    disabled_after_click = demo_page.evaluate("""() => {
        const btn = document.getElementById('run-btn');
        btn.click();
        return btn.disabled;
    }""")
    assert disabled_after_click, "Button should be disabled immediately after click"


def test_status_badge_transitions_to_complete(demo_page):
    expect(demo_page.locator("#status-badge")).to_have_text("idle")
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)
    expect(demo_page.locator("#run-btn")).to_be_enabled()


def test_conversation_events_render(demo_page):
    demo_page.locator("#run-btn").click()
    events = demo_page.locator("#chat-messages .bubble")
    expect(events.first).to_be_visible(timeout=10_000)
    count = events.count()
    assert count >= 3, f"Expected at least 3 conversation events, got {count}"


def test_agent_and_participant_roles(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator(".bubble.agent").first).to_be_visible(timeout=10_000)
    expect(demo_page.locator(".bubble.participant").first).to_be_visible(timeout=10_000)


def test_guardrail_highlight_appears(demo_page):
    demo_page.locator("#run-btn").click()
    probe = demo_page.locator(".probe-badge")
    expect(probe.first).to_be_visible(timeout=15_000)
    expect(probe.first).to_contain_text("PROBE")


def test_coverage_bars_update(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)

    high_confidence_cards = demo_page.locator(".insight-card.covered_high_confidence")
    assert high_confidence_cards.count() >= 1, "Expected at least one insight card at covered_high_confidence state"


def test_timeline_shows_pipeline_steps(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)

    steps = demo_page.locator("#phase-list .phase-item")
    assert steps.count() >= 3, f"Expected at least 3 pipeline steps, got {steps.count()}"

    done_dots = demo_page.locator(".phase-dot.done")
    assert done_dots.count() >= 1, "Expected at least one phase dot in 'done' state"


def test_error_event_renders(error_page):
    error_page.locator("#run-btn").click()
    error_event = error_page.locator(".bubble.error")
    expect(error_event.first).to_be_visible(timeout=10_000)
    expect(error_event.first).to_contain_text("Model quota exceeded")


@pytest.mark.live
def test_live_demo_completes(live_page):
    live_page.locator("#run-btn").click()
    expect(live_page.locator("#status-badge")).to_have_text("running", timeout=5_000)
    expect(live_page.locator("#status-badge")).to_have_text("complete", timeout=600_000)

    events = live_page.locator("#chat-messages .bubble")
    assert events.count() >= 5, f"Expected at least 5 events from live run, got {events.count()}"

    assert live_page.locator(".bubble.agent").count() >= 1
    assert live_page.locator(".bubble.participant").count() >= 1
