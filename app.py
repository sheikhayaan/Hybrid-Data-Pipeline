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
    page_title="Gurgaon Housing Pipeline Demo",
    layout="wide",
)


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


st.title("Hybrid Data Pipeline: Gurgaon Housing Price Predictor")
st.caption(
    "A synthetic data pipeline demo showing C++ generation -> Python ML, not a real property prediction tool."
)

st.subheader("Data Generation")
row_count = st.number_input("Rows to generate", min_value=100, max_value=10000, value=1000, step=100)

if st.button("Generate Data", type="primary"):
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
        st.success(f"Generated {row_count_int} rows at {DATA_FILE}")
        if result.stdout:
            st.code(result.stdout, language="text")
    except FileNotFoundError as exc:
        output_path = generate_data(row_count_int, DATA_FILE)
        st.session_state["last_generated_rows"] = row_count_int
        st.session_state["last_generation_mtime"] = DATA_FILE.stat().st_mtime
        cached_training_result.clear()
        st.warning(f"{exc} Used the Python fallback generator instead.")
        st.success(f"Generated {row_count_int} rows at {output_path}")
    except subprocess.CalledProcessError as exc:
        st.error("Compilation or data generation failed.")
        details = "\n".join(part for part in [exc.stdout, exc.stderr] if part)
        if details:
            st.code(details, language="text")

df = load_existing_data()
automatic_training_result = get_training_result() if df is not None else None

st.subheader("Generated Data Preview")
if df is None:
    st.info("Generate data first, or place synthetic_housing_data.csv in the project folder.")
else:
    expected_rows = st.session_state.get("last_generated_rows")
    actual_rows = len(df)

    st.caption(f"**Rows in CSV: {actual_rows}**")

    if expected_rows and actual_rows != expected_rows:
        st.error(
            f"Row count mismatch! Expected {expected_rows} rows from generation, "
            f"but the CSV file contains {actual_rows} rows. "
            "The file may be stale or was overwritten by another process."
        )

    st.caption(f"Showing first 20 of {actual_rows} total rows")
    show_all = st.checkbox("Show all rows")
    st.dataframe(df if show_all else df.head(20), width="stretch")

    col_download, _ = st.columns([1, 3])
    col_download.download_button(
        label="Download full CSV",
        data=df.to_csv(index=False),
        file_name="synthetic_housing_data.csv",
        mime="text/csv",
    )

    st.write("Summary statistics")
    st.dataframe(df.describe(), width="stretch")

    histogram = px.histogram(
        df,
        x="price_lakhs",
        nbins=40,
        title="Price Distribution",
        labels={"price_lakhs": "Price (Lakhs)"},
    )
    st.plotly_chart(histogram)

    sqft_scatter = px.scatter(
        df,
        x="sqft",
        y="price_lakhs",
        color="bedrooms",
        title="Sqft vs Price",
        labels={"sqft": "Sqft", "price_lakhs": "Price (Lakhs)", "bedrooms": "Bedrooms"},
    )
    st.plotly_chart(sqft_scatter)

    metro_scatter = px.scatter(
        df,
        x="metro_distance_km",
        y="price_lakhs",
        title="Metro Distance vs Price",
        labels={"metro_distance_km": "Metro Distance (km)", "price_lakhs": "Price (Lakhs)"},
    )
    st.plotly_chart(metro_scatter)

st.subheader("Model Training")
if st.button("Train Model"):
    if df is None:
        st.error("No dataset found. Generate data before training the model.")
    else:
        with st.spinner("Training RandomForestRegressor..."):
            training_result = automatic_training_result or get_training_result()

        if training_result is not None:
            metric_a, metric_b = st.columns(2)
            metric_a.metric("Mean Absolute Error", f"{training_result['mae']:.2f} Lakhs")
            metric_b.metric("R2 Score", f"{training_result['r2']:.4f}")

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

st.info(METRIC_CAPTION)

st.subheader("Manual Prediction")
with st.form("manual_prediction_form"):
    input_sqft = st.slider("sqft", 450, 3500, 1500, step=50)
    input_bedrooms = st.slider("bedrooms", 1, 5, 3)
    input_age = st.slider("age_years", 0, 30, 8)
    input_metro_distance = st.slider("metro_distance_km", 0.1, 15.0, 3.0, step=0.1)
    submitted = st.form_submit_button("Predict Price")

if submitted:
    training_result = automatic_training_result or get_training_result()
    if training_result is None:
        st.error("No dataset found. Generate data before making predictions.")
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
        st.metric("Predicted Price", f"{predicted_price:.2f} Lakhs")
