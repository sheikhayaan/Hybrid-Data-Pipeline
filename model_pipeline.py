from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


DATA_PATH = Path("synthetic_housing_data.csv")
FEATURES = ["sqft", "bedrooms", "age_years", "metro_distance_km"]
TARGET = "price_lakhs"


def load_and_clean_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    starting_rows = len(data)

    data = data.dropna()
    data = data[(data["sqft"] > 0) & (data["price_lakhs"] > 0)]

    dropped_rows = starting_rows - len(data)
    print(f"Loaded {starting_rows} rows from {path}")
    print(f"Dropped {dropped_rows} rows during cleaning")

    return data


def train_and_evaluate(data: pd.DataFrame, verbose: bool = True) -> dict:
    x = data[FEATURES]
    y = data[TARGET]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    importances = sorted(
        zip(FEATURES, model.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    )

    if verbose:
        print("Model: RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)")
        print(f"Mean Absolute Error: {mae:.2f} Lakhs")
        print(f"R2 Score: {r2:.4f}")
        print("Feature importances:")

        for feature, importance in importances:
            print(f"  {feature}: {importance:.4f}")

        print()
        print(
            "Reminder: these metrics reflect fit quality on synthetic, formula-generated "
            "data. They demonstrate a working ingestion -> training -> evaluation "
            "pipeline, not real-world predictive accuracy. See README.md for scope."
        )

    return {
        "model": model,
        "mae": mae,
        "r2": r2,
        "feature_importances": importances,
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
        "predictions": predictions,
    }


def main() -> None:
    try:
        data = load_and_clean_data(DATA_PATH)
    except FileNotFoundError:
        print(
            "synthetic_housing_data.csv was not found. Compile and run data_engine "
            "first to generate the dataset."
        )
        return

    train_and_evaluate(data)


if __name__ == "__main__":
    main()
