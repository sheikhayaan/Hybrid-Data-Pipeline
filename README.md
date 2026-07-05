---
title: Hybrid Data Pipeline - Gurgaon Housing Price Predictor
emoji: 🏠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Hybrid Data Pipeline: Gurgaon Housing Price Predictor

[![Build Check](https://github.com/sheikhayaan/Hybrid-Data-Pipeline/actions/workflows/build-check.yml/badge.svg)](https://github.com/sheikhayaan/Hybrid-Data-Pipeline/actions/workflows/build-check.yml)

## What this project actually demonstrates

This is a cross-language systems integration project. A C++ data engine models and generates synthetic Gurgaon housing records, writes them to a CSV file boundary, and hands that file to a Python analytics layer built with Pandas and Scikit-Learn.

The headline is the pipeline shape: C++ file I/O, reproducible RNG, and simple struct-based data modeling feeding a Python ingestion, cleaning, training, and evaluation workflow.

## Architecture diagram

```text
+------------------+        +-----------------------------+        +---------------------------+
| data_engine.cpp  | -----> | synthetic_housing_data.csv  | -----> | model_pipeline.py         |
| C++ RNG/modeling |        | CSV file boundary           |        | Pandas + Scikit-Learn ML  |
+------------------+        +-----------------------------+        +---------------------------+
```

## Tech stack

- C++17-compatible standard library
- g++
- Python 3
- Pandas
- Scikit-Learn
- Streamlit
- Plotly
- Docker

## Running it

Compile and run the C++ generator:

```bash
g++ -O2 data_engine.cpp -o data_engine
./data_engine
```

Run the Python model pipeline:

```bash
python model_pipeline.py
```

## Running the frontend

Install the frontend dependencies:

```bash
pip install -r requirements.txt
```

Start the Streamlit app:

```bash
streamlit run app.py
```

Docker option:

```bash
docker compose up --build
```

## Results from this run

The full pipeline was run end to end. Console output:

```text
Generated 1000 rows in synthetic_housing_data.csv
Note: prices intentionally include non-linear age depreciation, diminishing metro-proximity effects, a sqft/metro interaction, Gaussian noise, and injected outliers.
This dataset is for systems integration and pipeline demonstration, not real-world valuation accuracy.

Loaded 1000 rows from synthetic_housing_data.csv
Dropped 0 rows during cleaning
Model: RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
Mean Absolute Error: 32.01 Lakhs
R2 Score: 0.7704
Feature importances:
  sqft: 0.8203
  metro_distance_km: 0.0789
  age_years: 0.0742
  bedrooms: 0.0267

Reminder: these metrics reflect fit quality on synthetic, formula-generated data. They demonstrate a working ingestion -> training -> evaluation pipeline, not real-world predictive accuracy. See README.md for scope.
```

## Why the accuracy numbers are not the headline

The data is synthetic and formula-generated. A model trained on data produced by a known formula partially learns the behavior of that formula, so the reported metrics should not be read as real Gurgaon price prediction accuracy.

The generator deliberately avoids a clean linear target by including:

- Non-linear age depreciation using exponential decay
- Diminishing returns for metro proximity
- An interaction term between sqft and metro proximity
- Additive Gaussian noise
- Extra random shocks on a small percentage of rows to simulate outliers or data entry noise

Measured on this run:

- Mean Absolute Error: 32.01 Lakhs
- R2 Score: 0.7704

These numbers are useful as a sanity check that ingestion, cleaning, model fitting, and evaluation all work. They are not evidence of real-world valuation performance.

## Honest limitations / what I'd do next

- Swap in real housing transaction or listing data
- Add categorical features such as locality, floor, furnishing status, builder, and property type
- Move generator constants and model parameters into config files instead of hardcoding them
- Add unit tests around data generation bounds, cleaning rules, and pipeline behavior

## Deployment on Hugging Face Spaces

This project ships as a Docker image and is configured to deploy to
[Hugging Face Spaces](https://huggingface.co/spaces) using the Docker SDK.
The app listens on port 7860 (the HF Spaces default) via the Dockerfile `CMD`.

### One-time setup (manual, on huggingface.co)

1. Create a new Space at **https://huggingface.co/new-space**
   - **Space name:** `hybrid-data-pipeline` (or similar)
   - **SDK:** Docker
   - **Hardware:** CPU basic (free)
2. Hugging Face will create a new, empty git repo for the Space at
   `https://huggingface.co/spaces/<your-hf-username>/hybrid-data-pipeline`.

### Push this code to the Space

Hugging Face Spaces are their own git repos, separate from GitHub, but they
can be kept in sync. From the root of this project:

```bash
# Add the Space as a second remote (replace <your-hf-username>)
git remote add space https://huggingface.co/spaces/<your-hf-username>/hybrid-data-pipeline

# Push the main branch to the Space remote
git push space main
```

The Space will automatically build the `Dockerfile` and deploy. Build logs are
visible in the Space's **Logs** tab on huggingface.co.

### Notes

- `git push origin main` still pushes to GitHub; `git push space main` pushes
  to the HF Space. Run both to keep them in sync.
- The first push will prompt for your HF credentials. Use your HF username and
  a [access token with write permission](https://huggingface.co/settings/tokens)
  as the password.
- If you change the `app_port` in the README frontmatter, update the port in
  the Dockerfile `CMD` and `EXPOSE` to match.
