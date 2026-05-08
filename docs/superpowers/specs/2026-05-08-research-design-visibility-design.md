# Research Design Visibility — Editable Questions & Static Survey Fork Point

## Goal

Make the research design (8 fields, their questions, follow-up policies) visible and editable throughout the interview lifecycle. Show judges the fork point where a static survey tool would stop and Methodic's adaptive interview begins.

## Motivation

The current UI hides the research design:
- Config screen shows presets but not the 8 target fields or their questions
- Sidebar insight cards reveal question text only on hover/focus (practically invisible)
- Methodology review card renders issue IDs as "1, 2, 3, 4, 5" instead of summaries
- No visual narrative showing how Methodic improves on static surveys

Judges need to see: (1) what data the study targets, (2) where the static path ends, and (3) how the adaptive interview goes further.

## Architecture

```
Config Screen (Step 1: Preset → Step 2: Question Editor)
        │
        │  custom_questions payload
        ▼
/api/interactive/start  ← accepts custom_questions (new field)
        │
        │  injected into interviewer prompt
        ▼
Interview loop (interviewer uses custom questions as framework)
        │
        │  SSE events with state_delta
        ▼
UI: fork-point card → chat → sidebar with always-visible questions
```

No changes to organizer, methodology_reviewer, or extractor agents. The custom questions supplement the methodology — they seed the interviewer's question framework but don't override the autonomous pipeline.

## Component 1: Config Screen — Research Design Editor

### Current state

Three preset cards (Lost Deal Analysis, Enterprise Churn, Competitive Displacement) with title, description, and persona hint. A hidden advanced panel with custom topic/persona inputs. Start button at the bottom.

### New behavior

After selecting a preset, a "Research Design" panel slides open between the preset grid and the start button. It shows all 8 fields as editable cards:

```
┌─────────────────────────────────────────────────────────────┐
│ Research Design                                    8 fields │
│                                                             │
│ ┌─ Primary Loss Reason ──────────────────────── [enabled] ─┐│
│ │ Question: [What changed between initial interest and the ││
│ │            decision not to move forward?               ] ││
│ │ Follow-up: [Clarify vague reasons — probe for specific  ││
│ │             factors                                     ] ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─ ROI Clarity ──────────────────────────────── [enabled] ─┐│
│ │ Question: [What evidence would your team have needed...  ││
│ │ Follow-up: [Probe for missing evidence or unclear metr...││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ ... (6 more fields)                                         │
│                                                             │
│ [Collapse ▲]                                                │
└─────────────────────────────────────────────────────────────┘
```

Each field card has:
- **Field label** (read-only) — e.g. "Primary Loss Reason"
- **Question textarea** (editable) — pre-filled from `FIELD_QUESTIONS[field].question`
- **Follow-up textarea** (editable) — pre-filled from `FIELD_QUESTIONS[field].follow_up`
- **Enable/disable toggle** — lets user skip fields. Disabled fields are greyed out and excluded from the custom_questions payload.

The panel is collapsible. Default state: expanded after preset selection, showing all 8 fields.

### Data flow

On "Start Interview" click, the UI collects:
```javascript
var customQuestions = {};
FIELDS.forEach(function(field) {
  if (fieldEnabled[field]) {
    customQuestions[field] = {
      question: document.getElementById('q-' + field).value,
      follow_up: document.getElementById('fu-' + field).value
    };
  }
});
```

This is sent as part of the start request body alongside the existing preset/topic/persona fields.

## Component 2: Backend — Accept Custom Questions

### `/api/interactive/start` modification

Add `custom_questions` to the accepted request body:
```python
custom_questions = data.get("custom_questions", None)
```

Store on the `InteractiveSession` dataclass:
```python
@dataclass
class InteractiveSession:
    ...
    custom_questions: dict | None = None
```

### Interviewer prompt injection

In `_start_interactive_pipeline()`, if `custom_questions` is present, prepend them to the interviewer agent's system prompt:

```
The participant has defined these specific research questions. Use them as your framework:

1. Primary Loss Reason: "What changed between initial interest and the decision not to move forward?"
   Follow-up policy: Clarify vague reasons — probe for specific factors

2. ROI Clarity: "What evidence would your team have needed to feel confident in the ROI?"
   Follow-up policy: Probe for missing evidence or unclear metrics

...

Adapt your follow-ups based on the participant's actual responses. You are not limited to these exact questions — probe deeper where the participant gives interesting answers. But ensure all enabled fields are addressed before concluding.
```

This is appended to the existing interviewer prompt. The organizer and methodology reviewer continue to run their standard flow — the custom questions are a supplementary instruction to the interviewer, not a replacement for the autonomous methodology pipeline.

## Component 3: Fork Point Card

After the methodology reviewer's verdict appears and before the first interviewer message, insert a styled transition card in the chat panel:

```html
<div class="bubble system fork-point">
  <div class="fork-label">Where static surveys stop</div>
  <div class="fork-text">
    A traditional tool would export these 8 questions as a static form and wait
    for responses. Methodic conducts a live conversation instead — adapting
    follow-ups based on what you actually say.
  </div>
</div>
```

### Styling
- Dashed border, muted background (`#1a1a2e`)
- Small icon or divider mark to visually separate "setup phase" from "interview phase"
- Appears once, not repeated

### Trigger
In `handleEvent()`, after processing a `methodology_reviewer` or `methodology` event with `verdict: "APPROVED"`, set a flag `state.forkPointShown = false`. When the first `interviewer` event arrives and `!state.forkPointShown`, insert the fork card before the interviewer bubble, then set `state.forkPointShown = true`.

## Component 4: Sidebar — Always-Visible Question Text

### Current state
Insight cards show field label + status icon. Question text is hidden (`max-height: 0`) and only appears on hover/focus.

### New behavior
Remove the hover-gating. Show question text always, in a smaller font below the field label. The card layout becomes:

```
┌──────────────────────────────────────┐
│ [+] primary_loss         HIGH        │
│     What changed between initial     │
│     interest and the decision...     │
└──────────────────────────────────────┘
```

### CSS change
Replace:
```css
.insight-question {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.insight-card:hover .insight-question,
.insight-card:focus-within .insight-question {
  max-height: 60px;
}
```

With:
```css
.insight-question {
  max-height: 60px;
}
```

The question text becomes always visible. The focus outline styling remains for keyboard accessibility.

### Frontend field targeting heuristic

When an interviewer message arrives, do a simple keyword match against `FIELD_QUESTIONS` to guess which field is being targeted:

```javascript
function guessTargetField(interviewerText) {
  var lower = interviewerText.toLowerCase();
  var bestField = null;
  var bestScore = 0;
  FIELDS.forEach(function(field) {
    var q = FIELD_QUESTIONS[field];
    if (!q) return;
    var keywords = q.question.toLowerCase().split(/\s+/).filter(function(w) {
      return w.length > 4;
    });
    var score = keywords.filter(function(kw) {
      return lower.indexOf(kw) >= 0;
    }).length;
    if (score > bestScore) {
      bestScore = score;
      bestField = field;
    }
  });
  return bestScore >= 2 ? bestField : null;
}
```

When a target field is guessed, add a `targeting` class to that insight card (pulsing border). Remove it when the next participant response arrives.

```css
.insight-card.targeting {
  border: 1px solid #85c1e9;
  animation: targetPulse 1.5s ease-in-out infinite;
}
```

This is a heuristic — it won't be perfect, but it's good enough for demos. A backend `targeting_fields` signal is the right long-term fix.

## Component 5: Methodology Card Fix

### Bug
`routeToAgenticMoment()` line 1630:
```javascript
parsed.issues.map(function(i) { return i.summary || i.id; }).join(', ');
```

When Gemini returns issues where `summary` is undefined and `id` is a number, the card shows "1, 2, 3, 4, 5".

### Fix
Handle edge cases in issue rendering:
```javascript
if (parsed.issues && parsed.issues.length) {
  var issueTexts = parsed.issues.map(function(issue) {
    if (typeof issue === 'string') return issue;
    return issue.summary || issue.id || 'issue';
  });
  displayText += ' — ' + parsed.issues.length + ' issue(s): ' + issueTexts.join(', ');
}
```

Also: if issues are just an array of strings (not objects), handle that case. And if the text exceeds 200 chars, truncate individual issue summaries rather than cutting the whole string mid-sentence.

## Files to create/modify

| File | Action | Description |
|------|--------|-------------|
| `methodic/static/interactive.html` | Modify | Research design editor, fork point card, always-visible sidebar questions, field targeting heuristic, methodology card fix |
| `methodic/server.py` | Modify | Accept `custom_questions` in start endpoint, store on session, inject into interviewer prompt |
| `tests/e2e/test_interactive_ui.py` | Modify | Tests for config editor, fork point card, visible question text |
| `tests/e2e/test_interactive_scenarios.py` | Modify | Tests for methodology card rendering with various issue formats |
| `tests/e2e/fixtures/sse_interactive_run.txt` | Modify | Ensure fixture triggers fork point card |

## Testing approach

1. **Config editor** — preset selection populates question editor; editing text persists; disabled fields are excluded
2. **Start request** — verify custom_questions payload is sent in fetch body
3. **Fork point** — card appears after methodology approval, before first interviewer message
4. **Sidebar questions** — question text visible without hover on initial render
5. **Field targeting** — interviewer message about ROI highlights roi_clarity card
6. **Methodology card** — issue summaries render for objects, strings, and edge cases
7. **Regression** — all existing 34 e2e tests continue to pass

## Out of scope

- Adding/removing fields (always 8 canonical fields, enable/disable only)
- Saving custom question sets across sessions
- Backend `targeting_fields` signal (future enhancement — use frontend heuristic for now)
- Changes to organizer, methodology_reviewer, or extractor agents
