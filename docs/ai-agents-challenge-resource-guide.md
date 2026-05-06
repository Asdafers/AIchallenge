# AI Agents Challenge — Complete Resource Guide (2026)

Source: Google for Startups AI Agents Challenge PDF

## Overview

$500 in credits for all eligible startups. $90,000 prize pool. Three tracks.

## Three Tracks

### Track 1: Build (Net-new agents)

For those starting with a blank canvas. Use ADK (or LangChain/CrewAI) to architect autonomous agents using MCP to connect to external tools.

**Bootstrapping:**
- Core ADK Framework: Agents, Sessions, Runners
- **Agents CLI**: Newly launched CLI to scaffold and clone production-ready templates for ReAct, RAG, Multi-Agent
- Agent Starter Pack repository: Foundational code for ReAct, RAG, Multi-Agent patterns
- Awesome ADK Agents: 80+ hackathon-winning and pre-configured agents
- Cloud Shell: Quick setup directly in GCP console

**Key resources:**
- Official Python ADK repository (google/adk-python): 5-layer architecture, agent logic, MCP/OpenAPI, AgentEngineSandboxCodeExecutor
- Official Agent Platform documentation: Bridges local code to cloud deployment
- ADK Agents community collection: 80+ production-ready templates on GitHub
- Agent Search and grounding notebooks: Jupyter notebooks for Datastores and Google Search grounding

### Track 2: Optimize (Existing agents)

Transition from sandbox to real-world reliability. Stress-test multi-step reasoning, debug stalled logic, refine system instructions.

**Testing/Refining:**
- Agent Simulation and Evaluation: Generate synthetic interactions, measure against baselines
- Agent Observability: Visually trace complex reasoning, debug bottlenecks
- Managing State (Sessions, Runtime, Memory Bank): Configure AdkApp for Sessions and Memory Banks
- Public grounding (Google Search): Real-time public data grounding

**Deploying:**
- Deploy to Agent Runtime: Fully-managed runtime with scaling, IAM, container customization
- Grounding (Custom RAG): Agent Search Data Stores with Cloud Storage or BigQuery
- Public grounding (Google Search): "Grounding with Google Search" tool
- Capture your demo: Build a simple frontend or use Cloud console UI. **Tip: Demo video should clearly highlight "before and after"**

### Track 3: Refactor for Google Cloud Marketplace and Gemini Enterprise

Transform MVP into scalable, monetizable enterprise asset.

**Step-by-step:**
- Validate B2B use case: Must be explicitly designed for business workflows
- Migrate to Google Cloud Runtime: Cloud Run (stateless) or GKE (stateful)
- Route LLMs through Model Garden: Gemini or third-party via Model Garden
- Implement A2A Protocol: Refactor to A2A-native for agent-to-agent exchange
- Multi-agent orchestration (Agent Builder overview): Agent2Agent protocol and Agent Garden tools
- Finalize documentation: GKE/Cloud Run deployment architecture, model usage, A2A intents

*Important: Track 3 completion does not guarantee Marketplace listing. Requires further business/security evaluations and formal partnership agreements.*

## Sign up for Google Cloud

Existing users: visit cloud.google.com/ and create a new project.

New users:
1. **Sign in:** Go to cloud.google.com, click Get started for free, log in with Gmail
2. **Initial setup:** Select country, agree to ToS, click Continue
3. **Verify identity:** Select Individual, enter name/address/payment method, click Start My Free Trial
4. **Initiate project:** In Cloud Console, click project drop-down, select New Project
5. **Create project:** Enter project name (e.g., Startup-AI-Challenge-app), Organization = No organization, click Create

## Why Participate

- Cloud credits: $500 per eligible startup
- Prize pool: $90,000+ total
- Technical support: Google experts, webinars, resource guides
- Global recognition: Panel of expert judges, Google Cloud ecosystem showcase
