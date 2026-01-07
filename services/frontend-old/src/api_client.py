import requests
import os
import streamlit as st

API_URL = os.environ.get("RAG_API_URL", "http://rag_core:8000")


def check_backend_health():
    """Checks if the backend is online/reachable."""
    try:
        # We request /docs because it's a lightweight standard FastAPI endpoint
        resp = requests.get(f"{API_URL}/docs", timeout=3)
        return resp.status_code == 200
    except:
        return False


def get_sessions():
    try:
        resp = requests.get(f"{API_URL}/sessions")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Failed to connect to RAG API: {e}")
    return []


def create_session(filenames):
    try:
        resp = requests.post(f"{API_URL}/sessions", json={"filenames": filenames})
        if resp.status_code == 200:
            return resp.json()["session_id"]
    except Exception as e:
        st.error(f"Error creating session: {e}")
    return None


def get_session_documents(session_id):
    """
    Fetches the list of documents associated with a session.
    Used for populating the Chart Browser and Session Info.
    """
    try:
        resp = requests.get(f"{API_URL}/sessions/{session_id}/documents")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        # Don't show error immediately on UI to avoid clutter if just loading
        print(f"Failed to fetch session documents: {e}")
    return []


def process_document(session_id, filename, vision_model):
    payload = {
        "session_id": session_id,
        "filename": filename,
        "vision_model": vision_model,
    }
    try:
        # Use a long timeout for processing (10 mins)
        resp = requests.post(f"{API_URL}/process", json=payload, timeout=600)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def query_system(session_id, question):
    payload = {"session_id": session_id, "question": question}
    try:
        # Timeout 120s for LLM generation
        resp = requests.post(f"{API_URL}/query", json=payload, timeout=120)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_history(session_id):
    try:
        resp = requests.get(f"{API_URL}/sessions/{session_id}/history")
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []