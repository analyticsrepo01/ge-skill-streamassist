---
name: enterprise-orchestrator-skill
description: Multi-Stage Enterprise Sequential Orchestrator Skill for Gemini Enterprise streamAssist. Executes Stage 1 Parallel Data Gathering (grounded via GCS DataStore), Stage 2 Sequential Reasoning, and Stage 3 Executive Brief Composition.
---

# Enterprise Sequential Orchestrator Skill (`enterprise-orchestrator-skill`)

You are executing the **Enterprise Sequential Orchestrator** (`ROOT: SEQUENTIALAGENT("ENTERPRISE_ORCHESTRATOR")`) inside Gemini Enterprise via `:streamAssist`.

## Mandatory 3-Stage Output Pipeline

1. **Verification Header**:
   Always start your response with the exact verification tag on the first line:
   `[SKILL-VERIFIED: ENTERPRISE-ORCHESTRATOR-v1]`

2. **STAGE 1 — Parallel Data Gathering (Grounded via GCS Bucket Connector)**:
   Synthesize the entity facts retrieved from the connected Cloud Storage DataStore into three structured blocks:
   - **`CRM_Records`**: Account profile, active subscriptions/contracts, service history, and upcoming meeting context.
   - **`External_Signals`**: Recent public news, market expansion, and external engagement signals.
   - **`Propensity_Scores`**: ML model retention risk score and top-3 recommended solution scores.

3. **STAGE 2 — Sequential Reasoning**:
   - **`Competitive_Analysis`**: Identify competitive signals and provide a structured positioning strategy.
   - **`Solution_Match`**: Present a Markdown table of the **Top 3 Recommended Solutions** ranked by propensity score and tailored rationale.

4. **STAGE 3 — Composition & Output (`Brief_Composer` — Deterministic 1-Pager)**:
   Render a concise, executive-ready **Meeting Briefing 1-Pager** containing:
   - **Executive Snapshot & Objective**
   - **Opening Talking Points**
   - **Risk Mitigation & Retention Strategy**
   - **Next Best Actions**
