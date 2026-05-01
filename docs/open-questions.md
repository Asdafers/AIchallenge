# Open Questions

## Product Scope

- Which buyer should the demo target first: product research, HR, customer success, market research, or operations?
- Should the first workflow be called a survey, interview, intake, research study, or data-capture campaign?
- What type of data quality failure should the demo make most visible: low completion, shallow answers, ambiguity, bias, missing variables, or inconsistent schema?

## Methodology

- What level of statistical grounding is credible for a prototype without over-claiming?
- Should the system recommend sample size, confidence level, stratification, and segment quotas?
- How should the system explain qualitative research rigor, such as saturation, coding consistency, and interviewer bias?
- What guardrails prevent survey agents from leading participants or changing measurement intent?

## Architecture

- Should the initial prototype use ADK directly, or start with a simpler orchestration layer and migrate into ADK?
- Which external tools should be exposed through MCP first?
- Should participant sessions be real-time chat only, or should voice be part of the demo?
- What storage model best supports study design, response records, evidence snippets, and quality metadata?

## Challenge Positioning

- Should the submission emphasize data quality, participant engagement, research operations speed, or enterprise-ready governance?
- What visual review package would best impress judges in a short demo?
- How do we make the business case quantifiable without needing a real customer dataset?

## Suggested Defaults

- Buyer: SaaS product team.
- Workflow name: agentic research campaign.
- Demo study: why mid-market enterprise deals are being lost or slipping.
- Main quality claim: fewer ambiguous answers and better coverage of decision-critical variables.
- Prototype scope: web chat plus simulated participant pool.
