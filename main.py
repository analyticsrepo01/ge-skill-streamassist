import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage
from pydantic import BaseModel
import requests

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
PROJECT_NUM = os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER", "000000000000")
LOCATION = os.environ.get("GE_LOCATION", "global")
COLLECTION_ID = os.environ.get("GE_COLLECTION_ID", "default_collection")
ENGINE_ID = os.environ.get("GE_ENGINE_ID", "your-gemini-enterprise-engine-id")
ASSISTANT_ID = os.environ.get("GE_ASSISTANT_ID", "default_assistant")
WIDGET_CID = os.environ.get("GE_WIDGET_CID", "your-console-widget-cid")

PRIMARY_SKILL_ID = os.environ.get(
    "GE_PRIMARY_SKILL_ID", "private-enterprise-triage-skill"
)
PRIMARY_AGENT_ID = os.environ.get("GE_PRIMARY_AGENT_ID", "your-primary-agent-id")
ORCHESTRATOR_SKILL_ID = os.environ.get(
    "GE_ORCHESTRATOR_SKILL_ID", "private-enterprise-orchestrator-skill"
)
ORCHESTRATOR_AGENT_ID = os.environ.get(
    "GE_ORCHESTRATOR_AGENT_ID", "your-orchestrator-agent-id"
)

DATASTORE_ID = os.environ.get("GE_DATASTORE_ID", "your-gcs-datastore-id")
BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name")

UI_APP_TITLE = os.environ.get("UI_APP_TITLE", "Enterprise Assistant")
UI_APP_SUBTITLE = os.environ.get(
    "UI_APP_SUBTITLE", "Gemini Enterprise streamAssist Portal"
)
UI_PRIMARY_COLOR = os.environ.get("UI_PRIMARY_COLOR", "#2563EB")

BASE_URL = "https://discoveryengine.googleapis.com/v1alpha"

SKILLS_CATALOG = {
    "enterprise-orchestrator-skill": {
        "id": "enterprise-orchestrator-skill",
        "displayName": "enterprise-orchestrator-skill (Sequential Orchestrator)",
        "rootOrchestrator": 'ROOT: SEQUENTIALAGENT("ENTERPRISE_ORCHESTRATOR")',
        "discoveryEngineSkill": f"projects/{PROJECT_NUM}/locations/{LOCATION}/skills/{ORCHESTRATOR_SKILL_ID}",
        "geSkillAgentId": ORCHESTRATOR_AGENT_ID,
        "verificationBadge": "[SKILL-VERIFIED: ENTERPRISE-ORCHESTRATOR-v1]",
        "skillDir": "enterprise-orchestrator-skill",
    },
    "enterprise-triage-skill": {
        "id": "enterprise-triage-skill",
        "displayName": "enterprise-triage-skill (Request & Risk Triage)",
        "rootOrchestrator": "ENTERPRISE-TRIAGE-v1",
        "discoveryEngineSkill": f"projects/{PROJECT_NUM}/locations/{LOCATION}/skills/{PRIMARY_SKILL_ID}",
        "geSkillAgentId": PRIMARY_AGENT_ID,
        "verificationBadge": "[SKILL-VERIFIED: ENTERPRISE-TRIAGE-v1]",
        "skillDir": "enterprise-triage-skill",
    },
}

DATASTORES = {
    DATASTORE_ID: {
        "id": DATASTORE_ID,
        "displayName": f"Cloud Storage DataStore Connector ({DATASTORE_ID})",
        "bucket": f"gs://{BUCKET_NAME}",
        "resource": f"projects/{PROJECT_NUM}/locations/{LOCATION}/collections/{COLLECTION_ID}/dataStores/{DATASTORE_ID}",
    },
}

app = FastAPI(
    title=f"{UI_APP_TITLE} — Gemini Enterprise streamAssist API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_headers() -> Dict[str, str]:
  creds, _ = google.auth.default(
      scopes=["https://www.googleapis.com/auth/cloud-platform"]
  )
  creds.refresh(Request())
  return {
      "Authorization": f"Bearer {creds.token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": PROJECT_ID,
  }


def load_skill_markdown(skill_id: str = "enterprise-triage-skill") -> str:
  skill_info = SKILLS_CATALOG.get(
      skill_id, SKILLS_CATALOG["enterprise-triage-skill"]
  )
  skill_path = os.path.join(
      os.path.dirname(__file__),
      "skills",
      skill_info["skillDir"],
      "SKILL.md",
  )
  if os.path.exists(skill_path):
    with open(skill_path, "r", encoding="utf-8") as f:
      return f.read()
  return f"Always prefix output with {skill_info['verificationBadge']}."


def resolve_skill_id(query: str, requested_skill_id: Optional[str]) -> str:
  if requested_skill_id and requested_skill_id in SKILLS_CATALOG:
    return requested_skill_id
  q_lower = query.lower()
  orchestrator_keywords = [
      "prep me",
      "meeting",
      "brief",
      "orchestrator",
      "propensity",
      "stage 1",
  ]
  if any(k in q_lower for k in orchestrator_keywords):
    return "enterprise-orchestrator-skill"
  return "enterprise-triage-skill"


def parse_stream_assist_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
  texts: List[str] = []
  thoughts: List[str] = []
  citations: List[Dict[str, str]] = []
  search_results: List[Dict[str, str]] = []
  session: Optional[str] = None
  invoked_skills: List[Any] = []
  assist_token: Optional[str] = None

  for c in chunks:
    if c.get("sessionInfo", {}).get("session"):
      session = c["sessionInfo"]["session"]
    if c.get("assistToken"):
      assist_token = c["assistToken"]
    if c.get("invokedSkills"):
      invoked_skills.extend(c["invokedSkills"])

    ans = c.get("answer", {})
    for rep in ans.get("replies", []):
      gc = rep.get("groundedContent", {})
      content = gc.get("content", {})
      if content.get("thought", False):
        if content.get("text"):
          thoughts.append(content["text"])
      elif content.get("text"):
        texts.append(content["text"])

      tgm = gc.get("textGroundingMetadata", {})
      for ref in tgm.get("references", []):
        doc_meta = ref.get("documentMetadata", {})
        citations.append({
            "title": doc_meta.get("title", "GCS Document"),
            "uri": doc_meta.get("uri", ""),
            "page": str(doc_meta.get("pageIdentifier", "")),
        })

    for step in ans.get("steps", []):
      for action in step.get("actions", []):
        obs = action.get("observation", {})
        for sr in obs.get("searchResults", []):
          search_results.append({
              "title": sr.get("title", ""),
              "uri": sr.get("uri", ""),
          })

  seen = set()
  unique_citations = []
  for cit in citations:
    key = (cit["title"], cit["uri"])
    if key not in seen:
      seen.add(key)
      unique_citations.append(cit)

  full_answer = "".join(texts)
  verified_skill_id = None
  for sk_id, sk_meta in SKILLS_CATALOG.items():
    badge_core = sk_meta["verificationBadge"].strip("[]")
    if badge_core in full_answer:
      verified_skill_id = sk_id
      break

  return {
      "answer": full_answer,
      "thoughts": "".join(thoughts),
      "citations": unique_citations,
      "searchResults": search_results,
      "session": session,
      "assistToken": assist_token,
      "invokedSkills": invoked_skills,
      "skillVerified": verified_skill_id is not None,
      "verifiedSkillId": verified_skill_id,
      "chunkCount": len(chunks),
  }


class ChatRequest(BaseModel):
  query: str
  session: Optional[str] = None
  use_skill: bool = False
  skill_id: Optional[str] = "auto"
  use_gcs_connector: bool = True
  selected_datastores: Optional[List[str]] = None


class GcsSyncRequest(BaseModel):
  filename: str
  title: str
  content: str


@app.get("/api/config")
def get_config():
  return {
      "ui": {
          "title": UI_APP_TITLE,
          "subtitle": UI_APP_SUBTITLE,
          "primaryColor": UI_PRIMARY_COLOR,
      },
      "projectId": PROJECT_ID,
      "projectNumber": PROJECT_NUM,
      "engineId": ENGINE_ID,
      "widgetCid": WIDGET_CID,
      "streamAssistEndpoint": f"{BASE_URL}/projects/{PROJECT_NUM}/locations/{LOCATION}/collections/{COLLECTION_ID}/engines/{ENGINE_ID}/assistants/{ASSISTANT_ID}:streamAssist",
      "skillsCatalog": SKILLS_CATALOG,
      "gcsConnectors": list(DATASTORES.values()),
      "triageSkillMarkdown": load_skill_markdown("enterprise-triage-skill"),
      "orchestratorSkillMarkdown": load_skill_markdown(
          "enterprise-orchestrator-skill"
      ),
  }


@app.get("/api/gcs-documents")
def list_gcs_documents():
  headers = get_headers()
  result = {}
  for ds_id, ds_info in DATASTORES.items():
    url = f"{BASE_URL}/{ds_info['resource']}/branches/0/documents"
    r = requests.get(url, headers=headers, timeout=20)
    docs = []
    if r.status_code == 200:
      for d in r.json().get("documents", []):
        docs.append({
            "id": d.get("id"),
            "uri": d.get("content", {}).get("uri", ""),
            "mimeType": d.get("content", {}).get("mimeType", ""),
            "indexTime": d.get("indexTime", ""),
        })
    result[ds_id] = {
        **ds_info,
        "documents": docs,
    }
  return {"datastores": result}


@app.post("/api/chat")
def chat_stream_assist(req: ChatRequest):
  if not req.query.strip():
    raise HTTPException(status_code=400, detail="Query cannot be empty.")

  t0 = time.time()
  headers = get_headers()
  assistant_url = f"{BASE_URL}/projects/{PROJECT_NUM}/locations/{LOCATION}/collections/{COLLECTION_ID}/engines/{ENGINE_ID}/assistants/{ASSISTANT_ID}"
  stream_url = f"{assistant_url}:streamAssist"

  payload: Dict[str, Any] = {
      "query": {"text": req.query},
  }
  if req.session:
    payload["session"] = req.session

  # 1. GCS Connector Grounding (toolsSpec.vertexAiSearchSpec.dataStoreSpecs)
  ds_ids = req.selected_datastores or list(DATASTORES.keys())
  if req.use_gcs_connector and ds_ids:
    ds_specs = [
        {"dataStore": DATASTORES[d]["resource"]}
        for d in ds_ids
        if d in DATASTORES
    ]
    if ds_specs:
      payload["toolsSpec"] = {
          "vertexAiSearchSpec": {"dataStoreSpecs": ds_specs}
      }

  # 2. Custom Skill & Agent Invocation via streamAssist
  active_skill_id = resolve_skill_id(req.query, req.skill_id)
  active_skill = SKILLS_CATALOG[active_skill_id]
  skill_md = load_skill_markdown(active_skill_id)

  if req.use_skill:
    payload["skillsSpec"] = {
        "skills": [{"name": active_skill["discoveryEngineSkill"]}]
    }
    payload["agentsSpec"] = {
        "agentSpecs": [{"agentId": active_skill["geSkillAgentId"]}]
    }

  r = requests.post(stream_url, headers=headers, json=payload, timeout=120)

  # Fallback for Cloud Run IAM Service Account when Workspace-scoped agentId returns 403
  if req.use_skill and r.status_code == 403:
    fallback_payload = dict(payload)
    fallback_payload.pop("agentsSpec", None)
    fallback_payload["query"] = {
        "text": (
            f"You are executing the registered Gemini Enterprise Skill `{active_skill_id}` "
            f"({active_skill['rootOrchestrator']} — {active_skill['discoveryEngineSkill']}).\n"
            f"Follow this exact skill specification strictly:\n\n{skill_md}\n\n---\n"
            f"USER REQUEST:\n{req.query}"
        )
    }
    r = requests.post(
        stream_url, headers=headers, json=fallback_payload, timeout=120
    )

  latency_ms = int((time.time() - t0) * 1000)

  if r.status_code != 200:
    raise HTTPException(
        status_code=r.status_code,
        detail={
            "message": "streamAssist API returned an error",
            "upstreamStatus": r.status_code,
            "upstreamBody": r.text[:1000],
            "sentPayload": payload,
        },
    )

  chunks = r.json()
  parsed = parse_stream_assist_chunks(chunks)

  if req.use_skill and req.use_gcs_connector and not parsed["citations"]:
    ds_specs = [
        {"dataStore": DATASTORES[d]["resource"]}
        for d in ds_ids
        if d in DATASTORES
    ]
    r_ground = requests.post(
        stream_url,
        headers=headers,
        json={
            "query": {"text": req.query},
            "toolsSpec": {"vertexAiSearchSpec": {"dataStoreSpecs": ds_specs}},
        },
        timeout=90,
    )
    if r_ground.status_code == 200:
      ground_parsed = parse_stream_assist_chunks(r_ground.json())
      if ground_parsed["citations"]:
        parsed["citations"] = ground_parsed["citations"]
        if ground_parsed["answer"]:
          parsed["answer"] += (
              "\n\n---\n### 📂 Connected GCS Bucket Grounding Context\n"
              + ground_parsed["answer"]
          )

  return {
      **parsed,
      "activeSkillId": active_skill_id if req.use_skill else None,
      "latencyMs": latency_ms,
      "requestPayload": payload,
      "endpoint": stream_url,
  }


@app.post("/api/gcs-upload-and-sync")
def gcs_upload_and_sync(req: GcsSyncRequest):
  headers = get_headers()
  storage_client = storage.Client(project=PROJECT_ID)
  bucket = storage_client.bucket(BUCKET_NAME)

  safe_name = req.filename.strip().replace(" ", "_")
  if not safe_name.endswith((".html", ".txt")):
    safe_name += ".html"

  html_doc = f"""<!DOCTYPE html>
<html>
<head><title>{req.title}</title></head>
<body>
  <h1>{req.title}</h1>
  <div>{req.content}</div>
</body>
</html>"""

  blob = bucket.blob(safe_name)
  blob.upload_from_string(html_doc, content_type="text/html")
  gcs_uri = f"gs://{BUCKET_NAME}/{safe_name}"

  import_url = (
      f"{BASE_URL}/{DATASTORES[DATASTORE_ID]['resource']}/branches/0/documents:import"
  )
  import_payload = {
      "gcsSource": {"inputUris": [gcs_uri], "dataSchema": "content"},
      "reconciliationMode": "INCREMENTAL",
  }
  r_imp = requests.post(
      import_url, headers=headers, json=import_payload, timeout=30
  )
  return {
      "status": "UPLOADED_AND_IMPORT_TRIGGERED",
      "gcsUri": gcs_uri,
      "importStatus": r_imp.status_code,
      "importOperation": r_imp.json() if r_imp.status_code == 200 else r_imp.text,
  }


static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index():
  return FileResponse(os.path.join(static_dir, "index.html"))
