import os
from pathlib import Path
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Hybrid Data Pipeline | Enterprise Data Observatory",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit chrome, header, footer, and set full-bleed iframe margins
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none !important;}
    .stApp {
        background-color: #05070A !important;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin: 0rem !important;
        max-width: 100% !important;
    }
    iframe {
        width: 100% !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Read and render full cyber neon index.html interface
html_path = PROJECT_DIR / "index.html"
if html_path.exists():
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=980, scrolling=True)
else:
    st.error("index.html file not found.")
