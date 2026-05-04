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
  |     |           +-- participant_sim (LlmAgent)
  |     |           +-- extractor_step (custom BaseAgent, assembles transcript)
  |     |           +-- turn_checker (custom BaseAgent, escalates inner loop)
  |     +-- coverage_step (custom BaseAgent)
  |     +-- replanner (custom BaseAgent, escalates outer loop on STOP)
  |
  +-- finalize (SequentialAgent)
        +-- quality_reviewer (LlmAgent)
        +-- bigquery_export (custom BaseAgent)
        +-- completion_responder (LlmAgent)
"""

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

# Phase 1: Study Planning
study_planner = SequentialAgent(
    name="study_planner",
    sub_agents=[organizer_agent, methodology_agent, question_design_agent],
)

# Phase 2: Fieldwork Loop
interview_loop = LoopAgent(
    name="interview_loop",
    max_iterations=6,
    sub_agents=[
        interviewer_agent,
        participant_sim_agent,
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
        replanner_agent,
    ],
)

# Phase 3: Finalize
completion_responder = Agent(
    name="completion_responder",
    model=MODEL,
    instruction="""Summarize the study results. Include key findings,
coverage achieved, themes, and BigQuery export status.""",
)

finalize = SequentialAgent(
    name="finalize",
    sub_agents=[
        quality_agent,
        BigQueryExportStep(name="bigquery_export"),
        completion_responder,
    ],
)

# Root Agent
root_agent = SequentialAgent(
    name="methodic",
    sub_agents=[study_planner, fieldwork_loop, finalize],
)
