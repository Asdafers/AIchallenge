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


def test_interviewer_agent():
    from methodic.agents.participant import interviewer_agent
    assert isinstance(interviewer_agent, Agent)
    assert interviewer_agent.name == "interviewer"
    assert interviewer_agent.output_key == "latest_interviewer_turn"
    assert "gemini" in interviewer_agent.model.lower()


def test_participant_sim_agent():
    from methodic.agents.participant_sim import participant_sim_agent
    assert isinstance(participant_sim_agent, Agent)
    assert participant_sim_agent.name == "participant_sim"
    assert participant_sim_agent.output_key == "latest_participant_turn"
    assert "gemini" in participant_sim_agent.model.lower()


def test_quality_agent():
    from methodic.agents.quality import quality_agent
    assert isinstance(quality_agent, Agent)
    assert quality_agent.name == "quality_reviewer"
    assert quality_agent.output_key == "quality_report"


def test_replanner_agent():
    from methodic.agents.replanner import replanner_agent
    assert isinstance(replanner_agent, Agent)
    assert replanner_agent.name == "replanner"
    assert replanner_agent.output_key == "replan_decision"
    assert len(replanner_agent.tools) > 0, "replanner must have check_coverage tool"
