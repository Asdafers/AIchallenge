# Gemini Review: Data Quality Layer Design

## STRENGTHS
* **Immediate Visibility:** Lifting the offline composite score (from `wp7_data_quality.py`) into the live pipeline provides immediate, tangible proof of the platform's analytical rigor to judges.
* **Auditability & Grounded Baseline:** The Deterministic Signal Extractor creates a powerful "what was available" vs. "what the LLM did" comparison. This demonstrates that the system isn't a black box and actively audits its own LLM.
* **Clear Separation of Concerns:** By keeping the new `CompositeScore` isolated from the `QualityMetrics` used by the replanner/turn checker, the design cleverly avoids introducing regressions into the core interview loop logic while adding a robust observability layer.
* **Compelling Narrative:** The UI integration with evidence chains (Participant Quote -> Deterministic Signal -> LLM Classification) provides a clear, transparent narrative of the AI's reasoning process.

## GAPS
* **LLM Confidence Calibration:** The design trusts Gemini's self-reported `field_confidence` as 25% of the total composite score. LLMs are notoriously poorly calibrated for self-reported confidence. Relying on this for a judge-facing metric without secondary validation is risky.
* **Signal/LLM Mismatch Handling:** The spec states: *"if a signal exists for a field but the LLM said 'unknown', flag it as a potential miss"*. However, the architecture doesn't specify *how* or *where* this flag is surfaced in the UI or data model. Does it lower the composite score? Does it turn a badge amber?
* **Regex Limitations:** Using simple regex for "sentiment signals" (e.g., "frustrated") or "competitor names" is highly brittle. It will yield false positives (e.g., "I was frustrated with my commute, but the software is great") and false negatives, undermining the deterministic layer's credibility.
* **UI File Bloat:** `methodic/static/interactive.html` is already ~2050 lines long. Adding complex new components (scorecards, dimension bars, evidence chains) will push it well past maintainability.
* **Early-Turn Score Volatility:** The composite score heavily weights coverage (30%). In the first few turns of an interview, coverage will naturally be low. If the UI flashes a red "INSUFFICIENT" badge on Turn 1, it will look like the AI is failing, rather than just starting.

## ADDITIONAL PATTERNS
The spec correctly excluded expensive patterns like self-consistency sampling and formal argument graphs for a live demo. However, it missed several high-impact, low-latency quality assurance patterns:

* **Reverse Verification (Hallucination Checking):** Instead of just extracting hints *before* the LLM call, verify the LLM's output *after*. If the LLM claims a specific value or competitor, deterministically check if that exact string (or a close match) exists in the raw transcript. If not, penalize the Evidence-link score.
* **Confidence Downgrading via Heuristics:** Do not trust `field_confidence` blindly. Cap or downgrade it based on objective factors. For example, if the LLM reports 0.9 confidence but the evidence quote is only 3 words long, or if no deterministic signals were found, artificially cap the confidence score.
* **Contradiction Detection (Internal Consistency):** Data quality isn't just about coverage; it's about consistency. A lightweight check to see if a newly extracted field value contradicts a previously extracted value (e.g., budget changing from `in_cycle` to `out_of_cycle`) could trigger a powerful "WARN" state, showcasing advanced quality control.
* **Progressive / Expected Coverage Scaling:** Instead of an absolute coverage score, measure *expected* coverage. Turn 1 shouldn't be penalized for not covering all 8 fields. The gate bands should scale based on the turn count (e.g., reaching 60% coverage by Turn 3 is a "PASS").

## RISK
* **False Positives in Pre-check:** If the regex pre-check flags "we have a strong security team" as a `security_concern` signal, but the LLM correctly ignores it because it's not a concern *about the product*, the system will incorrectly flag it as an LLM "miss." Judges might mistakenly conclude the LLM is faulty.
* **UI Performance & Payload Size:** Sending the full `CompositeScore` (including all per-field breakdowns and signals) over SSE on every extraction cycle could bloat the payload and cause UI jitter if the updates are not batched or smoothed.

## VERDICT
**REVISE_REQUIRED**

The core concept is excellent and directly addresses the need for judge-facing transparency. However, the reliance on brittle regex for subjective fields and the uncalibrated LLM confidence scores introduce too much risk for a live demo.

**Required Revisions:**
1. **Refine Deterministic Extraction:** Limit the regex pre-check to highly reliable, objective patterns (dollar amounts, timelines). Remove subjective patterns (sentiment) unless using a dedicated, fast NLP model.
2. **Address Early-Turn Volatility:** Define how the score and gate badge are handled in early turns (e.g., hide the gate badge until Turn 3, or use a "Progressive Coverage" metric).
3. **Clarify Mismatch Logic:** Explicitly define how a "potential miss" (Signal found, LLM says unknown) affects the score or UI.
4. **Mitigate File Bloat:** Include a task to extract CSS and JavaScript from `interactive.html` into separate files before adding the new UI logic.