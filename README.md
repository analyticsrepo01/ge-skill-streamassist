# ge-skill-streamassist

End-to-end reference application demonstrating how to integrate **Google Cloud Gemini Enterprise (Discovery Engine `:streamAssist`)** with:
1. **Multi-Turn Conversational Sessions** (`sessionInfo.session`) exclusively via `:streamAssist` (zero direct LLM SDK calls).
2. **Registered Gemini Enterprise Custom Skills & Low-Code Agents** (`skillsSpec` + `agentsSpec`, including automatic IAM service-account fallback for Cloud Run deployments).
3. **Cloud Storage (GCS) Bucket Connector Grounding** (`toolsSpec.vertexAiSearchSpec.dataStoreSpecs`) with live document upload, incremental indexing (`documents:import`), and inline grounding citations.
4. **Sequential Multi-Stage Orchestration (`enterprise-orchestrator-skill`)** and **4-Tier Request Triage (`enterprise-triage-skill`)** powered by FastAPI and a modern single-page Web UI deployable to Google Cloud Run.

---

## Architecture Overview

```text
Browser UI (static/index.html)
   │
   ▼
FastAPI Backend (main.py on Cloud Run)
   │
   ▼  POST https://discoveryengine.googleapis.com/v1alpha/.../assistants/default_assistant:streamAssist
Gemini Enterprise Engine (:streamAssist)
   ├── skillsSpec / agentsSpec ──► Registered GE Skills (SKILL.md) & Low-Code Agents
   └── toolsSpec.vertexAiSearchSpec.dataStoreSpecs ──► Connected GCS Bucket DataStore
```

---

## Project Structure

```text
.
├── .env.example                                   # Environment variable template (no secrets)
├── .gitignore                                     # Ignores donoshare/, .env, credentials, images
├── Dockerfile                                     # Cloud Run container definition
├── requirements.txt                               # Python dependencies (no direct LLM SDKs)
├── main.py                                        # FastAPI backend calling :streamAssist
├── static/
│   └── index.html                                 # Interactive Web UI
├── skills/
│   ├── enterprise-orchestrator-skill/SKILL.md     # 3-Stage Sequential Orchestrator Skill
│   └── enterprise-triage-skill/SKILL.md           # 4-Tier Request & Risk Triage Skill
└── scripts/
    └── verify_streamassist_backend.py             # Backend verification script
```

---

## Quickstart

### 1. Configure Environment Variables

Copy `.env.example` to `.env` (which is gitignored) and fill in your Google Cloud project and Gemini Enterprise engine details:

```bash
cp .env.example .env
export $(grep -v '^#' .env | xargs)
```

### 2. Verify Backend (`:streamAssist`, Skills & GCS Grounding)

```bash
pip install -r requirements.txt
python3 scripts/verify_streamassist_backend.py
```

### 3. Run Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. Deploy to Google Cloud Run

```bash
gcloud run deploy ge-skill-streamassist \
  --source=. \
  --project="${GOOGLE_CLOUD_PROJECT}" \
  --region=us-central1 \
  --allow-unauthenticated
```
