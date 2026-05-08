# Data Quality Layer — Live Scoring and Evidence Transparency

## Goal

Integrate quality scoring into Methodic's live interview pipeline and interactive UI so that judges can see a numeric quality score, per-field evidence trails, and deterministic signal extraction — not just categorical coverage badges.

## Motivation

Methodic already has the pieces:
- `quality_scorer.py`: 4 boolean/float metrics (no composite)
- `wp7_data_quality.py`: composite score formula (0.30×coverage + 0.25×confidence + 0.25×ambiguity + 0.20×evidence), but offline-only
- `extractor.py`: Gemini-based extraction with hardcoded confidence thresholds
- Interactive UI: coverage badges (HIGH/LOW/AMBIG/MISSING) but no numeric score

The researchagent's document validator demonstrates patterns worth adopting:
1. **Penalty-based scoring with gate bands** → numeric quality gate visible to judges
2. **Deterministic pre-checks before LLM** → regex-based signal extraction that shows the model isn't operating blindly
3. **Evidence chains** → participant quote → extracted signal → coverage classification

This is a **judge-facing feature** for the AI Challenge, not an end-user production feature. The scoring needs to be visible, interpretable, and narratively compelling.

## Architecture

Three new components, layered onto the existing pipeline:

```
Participant response (transcript text)
        │
        ▼
┌──────────────────────────┐
│  Deterministic Pre-Check │  NEW: regex extraction of entities
│  (no LLM calls)          │  (competitor names, dollar amounts,
│                          │   timelines, sentiment signals)
└──────────┬───────────────┘
           │ enriched transcript + entity annotations
           ▼
┌──────────────────────────┐
│  Gemini Extractor        │  EXISTING: extract_structured_fields()
│  (LLM-based)             │  modified to receive entity hints
└──────────┬───────────────┘
           │ ParticipantResponse with coverage_state
           ▼
┌──────────────────────────┐
│  Composite Quality Score │  NEW: lifted from wp7_data_quality.py
│  (deterministic)         │  integrated into quality_scorer.py
└──────────┬───────────────┘
           │ score + gate_result + per_field breakdown
           ▼
┌──────────────────────────┐
│  Interactive UI           │  MODIFIED: quality score card,
│  (results overlay)        │  evidence chain display,
│                           │  gate badge (PASS/WARN/FAIL)
└───────────────────────────┘
```

## Component 1: Composite Quality Score

### What it does

Replaces the sparse `QualityMetrics` (4 booleans/floats) with a composite numeric score (0-100) using the WP7 rubric, plus gate bands.

### Design

Move the scoring logic from `scripts/wp7_data_quality.py` into `methodic/tools/quality_scorer.py` as a new function:

```python
def compute_composite_score(response: ParticipantResponse) -> CompositeScore:
    # Returns: score (0-100), gate_result, per_dimension breakdown
```

**Dimensions (same as WP7):**
| Dimension | Weight | Calculation |
|-----------|--------|-------------|
| Coverage | 0.30 | fraction of 8 fields with coverage_state != missing |
| Confidence | 0.25 | mean field_confidence across 8 fields |
| Resolution | 0.25 | fraction of fields resolved (not missing, not ambiguous, value != unknown) |
| Evidence-link | 0.20 | fraction of covered fields with ≥1 evidence item |

**Gate bands:**
| Score | Gate | Meaning |
|-------|------|---------|
| 85-100 | PASS | High-quality interview data |
| 60-84 | NEEDS_REVIEW | Usable but has gaps |
| 0-59 | INSUFFICIENT | Requires follow-up or re-interview |

**Data model addition:**
```python
class CompositeScore(BaseModel):
    score: int  # 0-100
    gate_result: str  # PASS, NEEDS_REVIEW, INSUFFICIENT
    dimensions: dict[str, float]  # coverage, confidence, resolution, evidence_link
    per_field: list[FieldScore]  # per-field breakdown

class FieldScore(BaseModel):
    field: str
    value: str | None
    coverage_state: str
    confidence: float
    has_evidence: bool
    entity_signals: list[str]  # from deterministic pre-check
```

### Integration point

Called in `ExtractorStep._run_async_impl()` after `extract_structured_fields()` returns, before coverage deltas are sent to the UI. The composite score is included in the results endpoint response.

### What stays the same

The existing `score_quality()` function and `QualityMetrics` model remain unchanged — they're used by the replanner and turn checker for loop control. The composite score is an additional layer for display and judge evaluation.

## Component 2: Deterministic Signal Extractor

### What it does

Before Gemini classifies coverage, apply regex-based extraction to find entities that the LLM *should* be able to use. This creates a "what was available" layer that makes the LLM's work auditable.

### Signals to extract (regex-based, no LLM)

| Signal type | Pattern examples | Purpose |
|-------------|-----------------|---------|
| Competitor names | "CompetitorX", "we went with [Name]", "alternative" | Validates competitor_pressure field |
| Dollar amounts | "$50K", "40% cheaper", "12-month payback" | Validates roi_clarity, budget_timing |
| Timelines | "6 weeks", "next quarter", "FY2026" | Validates budget_timing, procurement_friction |
| Security terms | "SOC2", "compliance", "security review" | Validates security_concern |
| Sentiment signals | "frustrated", "impressed", "never got to test" | Validates aha_moment_reached |

### Design

New file: `methodic/tools/signal_extractor.py`

```python
def extract_signals(transcript_text: str) -> list[Signal]:
    """Deterministic regex-based entity extraction. No LLM calls."""

class Signal(BaseModel):
    type: str  # competitor, amount, timeline, security, sentiment
    text: str  # matched text span
    turn_id: str  # which transcript turn
    relevant_fields: list[str]  # which canonical fields this could inform
```

### Integration point

Called at the start of `extract_structured_fields()`, before the Gemini call. Signals are:
1. Passed as hints to the extraction prompt (optional — helps Gemini but doesn't constrain it)
2. Stored alongside evidence in the response for UI display
3. Used in the composite score: if a signal exists for a field but the LLM said "unknown", flag it as a potential miss

### What it does NOT do

- Does not override LLM classification — signals are advisory
- Does not attempt NLP or entity disambiguation — simple regex patterns only
- Does not validate external facts — only extracts what's present in the transcript

## Component 3: UI Quality Display

### Results overlay additions

**Quality score card** — new card at the top of the results overlay (above field cards):
- Large composite score number (0-100) with color (green/amber/red)
- Gate badge: "PASS" / "NEEDS REVIEW" / "INSUFFICIENT"
- 4 dimension bars showing coverage, confidence, resolution, evidence-link
- Rubric weights visible on hover

**Evidence chain in field cards** — extend the existing expandable field cards:
- When expanded, show: participant quote → deterministic signals found → LLM classification
- Signal annotations are highlighted in the quote text (e.g., "$50K" highlighted as an amount signal)

### SSE integration

Add a new SSE event type for quality score updates. After each extraction cycle, send:
```json
{"author": "system", "text": "", "state_delta": {
  "quality_score": {
    "score": 78,
    "gate_result": "NEEDS_REVIEW",
    "dimensions": {"coverage": 0.875, "confidence": 0.71, ...}
  }
}}
```

The UI renders this as an animated score update in the sidebar (live during interview) and in the results overlay (final).

### Sidebar quality indicator

Add a small composite score badge next to the coverage counter ("6/8 fields • 78/100 quality"). Updates live as extraction runs.

## What is explicitly out of scope

1. **Self-consistency sampling** — running extraction 3x is expensive (3× Gemini calls per turn) and hard to justify for a single-participant interactive demo. Valuable in batch mode but not for live interviews.
2. **Argument graph** — the response→coverage→follow-up chain is implicit in the existing turn checker and replanner. Building a formal graph data structure adds complexity without clear judge-facing value in the demo timeframe.
3. **Uncertainty-aware downgrading** — requires multiple extraction runs (see #1). The confidence scores from Gemini already serve as a single-shot uncertainty signal.
4. **Gate-based loop control** — the composite score does NOT affect the interviewer's behavior. The existing turn checker and replanner continue to use the existing `QualityMetrics` for loop decisions. The composite score is display-only.

## Files to create/modify

| File | Action | Description |
|------|--------|-------------|
| `methodic/tools/quality_scorer.py` | Modify | Add `CompositeScore`, `FieldScore`, `compute_composite_score()` |
| `methodic/tools/signal_extractor.py` | Create | Deterministic regex-based signal extraction |
| `methodic/schemas.py` | Modify | Add `CompositeScore`, `FieldScore`, `Signal` models |
| `methodic/tools/extractor.py` | Modify | Call signal extractor, pass hints to prompt, include signals in response |
| `methodic/agents/extractor_step.py` | Modify | Compute composite score after extraction, send SSE event |
| `methodic/server.py` | Modify | Include composite score in `/results` endpoint |
| `methodic/static/interactive.html` | Modify | Quality score card, dimension bars, evidence chain in field cards, sidebar badge |
| `tests/test_quality_scorer.py` | Create | Tests for composite scoring with known inputs |
| `tests/test_signal_extractor.py` | Create | Tests for regex signal extraction |
| `tests/e2e/test_interactive_scenarios.py` | Modify | Add quality score assertions to scenario tests |

## Testing approach

1. **Unit tests for signal extractor** — known transcript snippets → expected signals
2. **Unit tests for composite score** — known coverage/confidence/evidence → expected score and gate
3. **E2e fixture updates** — add `quality_score` to SSE fixture state_delta, verify UI renders score card
4. **Regression** — existing 34 e2e tests continue to pass (quality score is additive, not breaking)

## Risks

1. **Signal extractor false positives** — regex may match "competitor" in unrelated contexts. Mitigation: keep patterns conservative, label as "signals detected" not "facts found."
2. **Score inflation/deflation** — WP7 weights were calibrated for fixture data. Live interview data may produce different distributions. Mitigation: use the same weights but validate with 3-4 real interview runs before finalizing.
3. **interactive.html growth** — file is already ~2050 lines. Quality score card adds ~100 more. Still manageable for single-file constraint but approaching the limit where extraction should be considered.
4. **SSE fixture maintenance** — adding `quality_score` to state_delta means updating all 5 SSE fixtures. Tests must be scoped to handle both old (no quality_score) and new fixtures.
