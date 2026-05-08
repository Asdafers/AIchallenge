# Static Survey Preview — Question Types & Corporate Form Modal

## Goal

Add question type metadata to the 8 research fields, display type badges in the editor and sidebar, and render a "Preview as Survey" modal that shows what a traditional static survey tool would generate — creating a powerful visual contrast before Methodic's adaptive conversation begins.

## Motivation

The fork point card tells judges that Methodic is better than static surveys, but showing is more powerful than telling. By rendering the actual static form those questions would produce — radio buttons, sliders, checkboxes, textareas — judges see the limitations firsthand. The corporate styling (white background, serif fonts, gray borders) creates a jarring visual break from Methodic's dark theme, making the adaptive interview feel dramatically more sophisticated by comparison.

## Architecture

```
FIELD_QUESTIONS (+ question_type)
    |
    +-- Editor: type badge per field card
    +-- Sidebar: type badge per insight card
    |
    +-- "Preview as Survey" button
            |
            v
        Modal overlay (corporate styling)
            |  renders each enabled field as its static widget
            |
            +-- Close -> return to editor -> Start Interview
                    |
                    v
                Fork point card (updated text references the preview)
```

All changes are in `methodic/static/interactive.html`. No backend modifications.

## Component 1: Question Type Metadata

### FIELD_QUESTIONS extension

Add `question_type` to each entry in the existing `FIELD_QUESTIONS` constant. Also add a `QUESTION_TYPES` constant mapping type ID to display metadata.

```javascript
var QUESTION_TYPES = {
  open_ended:       { label: 'Open-ended',    color: '#3498db' },
  rating_scale:     { label: 'Rating Scale',  color: '#e67e22' },
  single_choice:    { label: 'Single Choice', color: '#9b59b6' },
  multi_select:     { label: 'Multi-select',  color: '#2ecc71' },
  yes_no_elaborate: { label: 'Yes / No',      color: '#e74c3c' },
  ranking:          { label: 'Ranking',        color: '#1abc9c' }
};
```

Field-to-type mapping:

| Field | question_type | Rationale |
|-------|--------------|-----------|
| primary_loss_reason | `open_ended` | Core narrative question — needs free-text |
| secondary_loss_reason | `multi_select` | Multiple contributing factors possible |
| roi_clarity | `rating_scale` | "How confident were you in the ROI?" maps to a 1-10 scale |
| budget_timing | `single_choice` | Discrete phases: planning / approved / post-cycle / not a factor |
| procurement_friction | `rating_scale` | "How much friction?" maps to a 1-5 scale |
| security_concern | `yes_no_elaborate` | Binary gate with optional explanation |
| competitor_pressure | `ranking` | Rank alternatives that were evaluated |
| aha_moment_reached | `yes_no_elaborate` | Binary gate with optional elaboration |

These types describe what a static survey tool would generate for each question. They do not affect the adaptive interview — the interviewer always uses conversational probing regardless of type.

## Component 2: Type Badges in Editor

In `buildResearchEditor()`, after the field label, insert a small colored pill showing the question type. Build using DOM methods:

```javascript
var badge = document.createElement('span');
badge.className = 'type-badge';
badge.style.background = QUESTION_TYPES[qInfo.question_type].color;
badge.textContent = QUESTION_TYPES[qInfo.question_type].label;
label.appendChild(badge);
```

### CSS

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

The badge color comes from `QUESTION_TYPES[field.question_type].color`. The label text comes from `QUESTION_TYPES[field.question_type].label`.

## Component 3: Type Badges in Sidebar

In `renderInsightCard()` (or equivalent), add the same type badge after the field label in each insight card. The badge is always visible (not hover-gated) since sidebar questions are already always-visible per the research design visibility spec.

Use the same `.type-badge` CSS class. The badge appears between the field label and the confidence indicator.

## Component 4: "Preview as Survey" Button

### Placement

Between the research design editor div and the start button. Added via DOM in `buildResearchEditor()` or shown/hidden alongside the editor.

### Behavior

- Hidden by default, shown when research design editor is visible
- Disabled when zero fields are enabled (same logic as start button)
- On click: calls `showSurveyPreview()` which builds and displays the modal
- Styled as a secondary/ghost button (outline, not filled) to distinguish from the primary start button

### CSS

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
}

#preview-survey-btn:hover {
  background: rgba(41, 128, 185, 0.15);
}

#preview-survey-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

## Component 5: Survey Preview Modal

### Structure

A full-viewport overlay with a centered content area styled to look like a corporate survey tool from the early 2010s — intentionally bland and old-fashioned. Built entirely via DOM methods (no innerHTML).

### Modal container (static HTML in page):

```html
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
      <div class="survey-footer-text"></div>
      <button class="survey-close-btn" id="survey-close-btn">Close Preview</button>
    </div>
  </div>
</div>
```

The footer text and close button event are set via JS using `textContent` and `addEventListener` (no inline onclick or innerHTML).

### Styling (intentionally corporate/bland)

```css
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
```

### Widget Renderers

`showSurveyPreview()` iterates over enabled fields and renders each according to its `question_type`. All widgets are built using safe DOM methods (`createElement`, `textContent`, `appendChild`). No `innerHTML` usage.

**open_ended** — Large disabled textarea with placeholder text.

**rating_scale** — Horizontal radio buttons labeled 1-N. The range is field-specific: `procurement_friction` uses 1-5, `roi_clarity` uses 1-10. Low/high labels from `SCALE_RANGES`.

**single_choice** — Disabled radio buttons with predefined options from `SURVEY_OPTIONS`.

**multi_select** — Disabled checkboxes with predefined options from `SURVEY_OPTIONS`.

**yes_no_elaborate** — Two disabled radio buttons (Yes / No) plus a disabled textarea with placeholder "If yes, please elaborate..."

**ranking** — Numbered list items with drag handle icon (static, non-functional).

### Widget-specific CSS

```css
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

### Data for static options

```javascript
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

### Open/close behavior

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
```

The overlay closes on clicking the close button (`addEventListener` attached during init). It also closes if the user clicks the dark overlay background:

```javascript
document.getElementById('survey-preview-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeSurveyPreview();
});
```

## Component 6: Updated Fork Point Card

### Current text
```
A traditional tool would export these 8 questions as a static form and wait
for responses. Methodic conducts a live conversation instead -- adapting
follow-ups based on what you actually say.
```

### New text (conditional)
If the user opened the survey preview before starting (tracked via `state.surveyPreviewed` flag):
```
You just saw the static survey those questions would produce -- radio buttons,
sliders, checkboxes. Methodic asks the same questions as a live conversation,
adapting follow-ups based on what you actually say.
```

If not previewed (existing text, slightly updated):
```
A traditional tool would export those questions as a fixed form with radio
buttons and text boxes. Methodic conducts a live conversation instead --
adapting follow-ups based on what you actually say.
```

Set `state.surveyPreviewed = true` in `showSurveyPreview()`. Reset to `false` on session reset (alongside existing `forkPointShown` and `methodologyApproved` resets).

## Files to modify

| File | Action | Description |
|------|--------|-------------|
| `methodic/static/interactive.html` | Modify | Add QUESTION_TYPES, SURVEY_OPTIONS, SCALE_RANGES constants; extend FIELD_QUESTIONS with question_type; type badges in editor and sidebar; preview button; modal overlay with widget renderers; updated fork point text |

## Testing approach

1. **Type badges** — verify each field shows correct type badge in editor and sidebar
2. **Preview button** — visible after preset selection, disabled when zero fields enabled
3. **Modal rendering** — each question type renders its correct widget
4. **Disabled fields excluded** — disabled fields do not appear in survey preview
5. **Close behavior** — close button and overlay click both dismiss modal
6. **Fork point text** — conditional text based on whether preview was opened
7. **Regression** — all existing tests continue to pass

## Out of scope

- Backend changes (question_type is frontend-only metadata)
- Functional form inputs (all widgets are disabled/static)
- Custom option editing (predefined options only)
- Saving preview state across sessions
- Print/export of the static survey
