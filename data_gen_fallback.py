from __future__ import annotations

import csv
import math
import random
from pathlib import Path


OUTPUT_PATH = Path("synthetic_housing_data.csv")


def compute_price_lakhs(
    sqft: int,
    bedrooms: int,
    age_years: int,
    metro_distance_km: float,
    rng: random.Random,
) -> float:
    base_price = 18.0
    sqft_component = 0.105 * sqft
    bedroom_component = 7.5 * bedrooms

    age_multiplier = 0.72 + 0.28 * math.exp(-age_years / 9.0)
    metro_proximity = 1.0 / (1.0 + metro_distance_km)
    metro_component = 42.0 * metro_proximity
    sqft_metro_interaction = 0.035 * sqft * (metro_proximity**1.25)

    price = (
        (base_price + sqft_component + bedroom_component) * age_multiplier
        + metro_component
        + sqft_metro_interaction
    )
    price += rng.gauss(0.0, 30.0)

    if rng.random() < 0.055:
        price += rng.gauss(0.0, 85.0)

    return max(18.0, price)


def generate_data(row_count: int = 1000, output_path: Path = OUTPUT_PATH) -> Path:
    rng = random.Random(42)

    with output_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["sqft", "bedrooms", "age_years", "metro_distance_km", "price_lakhs"])

        for _ in range(row_count):
            sqft = rng.randint(450, 3500)
            bedrooms = rng.randint(1, 5)
            age_years = rng.randint(0, 30)
            metro_distance_km = rng.uniform(0.1, 15.0)
            price_lakhs = compute_price_lakhs(sqft, bedrooms, age_years, metro_distance_km, rng)

            writer.writerow(
                [
                    sqft,
                    bedrooms,
                    age_years,
                    f"{metro_distance_km:.2f}",
                    f"{price_lakhs:.2f}",
                ]
            )

    return output_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate fallback synthetic housing data in Python.")
    parser.add_argument("rows", nargs="?", type=int, default=1000)
    args = parser.parse_args()

    if args.rows <= 0:
        raise SystemExit("Row count must be positive.")

    output_path = generate_data(args.rows)
    print(f"Generated {args.rows} rows in {output_path}")
    print(
        "Note: this Python fallback mirrors the synthetic non-linear/noisy data shape "
        "for deployment environments where g++ is unavailable."
    )


if __name__ == "__main__":
    main()
