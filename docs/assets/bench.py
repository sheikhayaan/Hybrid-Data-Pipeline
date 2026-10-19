"""Measure the real pipeline and write docs/assets/bench_result.json.

Every number in README.md that is not a line count comes from this file.
Run:  py docs/assets/bench.py --runs 12
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent
ENGINE = ROOT / ("data_engine.exe" if sys.platform == "win32" else "data_engine")
CSV = ROOT / "synthetic_housing_data.csv"
ROWS = 1000


def timed(fn):
    """Return (result, elapsed_ms) for a zero-argument callable."""
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000.0


def run_engine() -> None:
    """Regenerate the CSV from the compiled C++ engine."""
    subprocess.run([str(ENGINE), str(ROWS)], check=True, stdout=subprocess.DEVNULL)


def run_python_fallback() -> None:
    """Regenerate the CSV from the Python fallback generator."""
    subprocess.run(
        [sys.executable, str(ROOT / "data_gen_fallback.py"), str(ROWS)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def compile_engine() -> tuple[Path, float]:
    """Compile data_engine.cpp with g++ -O2 and return (binary, ms)."""
    out = ASSETS / "_engine_probe"
    start = time.perf_counter()
    subprocess.run(
        ["g++", "-O2", str(ROOT / "data_engine.cpp"), "-o", str(out)],
        check=True,
        capture_output=True,
    )
    elapsed = (time.perf_counter() - start) * 1000.0
    return out, elapsed


def load_and_clean():
    """Import the model module lazily and time load + clean."""
    sys.path.insert(0, str(ROOT))
    import model_pipeline

    return model_pipeline.load_and_clean_data(CSV)


def train():
    """Train and evaluate the RandomForest on the current CSV."""
    sys.path.insert(0, str(ROOT))
    import model_pipeline

    data = model_pipeline.load_and_clean_data(CSV)
    return model_pipeline.train_and_evaluate(data, verbose=False)


def main() -> None:
    """Collect 12 representative samples per stage and persist them as JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=12)
    args = parser.parse_args()

    if not ENGINE.exists():
        raise SystemExit(f"Missing {ENGINE.name}. Compile data_engine.cpp first.")

    sys.path.insert(0, str(ROOT))
    import model_pipeline
    import pandas as pd
    import sklearn

    probe, compile_ms = compile_engine()
    # First spawn of a freshly written binary is the realistic cold path.
    cold_ms = timed(lambda: subprocess.run([str(probe), str(ROWS)], check=True,
                                          stdout=subprocess.DEVNULL))[1]
    Path(str(probe) + ".exe").unlink(missing_ok=True)
    probe.unlink(missing_ok=True)

    samples = {"engine": [], "fallback": [], "load_clean": [], "train": []}
    for _ in range(args.runs):
        _, ms = timed(run_engine)
        samples["engine"].append(ms)

        _, ms = timed(run_python_fallback)
        samples["fallback"].append(ms)

        _, ms = timed(load_and_clean)
        samples["load_clean"].append(ms)

        _, ms = timed(train)
        samples["train"].append(ms)

    # Restore the canonical C++-generated file as the committed artifact.
    run_engine()

    result = train()
    data = model_pipeline.load_and_clean_data(CSV)

    summary = {}
    for stage, values in samples.items():
        summary[stage] = {
            "runs": len(values),
            "min_ms": round(min(values), 2),
            "median_ms": round(statistics.median(values), 2),
            "max_ms": round(max(values), 2),
            "mean_ms": round(statistics.fmean(values), 2),
        }

    payload = {
        "generated_by": "docs/assets/bench.py",
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "rows": ROWS,
        },
        "compile": {
            "command": "g++ -O2 data_engine.cpp",
            "ms": round(compile_ms, 2),
            "cold_first_spawn_ms": round(cold_ms, 2),
        },
        "stages": summary,
        "samples": {k: [round(v, 2) for v in vals] for k, vals in samples.items()},
        "model": {
            "estimator": "RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)",
            "rows_loaded": int(len(data)),
            "rows_dropped": int(ROWS - len(data)),
            "mae_lakhs": round(float(result["mae"]), 2),
            "r2": round(float(result["r2"]), 4),
            "feature_importances": {k: round(float(v), 4) for k, v in result["feature_importances"]},
        },
    }

    out = ASSETS / "bench_result.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("stages", "model", "compile")}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
