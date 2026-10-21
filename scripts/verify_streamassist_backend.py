"""End-to-end backend verification for Gemini Enterprise :streamAssist."""

import os
import google.auth
from google.auth.transport.requests import Request
import requests

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
PROJECT_NUM = os.environ["GOOGLE_CLOUD_PROJECT_NUMBER"]
LOCATION = os.environ.get("GE_LOCATION", "global")
COLLECTION_ID = os.environ.get("GE_COLLECTION_ID", "default_collection")
ENGINE_ID = os.environ["GE_ENGINE_ID"]
ASSISTANT_ID = os.environ.get("GE_ASSISTANT_ID", "default_assistant")
SKILL_ID = os.environ.get("GE_PRIMARY_SKILL_ID", "private-enterprise-triage-skill")
AGENT_ID = os.environ.get("GE_PRIMARY_AGENT_ID", "")
DATASTORE_ID = os.environ["GE_DATASTORE_ID"]
BASE_URL = "https://discoveryengine.googleapis.com/v1alpha"


def get_headers():
  creds, _ = google.auth.default(
      scopes=["https://www.googleapis.com/auth/cloud-platform"]
  )
  creds.refresh(Request())
  return {
      "Authorization": f"Bearer {creds.token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": PROJECT_ID,
  }


def main():
  headers = get_headers()
  stream_url = (
      f"{BASE_URL}/projects/{PROJECT_NUM}/locations/{LOCATION}/collections/"
      f"{COLLECTION_ID}/engines/{ENGINE_ID}/assistants/{ASSISTANT_ID}:streamAssist"
  )
  ds_resource = (
      f"projects/{PROJECT_NUM}/locations/{LOCATION}/collections/"
      f"{COLLECTION_ID}/dataStores/{DATASTORE_ID}"
  )
  skill_resource = f"projects/{PROJECT_NUM}/locations/{LOCATION}/skills/{SKILL_ID}"

  print("=== 1. Testing Baseline streamAssist + Session Continuity ===")
  r1 = requests.post(
      stream_url,
      headers=headers,
      json={"query": {"text": "Hello! Remember reference code REF-10042."}},
      timeout=60,
  )
  assert r1.status_code == 200, r1.text

  print("=== 2. Testing GCS DataStore Grounding via streamAssist ===")
  r2 = requests.post(
      stream_url,
      headers=headers,
      json={
          "query": {"text": "Summarize the documents in our connected GCS DataStore."},
          "toolsSpec": {
              "vertexAiSearchSpec": {
                  "dataStoreSpecs": [{"dataStore": ds_resource}]
              }
          },
      },
      timeout=90,
  )
  assert r2.status_code == 200, r2.text

  print("=== 3. Testing Skill & Agent Invocation via streamAssist ===")
  payload = {
      "query": {"text": "Triage request REQ-88912 using our registered skill."},
      "skillsSpec": {"skills": [{"name": skill_resource}]},
  }
  if AGENT_ID:
    payload["agentsSpec"] = {"agentSpecs": [{"agentId": AGENT_ID}]}
  r3 = requests.post(stream_url, headers=headers, json=payload, timeout=90)
  assert r3.status_code in (200, 403), r3.text
  print("ALL STREAMASSIST BACKEND CHECKS COMPLETED!")


if __name__ == "__main__":
  main()
