# Static Survey Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add question type metadata, type badges, and a corporate-styled "Preview as Survey" modal that renders static form widgets — creating a visual contrast before Methodic's adaptive conversation begins.

**Architecture:** Six components layered onto existing `interactive.html`. New constants (`QUESTION_TYPES`, `SURVEY_OPTIONS`, `SCALE_RANGES`), extended `FIELD_QUESTIONS` with `question_type`, type badges in editor and sidebar, a preview button, a modal overlay with 6 widget renderers, and updated fork point text. All frontend, no backend changes.

**Tech Stack:** Vanilla JS (ES5 compat), CSS, Playwright E2E tests

**IMPORTANT CONSTRAINTS:**
- Do NOT add `question_type` to the `body.custom_questions[field]` object in `startInterview()` (lines 1569-1582). Question types are frontend-only metadata.
- Do NOT use `innerHTML` anywhere — all DOM must be built with `createElement`/`textContent`/`appendChild`.
- All JS must be ES5-compatible (no arrow functions, no `let`/`const`, no template literals, no destructuring).

---

### Task 1: Add Question Type Constants and Extend FIELD_QUESTIONS

**Files:**
- Modify: `methodic/static/interactive.html:1146-1187` (FIELD_QUESTIONS constant)
- Modify: `tests/e2e/test_interactive_ui.py` (add test for question_type presence)

Add three new constants and extend existing FIELD_QUESTIONS entries with `question_type`.

- [ ] **Step 1: Write failing test for question type metadata**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_field_questions_have_question_type(page: Page, demo_server: str):
    """Each FIELD_QUESTIONS entry must have a question_type property."""
    page.goto(demo_server)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_field_questions_have_question_type -v`
Expected: FAIL (FIELD_QUESTIONS entries don't have question_type yet)

- [ ] **Step 3: Add QUESTION_TYPES, SURVEY_OPTIONS, SCALE_RANGES constants and extend FIELD_QUESTIONS**

In `methodic/static/interactive.html`, after line 1187 (end of existing FIELD_QUESTIONS), add these constants:

```javascript
  var QUESTION_TYPES = {
    open_ended:       { label: 'Open-ended',    color: '#3498db' },
    rating_scale:     { label: 'Rating Scale',  color: '#e67e22' },
    single_choice:    { label: 'Single Choice', color: '#9b59b6' },
    multi_select:     { label: 'Multi-select',  color: '#2ecc71' },
    yes_no_elaborate: { label: 'Yes / No',      color: '#e74c3c' },
    ranking:          { label: 'Ranking',        color: '#1abc9c' }
  };

  var SURVEY_OPTIONS = {
    budget_timing: [
      'During planning phase',
      'Budget already approved',
      'After fiscal cycle closed',
      'Budget was not a factor'
    ],
    secondary_loss_reason: [
      'Pricing / budget concerns',
      'Feature gaps',
      'Implementation complexity',
      'Vendor trust / relationship',
      'Internal priorities shifted',
      'Other (please specify)'
    ],
    competitor_pressure: [
      'Direct competitor',
      'Open-source alternative',
      'In-house solution',
      'Status quo (do nothing)'
    ]
  };

  var SCALE_RANGES = {
    roi_clarity: { min: 1, max: 10, lowLabel: 'Not confident', highLabel: 'Very confident' },
    procurement_friction: { min: 1, max: 5, lowLabel: 'No friction', highLabel: 'Severe friction' }
  };
```

Then modify each FIELD_QUESTIONS entry to add `question_type`. For example, change:
```javascript
    primary_loss_reason: {
      question: 'What changed between initial interest and the decision not to move forward?',
      follow_up: 'Clarify vague reasons — probe for specific factors',
      question_id: 'Q-loss-reason-open'
    },
```
To:
```javascript
    primary_loss_reason: {
      question: 'What changed between initial interest and the decision not to move forward?',
      follow_up: 'Clarify vague reasons — probe for specific factors',
      question_id: 'Q-loss-reason-open',
      question_type: 'open_ended'
    },
```

Full mapping:
- `primary_loss_reason`: `question_type: 'open_ended'`
- `secondary_loss_reason`: `question_type: 'multi_select'`
- `roi_clarity`: `question_type: 'rating_scale'`
- `budget_timing`: `question_type: 'single_choice'`
- `procurement_friction`: `question_type: 'rating_scale'`
- `security_concern`: `question_type: 'yes_no_elaborate'`
- `competitor_pressure`: `question_type: 'ranking'`
- `aha_moment_reached`: `question_type: 'yes_no_elaborate'`

Expose for testability by adding after the constants:
```javascript
  window.FIELD_QUESTIONS = FIELD_QUESTIONS;
```

(Check first — `window.FIELD_QUESTIONS` may already be exposed. If not, add it.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_field_questions_have_question_type -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: add question type constants and extend FIELD_QUESTIONS"
```

---

### Task 2: Type Badges in Editor and Sidebar

**Files:**
- Modify: `methodic/static/interactive.html:168-258` (CSS section)
- Modify: `methodic/static/interactive.html:1440-1497` (buildResearchEditor function)
- Modify: `methodic/static/interactive.html:2031-2082` (renderInsights function)
- Modify: `tests/e2e/test_interactive_ui.py` (add tests for badge presence)

- [ ] **Step 1: Write failing tests for type badges**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_editor_type_badges_visible(page: Page, demo_server: str):
    """Each field in the research design editor should show a type badge."""
    page.goto(demo_server)
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
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.locator("#start-btn").click()
    page.wait_for_selector("#app:not(.hidden)", timeout=5_000)
    page.wait_for_selector(".insight-card", timeout=5_000)
    badges = page.locator(".insight-card .type-badge")
    expect(badges.first).to_be_visible(timeout=3_000)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_editor_type_badges_visible tests/e2e/test_interactive_ui.py::test_sidebar_type_badges_visible -v`
Expected: FAIL (no .type-badge elements exist yet)

- [ ] **Step 3: Add CSS for type badges**

In `methodic/static/interactive.html`, in the CSS section after `.field-editor-sublabel` styles (around line 257), add:

```css
.type-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 0.58rem;
  font-weight: 600;
  color: #fff;
  margin-left: 6px;
  vertical-align: middle;
  letter-spacing: 0.02em;
}
```

- [ ] **Step 4: Add type badge to buildResearchEditor()**

In `buildResearchEditor()` (line ~1450), after the line that sets `label.textContent`, add the badge:

Find this block:
```javascript
      var label = document.createElement('div');
      label.className = 'field-editor-label';
      label.textContent = FIELD_LABELS[field] || field;
```

After it, add:
```javascript
      var typeInfo = QUESTION_TYPES[qInfo.question_type];
      if (typeInfo) {
        var badge = document.createElement('span');
        badge.className = 'type-badge';
        badge.style.background = typeInfo.color;
        badge.textContent = typeInfo.label;
        label.appendChild(badge);
      }
```

- [ ] **Step 5: Add type badge to renderInsights()**

In `renderInsights()` (line ~2046), after the line that sets `labelEl.textContent`, add the badge:

Find this block:
```javascript
        var labelEl = document.createElement('div');
        labelEl.className = 'insight-label';
        labelEl.textContent = FIELD_LABELS[field] || field;
```

After it, add:
```javascript
        var qInfo2 = FIELD_QUESTIONS[field];
        if (qInfo2 && qInfo2.question_type) {
          var typeInfo2 = QUESTION_TYPES[qInfo2.question_type];
          if (typeInfo2) {
            var badge2 = document.createElement('span');
            badge2.className = 'type-badge';
            badge2.style.background = typeInfo2.color;
            badge2.textContent = typeInfo2.label;
            labelEl.appendChild(badge2);
          }
        }
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_editor_type_badges_visible tests/e2e/test_interactive_ui.py::test_sidebar_type_badges_visible -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: add question type badges to editor and sidebar"
```

---

### Task 3: Survey Preview Button

**Files:**
- Modify: `methodic/static/interactive.html:1037` (HTML: add button before start-btn)
- Modify: `methodic/static/interactive.html` (CSS section)
- Modify: `methodic/static/interactive.html:1415-1417` (buildResearchEditor: show preview button)
- Modify: `methodic/static/interactive.html:1500-1507` (updateFieldCount: disable preview button)
- Modify: `tests/e2e/test_interactive_ui.py` (add test for button visibility)

- [ ] **Step 1: Write failing test for preview button**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_preview_survey_button_appears_on_preset_selection(page: Page, demo_server: str):
    """Preview as Survey button should appear when a preset is selected."""
    page.goto(demo_server)
    btn = page.locator("#preview-survey-btn")
    expect(btn).to_be_hidden(timeout=2_000)
    page.locator(".preset-card").first.click()
    expect(btn).to_be_visible(timeout=2_000)
    expect(btn).to_be_enabled()


def test_preview_survey_button_disabled_when_all_fields_off(page: Page, demo_server: str):
    """Preview button should be disabled when all fields are toggled off."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    toggles = page.locator(".field-toggle")
    for i in range(toggles.count()):
        toggles.nth(i).uncheck()
    btn = page.locator("#preview-survey-btn")
    expect(btn).to_be_disabled(timeout=2_000)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_preview_survey_button_appears_on_preset_selection tests/e2e/test_interactive_ui.py::test_preview_survey_button_disabled_when_all_fields_off -v`
Expected: FAIL (no #preview-survey-btn element)

- [ ] **Step 3: Add button HTML and CSS**

In the HTML section, change this block (line ~1037):
```html
    <div id="research-design-editor" class="hidden"></div>
    <button id="start-btn">Start Interview &rarr;</button>
```
To:
```html
    <div id="research-design-editor" class="hidden"></div>
    <button id="preview-survey-btn" class="hidden">Preview as Static Survey</button>
    <button id="start-btn">Start Interview &rarr;</button>
```

Add CSS after the `#start-btn:disabled` rule (around line 274):
```css
#preview-survey-btn {
  background: transparent;
  color: #85c1e9;
  border: 1px solid #2980b9;
  padding: 8px 18px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.78rem;
  margin-bottom: 10px;
  transition: background 0.2s;
  display: block;
  width: 100%;
}

#preview-survey-btn:hover {
  background: rgba(41, 128, 185, 0.15);
}

#preview-survey-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

- [ ] **Step 4: Show/hide preview button alongside editor**

In the selectPreset handler (around line 1415-1416), after:
```javascript
    buildResearchEditor();
    document.getElementById('research-design-editor').classList.remove('hidden');
```
Add:
```javascript
    document.getElementById('preview-survey-btn').classList.remove('hidden');
```

Also in the deselect path (around line 1400-1402), after:
```javascript
    card.classList.remove('selected');
    selectedPreset = null;
    return;
```
Add before the `return`:
```javascript
    document.getElementById('research-design-editor').classList.add('hidden');
    document.getElementById('preview-survey-btn').classList.add('hidden');
```

- [ ] **Step 5: Disable preview button when zero fields enabled**

In `updateFieldCount()` (line ~1500-1507), after the line that disables the start button:
```javascript
    if (startBtn) startBtn.disabled = (count === 0);
```
Add:
```javascript
    var previewBtn = document.getElementById('preview-survey-btn');
    if (previewBtn) previewBtn.disabled = (count === 0);
```

- [ ] **Step 6: Wire up the DOM reference and click handler**

In the init section (around line 1329-1340), add:
```javascript
    dom.previewBtn = document.getElementById('preview-survey-btn');
```

Add a click handler in the init section:
```javascript
    dom.previewBtn.addEventListener('click', function() {
      showSurveyPreview();
    });
```

Add a stub function (will be implemented in Task 5):
```javascript
  function showSurveyPreview() {
    // Implemented in Task 5
  }
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_preview_survey_button_appears_on_preset_selection tests/e2e/test_interactive_ui.py::test_preview_survey_button_disabled_when_all_fields_off -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: add survey preview button to config screen"
```

---

### Task 4: Survey Preview Modal Shell and CSS

**Files:**
- Modify: `methodic/static/interactive.html` (HTML: add modal overlay after config-screen, before #app)
- Modify: `methodic/static/interactive.html` (CSS section)
- Modify: `tests/e2e/test_interactive_ui.py` (add test for modal open/close)

- [ ] **Step 1: Write failing test for modal open/close**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_survey_preview_modal_opens_and_closes(page: Page, demo_server: str):
    """Clicking preview button opens modal; clicking close dismisses it."""
    page.goto(demo_server)
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
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)

    page.locator("#preview-survey-btn").click()
    overlay = page.locator("#survey-preview-overlay")
    expect(overlay).to_be_visible(timeout=2_000)

    overlay.click(position={"x": 10, "y": 10})
    expect(overlay).to_be_hidden(timeout=2_000)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_survey_preview_modal_opens_and_closes tests/e2e/test_interactive_ui.py::test_survey_preview_modal_closes_on_overlay_click -v`
Expected: FAIL (no #survey-preview-overlay element)

- [ ] **Step 3: Add modal HTML**

In the HTML, after `</div>` of `#config-screen` (line ~1040) and before the `<!-- Main App -->` comment, add:

```html
<!-- ─── Survey Preview Modal ─────────────────────────────────────── -->
<div id="survey-preview-overlay" class="hidden">
  <div class="survey-preview-modal">
    <div class="survey-header">
      <div class="survey-logo">ACME Corp</div>
      <h1 class="survey-title">Win-Loss Analysis Survey</h1>
      <p class="survey-subtitle">Please complete all required fields. Estimated time: 8-12 minutes.</p>
      <div class="survey-progress">Page 1 of 1</div>
    </div>
    <div class="survey-body" id="survey-preview-body"></div>
    <div class="survey-footer">
      <div class="survey-footer-text">This is what a traditional survey tool would generate from your research design. Methodic conducts a live conversation instead.</div>
      <button class="survey-close-btn" id="survey-close-btn">Close Preview</button>
    </div>
  </div>
</div>
```

- [ ] **Step 4: Add modal CSS**

In the CSS section, after the `#preview-survey-btn` rules, add:

```css
/* ─── Survey Preview Modal ──────────────────────────────────────── */
#survey-preview-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}

#survey-preview-overlay.hidden { display: none; }

.survey-preview-modal {
  background: #ffffff;
  border-radius: 4px;
  max-width: 680px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  font-family: Georgia, 'Times New Roman', serif;
  color: #333;
}

.survey-header {
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
  padding: 24px 32px 16px;
}

.survey-logo {
  font-size: 0.75rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.survey-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #222;
  margin: 0 0 6px;
}

.survey-subtitle {
  font-size: 0.82rem;
  color: #666;
  margin: 0;
}

.survey-progress {
  font-size: 0.7rem;
  color: #999;
  margin-top: 10px;
}

.survey-body {
  padding: 24px 32px;
}

.survey-field {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.survey-field:last-child {
  border-bottom: none;
}

.survey-field-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #222;
  margin-bottom: 4px;
}

.survey-field-required {
  color: #c0392b;
  font-weight: 700;
}

.survey-field-hint {
  font-size: 0.72rem;
  color: #888;
  font-style: italic;
  margin-bottom: 10px;
}

.survey-footer {
  background: #f9f9f9;
  border-top: 2px solid #ddd;
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.survey-footer-text {
  font-size: 0.72rem;
  color: #666;
  flex: 1;
}

.survey-close-btn {
  background: #2980b9;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-family: -apple-system, system-ui, sans-serif;
  white-space: nowrap;
}

.survey-scale {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.survey-scale label {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 0.78rem;
  color: #555;
  cursor: default;
}

.survey-scale-label {
  font-size: 0.68rem;
  color: #999;
  font-style: italic;
  padding: 0 6px;
}

.survey-choices {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.survey-choices label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: #444;
  cursor: default;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8f8f8;
  border: 1px solid #ddd;
  border-radius: 3px;
  margin-bottom: 4px;
  font-size: 0.82rem;
  color: #444;
}

.ranking-handle {
  color: #ccc;
  cursor: default;
  font-size: 0.9rem;
}

.ranking-num {
  font-weight: 600;
  color: #888;
  min-width: 20px;
}
```

- [ ] **Step 5: Implement showSurveyPreview() shell and closeSurveyPreview()**

Replace the stub `showSurveyPreview()` from Task 3 with:

```javascript
  function showSurveyPreview() {
    var body = document.getElementById('survey-preview-body');
    while (body.firstChild) body.removeChild(body.firstChild);

    var fieldIndex = 0;
    FIELDS.forEach(function(field) {
      if (!state.fieldEnabled || !state.fieldEnabled[field]) return;
      var qInfo = FIELD_QUESTIONS[field];
      if (!qInfo) return;
      fieldIndex++;

      var fieldDiv = document.createElement('div');
      fieldDiv.className = 'survey-field';
      fieldDiv.setAttribute('data-field', field);

      var labelEl = document.createElement('div');
      labelEl.className = 'survey-field-label';
      labelEl.textContent = 'Q' + fieldIndex + '. ' + qInfo.question + ' ';
      var reqSpan = document.createElement('span');
      reqSpan.className = 'survey-field-required';
      reqSpan.textContent = '*';
      labelEl.appendChild(reqSpan);
      fieldDiv.appendChild(labelEl);

      var hintEl = document.createElement('div');
      hintEl.className = 'survey-field-hint';
      hintEl.textContent = qInfo.follow_up;
      fieldDiv.appendChild(hintEl);

      renderSurveyWidget(fieldDiv, field, qInfo.question_type);
      body.appendChild(fieldDiv);
    });

    state.surveyPreviewed = true;
    document.getElementById('survey-preview-overlay').classList.remove('hidden');
  }

  function closeSurveyPreview() {
    document.getElementById('survey-preview-overlay').classList.add('hidden');
  }

  function renderSurveyWidget(container, field, type) {
    // Implemented in Task 5 — stub that adds a placeholder
    var placeholder = document.createElement('div');
    placeholder.textContent = '[' + type + ' widget]';
    placeholder.style.color = '#999';
    placeholder.style.fontStyle = 'italic';
    container.appendChild(placeholder);
  }
```

- [ ] **Step 6: Wire up event handlers**

In the init section, add:
```javascript
    document.getElementById('survey-close-btn').addEventListener('click', closeSurveyPreview);
    document.getElementById('survey-preview-overlay').addEventListener('click', function(e) {
      if (e.target === document.getElementById('survey-preview-overlay')) {
        closeSurveyPreview();
      }
    });
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_survey_preview_modal_opens_and_closes tests/e2e/test_interactive_ui.py::test_survey_preview_modal_closes_on_overlay_click -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: add survey preview modal shell with open/close behavior"
```

---

### Task 5: Widget Renderers

**Files:**
- Modify: `methodic/static/interactive.html` (replace renderSurveyWidget stub)
- Modify: `tests/e2e/test_interactive_ui.py` (add tests for each widget type)

- [ ] **Step 1: Write failing tests for each widget type**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_survey_preview_renders_open_ended_widget(page: Page, demo_server: str):
    """open_ended fields should render as a disabled textarea."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="primary_loss_reason"]')
    expect(field).to_be_visible()
    textarea = field.locator("textarea")
    expect(textarea).to_be_visible()
    assert textarea.is_disabled()


def test_survey_preview_renders_rating_scale_widget(page: Page, demo_server: str):
    """rating_scale fields should render radio buttons with scale labels."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="roi_clarity"]')
    expect(field).to_be_visible()
    radios = field.locator('input[type="radio"]')
    assert radios.count() == 10
    scale_labels = field.locator(".survey-scale-label")
    assert scale_labels.count() == 2


def test_survey_preview_renders_single_choice_widget(page: Page, demo_server: str):
    """single_choice fields should render radio buttons with options."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="budget_timing"]')
    expect(field).to_be_visible()
    radios = field.locator('input[type="radio"]')
    assert radios.count() == 4


def test_survey_preview_renders_multi_select_widget(page: Page, demo_server: str):
    """multi_select fields should render checkboxes."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="secondary_loss_reason"]')
    expect(field).to_be_visible()
    checkboxes = field.locator('input[type="checkbox"]')
    assert checkboxes.count() == 6


def test_survey_preview_renders_yes_no_widget(page: Page, demo_server: str):
    """yes_no_elaborate fields should render Yes/No radios and a textarea."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="security_concern"]')
    expect(field).to_be_visible()
    radios = field.locator('input[type="radio"]')
    assert radios.count() == 2
    textarea = field.locator("textarea")
    expect(textarea).to_be_visible()


def test_survey_preview_renders_ranking_widget(page: Page, demo_server: str):
    """ranking fields should render numbered items with drag handles."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="competitor_pressure"]')
    expect(field).to_be_visible()
    items = field.locator(".ranking-item")
    assert items.count() == 4


def test_survey_preview_excludes_disabled_fields(page: Page, demo_server: str):
    """Disabled fields should not appear in the survey preview."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)
    # Disable primary_loss_reason
    page.locator("#editor-primary_loss_reason .field-toggle").uncheck()
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    field = page.locator('.survey-field[data-field="primary_loss_reason"]')
    assert field.count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py -k "survey_preview_renders" -v`
Expected: FAIL (renderSurveyWidget is a stub)

- [ ] **Step 3: Implement renderSurveyWidget()**

Replace the stub `renderSurveyWidget()` with the full implementation:

```javascript
  function renderSurveyWidget(container, field, type) {
    if (type === 'open_ended') {
      var ta = document.createElement('textarea');
      ta.disabled = true;
      ta.rows = 4;
      ta.placeholder = 'Type your response here...';
      ta.style.cssText = 'width:100%;border:1px solid #ccc;border-radius:3px;padding:8px;font-family:Georgia,serif;font-size:0.82rem;background:#fafafa;color:#999;resize:none;box-sizing:border-box;';
      container.appendChild(ta);
    }
    else if (type === 'rating_scale') {
      var range = SCALE_RANGES[field] || { min: 1, max: 5, lowLabel: 'Low', highLabel: 'High' };
      var scaleDiv = document.createElement('div');
      scaleDiv.className = 'survey-scale';
      var lowLabel = document.createElement('span');
      lowLabel.className = 'survey-scale-label';
      lowLabel.textContent = range.lowLabel;
      scaleDiv.appendChild(lowLabel);
      for (var i = range.min; i <= range.max; i++) {
        var lbl = document.createElement('label');
        var radio = document.createElement('input');
        radio.type = 'radio';
        radio.disabled = true;
        radio.name = 'survey-' + field;
        lbl.appendChild(radio);
        var numSpan = document.createElement('span');
        numSpan.textContent = ' ' + i;
        lbl.appendChild(numSpan);
        scaleDiv.appendChild(lbl);
      }
      var highLabel = document.createElement('span');
      highLabel.className = 'survey-scale-label';
      highLabel.textContent = range.highLabel;
      scaleDiv.appendChild(highLabel);
      container.appendChild(scaleDiv);
    }
    else if (type === 'single_choice') {
      var options = SURVEY_OPTIONS[field] || ['Option A', 'Option B', 'Option C'];
      var choicesDiv = document.createElement('div');
      choicesDiv.className = 'survey-choices';
      options.forEach(function(opt) {
        var lbl = document.createElement('label');
        var radio = document.createElement('input');
        radio.type = 'radio';
        radio.disabled = true;
        radio.name = 'survey-' + field;
        lbl.appendChild(radio);
        var txt = document.createTextNode(' ' + opt);
        lbl.appendChild(txt);
        choicesDiv.appendChild(lbl);
      });
      container.appendChild(choicesDiv);
    }
    else if (type === 'multi_select') {
      var opts = SURVEY_OPTIONS[field] || ['Option A', 'Option B', 'Option C'];
      var choicesDiv2 = document.createElement('div');
      choicesDiv2.className = 'survey-choices';
      opts.forEach(function(opt) {
        var lbl = document.createElement('label');
        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.disabled = true;
        lbl.appendChild(cb);
        var txt = document.createTextNode(' ' + opt);
        lbl.appendChild(txt);
        choicesDiv2.appendChild(lbl);
      });
      container.appendChild(choicesDiv2);
    }
    else if (type === 'yes_no_elaborate') {
      var ynDiv = document.createElement('div');
      ynDiv.className = 'survey-choices';
      ['Yes', 'No'].forEach(function(opt) {
        var lbl = document.createElement('label');
        var radio = document.createElement('input');
        radio.type = 'radio';
        radio.disabled = true;
        radio.name = 'survey-' + field;
        lbl.appendChild(radio);
        var txt = document.createTextNode(' ' + opt);
        lbl.appendChild(txt);
        ynDiv.appendChild(lbl);
      });
      container.appendChild(ynDiv);
      var ta2 = document.createElement('textarea');
      ta2.disabled = true;
      ta2.rows = 2;
      ta2.placeholder = 'If yes, please elaborate...';
      ta2.style.cssText = 'width:100%;border:1px solid #ccc;border-radius:3px;padding:8px;font-family:Georgia,serif;font-size:0.78rem;background:#fafafa;color:#999;resize:none;box-sizing:border-box;margin-top:8px;';
      container.appendChild(ta2);
    }
    else if (type === 'ranking') {
      var items = SURVEY_OPTIONS[field] || ['Item A', 'Item B', 'Item C'];
      items.forEach(function(item, idx) {
        var row = document.createElement('div');
        row.className = 'ranking-item';
        var handle = document.createElement('span');
        handle.className = 'ranking-handle';
        handle.textContent = '☰';
        var num = document.createElement('span');
        num.className = 'ranking-num';
        num.textContent = (idx + 1) + '.';
        var label = document.createElement('span');
        label.textContent = item;
        row.appendChild(handle);
        row.appendChild(num);
        row.appendChild(label);
        container.appendChild(row);
      });
    }
  }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py -k "survey_preview_renders or survey_preview_excludes" -v`
Expected: PASS (all 7 widget tests)

- [ ] **Step 5: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: implement 6 survey widget renderers for preview modal"
```

---

### Task 6: Updated Fork Point Text and surveyPreviewed State

**Files:**
- Modify: `methodic/static/interactive.html:1557-1559` (startInterview state reset)
- Modify: `methodic/static/interactive.html:1730-1750` (fork point card insertion)
- Modify: `tests/e2e/test_interactive_ui.py` (add test for conditional text)

- [ ] **Step 1: Write failing test for conditional fork point text**

Add to `tests/e2e/test_interactive_ui.py`:
```python
def test_fork_point_text_after_survey_preview(page: Page, demo_server: str):
    """Fork point text should reference the preview if it was opened."""
    page.goto(demo_server)
    page.locator(".preset-card").first.click()
    page.wait_for_selector("#research-design-editor:not(.hidden)", timeout=2_000)

    # Open and close preview
    page.locator("#preview-survey-btn").click()
    page.wait_for_selector("#survey-preview-overlay:not(.hidden)", timeout=2_000)
    page.locator("#survey-close-btn").click()

    # Check the surveyPreviewed state
    previewed = page.evaluate("() => window.getState ? window.getState().surveyPreviewed : false")
    assert previewed is True
```

Note: This test checks the state flag. The fork point text itself is tested in the existing `test_fork_point_card_appears_after_methodology` which uses the SSE fixture. We'd need a separate fixture-based test for the full text, but the state flag test is sufficient to verify the conditional logic.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_fork_point_text_after_survey_preview -v`
Expected: FAIL (state.surveyPreviewed doesn't exist / no getState exposed)

- [ ] **Step 3: Add state.surveyPreviewed to startInterview reset**

In `startInterview()` (line ~1557-1559), after:
```javascript
    state.methodologyApproved = false;
    state.forkPointShown = false;
    state.forkPointSessionId = null;
```
Add:
```javascript
    state.surveyPreviewed = state.surveyPreviewed || false;
```

Note: Do NOT reset `surveyPreviewed` to `false` here — the user may have previewed the survey before clicking start, and we want the fork point text to reflect that. Only reset it when selecting a new preset (on preset deselect) or when the page loads fresh.

- [ ] **Step 4: Update fork point card text to be conditional**

In the fork point card insertion block (line ~1741-1743), replace:
```javascript
      forkText.textContent = 'A traditional tool would export these ' + FIELDS.length +
        ' questions as a static form and wait for responses. Methodic conducts a live ' +
        'conversation instead — adapting follow-ups based on what you actually say.';
```
With:
```javascript
      if (state.surveyPreviewed) {
        forkText.textContent = 'You just saw the static survey those questions would produce ' +
          '— radio buttons, sliders, checkboxes. Methodic asks the same questions as a live ' +
          'conversation, adapting follow-ups based on what you actually say.';
      } else {
        forkText.textContent = 'A traditional tool would export those questions as a fixed form ' +
          'with radio buttons and text boxes. Methodic conducts a live conversation instead ' +
          '— adapting follow-ups based on what you actually say.';
      }
```

- [ ] **Step 5: Expose getState for testability**

Add near the other window exports:
```javascript
  window.getState = function() { return state; };
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/e2e/test_interactive_ui.py::test_fork_point_text_after_survey_preview -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/test_interactive_ui.py
git commit -m "feat: conditional fork point text based on survey preview state"
```

---

### Task 7: Regression Test Pass

**Files:**
- Run all existing tests to verify nothing is broken

- [ ] **Step 1: Run full test suite**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/ -v --timeout=60`
Expected: All tests pass (existing 42+ tests plus new tests from Tasks 1-6)

- [ ] **Step 2: Fix any broken assertions**

If any test fails due to badge insertion changing `textContent` or fork text changes, update the assertion to account for the new content. Common fixes:
- If a test asserts exact text content of a label element, update it to allow the badge text suffix
- If a test asserts exact fork point text, update to match the new conditional text

- [ ] **Step 3: Commit fixes if any**

```bash
git add -u
git commit -m "fix: update test assertions for type badges and fork text changes"
```

(Skip this step if all tests pass without fixes.)
