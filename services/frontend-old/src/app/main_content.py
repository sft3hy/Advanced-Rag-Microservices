import streamlit as st
from pathlib import Path
import traceback
import requests
import os
import json

# Import the UI utility functions from the same app directory
from .ui_utils import get_all_chart_images, extract_page_number, get_charts_for_page

# Configuration
RAG_API_URL = os.environ.get("RAG_API_URL", "http://rag_core:8000")
with open("static/doggie.svg", "r") as bot_file:
    bot_svg = bot_file.read()

with open("static/user.svg", "r") as user_file:
    user_svg = user_file.read()


def _fetch_session_documents(session_id):
    """
    Fetches document metadata (chart dirs, descriptions) for the session from the API.
    """
    try:
        resp = requests.get(f"{RAG_API_URL}/sessions/{session_id}/documents", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching docs: {e}")
    return []


def _display_interaction_details(results: list):
    """
    A reusable helper function to display the sources and related charts for a query.
    """
    if not results:
        return

    with st.expander("📚 View Sources & Related Charts"):
        # Step 1: Find all unique charts related to the source documents
        chart_images = []
        documents = st.session_state.get("session_documents", [])

        if documents:
            for doc in documents:
                for result in results:
                    if (
                        "[CHART DESCRIPTION" in result["text"]
                        or "[SLIDE VISUAL DESCRIPTION" in result["text"]
                    ):
                        page = result.get("page", 0)
                        chart_dir = Path(doc.get("chart_dir", ""))
                        if chart_dir.exists():
                            page_charts = get_charts_for_page(chart_dir, page)
                            chart_images.extend(page_charts)

        unique_chart_images = list(dict.fromkeys(chart_images))

        # Step 2: Display the related charts
        if unique_chart_images:
            st.markdown("##### 🖼️ Related Charts")
            cols = st.columns(min(len(unique_chart_images), 3))

            # Helper to find description across all docs
            def find_description(img_name):
                for doc in documents:
                    # Robust lookup: Try parsed key first, then raw column
                    descriptions = doc.get(
                        "chart_descriptions", doc.get("chart_descriptions_json", {})
                    )

                    if isinstance(descriptions, str):
                        try:
                            descriptions = json.loads(descriptions)
                        except:
                            descriptions = {}

                    if img_name in descriptions:
                        return descriptions[img_name]
                return "Chart from document"

            for i, img_path in enumerate(unique_chart_images):
                with cols[i % 3]:
                    description = find_description(img_path.name)
                    st.image(str(img_path), caption=description)
            st.divider()

        # Step 3: Display the text sources
        st.markdown("##### 📄 Text Sources")
        for idx, result in enumerate(results, 1):
            source_path = result.get("source", "Unknown")
            source_name = Path(source_path).name
            try:
                score = float(result.get("score", 1))
                relevance_score = (1 / (1 + score)) * 100
                source_info = f"**Source {idx} (from {source_name} - Page {result.get('page', 'N/A')})** - Relevance: {relevance_score:.1f}%"
            except (ValueError, TypeError):
                source_info = f"**Source {idx} (from {source_name} - Page {result.get('page', 'N/A')})**"

            with st.container(border=True):
                st.write(source_info)
                st.markdown(result["text"])


def display_main_content():
    """Controls the display of the main content area."""

    if not st.session_state.get("session_id"):
        display_welcome_screen()
        return

    session_id = st.session_state.session_id

    # Fetch/Refresh Session Data
    if (
        "session_documents" not in st.session_state
        or st.session_state.get("doc_session_id") != session_id
    ):
        st.session_state.session_documents = _fetch_session_documents(session_id)
        st.session_state.doc_session_id = session_id

    documents = st.session_state.get("session_documents", [])
    doc_count = len(documents)
    query_count = len(st.session_state.get("chat_history", []))

    if doc_count > 0:
        if doc_count == 1:
            doc_name = documents[0].get("original_filename", "Document")
            st.info(f"📄 Active Document: **{doc_name}** | 💬 {query_count} queries")
        else:
            st.info(
                f"📚 Active Session | 📄 {doc_count} documents | 💬 {query_count} queries"
            )

            with st.expander("📋 View all documents in this session"):
                for i, doc in enumerate(documents, 1):
                    v_model = doc.get("vision_model_used", "Unknown")
                    st.markdown(
                        f"{i}. **{doc['original_filename']}** (processed with {v_model})"
                    )

    display_chat_history()
    display_qa_interface()
    display_chart_browser()


def display_chat_history():
    """Loads and displays the full Q&A history for the active session."""
    history = st.session_state.get("chat_history", [])

    for interaction in history:
        with st.chat_message("user", avatar=user_svg):
            st.markdown(interaction["question"])
        with st.chat_message("assistant", avatar=bot_svg):
            st.markdown(interaction["response"])
            _display_interaction_details(interaction.get("sources", []))


def display_welcome_screen():
    st.markdown(
        """
    <div style='text-align: center; padding: 4rem 2rem; background: rgba(255, 255, 255, 0.05); border-radius: 20px; backdrop-filter: blur(10px);'>
        <h2 style='font-size: 2rem; margin-bottom: 1rem;'>👋 Welcome to Smart RAG</h2>
        <p style='font-size: 1.2rem; color: #e0e0ff; margin-bottom: 2rem;'>
            Upload a document or load a past session from the sidebar to begin.
        </p>
        </div>
    """,
        unsafe_allow_html=True,
    )


def display_qa_interface():
    question = st.chat_input("Ask a question about your document(s)...")

    if question:
        session_id = st.session_state.get("session_id")

        if not session_id:
            st.error("Error: No active session. Please start one in the sidebar.")
            return

        with st.chat_message("user", avatar=user_svg):
            st.markdown(question)

        with st.chat_message("assistant", avatar=bot_svg):
            with st.spinner("🤔 Finding answers..."):
                try:
                    payload = {"session_id": session_id, "question": question}
                    response = requests.post(
                        f"{RAG_API_URL}/query", json=payload, timeout=120
                    )

                    if response.status_code != 200:
                        st.error(f"API Error: {response.text}")
                        return

                    data = response.json()
                    if "error" in data:
                        st.error(f"Backend Error: {data['error']}")
                        return

                    answer = data.get("response", "No response.")
                    results = data.get("results", [])

                    st.markdown(answer)

                    if "chat_history" not in st.session_state:
                        st.session_state.chat_history = []

                    st.session_state.chat_history.append(
                        {"question": question, "response": answer, "sources": results}
                    )
                    _display_interaction_details(results)

                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    traceback.print_exc()


def display_chart_browser():
    """
    Displays an interactive browser for all charts detected in all active documents.
    """
    documents = st.session_state.get("session_documents", [])
    if not documents:
        return

    all_chart_files = []
    chart_to_doc = {}

    for doc in documents:
        chart_dir = Path(doc.get("chart_dir", "")).resolve()

        if chart_dir.exists():
            chart_files = get_all_chart_images(chart_dir)
            # print("Chart files:", chart_files)
            for chart_file in chart_files:
                if not chart_file.is_absolute():
                    full_path = chart_dir / chart_file.name
                else:
                    full_path = chart_file.resolve()

                all_chart_files.append(full_path)
                chart_to_doc[str(full_path)] = doc

    if not all_chart_files:
        return

    st.divider()
    total_charts = len(all_chart_files)
    if total_charts == 0:
        st.write("No charts detected.")
        return

    if "chart_browser_idx" not in st.session_state:
        st.session_state.chart_browser_idx = 0
    if st.session_state.chart_browser_idx >= total_charts:
        st.session_state.chart_browser_idx = 0

    with st.expander(f"📊 Detected Charts ({total_charts} total)", expanded=False):
        idx = st.session_state.chart_browser_idx

        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 3, 1, 1])

        with nav_col1:
            if st.button("⬅️", width="stretch", disabled=total_charts <= 1):
                st.session_state.chart_browser_idx = (idx - 1) % total_charts
                st.rerun()

        chart_path = all_chart_files[idx]
        current_doc = chart_to_doc[str(chart_path)]

        with nav_col2:
            page_number = extract_page_number(chart_path)
            st.markdown(
                f"<h4 style='text-align: center; margin: 0;'>Chart {idx + 1} of {total_charts} (Page {page_number} - {current_doc['original_filename']})</h4>",
                unsafe_allow_html=True,
            )

        with nav_col3:
            if st.button("➡️", width="stretch", disabled=total_charts <= 1):
                st.session_state.chart_browser_idx = (idx + 1) % total_charts
                st.rerun()

        with nav_col4:
            new_idx = st.number_input(
                "Jump", 1, total_charts, idx + 1, label_visibility="collapsed"
            )
            if new_idx - 1 != idx:
                st.session_state.chart_browser_idx = int(new_idx - 1)
                st.rerun()

        # --- FIX IS HERE ---
        # 1. Try 'chart_descriptions' (Parsed from DB Utils)
        # 2. Try 'chart_descriptions_json' (Raw from DB)
        descriptions = current_doc.get(
            "chart_descriptions", current_doc.get("chart_descriptions_json", {})
        )

        # Ensure it is a dict
        if isinstance(descriptions, str):
            try:
                descriptions = json.loads(descriptions)
            except:
                descriptions = {}

        description = descriptions.get(chart_path.name, "No description available.")

        cols = st.columns([1, 1.5, 1])
        cols[1].image(str(chart_path))
        st.markdown(description)
