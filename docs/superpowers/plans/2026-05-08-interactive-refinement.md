# Interactive Mode Refinement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add plain-English question detail view to the interactive results, create canned SSE scenario fixtures for systematic testing, and add Playwright e2e tests for each scenario.

**Architecture:** Extend `interactive.html` results overlay with expandable field cards showing the original survey question and follow-up policy. Add 4 canned SSE scenario fixtures covering common interview outcomes. Add Playwright tests for each scenario.

**Tech Stack:** Vanilla JS (no framework), Playwright (pytest-playwright), SSE fixtures

---

## File Structure

| File | Responsibility |
|---|---|
| `methodic/static/interactive.html` | Add question detail to results overlay field cards; add question detail to sidebar insight cards |
| `tests/e2e/fixtures/sse_scenario_*.txt` | 4 scenario fixtures (perfect, partial, error, edge) |
| `tests/e2e/test_interactive_scenarios.py` | Scenario-based e2e tests |
| `tests/e2e/test_interactive_ui.py` | Existing tests (no changes) |

---

### Task 1: Add Plain-English Question Detail to Results Overlay

The current results overlay shows field names (`primary_loss`, `roi_clarity`) with coverage badges (`HIGH`, `LOW`, `MISSING`). Users requested seeing the actual survey questions that correspond to each field.

**Files:**
- Modify: `methodic/static/interactive.html` — `showResults()` function (~line 1717) and JS constants section (~line 940)

- [ ] **Step 1: Add FIELD_QUESTIONS constant**

Add after the existing `FIELD_LABELS` constant (line 951):

```javascript
var FIELD_QUESTIONS = {
  primary_loss_reason: {
    question: 'What changed between initial interest and the decision not to move forward?',
    follow_up: 'Clarify vague reasons — probe for specific factors',
    question_id: 'Q-loss-reason-open'
  },
  secondary_loss_reason: {
    question: 'Beyond the primary factor, was there a secondary issue that contributed to the outcome?',
    follow_up: 'Probe if answer is vague or too general',
    question_id: 'Q-secondary-loss'
  },
  roi_clarity: {
    question: 'What evidence would your team have needed to feel confident in the ROI?',
    follow_up: 'Probe for missing evidence or unclear metrics',
    question_id: 'Q-roi-clarity'
  },
  budget_timing: {
    question: 'Was budget timing or fiscal-cycle alignment a factor in the decision?',
    follow_up: 'Confirm or deny — avoid leading if unprompted',
    question_id: 'Q-budget-timing'
  },
  procurement_friction: {
    question: 'Walk me through the procurement process — where, if anywhere, did it slow down or create friction?',
    follow_up: 'Probe specific stages where friction occurred',
    question_id: 'Q-procurement-friction'
  },
  security_concern: {
    question: 'Did security review or compliance requirements affect the timeline or outcome?',
    follow_up: 'Confirm or deny',
    question_id: 'Q-security-concern'
  },
  competitor_pressure: {
    question: 'Were you evaluating alternatives or did a competitor offer influence the decision?',
    follow_up: 'Identify named competitor if mentioned',
    question_id: 'Q-competitor-pressure'
  },
  aha_moment_reached: {
    question: 'Was there a moment during the evaluation where the core value clicked — or did that never happen?',
    follow_up: 'Probe trial experience',
    question_id: 'Q-aha-moment'
  }
};
```

- [ ] **Step 2: Add CSS for expandable question detail**

Add to the style section, after the existing `.field-card` styles:

```css
.field-question {
  display: none;
  margin-top: 8px;
  padding: 8px 10px;
  background: #1a1a2e;
  border-radius: 6px;
  border-left: 3px solid #2980b9;
}

.field-card.expanded .field-question {
  display: block;
}

.field-card {
  cursor: pointer;
}

.question-text {
  font-size: 0.78rem;
  color: #c0d0e0;
  line-height: 1.5;
  margin-bottom: 4px;
}

.question-followup {
  font-size: 0.7rem;
  color: #6a8fa8;
  font-style: italic;
}

.expand-hint {
  font-size: 0.65rem;
  color: #556;
  float: right;
}
```

- [ ] **Step 3: Modify showResults() to add question detail to field cards**

In the `showResults()` function, replace the `FIELDS.forEach` block (lines 1768-1797) that builds field cards. After `fc.appendChild(badge)`, add the question detail element:

```javascript
var qInfo = FIELD_QUESTIONS[field];
if (qInfo) {
  var hint = document.createElement('span');
  hint.className = 'expand-hint';
  hint.textContent = 'click to expand';
  fc.appendChild(hint);

  var qDetail = document.createElement('div');
  qDetail.className = 'field-question';

  var qText = document.createElement('div');
  qText.className = 'question-text';
  qText.textContent = qInfo.question;
  qDetail.appendChild(qText);

  var qFollowUp = document.createElement('div');
  qFollowUp.className = 'question-followup';
  qFollowUp.textContent = 'Follow-up: ' + qInfo.follow_up;
  qDetail.appendChild(qFollowUp);

  fc.appendChild(qDetail);

  fc.addEventListener('click', function () {
    fc.classList.toggle('expanded');
    hint.textContent = fc.classList.contains('expanded') ? 'click to collapse' : 'click to expand';
  });
}
```

- [ ] **Step 4: Run existing e2e tests to verify no regressions**

Run: `python3 -m pytest tests/e2e/test_interactive_ui.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add methodic/static/interactive.html
git commit -m "feat: add plain-English question detail to interactive results overlay"
```

---

### Task 2: Add Question Detail to Sidebar Insight Cards

The sidebar insight cards currently show only field labels and coverage state icons. Add a tooltip or subtitle showing the question text.

**Files:**
- Modify: `methodic/static/interactive.html` — `renderInsights()` function (~line 1563) and CSS

- [ ] **Step 1: Add CSS for insight question subtitle**

```css
.insight-question {
  font-size: 0.62rem;
  color: #556;
  line-height: 1.4;
  margin-top: 2px;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.insight-card:hover .insight-question {
  max-height: 60px;
}
```

- [ ] **Step 2: Add question text to insight card creation**

In `renderInsights()`, after `card.appendChild(stateEl)` (line 1588), add:

```javascript
var qInfo = FIELD_QUESTIONS[field];
if (qInfo) {
  var qSub = document.createElement('div');
  qSub.className = 'insight-question';
  qSub.textContent = qInfo.question;
  card.appendChild(qSub);
}
```

- [ ] **Step 3: Run existing e2e tests**

Run: `python3 -m pytest tests/e2e/test_interactive_ui.py -v`
Expected: 11 passed

- [ ] **Step 4: Commit**

```bash
git add methodic/static/interactive.html
git commit -m "feat: add question detail hover to sidebar insight cards"
```

---

### Task 3: Create Canned SSE Scenario Fixtures

Create 4 scenario fixtures that represent different interview outcomes. These will power both e2e tests and can be used to manually play through the UI for fine-tuning.

**Files:**
- Create: `tests/e2e/fixtures/sse_scenario_perfect.txt` — all 8 fields reach high confidence
- Create: `tests/e2e/fixtures/sse_scenario_partial.txt` — 4 fields high, 2 low, 2 missing
- Create: `tests/e2e/fixtures/sse_scenario_error.txt` — error mid-stream after 2 turns
- Create: `tests/e2e/fixtures/sse_scenario_edge.txt` — methodology REVISE_REQUIRED, then approved on retry, single-turn interview

- [ ] **Step 1: Create sse_scenario_perfect.txt**

Full interview with 5 turns covering all 8 fields to high confidence. Events:
1. `organizer` — study brief
2. `methodology_reviewer` — JSON verdict APPROVED
3. `interviewer` turn 1 — loss reason question
4. `system` — input_requested: true
5. `participant` — detailed loss reason answer (covers primary_loss, secondary_loss)
6. `interviewer` turn 2 — ROI question
7. `system` — input_requested: true
8. `participant` — ROI answer (covers roi_clarity, budget_timing)
9. `interviewer` turn 3 — procurement question
10. `system` — input_requested: true
11. `participant` — procurement answer (covers procurement_friction, security_concern)
12. `interviewer` turn 4 — competitor question
13. `system` — input_requested: true
14. `participant` — competitor answer (covers competitor_pressure, aha_moment_reached)
15. `system` — Stream complete

Coverage delta progression: each participant event should add 2 fields at high confidence, ending with all 8 at `covered_high_confidence`.

```
data: {"author": "organizer", "text": "Study plan: Q1 2026 Lost Deal Analysis. Target: 1 participant interview, 8 structured variables.", "state_delta": {}}

data: {"author": "methodology_reviewer", "text": "{\"verdict\": \"APPROVED\", \"issues\": []}", "state_delta": {}}

data: {"author": "interviewer", "text": "Thank you for joining. I'd like to understand the factors that influenced your recent purchasing decision. What changed between initial interest and the decision not to move forward?", "state_delta": {"turn_count": 1}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "The primary issue was unclear ROI. Our CFO couldn't justify the investment without clear cost savings data. Beyond that, we were also concerned about a competitor who offered a more integrated solution.", "state_delta": {"input_requested": false, "turn_count": 2, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "That's very helpful. What evidence would your team have needed to feel confident in the ROI? And was budget timing a factor?", "state_delta": {"turn_count": 3}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "We needed a 12-month payback analysis with clear cost savings projections mapped to our business units. Budget timing was also tricky — we were out of cycle and would have needed to pull from next year's allocation.", "state_delta": {"input_requested": false, "turn_count": 4, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "budget_timing": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "Walk me through the procurement process. Where, if anywhere, did it slow down? And did security review affect the timeline?", "state_delta": {"turn_count": 5}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "Procurement was actually smooth — low friction there. But security review took 6 weeks because your SOC2 report was from last year. That delay killed our window.", "state_delta": {"input_requested": false, "turn_count": 6, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "covered_high_confidence", "security_concern": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "Were you evaluating alternatives? Was there a moment during evaluation where the core value clicked?", "state_delta": {"turn_count": 7}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "Yes, we were comparing with CompetitorX who offered native integrations. As for the aha moment — the report builder demo was impressive, but we never got to test it ourselves during the trial.", "state_delta": {"input_requested": false, "turn_count": 8, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "covered_high_confidence", "security_concern": "covered_high_confidence", "competitor_pressure": "covered_high_confidence", "aha_moment_reached": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "Thank you for your thorough and candid responses. That concludes our interview.", "state_delta": {"turn_count": 9}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 2: Create sse_scenario_partial.txt**

Interview with 3 turns, partial coverage. 4 fields high, 2 low, 2 missing.

```
data: {"author": "organizer", "text": "Study plan: Competitive displacement analysis.", "state_delta": {}}

data: {"author": "methodology_reviewer", "text": "{\"verdict\": \"APPROVED\", \"issues\": [{\"id\": \"SCOPE_NARROW\", \"summary\": \"Only one participant planned\"}]}", "state_delta": {}}

data: {"author": "interviewer", "text": "What were the main factors in your decision to switch vendors?", "state_delta": {"turn_count": 1}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "Mostly price. The competitor was 40% cheaper and had the features we needed.", "state_delta": {"input_requested": false, "turn_count": 2, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "competitor_pressure": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "Can you tell me more about the ROI analysis your team conducted?", "state_delta": {"turn_count": 3}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "I think there was some analysis but I wasn't directly involved. I believe the numbers were close.", "state_delta": {"input_requested": false, "turn_count": 4, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "secondary_loss_reason": "covered_low_confidence", "roi_clarity": "covered_low_confidence", "competitor_pressure": "covered_high_confidence", "aha_moment_reached": "covered_high_confidence", "security_concern": "covered_high_confidence"}}}

data: {"author": "interviewer", "text": "Thank you for your time. That concludes our session.", "state_delta": {"turn_count": 5}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 3: Create sse_scenario_error.txt**

Error occurs mid-stream after methodology review.

```
data: {"author": "organizer", "text": "Study plan: Enterprise churn investigation.", "state_delta": {}}

data: {"author": "methodology_reviewer", "text": "{\"verdict\": \"APPROVED\", \"issues\": []}", "state_delta": {}}

data: {"author": "interviewer", "text": "Welcome. I'd like to understand why your team decided to discontinue the service.", "state_delta": {"turn_count": 1}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "We had budget cuts across the board.", "state_delta": {"input_requested": false, "turn_count": 2, "participant_coverage": {"primary_loss_reason": "covered_high_confidence", "budget_timing": "covered_low_confidence"}}}

data: {"author": "error", "text": "Model quota exceeded. Please try again later.", "state_delta": {}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 4: Create sse_scenario_edge.txt**

Methodology initially requires revision, then approves. Single-turn interview.

```
data: {"author": "organizer", "text": "Study plan: Single-participant quick assessment.", "state_delta": {}}

data: {"author": "methodology_reviewer", "text": "```json\n{\"verdict\": \"REVISE_REQUIRED\", \"issues\": [{\"id\": \"SAMPLING_BIAS\", \"summary\": \"Single participant insufficient for generalization\"}, {\"id\": \"LEADING_QUESTION\", \"summary\": \"Budget question may prime respondent\"}]}\n```", "state_delta": {}}

data: {"author": "methodology", "text": "{\"verdict\": \"APPROVED\", \"issues\": [{\"id\": \"SAMPLING_BIAS\", \"summary\": \"Acknowledged — study is exploratory, not generalizable\"}]}", "state_delta": {}}

data: {"author": "interviewer", "text": "Tell me about your recent evaluation experience.", "state_delta": {"turn_count": 1}}

data: {"author": "system", "text": "", "state_delta": {"input_requested": true}}

data: {"author": "participant", "text": "It was fine. We just went with someone else.", "state_delta": {"input_requested": false, "turn_count": 2, "participant_coverage": {"primary_loss_reason": "ambiguous", "competitor_pressure": "covered_low_confidence"}}}

data: {"author": "interviewer", "text": "Thank you for your time.", "state_delta": {"turn_count": 3}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/fixtures/sse_scenario_*.txt
git commit -m "test: add 4 canned SSE scenario fixtures for interactive mode testing"
```

---

### Task 4: Add Playwright Scenario Tests

Create e2e tests that exercise each scenario fixture and verify the UI renders correctly for each case.

**Files:**
- Create: `tests/e2e/test_interactive_scenarios.py`

- [ ] **Step 1: Write the scenario test file**

```python
"""Scenario-based e2e tests for interactive interview UI."""

import json
from pathlib import Path

from playwright.sync_api import Page, expect

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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

    page.goto(f"{demo_server}/interactive.html")
    page.locator(".preset-card").first.click()
    page.locator("#start-btn").click()
    page.locator("#app").wait_for(state="visible", timeout=5_000)
    return page


# ─── Perfect Coverage Scenario ──────────────────────────────────────

def test_perfect_all_fields_high(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    high_badges = page.locator(".coverage-badge.high")
    assert high_badges.count() == 8, f"Expected 8 HIGH badges, got {high_badges.count()}"


def test_perfect_no_missing_fields(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    miss_badges = page.locator(".coverage-badge.miss")
    assert miss_badges.count() == 0, f"Expected 0 MISSING badges, got {miss_badges.count()}"


def test_perfect_turn_count(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_perfect.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    results = page.locator("#results-overlay")
    expect(results).to_contain_text("9")


# ─── Partial Coverage Scenario ──────────────────────────────────────

def test_partial_mixed_coverage(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_partial.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    high_badges = page.locator(".coverage-badge.high")
    assert high_badges.count() >= 3, f"Expected at least 3 HIGH badges, got {high_badges.count()}"

    miss_badges = page.locator(".coverage-badge.miss")
    assert miss_badges.count() >= 1, f"Expected at least 1 MISSING badge"


def test_partial_needs_clarification_count(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_partial.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    low_badges = page.locator(".coverage-badge.low")
    assert low_badges.count() >= 1, f"Expected at least 1 LOW badge"


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
    """Even after error, coverage data from before the error should be visible."""
    _route_and_start(page, demo_server, "sse_scenario_error.txt")
    expect(page.locator("#status-badge")).to_have_text("failed", timeout=10_000)

    # The error fixture includes 1 participant response with coverage
    insight_cards = page.locator(".insight-card")
    assert insight_cards.count() >= 1, "Expected insight cards even after error"


# ─── Edge Case Scenario ─────────────────────────────────────────────

def test_edge_methodology_revision_then_approval(page: Page, demo_server: str):
    """Methodology REVISE_REQUIRED followed by APPROVED should show both cards."""
    _route_and_start(page, demo_server, "sse_scenario_edge.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    agentic_cards = page.locator(".agentic-card.methodology")
    assert agentic_cards.count() >= 2, f"Expected 2 methodology cards, got {agentic_cards.count()}"

    # First card should contain REVISE_REQUIRED
    first_text = agentic_cards.nth(0).locator(".agentic-text").text_content() or ""
    assert "REVISE_REQUIRED" in first_text, f"Expected REVISE_REQUIRED in first card: {first_text}"

    # Second card should contain APPROVED
    second_text = agentic_cards.nth(1).locator(".agentic-text").text_content() or ""
    assert "APPROVED" in second_text, f"Expected APPROVED in second card: {second_text}"


def test_edge_ambiguous_field_shown(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_scenario_edge.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    ambig_badges = page.locator(".coverage-badge.ambig")
    assert ambig_badges.count() >= 1, f"Expected at least 1 AMBIG badge"
```

- [ ] **Step 2: Run the scenario tests**

Run: `python3 -m pytest tests/e2e/test_interactive_scenarios.py -v`
Expected: All pass

- [ ] **Step 3: Run full e2e suite**

Run: `python3 -m pytest tests/e2e/ -v --ignore=tests/e2e/test_demo_ui.py::test_live_demo_completes`
Expected: All non-live tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_interactive_scenarios.py
git commit -m "test: add scenario-based Playwright tests for interactive mode"
```

---

### Task 5: Add Question Detail Expansion E2E Test

Add a test that verifies the new question detail feature works in the browser.

**Files:**
- Modify: `tests/e2e/test_interactive_ui.py`

- [ ] **Step 1: Add test for question detail expansion**

```python
def test_results_field_card_expands_to_show_question(page: Page, demo_server: str):
    """Clicking a field card in results shows the plain-English question."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    field_card = page.locator(".field-card").first
    field_card.click()

    question_detail = field_card.locator(".field-question")
    expect(question_detail).to_be_visible(timeout=2_000)

    question_text = question_detail.locator(".question-text").text_content() or ""
    assert len(question_text) > 10, f"Expected question text, got: {question_text}"


def test_results_field_card_collapses(page: Page, demo_server: str):
    """Clicking a field card twice collapses the question detail."""
    _start_and_wait_for_app(page, demo_server)
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    field_card = page.locator(".field-card").first
    field_card.click()  # expand
    expect(field_card.locator(".field-question")).to_be_visible(timeout=2_000)
    field_card.click()  # collapse
    expect(field_card.locator(".field-question")).to_be_hidden(timeout=2_000)
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest tests/e2e/test_interactive_ui.py -v`
Expected: 13 passed (11 existing + 2 new)

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_interactive_ui.py
git commit -m "test: add e2e tests for question detail expansion in results"
```

---

### Task 6: Redeploy to Cloud Run

Deploy the latest code (including methodology JSON fix from `1a7ad13` and all new features) to Cloud Run.

**Files:**
- No file changes — deployment only

- [ ] **Step 1: Build and deploy**

```bash
gcloud run deploy methodic \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --max-instances=1 \
  --memory=1Gi \
  --timeout=600
```

- [ ] **Step 2: Verify deployment**

```bash
curl -s https://methodic-2030382823.us-central1.run.app/health | python3 -m json.tool
curl -s https://methodic-2030382823.us-central1.run.app/.well-known/agent-card.json | python3 -m json.tool
```

Expected: `{"status": "ok"}` and agent card JSON

- [ ] **Step 3: Smoke test interactive page**

Open `https://methodic-2030382823.us-central1.run.app/static/interactive.html` and verify:
- Config screen loads with 3 presets
- Start button works
- Methodology verdict renders as "Verdict: APPROVED" (not raw JSON)
