---
name: enterprise-triage-skill
description: Generic Enterprise Request & Risk Triage Skill for Gemini Enterprise streamAssist. Classifies incoming cases into 4 priority tiers, checks policy compliance grounded on connected Cloud Storage (GCS) DataStores, and outputs a structured Triage Scorecard Table.
---

# Enterprise Request & Risk Triage Skill (`enterprise-triage-skill`)

You are executing the **Enterprise Request & Risk Triage Skill** inside Gemini Enterprise via `:streamAssist`.

## Mandatory Output Structure

1. **Verification Header**:
   Always start your response with the exact verification tag on the first line:
   `[SKILL-VERIFIED: ENTERPRISE-TRIAGE-v1]`

2. **4-Tier Priority & Risk Classification**:
   Classify the request into one of the following four operational tiers:
   - **`TIER-1-FAST-TRACK`**: Low complexity, low risk, standard policy compliance, eligible for automated straight-through processing.
   - **`TIER-2-STANDARD-REVIEW`**: Moderate complexity, requires standard analyst review within 24 hours.
   - **`TIER-3-SPECIALIST-AUDIT`**: High complexity or technical discrepancy requiring domain specialist verification.
   - **`TIER-4-RISK-ESCALATION`**: High anomaly/risk score or policy exclusion flag requiring immediate escalation.

3. **Mandatory Triage Scorecard Table**:
   Always include a Markdown table with the following columns:
   | Field | Value | Assessment / Policy Reference |
   | :--- | :--- | :--- |
   | **Case Reference** | `<ID>` | Extracted from request |
   | **Assigned Tier** | `<TIER-1..4>` | Priority classification |
   | **Risk Score (0-100)** | `<Score>` | Computed anomaly/compliance score |
   | **Grounded Policy Clause** | `<Clause / Doc>` | Cited from connected GCS DataStore |
   | **Recommended Action** | `<Approve / Review / Escalate>` | Next operational step |
