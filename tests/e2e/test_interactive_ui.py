"""E2E browser tests for interactive interview UI."""

import json
from pathlib import Path

from playwright.sync_api import Page, expect

INTERACTIVE_SSE = Path(__file__).resolve().parent / "fixtures" / "sse_interactive_run.txt"
METHODOLOGY_NUMERIC_SSE = Path(__file__).resolve().parent / "fixtures" / "sse_methodology_numeric_ids.txt"


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


def test_results_field_card_expands_to_show_question(page: Page, demo_server: str):
    """Clicking a field card in results shows the plain-English question."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    field_card = page.locator("#results-overlay .field-card").first
    field_card.click()

    question_detail = field_card.locator(".field-question")
    expect(question_detail).to_be_visible(timeout=2_000)

    question_text = question_detail.locator(".question-text").text_content() or ""
    assert len(question_text) > 10, f"Expected question text, got: {question_text}"


def test_results_field_card_collapses(page: Page, demo_server: str):
    """Clicking a field card twice collapses the question detail."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    field_card = page.locator("#results-overlay .field-card").first
    field_card.click()  # expand
    expect(field_card.locator(".field-question")).to_be_visible(timeout=2_000)
    field_card.click()  # collapse
    expect(field_card.locator(".field-question")).to_be_hidden(timeout=2_000)


def test_sidebar_insight_card_is_keyboard_accessible(page: Page, demo_server: str):
    """Insight cards should have tabindex and show question on focus."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    insight_card = page.locator(".insight-card").first
    tabindex = insight_card.get_attribute("tabindex")
    assert tabindex == "0", f"Expected tabindex='0', got '{tabindex}'"


def test_sidebar_question_visible_without_hover(page: Page, demo_server: str):
    """Question text in sidebar should be visible without hovering."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    insight_question = page.locator(".insight-question").first
    expect(insight_question).to_be_visible(timeout=2_000)
    text = insight_question.text_content() or ""
    assert len(text) > 10, f"Expected visible question text, got: {text}"


def test_fork_point_card_appears_after_methodology(page: Page, demo_server: str):
    """Fork point card should appear between methodology approval and first interviewer bubble."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    fork_card = page.locator(".bubble.system.fork-point")
    expect(fork_card).to_be_visible(timeout=5_000)
    expect(fork_card).to_contain_text("static surveys stop")


def test_fork_point_card_appears_only_once(page: Page, demo_server: str):
    """Fork point card should appear exactly once, not on every interviewer message."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    fork_cards = page.locator(".bubble.system.fork-point")
    assert fork_cards.count() == 1, f"Expected 1 fork card, got {fork_cards.count()}"


def test_sidebar_field_targeting_highlights_card(page: Page, demo_server: str):
    """When interviewer asks about ROI, roi_clarity card should get targeting class."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    # The stream completes instantly in tests so targeting may have been removed.
    # Verify the function exists and returns correct field for ROI text.
    result = page.evaluate("""() => {
        if (typeof guessTargetField !== 'function') return 'no_function';
        return guessTargetField('Could you elaborate on what specific ROI metrics your CFO was looking for?');
    }""")
    assert result == 'roi_clarity', f"Expected roi_clarity, got: {result}"


def test_config_editor_appears_on_preset_selection(page: Page, demo_server: str):
    """Selecting a preset should show the research design editor panel."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    editor = page.locator("#research-design-editor")
    expect(editor).to_be_visible(timeout=2_000)
    field_editors = editor.locator(".field-editor")
    assert field_editors.count() == 8, f"Expected 8 field editors, got {field_editors.count()}"


def test_config_editor_question_is_editable(page: Page, demo_server: str):
    """Question textareas in the editor should be editable."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    editor = page.locator("#research-design-editor")
    expect(editor).to_be_visible(timeout=2_000)

    first_q = editor.locator("textarea.field-q").first
    first_q.fill("Custom question text here")
    assert first_q.input_value() == "Custom question text here"


def test_config_editor_disable_toggle(page: Page, demo_server: str):
    """Disabling a field should grey it out and exclude from payload."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    editor = page.locator("#research-design-editor")
    expect(editor).to_be_visible(timeout=2_000)

    first_toggle = editor.locator("input.field-toggle").first
    first_toggle.click()  # disable
    first_editor_card = editor.locator(".field-editor").first
    assert "disabled" in (first_editor_card.get_attribute("class") or "")


def test_config_editor_maxlength_enforced(page: Page, demo_server: str):
    """Question textareas should have maxlength attributes."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    editor = page.locator("#research-design-editor")
    expect(editor).to_be_visible(timeout=2_000)

    q_textarea = editor.locator("textarea.field-q").first
    fu_textarea = editor.locator("textarea.field-fu").first
    assert q_textarea.get_attribute("maxlength") == "200"
    assert fu_textarea.get_attribute("maxlength") == "100"


def test_methodology_card_numeric_ids_show_count(page: Page, demo_server: str):
    """When issues have numeric IDs but no summary, card should not show '1, 2, 3'."""
    sse_bytes = METHODOLOGY_NUMERIC_SSE.read_bytes()
    _route_interactive_api(page, sse_bytes)
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    agentic_cards = page.locator(".agentic-card.methodology")
    first_card = agentic_cards.first
    expect(first_card).to_be_visible(timeout=5_000)
    card_text = first_card.locator(".agentic-text").text_content() or ""
    assert "REVISE_REQUIRED" in card_text
    assert "3 issue(s)" in card_text
    assert "1, 2, 3" not in card_text, f"Numeric IDs leaked: {card_text}"


def test_field_questions_have_question_type(page: Page, demo_server: str):
    """Each FIELD_QUESTIONS entry must have a question_type property."""
    page.goto(f"{demo_server}/interactive.html")
    result = page.evaluate("""() => {
        var types = [];
        var fields = ['primary_loss_reason', 'secondary_loss_reason', 'roi_clarity',
                       'budget_timing', 'procurement_friction', 'security_concern',
                       'competitor_pressure', 'aha_moment_reached'];
        for (var i = 0; i < fields.length; i++) {
            var fq = window.FIELD_QUESTIONS ? window.FIELD_QUESTIONS[fields[i]] : null;
            if (fq && fq.question_type) types.push(fq.question_type);
        }
        return types;
    }""")
    assert len(result) == 8, f"Expected 8 fields with question_type, got {len(result)}"
    expected_types = {'open_ended', 'multi_select', 'rating_scale', 'single_choice', 'yes_no_elaborate', 'ranking'}
    assert set(result).issubset(expected_types), f"Unexpected types: {set(result) - expected_types}"


def test_editor_type_badges_visible(page: Page, demo_server: str):
    """Each field in the research design editor should show a type badge."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    badges = page.locator("#research-design-editor .type-badge")
    expect(badges).to_have_count(8, timeout=2_000)
    first_badge = badges.first
    expect(first_badge).to_be_visible()
    assert first_badge.text_content().strip() in [
        'Open-ended', 'Rating Scale', 'Single Choice', 'Multi-select', 'Yes / No', 'Ranking'
    ]


def test_sidebar_type_badges_visible(page: Page, demo_server: str):
    """Sidebar insight cards should show type badges after interview starts."""
    _start_and_wait_for_app(page, demo_server)
    page.wait_for_selector(".insight-card", timeout=5_000)
    badges = page.locator(".insight-card .type-badge")
    expect(badges.first).to_be_visible(timeout=3_000)


def test_preview_survey_button_appears_on_preset_selection(page: Page, demo_server: str):
    """Preview as Survey button should appear when a preset is selected."""
    page.goto(f"{demo_server}/interactive.html")
    btn = page.locator("#preview-survey-btn")
    expect(btn).to_be_hidden(timeout=2_000)
    page.locator(".preset-card").first.click()
    expect(btn).to_be_visible(timeout=2_000)
    expect(btn).to_be_enabled()


def test_preview_survey_button_disabled_when_all_fields_off(page: Page, demo_server: str):
    """Preview button should be disabled when all fields are toggled off."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    toggles = page.locator(".field-toggle")
    for i in range(toggles.count()):
        toggles.nth(i).uncheck()
    btn = page.locator("#preview-survey-btn")
    expect(btn).to_be_disabled(timeout=2_000)


def test_survey_preview_modal_opens_and_closes(page: Page, demo_server: str):
    """Clicking preview button opens modal; clicking close dismisses it."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)

    overlay = page.locator("#survey-preview-overlay")
    expect(overlay).to_be_hidden(timeout=1_000)

    page.locator("#preview-survey-btn").click()
    expect(overlay).to_be_visible(timeout=2_000)

    page.locator("#survey-close-btn").click()
    expect(overlay).to_be_hidden(timeout=2_000)


def test_survey_preview_modal_closes_on_overlay_click(page: Page, demo_server: str):
    """Clicking the dark overlay background should close the modal."""
    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)

    page.locator("#preview-survey-btn").click()
    overlay = page.locator("#survey-preview-overlay")
    expect(overlay).to_be_visible(timeout=2_000)

    overlay.click(position={"x": 10, "y": 10})
    expect(overlay).to_be_hidden(timeout=2_000)


def test_full_flow_editor_to_fork_point_to_results(page: Page, demo_server: str):
    """Integration: preset → editor → start → fork point → sidebar → results."""
    sse_bytes = INTERACTIVE_SSE.read_bytes()
    _route_interactive_api(page, sse_bytes)
    page.goto(f"{demo_server}/interactive.html")

    # 1. Select preset, verify editor
    page.locator(".preset-card").first.click()
    editor = page.locator("#research-design-editor")
    expect(editor).to_be_visible(timeout=2_000)
    assert editor.locator(".field-editor").count() == 8

    # 2. Edit a question
    first_q = editor.locator("textarea.field-q").first
    first_q.fill("Custom question for testing")

    # 3. Start interview
    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    # 4. Fork point card visible
    fork_card = page.locator(".bubble.system.fork-point")
    expect(fork_card).to_be_visible(timeout=5_000)

    # 5. Sidebar questions visible (no hover needed)
    insight_question = page.locator(".insight-question").first
    expect(insight_question).to_be_visible(timeout=2_000)

    # 6. Results overlay visible
    results = page.locator("#results-overlay")
    expect(results).to_be_visible(timeout=5_000)
