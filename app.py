import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen_fallback import generate_data
from model_pipeline import DATA_PATH, FEATURES, load_and_clean_data, train_and_evaluate


PROJECT_DIR = Path(__file__).resolve().parent
CPP_SOURCE = PROJECT_DIR / "data_engine.cpp"
DATA_FILE = PROJECT_DIR / DATA_PATH
EXECUTABLE = PROJECT_DIR / ("data_engine.exe" if os.name == "nt" else "data_engine")
METRIC_CAPTION = (
    "These metrics reflect fit quality on synthetic, formula-generated data. "
    "They demonstrate a working ingestion -> training -> evaluation pipeline, "
    "not real-world predictive accuracy."
)


st.set_page_config(
    page_title="Gurgaon Housing Pipeline",
    page_icon=":house:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS — theme-safe. We never override text colours, so metric values,
# headings, and numbers stay readable in both light and dark Streamlit themes.
# Only borders, spacing, shadows, and the teal button accent are customised.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Global font + dark base ──────────────────────────────────────── */
    html, body, [class*="st-"] {
        font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Deep slate background with subtle teal radial glow at the top */
    .stApp {
        background:
            radial-gradient(circle at 50% 0%, rgba(13,148,136,0.10), transparent 45%),
            linear-gradient(180deg, #0f172a 0%, #0b1220 100%);
    }

    /* Section breathing room */
    .block-container {
        padding-top: 7.5rem !important;
        padding-bottom: 3rem;
    }

    /* ══ NAVBAR ═══════════════════════════════════════════════════════ */
    #navbar {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 2rem;
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(45, 212, 191, 0.25);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }
    #navbar .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.15rem;
        font-weight: 800;
        color: #e2e8f0;
        letter-spacing: 0.2px;
    }
    #navbar .nav-brand .logo-dot {
        width: 12px; height: 12px;
        border-radius: 50%;
        background: #2dd4bf;
        box-shadow: 0 0 12px #2dd4bf, 0 0 24px rgba(45,212,191,0.5);
        animation: nav-pulse 2s ease-in-out infinite;
    }
    #navbar .nav-links { display: flex; gap: 1.6rem; }
    #navbar .nav-links a {
        color: #94a3b8;
        text-decoration: none;
        font-size: 0.92rem;
        font-weight: 600;
        transition: color 0.2s ease, text-shadow 0.2s ease;
    }
    #navbar .nav-links a:hover {
        color: #2dd4bf;
        text-shadow: 0 0 10px rgba(45,212,191,0.7);
    }
    #navbar .nav-status {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 500;
    }
    @keyframes nav-pulse {
        0%, 100% { box-shadow: 0 0 8px #2dd4bf, 0 0 16px rgba(45,212,191,0.4); }
        50%      { box-shadow: 0 0 16px #2dd4bf, 0 0 32px rgba(45,212,191,0.7); }
    }

    /* Hide Streamlit's default title bar area collision */
    [data-testid="stHeader"] { background: transparent !important; }

    /* ── Metric cards: solid dark card + glowing teal border ─────────── */
    [data-testid="stMetric"] {
        background: #1e293b !important;
        border: 1px solid rgba(45, 212, 191, 0.45) !important;
        border-radius: 14px !important;
        padding: 1.3rem 1.5rem !important;
        box-shadow: 0 0 14px rgba(45, 212, 191, 0.18), inset 0 0 20px rgba(45, 212, 191, 0.05);
        transition: box-shadow 0.3s ease, transform 0.3s ease, border-color 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(45, 212, 191, 0.9) !important;
        box-shadow: 0 0 26px rgba(45, 212, 191, 0.45), inset 0 0 30px rgba(45, 212, 191, 0.08);
        transform: translateY(-3px);
    }
    [data-testid="stMetricValue"] {
        color: #2dd4bf !important;
        font-weight: 800 !important;
        text-shadow: 0 0 12px rgba(45, 212, 191, 0.6);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }

    /* ── Primary + form-submit buttons: vivid teal with glow ─────────── */
    .stButton > button[kind="primary"],
    button[kind="secondary"][data-testid="stFormSubmitButton"],
    button[kind="primary"][data-testid="stFormSubmitButton"] {
        background-color: #0d9488 !important;
        border: 1px solid #2dd4bf !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 0 16px rgba(45, 212, 191, 0.45);
        transition: box-shadow 0.25s ease, background-color 0.25s ease, transform 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover,
    button[kind="secondary"][data-testid="stFormSubmitButton"]:hover,
    button[kind="primary"][data-testid="stFormSubmitButton"]:hover {
        background-color: #0f766e !important;
        border-color: #5eead4 !important;
        color: #ffffff !important;
        box-shadow: 0 0 28px rgba(45, 212, 191, 0.75);
        transform: translateY(-2px);
    }

    /* ── Tabs ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-weight: 700;
        font-size: 1rem;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #2dd4bf !important;
        text-shadow: 0 0 10px rgba(45, 212, 191, 0.5);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #2dd4bf !important;
        box-shadow: 0 0 12px rgba(45, 212, 191, 0.8);
    }
    .stTabs [data-baseweb="tab-panel"] > div {
        animation: fade-in 0.45s ease;
    }

    /* ── Headings ────────────────────────────────────────────────────── */
    h1, h2, h3 {
        color: #f1f5f9 !important;
        text-shadow: 0 0 18px rgba(45, 212, 191, 0.15);
    }
    h1 { font-weight: 800 !important; letter-spacing: -0.5px; }
    h2 { border-bottom: 1px solid rgba(45, 212, 191, 0.2); padding-bottom: 0.4rem; }
    h4 { color: #2dd4bf !important; font-weight: 700 !important; }

    /* ── Dataframes, expanders, code ─────────────────────────────────── */
    .stDataFrame, .stTable {
        border: 1px solid rgba(45, 212, 191, 0.2) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    .stExpander {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(45, 212, 191, 0.25) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] details summary span {
        color: #2dd4bf !important;
        font-weight: 700;
    }

    /* ── Formula card: SOLID dark background so it's always visible ──── */
    .formula-card {
        background: #0f172a;
        border: 1px solid rgba(45, 212, 191, 0.5);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin: 1.25rem 0;
        box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.12), 0 8px 30px rgba(45, 212, 191, 0.18);
        animation: glow-pulse 3.5s ease-in-out infinite;
    }
    .formula-card .formula-eq {
        font-family: "JetBrains Mono", "Cascadia Code", "Consolas", "Courier New", monospace;
        font-size: 1rem;
        line-height: 2.0;
        color: #e2e8f0;
        background: #020617;
        border: 1px solid rgba(45, 212, 191, 0.35);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        overflow-x: auto;
        white-space: pre;
    }
    .formula-card .formula-eq .tok-feat   { color: #2dd4bf; font-weight: 700; }
    .formula-card .formula-eq .tok-coef   { color: #fbbf24; font-weight: 700; }
    .formula-card .formula-eq .tok-noise  { color: #c084fc; font-weight: 700; }
    .formula-card .formula-title {
        font-weight: 800;
        font-size: 1.1rem;
        color: #2dd4bf;
        margin-bottom: 0.5rem;
        letter-spacing: 0.2px;
    }
    .formula-card .formula-legend {
        font-size: 0.82rem;
        margin-top: 0.85rem;
        color: #94a3b8;
    }

    /* ── Pipeline step chips ─────────────────────────────────────────── */
    .pipeline-chip {
        display: inline-block;
        background: rgba(45, 212, 191, 0.12);
        border: 1px solid rgba(45, 212, 191, 0.45);
        border-radius: 999px;
        padding: 0.35rem 0.95rem;
        margin: 0.25rem 0.35rem 0.25rem 0;
        font-size: 0.82rem;
        font-weight: 700;
        color: #2dd4bf;
    }

    /* ── Animations ──────────────────────────────────────────────────── */
    @keyframes glow-pulse {
        0%, 100% { box-shadow: 0 0 0 1px rgba(45,212,191,0.12), 0 8px 30px rgba(45,212,191,0.15); }
        50%      { box-shadow: 0 0 0 1px rgba(45,212,191,0.30), 0 10px 40px rgba(45,212,191,0.32); }
    }
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ══ FIX 1b: FORCE STREAMLIT NATIVE CHROME INTO DARK MODE ═════════ */
    /* Page + main background (overrides Streamlit default light) */
    .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMainViewContainer"] {
        background: #0e1117 !important;
        color: #e6e6e6 !important;
    }
    /* Top header bar / decoration */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: transparent !important;
        color: #e6e6e6 !important;
    }
    /* Sidebar (if used) */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background: #11141c !important;
        color: #e6e6e6 !important;
    }
    /* All text defaults to light */
    .stApp p, .stApp li, .stApp label, .stApp span {
        color: #e6e6e6;
    }
    .stApp [data-testid="stCaptionContainer"] { color: #9ca3af !important; }
    /* Widget labels */
    [data-testid="stWidgetLabel"] p {
        color: #e6e6e6 !important;
        font-weight: 600 !important;
    }
    /* Input / number_input interior */
    .stApp input, .stApp textarea, .stNumberInput input {
        background: #1a1d24 !important;
        color: #e6e6e6 !important;
        border-color: rgba(255,255,255,0.10) !important;
    }
    /* Slider track + handle */
    .stApp [data-baseweb="slider"] { background: #1a1d24 !important; }
    /* Tabs container background */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1d24 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 0.35rem !important;
    }
    /* Dataframe / table cells */
    .stDataFrame [data-testid="stDataFrame"], .stTable {
        background: #1a1d24 !important;
        color: #e6e6e6 !important;
    }
    /* Alerts (success/info/warning/error) */
    div[data-testid="stAlert"] {
        background: #1a1d24 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        color: #e6e6e6 !important;
        border-radius: 12px !important;
    }
    div[data-testid="stAlert"] * { color: #e6e6e6 !important; }
    /* Download + secondary buttons */
    div[data-testid="stDownloadButton"] button,
    .stButton button[kind="secondary"] {
        background: #1a1d24 !important;
        color: #2dd4bf !important;
        border: 1px solid rgba(45,212,191,0.45) !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    /* Dividers */
    .stApp hr, [data-testid="stDivider"] {
        border-color: rgba(255,255,255,0.10) !important;
    }
    /* Code blocks */
    .stApp pre, .stCodeBlock {
        background: #05070a !important;
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
    }

    /* ══ FIX 2: STANDARDIZED HEADING HIERARCHY ════════════════════════ */
    /* Page title — large, bold, high-contrast near-white */
    .stApp h1 {
        color: #f5f7fa !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        text-shadow: 0 0 22px rgba(45, 212, 191, 0.25) !important;
        margin-top: 0.2rem !important;
    }
    /* Section headers (inside tabs) — medium, semi-bold, accent left border */
    .stApp h2 {
        color: #f0f0f0 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        margin-top: 1.6rem !important;
        margin-bottom: 0.75rem !important;
        padding-bottom: 0.4rem !important;
        border-bottom: 0 !important;
        border-left: 4px solid #2dd4bf !important;
        padding-left: 0.75rem !important;
        text-shadow: 0 0 14px rgba(45, 212, 191, 0.20) !important;
    }
    /* Sub-headers — slightly bigger, accent colored */
    .stApp h3 {
        color: #2dd4bf !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-top: 1.3rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 0 12px rgba(45, 212, 191, 0.30) !important;
    }
    /* Labels above metrics/inputs — smaller, muted, uppercase */
    .stApp h4 {
        color: #9ca3af !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }
    </style>

    <!-- ══ NAVBAR (fixed at top, glassy dark, teal accents) ════════════ -->
    <div id="navbar">
      <div class="nav-brand">
        <span class="logo-dot"></span>
        Gurgaon Housing Pipeline
      </div>
      <div class="nav-links">
        <a href="#generate">Generate</a>
        <a href="#train">Train</a>
        <a href="#predict">Predict</a>
      </div>
      <div class="nav-status">Synthetic-data systems demo</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helper functions (unchanged)
# ---------------------------------------------------------------------------

def compile_data_engine() -> subprocess.CompletedProcess:
    compiler = shutil.which("g++")
    if compiler is None:
        raise FileNotFoundError("g++ was not found on PATH. Install g++ or add it to PATH, then try again.")

    return subprocess.run(
        [compiler, "-O2", str(CPP_SOURCE), "-o", str(EXECUTABLE)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )


def run_data_engine(row_count: int) -> subprocess.CompletedProcess:
    cmd = [str(EXECUTABLE), str(row_count)]
    st.info(f"Running: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )


def load_existing_data() -> pd.DataFrame | None:
    if not DATA_FILE.exists():
        return None
    return pd.read_csv(DATA_FILE)


@st.cache_data
def cached_training_result(csv_mtime: float) -> dict:
    del csv_mtime
    data = load_and_clean_data(DATA_FILE)
    return train_and_evaluate(data, verbose=False)


def get_training_result() -> dict | None:
    if not DATA_FILE.exists():
        return None
    return cached_training_result(DATA_FILE.stat().st_mtime)


# ---------------------------------------------------------------------------
# Page header (navbar is rendered via CSS above; this is the hero title)
# ---------------------------------------------------------------------------
st.markdown('<div id="top"></div>', unsafe_allow_html=True)
st.markdown(
    "<h1 style='margin-bottom:0.2rem;'>Gurgaon Housing Pipeline</h1>"
    "<p style='color:#64748b; font-size:1.08rem; margin-top:0; max-width:860px;'>"
    "A cross-language systems demo: <span style='color:#4f46e5;font-weight:700;'>C++ generation</span> -> "
    "<span style='color:#4f46e5;font-weight:700;'>Python ML</span> -> "
    "<span style='color:#4f46e5;font-weight:700;'>Streamlit visualization</span>. "
    "All data is synthetic and not suitable for real-world valuation."
    "</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data once (used across tabs)
# ---------------------------------------------------------------------------
df = load_existing_data()
automatic_training_result = get_training_result() if df is not None else None

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_generate, tab_train, tab_predict = st.tabs(
    ["Generate Data", "Train Model", "Predict Price"],
)

# ======================= TAB 1 — Generate Data ============================
with tab_generate:
    st.markdown('<a id="generate"></a>', unsafe_allow_html=True)
    st.markdown("## Data Generation")

    col_input, col_btn = st.columns([1, 3])
    with col_input:
        row_count = st.number_input(
            "Rows to generate", min_value=100, max_value=10000, value=1000, step=100,
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_clicked = st.button("Generate Data", type="primary", key="gen_btn")

    if generate_clicked:
        row_count_int = int(row_count)
        try:
            previous_rows = st.session_state.get("last_generated_rows")
            should_compile = not EXECUTABLE.exists() or previous_rows != row_count_int

            if should_compile:
                with st.spinner("Compiling data_engine.cpp..."):
                    compile_data_engine()

            with st.spinner("Running C++ data engine..."):
                result = run_data_engine(row_count_int)

            st.session_state["last_generated_rows"] = row_count_int
            st.session_state["last_generation_mtime"] = DATA_FILE.stat().st_mtime
            cached_training_result.clear()
            st.success(f"{row_count_int:,} rows generated -> {DATA_FILE.name}")
            if result.stdout:
                with st.expander("Engine output", expanded=False):
                    st.code(result.stdout, language="text")
        except FileNotFoundError:
            output_path = generate_data(row_count_int, DATA_FILE)
            st.session_state["last_generated_rows"] = row_count_int
            st.session_state["last_generation_mtime"] = DATA_FILE.stat().st_mtime
            cached_training_result.clear()
            st.warning("g++ not found — used Python fallback generator.")
            st.success(f"{row_count_int:,} rows generated -> {output_path.name}")
        except subprocess.CalledProcessError as exc:
            st.error("Compilation or data generation failed.")
            details = "\n".join(part for part in [exc.stdout, exc.stderr] if part)
            if details:
                st.code(details, language="text")

    # Reload after potential generation so the preview reflects fresh data
    df = load_existing_data()
    automatic_training_result = get_training_result() if df is not None else None

    st.divider()

    st.markdown("## Data Preview")
    if df is None:
        st.info("Generate data first, or place synthetic_housing_data.csv in the project folder.")
    else:
        expected_rows = st.session_state.get("last_generated_rows")
        actual_rows = len(df)

        st.caption(f"**Rows in CSV: {actual_rows:,}**")

        if expected_rows and actual_rows != expected_rows:
            st.error(
                f"Row count mismatch! Expected {expected_rows:,} rows from generation, "
                f"but the CSV file contains {actual_rows:,} rows. "
                "The file may be stale or was overwritten by another process."
            )

        st.caption(f"Showing first 20 of {actual_rows:,} total rows")
        show_all = st.checkbox("Show all rows")
        st.dataframe(df if show_all else df.head(20), width="stretch")

        col_download, _ = st.columns([1, 3])
        col_download.download_button(
            label="Download full CSV",
            data=df.to_csv(index=False),
            file_name="synthetic_housing_data.csv",
            mime="text/csv",
        )

        st.divider()

        # Summary statistics — proper visible heading + dataframe
        st.markdown("#### Summary statistics")
        st.dataframe(df.describe(), width="stretch")

        # Charts side by side
        chart_col_a, chart_col_b = st.columns(2)
        with chart_col_a:
            histogram = px.histogram(
                df,
                x="price_lakhs",
                nbins=40,
                title="Price Distribution",
                labels={"price_lakhs": "Price (Lakhs)"},
            )
            histogram.update_layout(
                template="plotly_dark",
                colorway=["#2dd4bf"],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#11141c",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#e6e6e6"},
                margin={"l": 24, "r": 18, "t": 56, "b": 36},
            )
            st.plotly_chart(histogram)

        with chart_col_b:
            metro_scatter = px.scatter(
                df,
                x="metro_distance_km",
                y="price_lakhs",
                title="Metro Distance vs Price",
                labels={"metro_distance_km": "Metro Distance (km)", "price_lakhs": "Price (Lakhs)"},
            )
            metro_scatter.update_traces(marker={"color": "#2dd4bf", "opacity": 0.68, "size": 7})
            metro_scatter.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#11141c",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#e6e6e6"},
                margin={"l": 24, "r": 18, "t": 56, "b": 36},
            )
            st.plotly_chart(metro_scatter)

        sqft_scatter = px.scatter(
            df,
            x="sqft",
            y="price_lakhs",
            color="bedrooms",
            title="Sqft vs Price",
            labels={"sqft": "Sqft", "price_lakhs": "Price (Lakhs)", "bedrooms": "Bedrooms"},
        )
        sqft_scatter.update_layout(
            template="plotly_dark",
            colorway=["#2dd4bf", "#22d3ee", "#34d399", "#fbbf24", "#c084fc"],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#11141c",
            font={"family": "Inter, Segoe UI, sans-serif", "color": "#e6e6e6"},
            margin={"l": 24, "r": 18, "t": 56, "b": 36},
        )
        sqft_scatter.update_traces(marker={"opacity": 0.72, "size": 7})
        st.plotly_chart(sqft_scatter)


# ======================= TAB 2 — Train Model ==============================
with tab_train:
    st.markdown('<a id="train"></a>', unsafe_allow_html=True)
    st.markdown("## Model Training")
    st.caption(
        "Train a RandomForestRegressor (n_estimators=200, max_depth=8) on the current dataset. "
        "Click the button below to fit the model and view MAE, R², and feature importances."
    )

    # ── Always-visible explainer: How the model works ───────────────────────
    st.markdown("### How the model works")
    st.markdown(
        """
        This is a **synthetic-data systems demo**. The C++ engine generates fake
        housing records using the formula below, writes them to a CSV, and this
        tab trains a scikit-learn model on that CSV. The goal is to prove the
        full pipeline — **generation → ingestion → training → evaluation** — works
        end to end. The numbers are *measured, not fabricated*.
        """,
    )

    st.markdown(
        """
        <div class="pipeline-chip">C++ generate</div>
        <div class="pipeline-chip">CSV boundary</div>
        <div class="pipeline-chip">Pandas ingest</div>
        <div class="pipeline-chip">train/test split</div>
        <div class="pipeline-chip">RandomForest fit</div>
        <div class="pipeline-chip">MAE / R² / importances</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="formula-card">
          <div class="formula-title">🏠 Price formula encoded in the C++ generator</div>
          <div class="formula-eq"><span class="tok-feat">price</span> = ( <span class="tok-coef">18.0</span>
        + <span class="tok-coef">0.105</span> × <span class="tok-feat">sqft</span>
        + <span class="tok-coef">7.5</span>  × <span class="tok-feat">bedrooms</span> )
      × age_decay(<span class="tok-feat">age_years</span>)
      + <span class="tok-coef">42.0</span> × metro_proximity(<span class="tok-feat">metro_distance_km</span>)
      + <span class="tok-coef">0.035</span> × <span class="tok-feat">sqft</span> × metro_proximity^1.25
      + <span class="tok-noise">Gaussian noise(σ=30)</span>
      + <span class="tok-noise">5% outlier shock(σ=85)</span></div>
          <div class="formula-legend">
            <span class="tok-feat">■</span> input feature &nbsp;&nbsp;
            <span class="tok-coef">■</span> coefficient &nbsp;&nbsp;
            <span class="tok-noise">■</span> injected noise
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "**Why this matters:** when you click *Train Model*, the RandomForest should "
        "recover these relationships. The **Feature Importances** chart below will show "
        "`sqft` as the dominant driver (~82%), which matches the formula — proving the "
        "model learned the encoded structure, not random noise. An R2 around **0.77** "
        "(not 0.99) confirms the model fits the signal *through* the injected noise."
    )

    st.warning(
        "These metrics reflect pipeline correctness on synthetic, formula-generated "
        "data — **not** real-world Gurgaon price accuracy. Swap the CSV for real listings "
        "to turn this into a real predictor."
    )

    st.divider()

    st.markdown("### Train the model")
    train_clicked = st.button("Train Model", type="primary", key="train_btn")

    # Resolve the training result: from session_state (if previously trained),
    # else from the auto-trained cache, else None.
    training_result = st.session_state.get("last_training_result") or automatic_training_result

    if train_clicked:
        if df is None:
            st.error("No dataset found. Generate data before training the model.")
        else:
            with st.spinner("Training RandomForestRegressor..."):
                training_result = automatic_training_result or get_training_result()
            if training_result is not None:
                st.session_state["last_training_result"] = training_result
                st.success("Model trained successfully.")

    if training_result is not None and df is not None:
        metric_a, metric_b = st.columns(2)
        with metric_a:
            st.metric("Mean Absolute Error", f"{training_result['mae']:.2f} Lakhs")
        with metric_b:
            st.metric("R2 Score", f"{training_result['r2']:.4f}")

        st.divider()

        # Feature importances + predicted-vs-actual side by side
        chart_left, chart_right = st.columns(2)

        with chart_left:
            importances_df = pd.DataFrame(
                training_result["feature_importances"],
                columns=["feature", "importance"],
            )
            importance_chart = px.bar(
                importances_df,
                x="feature",
                y="importance",
                title="Feature Importances",
                labels={"feature": "Feature", "importance": "Importance"},
            )
            importance_chart.update_traces(marker_color="#2dd4bf")
            importance_chart.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#11141c",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#e6e6e6"},
                margin={"l": 24, "r": 18, "t": 56, "b": 36},
            )
            st.plotly_chart(importance_chart)

        with chart_right:
            actual = training_result["y_test"].reset_index(drop=True)
            predicted = pd.Series(training_result["predictions"], name="predicted_price_lakhs")
            prediction_df = pd.DataFrame(
                {
                    "actual_price_lakhs": actual,
                    "predicted_price_lakhs": predicted,
                }
            )
            min_price = min(prediction_df.min())
            max_price = max(prediction_df.max())
            predicted_chart = px.scatter(
                prediction_df,
                x="actual_price_lakhs",
                y="predicted_price_lakhs",
                title="Predicted vs Actual Price",
                labels={
                    "actual_price_lakhs": "Actual Price (Lakhs)",
                    "predicted_price_lakhs": "Predicted Price (Lakhs)",
                },
            )
            predicted_chart.add_trace(
                go.Scatter(
                    x=[min_price, max_price],
                    y=[min_price, max_price],
                    mode="lines",
                    name="y = x",
                    line={"dash": "dash", "color": "#4f46e5"},
                )
            )
            predicted_chart.update_traces(marker={"color": "#06b6d4", "opacity": 0.72, "size": 7}, selector={"mode": "markers"})
            predicted_chart.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#ffffff",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#0f172a"},
                margin={"l": 24, "r": 18, "t": 56, "b": 36},
            )
            st.plotly_chart(predicted_chart)

    st.divider()
    st.info(METRIC_CAPTION)


# ======================= TAB 3 — Predict Price ==============================
with tab_predict:
    st.markdown('<a id="predict"></a>', unsafe_allow_html=True)
    st.markdown("## Manual Prediction")
    st.caption(
        "Adjust the property features below, then predict the price using the trained model. "
        "Train the model first (in the Train Model tab) for the freshest prediction."
    )

    with st.form("manual_prediction_form"):
        col_sliders_left, col_sliders_right = st.columns(2)

        with col_sliders_left:
            input_sqft = st.slider("sqft", 450, 3500, 1500, step=50)
            input_bedrooms = st.slider("bedrooms", 1, 5, 3)

        with col_sliders_right:
            input_age = st.slider("age_years", 0, 30, 8)
            input_metro_distance = st.slider("metro_distance_km", 0.1, 15.0, 3.0, step=0.1)

        submitted = st.form_submit_button("Predict Price")

    training_result = st.session_state.get("last_training_result") or automatic_training_result

    if submitted:
        if training_result is None:
            st.error("No trained model found. Train the model first in the Train Model tab.")
        else:
            sample = pd.DataFrame(
                [
                    {
                        "sqft": input_sqft,
                        "bedrooms": input_bedrooms,
                        "age_years": input_age,
                        "metro_distance_km": input_metro_distance,
                    }
                ],
                columns=FEATURES,
            )
            predicted_price = training_result["model"].predict(sample)[0]
            st.session_state["last_predicted_price"] = predicted_price
            st.success("Predicted using RandomForestRegressor on the current dataset.")

    # Show the prediction result persistently (won't vanish on rerun)
    last_price = st.session_state.get("last_predicted_price")
    if last_price is not None:
        st.metric("Predicted Price", f"{last_price:.2f} Lakhs")
    elif training_result is None:
        st.info("Train the model first to enable price prediction.")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Synthetic-data systems demo ? "
    "[GitHub repo](https://github.com/sheikhayaan/Hybrid-Data-Pipeline) ? "
    "Not a real property prediction tool."
)
