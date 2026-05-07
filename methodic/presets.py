"""Study preset configurations for interactive mode."""

from __future__ import annotations

PRESETS: dict[str, dict[str, str]] = {
    "lost_deals": {
        "title": "Q1 2026 Lost Deal Analysis",
        "brief": (
            "Run a win-loss study on recent Q1 2026 lost deals. "
            "Focus on understanding why deals were lost, especially "
            "around ROI clarity and procurement friction. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a VP of Engineering who evaluated our B2B analytics "
            "platform but chose a competitor. You liked the product but "
            "struggled to justify the per-seat cost internally."
        ),
    },
    "churn": {
        "title": "Enterprise Churn Analysis",
        "brief": (
            "Investigate why enterprise customers are not renewing. "
            "Focus on security concerns, competitor pressure, and ROI. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a CTO who decided not to renew after 2 years. "
            "The product worked but your team found a cheaper alternative "
            "that covered 80% of the use cases."
        ),
    },
    "competitive": {
        "title": "Competitive Displacement Study",
        "brief": (
            "Understand why customers are switching to competitors. "
            "Focus on feature gaps, pricing models, and support quality. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a Head of IT who switched from our product to a rival "
            "after a procurement review flagged integration concerns."
        ),
    },
}


def get_preset(name: str) -> dict[str, str] | None:
    return PRESETS.get(name)
