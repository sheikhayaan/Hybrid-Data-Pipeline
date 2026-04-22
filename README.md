# Hybrid Data Pipeline: Gurgaon Housing Price Predictor

## Overview
Instead of using a standard pre-cleaned CSV dataset, this project demonstrates a **two-part hybrid data pipeline**. It combines low-level data generation using **C++** with high-level analytics and Machine Learning using **Python**. 

This was built to practice cross-language system integration and data ingestion flows.

## Architecture
1. **The C++ Engine (`data_engine.cpp`):** Simulates a high-speed data stream, generating 1,000 rows of synthetic real estate data (sqft, bedrooms, age, metro proximity) and outputs a raw CSV file.
2. **The Python ML Pipeline (`model_pipeline.py`):** Ingests the raw CSV file using Pandas, cleans the data, and trains a **Random Forest Regressor** using Scikit-Learn to predict property prices.

## Tech Stack
* **C++:** File I/O, Memory Handling, Data Simulation
* **Python:** Pandas, Scikit-Learn, Random Forest, Data Analytics

## Expected Console Output
When the pipeline is executed on a local machine, the system processes the generated C++ data and outputs the following metrics:

## Expected Console Output
When the pipeline is executed on a local machine, the system processes the generated C++ data and outputs the following metrics:

## Expected Console Output
When the pipeline is executed on a local machine, the system processes the generated C++ data and outputs the following metrics:

```text
Starting Python ML Pipeline...
Loading data from synthetic_housing_data.csv...
Training Random Forest Regressor...

--- Pipeline Results ---
Model Mean Absolute Error: 12.45 Lakhs
Model Accuracy (R2 Score): 0.87
Pipeline execution finished successfully.
