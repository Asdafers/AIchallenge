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
    from methodic.agents.replanner import replanner_agent, ReplannerStep
    assert isinstance(replanner_agent, ReplannerStep)
    assert replanner_agent.name == "replanner"


from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents import LoopAgent


def test_root_agent():
    from methodic.agent import root_agent
    assert isinstance(root_agent, SequentialAgent)
    assert root_agent.name == "methodic"
    assert len(root_agent.sub_agents) == 3


def test_interview_loop_has_4_steps():
    from methodic.agent import interview_loop
    assert isinstance(interview_loop, LoopAgent)
    assert interview_loop.max_iterations == 6
    names = [a.name for a in interview_loop.sub_agents]
    assert "interviewer" in names
    assert "participant_sim" in names
    assert "extractor_step" in names
    assert "turn_checker" in names


def test_fieldwork_loop_has_replanner():
    from methodic.agent import fieldwork_loop
    assert isinstance(fieldwork_loop, LoopAgent)
    names = [a.name for a in fieldwork_loop.sub_agents]
    assert "replanner" in names


def test_finalize_has_export():
    from methodic.agent import finalize
    names = [a.name for a in finalize.sub_agents]
    assert "bigquery_export" in names
    assert "quality_reviewer" in names
