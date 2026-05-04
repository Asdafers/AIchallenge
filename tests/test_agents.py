"""Tests for agent definitions - verify wiring, not LLM behavior."""

import pytest
from google.adk.agents import Agent


def test_organizer_agent():
    from methodic.agents.organizer import organizer_agent
    assert isinstance(organizer_agent, Agent)
    assert organizer_agent.name == "organizer"
    assert organizer_agent.output_key == "study_brief"
    assert "gemini" in organizer_agent.model.lower()


def test_methodology_agent():
    from methodic.agents.methodology import methodology_agent
    assert isinstance(methodology_agent, Agent)
    assert methodology_agent.name == "methodology"
    assert methodology_agent.output_key == "methodology_review"


def test_question_design_agent():
    from methodic.agents.question_design import question_design_agent
    assert isinstance(question_design_agent, Agent)
    assert question_design_agent.name == "question_design"
    assert question_design_agent.output_key == "question_pool"
