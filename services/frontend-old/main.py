import streamlit as st
import os
from static.custom_css import custom_css
from src.app.header import display_header
from src.app.sidebar import display_sidebar
from src.app.main_content import display_main_content

# Initialize environment
os.makedirs("data/uploads", exist_ok=True)


def main():
    st.set_page_config(
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(custom_css, unsafe_allow_html=True)

    # Session State Initialization
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "selected_vision_model" not in st.session_state:
        st.session_state.selected_vision_model = "Moondream2"

    display_header()
    display_sidebar()
    display_main_content()


if __name__ == "__main__":
    main()
