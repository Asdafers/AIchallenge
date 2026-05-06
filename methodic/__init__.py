"""Methodic ADK Agent - B2B win-loss research multi-agent system."""

MODEL = "gemini-2.5-pro"
MODEL_FAST = "gemini-2.5-flash-lite"
MODEL_STABLE_FALLBACK = "gemini-2.5-flash"

from . import agent  # noqa: E402 — required by ADK deploy, must be after MODEL defs
