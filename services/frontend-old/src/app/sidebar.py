import streamlit as st
import os
import time
import requests
import json
from pathlib import Path

# Environment Variables
RAG_API_URL = os.environ.get("RAG_API_URL", "http://rag_core:8000")
SHARED_UPLOAD_DIR = "/app/data/uploads"


def display_sidebar():
    """Renders the entire sidebar, including session loading."""
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)

        # In microservice mode, the backend handles API keys,
        # but we check if the backend is reachable.
        if "backend_reachable" not in st.session_state:
            try:
                requests.get(f"{RAG_API_URL}/docs", timeout=2)
                st.session_state.backend_reachable = True
            except:
                st.error("❌ Cannot connect to RAG Backend. Is Docker running?")
                st.stop()

        display_session_loader()

        # Show the uploader only for new sessions
        # In API mode, we check if we have a valid session_id
        if not st.session_state.get("session_id"):
            display_vision_model_selection()
            display_document_uploader()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        display_technology_explanations()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        display_supported_formats_and_footer()


def display_session_loader():
    """Displays UI for loading past document processing sessions via API."""
    st.markdown("# 🧠 Smart RAG Document Analyzer")
    st.markdown("### 🗂️ Load Session")

    # Fetch sessions from API
    sessions = []
    try:
        response = requests.get(f"{RAG_API_URL}/sessions")
        if response.status_code == 200:
            sessions = response.json()
    except Exception as e:
        st.error(f"Error fetching sessions: {e}")

    # Create options for the selectbox
    # API returns: [{"id": 1, "name": "file.pdf", "date": "...", "docs": 1}]
    session_options = {}
    for s in sessions:
        doc_text = "doc" if s["docs"] == 1 else "docs"
        display_name = f"{s['name']} ({s['date']}) - {s['docs']} {doc_text}"
        session_options[display_name] = s["id"]

    options_list = ["✨ Start New Session"] + list(session_options.keys())

    selected_option = st.selectbox("Choose a previous session", options=options_list)

    if selected_option != "✨ Start New Session":
        if st.button("Load Selected Session", width="stretch"):
            session_id = session_options[selected_option]
            load_session(session_id)
    else:
        if st.button("Start New Session", width="stretch"):
            # Reset session state
            st.session_state.session_id = None
            st.session_state.chat_history = []
            st.rerun()


def load_session(session_id: int):
    """Handles the logic of loading a past session."""
    with st.spinner(f"Loading session {session_id}..."):
        try:
            # Fetch history to verify session exists and populate chat
            response = requests.get(f"{RAG_API_URL}/sessions/{session_id}/history")

            if response.status_code == 200:
                history = response.json()
                st.session_state.session_id = session_id
                st.session_state.chat_history = history
                st.success(f"Successfully loaded session ID {session_id}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Could not load session history.")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")


def display_vision_model_selection():
    """
    Handles the UI for selecting the vision model.
    List is hardcoded here to match Backend capabilities without extra API calls.
    """
    st.markdown("### Vision Model Selection")

    # These match the keys in VisionModelFactory (backend)
    available_models = [
        "Ollama-Granite3.2-Vision",
        "Ollama-Gemma3",
        "Moondream2",
        "Qwen3-VL-2B",
        "InternVL3.5-1B",
    ]

    model_descriptions = {
        "Moondream2": "Fast (1.6B) - Recommended (Python)",
        "Qwen3-VL-2B": "Balanced (2B) - High Accuracy",
        "InternVL3.5-1B": "Precise (1B) - Document optimized",
        "Ollama-Gemma3": "Gemma 3 (4B) - Requires Ollama",
        "Ollama-Granite3.2-Vision": "IBM Granite (2B) - Efficient Enterprise Vision",
    }

    selected_model = st.selectbox(
        "Choose a vision model",
        available_models,
        index=0,
        # format_func=lambda x: f"{x} - {model_descriptions.get(x, '')}",
        help="Select which vision model to use.",
    )

    st.session_state.selected_vision_model = selected_model

    with st.expander("ℹ️ Model Information"):
        if "Gemma3" in selected_model:
            st.markdown(
                """
                **Gemma 3 (4B)**
                *   **Provider:** Google (Open Weights)
                *   **Architecture:** Multimodal Decoder-only Transformer with SigLIP encoder.
                *   **Context Window:** 128k tokens.
                *   **Capabilities:** Strong general-purpose reasoning and multilingual support (140+ languages).
                *   **Performance:** Achieves ~71.3% on HumanEval and ~75.6% on MATH benchmarks, rivaling larger closed models.
                *   **Best For:** General image understanding, complex reasoning tasks, and multilingual visual Q&A.
                """
            )
        elif "Moondream" in selected_model:
            st.markdown(
                """
                **Moondream2 (1.6B)**
                *   **Provider:** Vikhyat (Open Source)
                *   **Architecture:** Tiny Vision Language Model (SigLIP + Phi-1.5 backbone).
                *   **Parameters:** ~1.6 Billion (optimized for CPU/Edge).
                *   **Speed:** Extremely fast inference; designed to run on laptops and mobile devices.
                *   **Best For:** Rapid image captioning, object detection, and basic visual Q&A where low latency is critical.
                """
            )
        elif "Granite" in selected_model:
            st.markdown(
                """
                **IBM Granite 3.2 Vision (2B)**
                *   **Provider:** IBM
                *   **Specialization:** Enterprise Document Understanding.
                *   **Training Data:** Fine-tuned on the "DocFM" dataset, focusing on charts, tables, and technical diagrams.
                *   **Benchmarks:** State-of-the-art performance for its size on DocVQA and ChartQA.
                *   **Best For:** Extracting data from financial reports, analyzing technical schematics, and reading dense tables.
                """
            )
        elif "Qwen" in selected_model:
            st.markdown(
                """
                **Qwen3-VL (2B)**
                *   **Provider:** Alibaba Cloud (Qwen Team)
                *   **Context Window:** Native 256k tokens (expandable to 1M).
                *   **Key Features:** "Visual Agent" capabilities (GUI understanding), 3D grounding, and structured output generation (JSON).
                *   **OCR Engine:** Support for 30+ languages with robust handling of rotated and blurred text.
                *   **Best For:** Complex OCR, long-context video understanding (>1 hour), and agentic tasks involving computer interfaces.
                """
            )
        elif "InternVL" in selected_model:
            st.markdown(
                """
                **InternVL 3.5 (1B)**
                *   **Provider:** OpenGVLab
                *   **Architecture:** 0.3B Vision Encoder + 0.8B Language Model (~1.1B Total).
                *   **Design:** Uses a "Progressive Scaling" strategy to align vision and language features efficiently.
                *   **Strengths:** High efficiency for "prototype" scale deployments with decent reasoning capabilities.
                *   **Best For:** Layout analysis, visual grounding, and high-throughput document parsing tasks on constrained hardware.
                """
            )


def display_document_uploader():
    """
    Handles the file uploader and the 'Process Document' button.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📄 Upload Document(s)")

    uploaded_files = st.file_uploader(
        "Choose a PDF, DOCX, or PPTX file",
        type=["pdf", "docx", "pptx"],
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    if uploaded_files:
        button_text = "🚀 Process Document"
        if len(uploaded_files) > 1:
            button_text += "s"

        if st.button(button_text, width="stretch"):
            process_documents(uploaded_files)


def process_documents(uploaded_files):
    """
    Handles uploading files to shared volume and triggering backend processing.
    """
    progress_bar = st.progress(0, text="Initializing...")
    status_text = st.empty()

    # Ensure upload directory exists
    os.makedirs(SHARED_UPLOAD_DIR, exist_ok=True)

    try:
        # 1. Create Session via API
        filenames = [f.name for f in uploaded_files]
        status_text.markdown(f"Creating session for {len(filenames)} files...")

        session_resp = requests.post(
            f"{RAG_API_URL}/sessions", json={"filenames": filenames}
        )

        if session_resp.status_code != 200:
            st.error(f"Failed to create session: {session_resp.text}")
            return

        session_id = session_resp.json()["session_id"]
        st.session_state.session_id = session_id  # Set immediately

        # 2. Process each file
        total_files = len(uploaded_files)

        for idx, file in enumerate(uploaded_files):
            # Update Progress
            status_text.markdown(
                f"📄 **Processing {file.name} ({idx+1}/{total_files})...**"
            )

            # A. Save file to Shared Volume
            file_path = os.path.join(SHARED_UPLOAD_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getvalue())

            # B. Trigger Processing API
            # Note: We use a long timeout because parsing + vision + embedding takes time
            try:
                payload = {
                    "session_id": session_id,
                    "filename": file.name,
                    "vision_model": st.session_state.selected_vision_model,
                }

                # This call waits for the backend to finish processing
                process_resp = requests.post(
                    f"{RAG_API_URL}/process",
                    json=payload,
                    timeout=600,  # 10 minute timeout per file
                )

                if process_resp.status_code != 200:
                    st.error(f"Error processing {file.name}: {process_resp.text}")

            except requests.exceptions.Timeout:
                st.error(
                    f"Timeout while processing {file.name}. It might still be running in the background."
                )
            except Exception as e:
                st.error(f"API Error: {e}")

            # Update bar
            progress_bar.progress((idx + 1) / total_files)

        status_text.empty()
        progress_bar.empty()
        st.success(f"✅ Successfully processed {total_files} document(s)!")

        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")


def display_technology_explanations():
    """Renders the expanders explaining the technologies used."""
    st.markdown("### 🔧 Technologies Used")

    with st.expander("🎯 Combined Chart Detection"):
        st.markdown(
            """
            This app uses a **microservice architecture**:
            - **Parser Service:** Uses **PubLayNet** to detect Tables and Figures.
            - **Vision Service:** dedicated container for running LLMs on images.
            """
        )
    with st.expander("👁️ Local Vision Models"):
        st.markdown(
            """
            Chart analysis is performed by the **Vision Service**.
            - **Test Mode (Mac):** Runs on CPU or via Native Ollama app.
            - **Prod Mode (Linux):** Runs on NVIDIA T4 GPU.
            """
        )
    with st.expander("🤖 RAG Core"):
        st.markdown(
            """
            The **RAG Core** orchestrates the pipeline:
            - **Vector Store:** FAISS (running in container).
            - **LLM:** Llama 4 (via Groq) or Sanctuary.
            - **Chunking:** Parent-Child strategy for better context.
            """
        )


def display_supported_formats_and_footer():
    """Renders the supported formats list and the sidebar footer."""
    st.markdown("### Supported Formats")
    st.markdown(
        """
            - 📕 PDF Documents (.pdf)
            - 📝 Word Documents (.docx)
            - 📊 PowerPoint (.pptx)
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #fff; font-size: 0.8rem;'>Built with Streamlit & Docker</p>",
        unsafe_allow_html=True,
    )
