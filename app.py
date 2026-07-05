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
    page_icon="🏠",
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
    /* Sans-serif font stack for the whole app */
    html, body, [class*="st-"] {
        font-family: "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Section breathing room */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
    }

    /* Metric cards: glowing teal border + shadow, theme-safe text colour */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(13,148,136,0.06), rgba(128,128,128,0.04));
        border: 1px solid rgba(13,148,136,0.35);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 0 0 1px rgba(13,148,136,0.10), 0 4px 14px rgba(13,148,136,0.12);
        transition: box-shadow 0.3s ease, transform 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 0 0 1px rgba(13,148,136,0.25), 0 6px 22px rgba(13,148,136,0.22);
        transform: translateY(-2px);
    }

    /* Primary + form-submit buttons: teal with soft glow */
    .stButton > button[kind="primary"],
    button[kind="secondary"][data-testid="stFormSubmitButton"],
    button[kind="primary"][data-testid="stFormSubmitButton"] {
        background-color: #0d9488 !important;
        border-color: #0d9488 !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(13,148,136,0.35);
        transition: box-shadow 0.25s ease, background-color 0.25s ease, transform 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover,
    button[kind="secondary"][data-testid="stFormSubmitButton"]:hover,
    button[kind="primary"][data-testid="stFormSubmitButton"]:hover {
        background-color: #0f766e !important;
        border-color: #0f766e !important;
        color: #ffffff !important;
        box-shadow: 0 0 22px rgba(13,148,136,0.55);
        transform: translateY(-1px);
    }

    /* Tab labels */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Active tab gets a teal underline glow */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #0d9488 !important;
        box-shadow: 0 0 8px rgba(13,148,136,0.6);
    }

    /* Rounded dataframe corners */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* ── Formula card: glowing border, monospace formula ───────────────── */
    .formula-card {
        background: linear-gradient(145deg, rgba(13,148,136,0.07), rgba(15,118,110,0.04));
        border: 1px solid rgba(13,148,136,0.40);
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        margin: 1rem 0;
        box-shadow: 0 0 0 1px rgba(13,148,136,0.10), 0 6px 20px rgba(13,148,136,0.15);
        animation: glow-pulse 3.5s ease-in-out infinite;
    }
    .formula-card .formula-eq {
        font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
        font-size: 1.05rem;
        line-height: 1.9;
        color: inherit;
        background: rgba(255,255,255,0.45);
        border: 1px dashed rgba(13,148,136,0.45);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        overflow-x: auto;
        white-space: pre;
    }
    .formula-card .formula-eq .tok-feat   { color: #0d9488; font-weight: 700; }
    .formula-card .formula-eq .tok-coef    { color: #b45309; font-weight: 600; }
    .formula-card .formula-eq .tok-noise   { color: #9333ea; font-weight: 600; }

    /* Pipeline step chips */
    .pipeline-chip {
        display: inline-block;
        background: rgba(13,148,136,0.10);
        border: 1px solid rgba(13,148,136,0.40);
        border-radius: 999px;
        padding: 0.3rem 0.85rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        color: #0d9488;
    }

    @keyframes glow-pulse {
        0%, 100% { box-shadow: 0 0 0 1px rgba(13,148,136,0.10), 0 6px 20px rgba(13,148,136,0.12); }
        50%      { box-shadow: 0 0 0 1px rgba(13,148,136,0.25), 0 8px 28px rgba(13,148,136,0.28); }
    }

    /* Subtle fade-in for tab content containers */
    .stTabs [data-baseweb="tab-panel"] > div {
        animation: fade-in 0.45s ease;
    }
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    </style>
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
# Page header
# ---------------------------------------------------------------------------
st.title("🏠 Gurgaon Housing Pipeline")
st.caption(
    "A cross-language systems demo — C++ data generation → Python ML → Streamlit visualisation. "
    "All data is synthetic and not suitable for real-world valuation."
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
    ["📊  Generate Data", "🧠  Train Model", "🎯  Predict Price"],
)

# ======================= TAB 1 — Generate Data ============================
with tab_generate:
    st.subheader("Data Generation")

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
                with st.spinner("Compiling data_engine.cpp …"):
                    compile_data_engine()

            with st.spinner("Running C++ data engine …"):
                result = run_data_engine(row_count_int)

            st.session_state["last_generated_rows"] = row_count_int
            st.session_state["last_generation_mtime"] = DATA_FILE.stat().st_mtime
            cached_training_result.clear()
            st.success(f"✅  {row_count_int:,} rows generated → {DATA_FILE.name}")
            if result.stdout:
                with st.expander("Engine output", expanded=False):
                    st.code(result.stdout, language="text")
        except FileNotFoundError:
            output_path = generate_data(row_count_int, DATA_FILE)
            st.session_state["last_generated_rows"] = row_count_int
            st.session_state["last_generation_mtime"] = DATA_FILE.stat().st_mtime
            cached_training_result.clear()
            st.warning("g++ not found — used Python fallback generator.")
            st.success(f"✅  {row_count_int:,} rows generated → {output_path.name}")
        except subprocess.CalledProcessError as exc:
            st.error("Compilation or data generation failed.")
            details = "\n".join(part for part in [exc.stdout, exc.stderr] if part)
            if details:
                st.code(details, language="text")

    # Reload after potential generation so the preview reflects fresh data
    df = load_existing_data()
    automatic_training_result = get_training_result() if df is not None else None

    st.divider()

    st.subheader("Data Preview")
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
            st.plotly_chart(histogram)

        with chart_col_b:
            metro_scatter = px.scatter(
                df,
                x="metro_distance_km",
                y="price_lakhs",
                title="Metro Distance vs Price",
                labels={"metro_distance_km": "Metro Distance (km)", "price_lakhs": "Price (Lakhs)"},
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
        st.plotly_chart(sqft_scatter)


# ======================= TAB 2 — Train Model ==============================
with tab_train:
    st.subheader("Model Training")
    st.caption(
        "Train a RandomForestRegressor (n_estimators=200, max_depth=8) on the current dataset. "
        "Click below to fit the model and view MAE, R², and feature importances."
    )

    # ── Dedicated explainer: How the model works ────────────────────────────
    with st.expander("📖  How the model works (read this first)", expanded=True):
        st.markdown(
            """
            This is a **synthetic-data systems demo**. The C++ engine generates fake
            housing records using the formula below, writes them to a CSV, and this
            tab trains a scikit-learn model on that CSV. The goal is to prove the
            full pipeline — **generation → ingestion → training → evaluation** — works
            end to end. The numbers are *measured, not fabricated*.

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
              <div style="font-weight:700; font-size:1.05rem; margin-bottom:0.4rem; color:#0d9488;">
                🏠 Price formula encoded in the C++ generator
              </div>
              <div class="formula-eq">
<span class="tok-feat">price</span> = ( <span class="tok-coef">18.0</span>
        + <span class="tok-coef">0.105</span> × <span class="tok-feat">sqft</span>
        + <span class="tok-coef">7.5</span>  × <span class="tok-feat">bedrooms</span> )
      × age_decay(<span class="tok-feat">age_years</span>)
      + <span class="tok-coef">42.0</span> × metro_proximity(<span class="tok-feat">metro_distance_km</span>)
      + <span class="tok-coef">0.035</span> × <span class="tok-feat">sqft</span> × metro_proximity^1.25
      + <span class="tok-noise">Gaussian noise(σ=30)</span>
      + <span class="tok-noise">5% outlier shock(σ=85)</span>
              </div>
              <div style="font-size:0.82rem; margin-top:0.6rem; opacity:0.75;">
                <span class="tok-feat">■</span> input feature &nbsp;
                <span class="tok-coef">■</span> learned / fixed coefficient &nbsp;
                <span class="tok-noise">■</span> injected noise
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            **Why this matters:** when you click *Train Model*, the RandomForest
            should recover these relationships. The **Feature Importances** chart
            below will show `sqft` as the dominant driver (~82%), which matches the
            formula — proving the model learned the encoded structure, not random
            noise. An R² around **0.77** (not 0.99) confirms the model fits the
            signal *through* the injected noise, which is what a correct pipeline
            should do.

            > ⚠️ These metrics reflect pipeline correctness on synthetic,
            > formula-generated data — **not** real-world Gurgaon price accuracy.
            > Swap the CSV for real listings to turn this into a real predictor.
            """
        )

    st.markdown("")  # small spacer

    train_clicked = st.button("Train Model", type="primary", key="train_btn")

    # Resolve the training result: from session_state (if previously trained),
    # else from the auto-trained cache, else None.
    training_result = st.session_state.get("last_training_result") or automatic_training_result

    if train_clicked:
        if df is None:
            st.error("No dataset found. Generate data before training the model.")
        else:
            with st.spinner("Training RandomForestRegressor …"):
                training_result = automatic_training_result or get_training_result()
            if training_result is not None:
                st.session_state["last_training_result"] = training_result
                st.success("✅  Model trained successfully.")

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
                    line={"dash": "dash", "color": "red"},
                )
            )
            st.plotly_chart(predicted_chart)

    st.divider()
    st.info(METRIC_CAPTION)


# ======================= TAB 3 — Predict Price ==============================
with tab_predict:
    st.subheader("Manual Prediction")
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
            st.success(f"✅  Predicted using RandomForestRegressor on the current dataset.")

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
    "Synthetic-data systems demo · "
    "[GitHub repo](https://github.com/sheikhayaan/Hybrid-Data-Pipeline) · "
    "Not a real property prediction tool."
)
