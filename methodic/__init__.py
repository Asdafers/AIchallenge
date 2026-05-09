"""Methodic ADK Agent - B2B win-loss research multi-agent system."""

MODEL = "gemini-3.1-pro-preview"
MODEL_FAST = "gemini-3.1-flash-lite-preview"
MODEL_STABLE_FALLBACK = "gemini-3-flash-preview"

from . import agent  # noqa: E402 — required by ADK deploy, must be after MODEL defs
