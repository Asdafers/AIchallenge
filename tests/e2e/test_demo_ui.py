"""E2E tests for Methodic demo UI — mock SSE and live Cloud Run modes."""

import pytest
from playwright.sync_api import expect


def test_page_loads_with_idle_state(demo_page):
    expect(demo_page.locator("#status-badge")).to_have_text("idle")
    expect(demo_page.locator("#run-btn")).to_be_enabled()
    expect(demo_page.locator("#conversation-log")).to_be_empty()


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
    events = demo_page.locator("#conversation-log .conv-event")
    expect(events.first).to_be_visible(timeout=10_000)
    count = events.count()
    assert count >= 3, f"Expected at least 3 conversation events, got {count}"


def test_agent_and_participant_roles(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator(".conv-event.agent").first).to_be_visible(timeout=10_000)
    expect(demo_page.locator(".conv-event.participant").first).to_be_visible(timeout=10_000)


def test_guardrail_highlight_appears(demo_page):
    demo_page.locator("#run-btn").click()
    guardrail = demo_page.locator(".conv-event.guardrail")
    expect(guardrail.first).to_be_visible(timeout=15_000)
    expect(guardrail.first).to_have_css("border-left-style", "solid")


def test_coverage_bars_update(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)

    fills = demo_page.locator(".cov-bar-fill")
    found_high_confidence = False
    for i in range(fills.count()):
        fill = fills.nth(i)
        bg = fill.evaluate("el => el.style.background")
        if "46, 204, 113" in bg:
            found_high_confidence = True
            width = fill.evaluate("el => el.style.width")
            assert width == "100%", f"High-confidence bar should be at 100%, got {width}"
            break
    assert found_high_confidence, "Expected at least one bar at covered_high_confidence color"


def test_timeline_shows_pipeline_steps(demo_page):
    demo_page.locator("#run-btn").click()
    expect(demo_page.locator("#status-badge")).to_have_text("complete", timeout=30_000)

    steps = demo_page.locator("#timeline .step")
    assert steps.count() >= 3, f"Expected at least 3 timeline steps, got {steps.count()}"

    done_dots = demo_page.locator(".step-dot.done")
    assert done_dots.count() >= 1, "Expected at least one step dot in 'done' state"


def test_error_event_renders(error_page):
    error_page.locator("#run-btn").click()
    error_event = error_page.locator(".conv-event.error")
    expect(error_event.first).to_be_visible(timeout=10_000)
    expect(error_event.first).to_contain_text("Model quota exceeded")


@pytest.mark.live
def test_live_demo_completes(live_page):
    live_page.locator("#run-btn").click()
    expect(live_page.locator("#status-badge")).to_have_text("running", timeout=5_000)
    expect(live_page.locator("#status-badge")).to_have_text("complete", timeout=600_000)

    events = live_page.locator("#conversation-log .conv-event")
    assert events.count() >= 5, f"Expected at least 5 events from live run, got {events.count()}"

    assert live_page.locator(".conv-event.agent").count() >= 1
    assert live_page.locator(".conv-event.participant").count() >= 1
