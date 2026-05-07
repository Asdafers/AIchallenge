# methodic/agent.py
"""Root agent definition - ADK entry point.

Agent graph (all sub_agents are agent instances, never raw FunctionTools):

root_agent (SequentialAgent)
  +-- study_planner (SequentialAgent)
  |     +-- organizer (LlmAgent)
  |     +-- methodology (LlmAgent)
  |     +-- question_design (LlmAgent)
  |
  +-- fieldwork_loop (LoopAgent, max_iterations=3)
  |     +-- session_runner (SequentialAgent)
  |     |     +-- session_init (custom BaseAgent, resets turn_count)
  |     |     +-- interview_loop (LoopAgent, max_iterations=6)
  |     |           +-- interviewer (LlmAgent + MCP tools)
  |     |           +-- participant_sim (LlmAgent) OR HumanInputStep (interactive)
  |     |           +-- extractor_step (custom BaseAgent, assembles transcript)
  |     |           +-- turn_checker (custom BaseAgent, escalates inner loop)
  |     +-- coverage_step (custom BaseAgent)
  |     +-- replanner (custom BaseAgent, escalates outer loop on STOP)
  |
  +-- finalize (SequentialAgent)
        +-- quality_reviewer (LlmAgent)       [demo only]
        +-- bigquery_export (custom BaseAgent) [demo only]
        +-- completion_responder (LlmAgent)
"""

from __future__ import annotations

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from methodic import MODEL
from methodic.agents.organizer import organizer_agent
from methodic.agents.methodology import methodology_agent
from methodic.agents.question_design import question_design_agent
from methodic.agents.participant import interviewer_agent
from methodic.agents.participant_sim import participant_sim_agent
from methodic.agents.quality import quality_agent
from methodic.agents.replanner import replanner_agent
from methodic.agents.extractor_step import ExtractorStep
from methodic.agents.turn_checker_step import TurnCheckerStep
from methodic.agents.coverage_step import CoverageStep
from methodic.agents.bigquery_export_step import BigQueryExportStep
from methodic.agents.session_init_step import SessionInitStep


def _build_demo_graph() -> SequentialAgent:
    """Build the demo-mode agent graph with fresh agent instances."""
    study_planner = SequentialAgent(
        name="study_planner",
        sub_agents=[
            organizer_agent.model_copy(deep=True),
            methodology_agent.model_copy(deep=True),
            question_design_agent.model_copy(deep=True),
        ],
    )

    interview_loop = LoopAgent(
        name="interview_loop",
        max_iterations=6,
        sub_agents=[
            interviewer_agent.model_copy(deep=True),
            participant_sim_agent.model_copy(deep=True),
            ExtractorStep(name="extractor_step"),
            TurnCheckerStep(name="turn_checker", max_turns=6),
        ],
    )

    session_runner = SequentialAgent(
        name="session_runner",
        sub_agents=[SessionInitStep(name="session_init"), interview_loop],
    )

    fieldwork_loop = LoopAgent(
        name="fieldwork_loop",
        max_iterations=3,
        sub_agents=[
            session_runner,
            CoverageStep(name="coverage_step"),
            replanner_agent.model_copy(deep=True),
        ],
    )

    completion = Agent(
        name="completion_responder",
        model=MODEL,
        instruction=(
            "Summarize the study results. Include key findings, "
            "coverage achieved, themes, and BigQuery export status."
        ),
    )
    finalize = SequentialAgent(
        name="finalize",
        sub_agents=[
            quality_agent.model_copy(deep=True),
            BigQueryExportStep(name="bigquery_export"),
            completion,
        ],
    )

    return SequentialAgent(
        name="methodic",
        sub_agents=[study_planner, fieldwork_loop, finalize],
    )


def build_agent_graph(
    interactive: bool = False,
    session_registry: dict | None = None,
) -> SequentialAgent:
    """Build and return a configured agent graph.

    Args:
        interactive: When True, swap participant_sim for HumanInputStep,
            cap fieldwork_loop to 1 iteration, and skip quality/export steps.
        session_registry: Required when interactive=True. Maps session IDs
            to InteractiveSession objects for HumanInputStep.

    Returns:
        A SequentialAgent root named "methodic" (demo) or
        "methodic_interactive" (interactive).
    """
    if not interactive:
        # Return the cached module-level demo graph (built at import time).
        # Avoids double-parenting: singleton agents are already claimed by
        # _root_agent; reusing _root_agent is safe, rebuilding is not.
        return _root_agent

    from methodic.agents.human_input_step import HumanInputStep
    participant_agent = HumanInputStep(
        name="participant", session_registry=session_registry or {},
    )

    study_planner = SequentialAgent(
        name="study_planner",
        sub_agents=[
            organizer_agent.model_copy(deep=True),
            methodology_agent.model_copy(deep=True),
            question_design_agent.model_copy(deep=True),
        ],
    )

    interview_loop = LoopAgent(
        name="interview_loop",
        max_iterations=6,
        sub_agents=[
            interviewer_agent.model_copy(deep=True),
            participant_agent,
            ExtractorStep(name="extractor_step"),
            TurnCheckerStep(name="turn_checker", max_turns=6),
        ],
    )

    session_runner = SequentialAgent(
        name="session_runner",
        sub_agents=[SessionInitStep(name="session_init"), interview_loop],
    )

    fieldwork_loop = LoopAgent(
        name="fieldwork_loop",
        max_iterations=1,
        sub_agents=[
            session_runner,
            CoverageStep(name="coverage_step"),
            replanner_agent.model_copy(deep=True),
        ],
    )

    completion = Agent(
        name="completion_responder",
        model=MODEL,
        instruction=(
            "Summarize the study results. Include key findings, "
            "coverage achieved, and themes discovered."
        ),
    )
    finalize = SequentialAgent(
        name="finalize",
        sub_agents=[completion],
    )

    return SequentialAgent(
        name="methodic_interactive",
        sub_agents=[study_planner, fieldwork_loop, finalize],
    )


# Module-level exports for ADK Dev UI, demo mode, and existing test compatibility.
# _root_agent is built once; build_agent_graph(interactive=False) returns it.
_root_agent = _build_demo_graph()
root_agent = _root_agent
study_planner = root_agent.sub_agents[0]
fieldwork_loop = root_agent.sub_agents[1]
interview_loop = fieldwork_loop.sub_agents[0].sub_agents[1]
finalize = root_agent.sub_agents[2]
