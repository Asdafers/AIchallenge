# Architecture Diagram

Mermaid source for the Methodic system architecture. Render with any Mermaid-compatible tool.

## System Flow

```mermaid
graph TD
    subgraph "External"
        SA["Sales Insights Agent<br/><i>request_study</i>"]
    end

    subgraph "Methodic Core"
        WP3["WP3: Organizer Flow<br/>Request → Clarification → Brief → Approval"]
        WP4["WP4: Methodology Agent<br/>Sample bias correction<br/>Question-variable mapping"]
        WP5["WP5: Conversation Engine<br/>3 adaptive participant sessions<br/>Probing + guardrail recovery"]
        WP6["WP6: MCP Boundary<br/>lookup_deal_context<br/>stdio JSON-RPC 2.0"]
        WP7["WP7: Data Quality Layer<br/>4-dimension rubric scoring<br/>Coverage tracking"]
        WP8["WP8: Re-Plan Trigger<br/>Autonomous gap detection<br/>Reserve session dispatch"]
        WP9a["WP9a: BigQuery Export<br/>Schema validation<br/>Structured row output"]
    end

    subgraph "Data Sources (MCP)"
        CRM["CRM Fixtures<br/>deal_stage, persona,<br/>crm_notes"]
        TEL["Telemetry Fixtures<br/>executive_logins,<br/>feature_touchpoints"]
    end

    subgraph "Infrastructure"
        DOCKER["Docker Container<br/>node:20-alpine + Python 3"]
        CR["Cloud Run<br/><i>deployment-ready</i>"]
        BQ["BigQuery<br/><i>dry-run validated</i>"]
    end

    SA -->|"request_study payload"| WP3
    WP3 -->|"research brief"| WP4
    WP4 -->|"revised sample + questions"| WP5
    WP5 -->|"participant responses"| WP7
    WP5 -.->|"context request"| WP6
    WP6 -->|"filtered context"| WP5
    WP6 -->|"stdio JSON-RPC"| CRM
    WP6 -->|"stdio JSON-RPC"| TEL
    WP7 -->|"coverage gaps"| WP8
    WP8 -->|"P-005 session"| WP7
    WP7 -->|"scored data"| WP9a
    WP9a -->|"structured rows"| BQ
    DOCKER -->|"orchestrates"| WP3
    DOCKER -.->|"deploys to"| CR
```

## Data Quality Comparison

```mermaid
graph LR
    subgraph "Static Survey"
        SS["Fixed questions<br/>No follow-up<br/>No context lookup"]
        SS --> SQ["Composite: 0.069"]
    end

    subgraph "Methodic"
        MA["Adaptive probing<br/>MCP context<br/>Guardrail recovery"]
        MA --> MQ["Composite: 0.761"]
    end

    SQ -.->|"Δ +0.692"| MQ
```

## Pipeline Sequence

```mermaid
sequenceDiagram
    participant E as External Agent
    participant O as Organizer (WP3)
    participant M as Methodology (WP4)
    participant P as Participants (WP5)
    participant MCP as MCP Server (WP6)
    participant Q as Quality (WP7)
    participant R as Re-Plan (WP8)
    participant BQ as BigQuery (WP9a)

    E->>O: request_study
    O->>E: clarification question
    E->>O: clarification response
    O->>M: research brief + biased sample
    M->>O: pushback + revised sample + questions
    
    loop 3 Participants (P-001, P-002, P-003)
        O->>P: approved study plan
        P->>MCP: lookup_deal_context(pid, allowed_fields)
        MCP->>P: filtered CRM+telemetry context
        P->>Q: structured response + transcript
    end

    Q->>R: coverage report (procurement_friction: ambiguous)
    R->>P: dispatch P-005 (reserve)
    P->>Q: P-005 response
    Q->>BQ: 6 scored rows (17 fields each)
```

## Google Stack Alignment

```mermaid
graph LR
    G["Gemini API"] -->|"reasoning"| WP4["Methodology<br/>Review"]
    ADK["ADK"] -.->|"future orchestration"| CORE["Methodic Core"]
    MCP["MCP"] -->|"tool boundary"| WP6["Context<br/>Lookup"]
    CR["Cloud Run"] -->|"deployment"| DOCKER["Container"]
    BQ["BigQuery"] -->|"export"| DATA["Structured<br/>Dataset"]

    style ADK stroke-dasharray: 5 5
```
