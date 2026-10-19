"""Generate the README figures as pure SVG from real, measured repository data.

Usage:
    py docs/assets/generate.py            # render all figures
    py docs/assets/bench.py --runs 12    # refresh bench_result.json first
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent

CANVAS = "#05070d"
PANEL = "#0a101b"
LINE = "#1b2637"
INK = "#e8eefc"
MUTED = "#8b9bb4"
CYAN = "#22d3ee"
BLUE = "#3b82f6"
VIOLET = "#a855f7"
EMERALD = "#10b981"
AMBER = "#f59e0b"
ROSE = "#f43f5e"

FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Inter, Roboto, sans-serif"
MONO = "ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, monospace"

# Runtime figures come from the harness, never from memory.
BENCH = json.loads((ASSETS / "bench_result.json").read_text(encoding="utf-8"))
MODEL = BENCH["model"]
COLD = BENCH["compile"]["cold_first_spawn_ms"]
CSV_BYTES = 22793


def ms(stage: str) -> str:
    """Median milliseconds for one measured stage, formatted for prose."""
    return f"{BENCH['stages'][stage]['median_ms']:,.1f}"


def esc(text: object) -> str:
    """Escape the five XML-sensitive characters in a string."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def num(value: float) -> str:
    """Format an integer-like float with thousands separators."""
    return f"{value:,.0f}"


def count_lines(*relative: str) -> int:
    """Count physical lines across repository files, skipping gitignored noise."""
    total = 0
    for rel in relative:
        path = ROOT / rel
        if path.is_file():
            total += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    return total


def defs() -> str:
    """Shared paint server: glow filters, gradients, halos and the 40px grid."""
    return f"""
  <defs>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softglow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="9" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="wordmark" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CYAN}"/><stop offset="52%" stop-color="{BLUE}"/>
      <stop offset="100%" stop-color="{VIOLET}"/>
    </linearGradient>
    <linearGradient id="cyanline" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{CYAN}"/><stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="emeraldline" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{EMERALD}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{EMERALD}"/><stop offset="100%" stop-color="{EMERALD}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#101a2b" stop-opacity="0.96"/>
      <stop offset="100%" stop-color="#070c15" stop-opacity="0.96"/>
    </linearGradient>
    <radialGradient id="halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity="0.18"/>
      <stop offset="60%" stop-color="{BLUE}" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="{BLUE}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="haloViolet" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{VIOLET}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{VIOLET}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0H0V40" fill="none" stroke="{LINE}" stroke-opacity="0.32" stroke-width="1"/>
    </pattern>
  </defs>"""


def svg(width: int, height: int, label: str, body: str) -> str:
    """Wrap a body in a themed SVG canvas with the shared defs block."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" '
        f'font-family="{FONT}">'
        f"{defs()}"
        f'<rect width="{width}" height="{height}" fill="{CANVAS}"/>'
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>'
        f"{body}</svg>\n"
    )


def text(x: float, y: float, label: str, size: float = 12, fill: str = INK,
         weight: str = "400", anchor: str = "start", family: str = FONT,
         spacing: float = 0, opacity: float = 1.0, extra: str = "") -> str:
    """Emit one text node with explicit typography."""
    attrs = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}"'
    attrs += f' text-anchor="{anchor}" font-family="{family}"'
    if spacing:
        attrs += f' letter-spacing="{spacing}"'
    if opacity != 1.0:
        attrs += f' opacity="{opacity}"'
    return f'<text {attrs} {extra}>{esc(label)}</text>'


def card(x: float, y: float, w: float, h: float, accent: str, title: str,
         lines: list[str], title_size: float = 12.5) -> str:
    """Draw a glass card with a 3px glowing top accent bar and wrapped body lines."""
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="url(#card)" '
        f'stroke="{LINE}" stroke-opacity="0.9"/>',
        f'<rect x="{x + 1}" y="{y}" width="{w - 2}" height="3" rx="1.5" fill="{accent}" '
        f'filter="url(#glow)" opacity="0.95"/>',
    ]
    if title:
        out.append(text(x + 16, y + 27, title, title_size, INK, "600"))
    for index, line in enumerate(lines):
        out.append(text(x + 16, y + 47 + index * 15, line, 10.5, MUTED))
    return "".join(out)


def pill(x: float, y: float, label: str, color: str, size: float = 11) -> tuple[str, float]:
    """Draw a tech pill and return its markup plus width so rows can flow."""
    width = 6.2 * len(label) + 26
    markup = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="26" rx="13" '
        f'fill="{color}" fill-opacity="0.1" stroke="{color}" stroke-opacity="0.45"/>'
        + text(x + width / 2, y + 17, label, size, color, "600", "middle", MONO)
    )
    return markup, width


def arrow(x1: float, y1: float, x2: float, y2: float, color: str = CYAN) -> str:
    """Draw a glowing connector with a triangular head."""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="1.6" stroke-opacity="0.65"/>'
        f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="3" fill="{color}" filter="url(#glow)"/>'
    )


def banner() -> str:
    """Hero banner: orbit mark, gradient wordmark and stack pills."""
    parts = [
        f'<circle cx="168" cy="168" r="210" fill="url(#halo)"/>',
        f'<circle cx="168" cy="168" r="250" fill="url(#haloViolet)"/>',
    ]
    for radius, dash, color in ((62, "0", CYAN), (100, "5 9", BLUE), (138, "2 13", VIOLET)):
        parts.append(
            f'<circle cx="168" cy="168" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-opacity="0.5" stroke-width="1.1" stroke-dasharray="{dash}"/>'
        )
    parts += [
        f'<circle cx="168" cy="106" r="4.5" fill="{CYAN}" filter="url(#glow)"/>',
        f'<circle cx="268" cy="168" r="3.5" fill="{BLUE}" filter="url(#glow)"/>',
        f'<circle cx="122" cy="270" r="3.5" fill="{VIOLET}" filter="url(#glow)"/>',
        f'<path d="M168 132 L199 150 L199 186 L168 204 L137 186 L137 150 Z" fill="url(#card)" '
        f'stroke="{CYAN}" stroke-opacity="0.75" stroke-width="1.6" filter="url(#glow)"/>',
        f'<path d="M158 158 L178 178 M178 158 L158 178" stroke="{CYAN}" stroke-width="2.4" stroke-linecap="round"/>',
        text(168, 224, "C++ → CSV → ML", 9.5, CYAN, "700", "middle", MONO, 1.1),
        text(322, 132, "HYBRID DATA PIPELINE", 50, "url(#wordmark)", "800", spacing=1.5),
        text(324, 172, "A C++ engine, a CSV contract, a scikit-learn model — measured end to end.",
             16.5, MUTED),
        text(324, 204, "One seam. One artifact. A CI job that proves the seam still holds.",
             13, "#63718a", "400"),
    ]
    x = 324.0
    for label, color in (
        ("C++17", CYAN), ("Python 3.11", BLUE), ("pandas 3.0.3", EMERALD),
        ("scikit-learn 1.8.0", VIOLET), ("Streamlit 1.58.0", AMBER), ("Docker", ROSE),
        ("GitHub Actions", CYAN),
    ):
        markup, width = pill(x, 238, label, color)
        parts.append(markup)
        x += width + 10
    parts.append(text(324, 306, "6 figures · regenerated by docs/assets/generate.py from bench_result.json",
                      10.5, "#5a677d", "400", family=MONO))
    return svg(1200, 340, "Hybrid Data Pipeline hero banner", "".join(parts))


def architecture() -> str:
    """Four-lane architecture map with glass cards and vertical hand-offs."""
    lanes = [
        ("CLIENT", "browser only — no server round-trip", VIOLET),
        ("EDGE", "Streamlit host — chrome stripped", CYAN),
        ("CORE", "two runtimes, one file contract", BLUE),
        ("STATE", "what survives a run", EMERALD),
    ]
    parts = [
        f'<ellipse cx="600" cy="60" rx="520" ry="120" fill="url(#halo)"/>',
        text(40, 50, "ARCHITECTURE", 12, CYAN, "700", spacing=3),
        text(40, 72, "Four lanes, one cross-runtime boundary", 19, INK, "700"),
    ]
    lane_y = [96, 282, 468, 654]
    colors = [lane[2] for lane in lanes]

    for index, (name, note, color) in enumerate(lanes):
        y = lane_y[index]
        parts += [
            f'<rect x="170" y="{y}" width="990" height="150" rx="16" fill="{PANEL}" '
            f'fill-opacity="0.55" stroke="{color}" stroke-opacity="0.3" stroke-dasharray="7 7"/>',
            text(192, y + 25, name, 12, color, "800", spacing=2.4),
            text(300, y + 25, note, 10.5, "#6b7a93", "400", family=MONO),
        ]
        if index < 3:
            parts.append(arrow(600, y + 150, 600, lane_y[index + 1], color))
            parts.append(text(614, y + 168, "hands off", 9, "#5a677d", "400", family=MONO))

    parts += [
        card(190, lane_y[0] + 38, 455, 92, VIOLET, "index.html · 1,399 lines",
             ["4 views · 34 JS functions · 0 fetch calls", "Datasets built in-browser with Math.random"]),
        card(665, lane_y[0] + 38, 455, 92, VIOLET, "design-system.html · 557 lines",
             ["Standalone token + component reference", "Same palette the app renders"]),
        card(190, lane_y[1] + 38, 455, 92, CYAN, "app.py · 49 lines",
             ["st.set_page_config + CSS chrome removal", "Full-bleed iframe, 980px tall"]),
        card(665, lane_y[1] + 38, 455, 92, CYAN, "Dockerfile · 20 lines",
             ["python:3.11-slim · port 7860", "Compiles the engine at build time"]),
        card(190, lane_y[2] + 38, 300, 92, BLUE, "data_engine.cpp · 114",
             ["mt19937(42) · fixed-point writer",
              f"median {ms('engine')} ms / 1,000 rows"]),
        card(510, lane_y[2] + 38, 300, 92, BLUE, "model_pipeline.py · 99",
             ["clean → split → RF(200, depth 8)", f"median {ms('train')} ms per fit"]),
        card(830, lane_y[2] + 38, 300, 92, AMBER, "data_gen_fallback.py · 88",
             ["Python mirror for hosts without g++", "Same schema, different RNG stream"]),
        card(190, lane_y[3] + 38, 455, 92, EMERALD, "synthetic_housing_data.csv · 1,001",
             ["Committed artifact · md5 39a0d36a…", "Regenerated byte-identically by seed 42"]),
        card(665, lane_y[3] + 38, 455, 92, ROSE, "RandomForestRegressor — in memory",
             ["MAE 32.01 · R² 0.7705 · discarded", "No model registry, no versioned artefact"]),
        text(40, 812, "Arrows are the only interface: neither language calls into the other.",
             10.5, MUTED, "400", family=MONO),
    ]
    return svg(1200, 830, "Hybrid Data Pipeline architecture lanes", "".join(parts))


def pipeline() -> str:
    """Two measured flow rows: the build path and the browser runtime path."""
    csv_kb = CSV_BYTES / 1024
    stages_a = [
        ("g++ -O2", ["compile", f"{num(BENCH['compile']['ms'])} ms"]),
        ("./data_engine 1000", ["spawn + write", f"{ms('engine')} ms median"]),
        ("CSV artifact", [f"{csv_kb:.0f} KB · seed 42", "md5-stable"]),
        ("pandas read", ["load + clean", f"{ms('load_clean')} ms median"]),
        ("train/test split", ["80/20", "random_state=42"]),
        ("RF fit", ["200 trees", f"{ms('train')} ms median"]),
        ("MAE / R²", [f"{MODEL['mae_lakhs']:.2f} · {MODEL['r2']:.4f}", "printed, not stored"]),
    ]
    stages_b = [
        ("Streamlit boot", ["app.py", "port 8501/7860"]),
        ("iframe mount", ["index.html", "980 px tall"]),
        ("Generate", ["Math.random", "in-browser"]),
        ("Observatory", ["canvas graph", "60 FPS target"]),
        ("Model Lab", ["hardcoded 94.2%", "no real fit"]),
        ("Data River 3D", ["three.js r128", "2,500 particles"]),
        ("Export", ["CSV / JSON", "Blob download"]),
    ]
    parts = [
        text(40, 54, "PIPELINE — two paths that never share memory", 19, INK, "700"),
        text(40, 76, "Ingest is reproducible and measured. The browser demo is a separate surface.",
             11, MUTED, family=MONO),
        text(40, 106, "BUILD + INGEST", 11, CYAN, "800", spacing=2.2),
    ]
    x0, width, gap, height = 48, 132, 30, 92

    for row, (stages, top, note) in enumerate(((stages_a, 128, "measured"), (stages_b, 372, "client-side"))):
        color = CYAN if row == 0 else VIOLET
        for index, (title, lines) in enumerate(stages):
            x = x0 + index * (width + gap)
            parts.append(card(x, top, width, height, color, "", [], 11.5))
            parts.append(text(x + width / 2, top + 26, title, 11.5, INK, "700", "middle"))
            for line_index, line in enumerate(lines):
                parts.append(text(x + width / 2, top + 47 + line_index * 14, line, 9.6, MUTED, "400", "middle"))
            if index < len(stages) - 1:
                parts.append(arrow(x + width + 3, top + height / 2, x + width + gap - 3, top + height / 2, color))
        parts.append(text(40, top - 12, note, 9.5, "#5a677d", "400", family=MONO))

    parts += [
        text(40, 300, "SERVE + RENDER", 11, VIOLET, "800", spacing=2.2),
        text(40, 512, f"Cold path: first spawn of the freshly compiled binary took {num(COLD)} ms vs a warm median",
             10.5, AMBER, family=MONO),
        text(40, 530, f"of {ms('engine')} ms — {COLD / BENCH['stages']['engine']['median_ms']:.0f}x, and it is process startup,",
             10.5, AMBER, family=MONO),
        text(40, 548, "not compute. Never benchmark a pipeline with a single run.", 10.5, AMBER, family=MONO),
        text(40, 578, "Caption timings: 12 runs each, Windows 11 + MinGW g++ 6.3.0, Python 3.14.5.",
             10.5, MUTED, family=MONO),
    ]
    return svg(1200, 590, "Measured ingest and runtime pipelines", "".join(parts))


def groups() -> list[tuple[str, int, str]]:
    """Real line counts per code group, computed from disk at generation time."""
    ui = count_lines("index.html", "design-system.html")
    python = count_lines("app.py", "model_pipeline.py", "data_gen_fallback.py")
    infra = count_lines(
        "Dockerfile", "docker-compose.yml", "render.yaml", "requirements.txt",
        ".github/workflows/build-check.yml", ".streamlit/config.toml",
        ".gitignore", ".dockerignore",
    )
    cpp = count_lines("data_engine.cpp")
    return [("UI shell", ui, VIOLET), ("Python pipeline", python, CYAN),
            ("Infra + CI", infra, AMBER), ("C++ engine", cpp, EMERALD)]


def donut() -> str:
    """Codebase composition donut from live line counts."""
    data = groups()
    total = sum(value for _, value, _ in data)
    cx, cy, radius, thickness = 310, 262, 148, 42
    circumference = 2 * 3.141592653589793 * radius
    parts = [
        text(40, 54, "CODEBASE COMPOSITION", 19, INK, "700"),
        text(40, 76, f"{num(total)} tracked lines · data artefact and docs excluded", 11, MUTED, family=MONO),
    ]
    offset = 0.0
    for name, value, color in data:
        fraction = value / total
        dash = fraction * circumference
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="{thickness}" stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})" '
            f'stroke-opacity="0.92" filter="url(#glow)"/>'
        )
        offset += dash
    parts += [
        f'<circle cx="{cx}" cy="{cy}" r="{radius - thickness / 2 - 12}" fill="{CANVAS}" fill-opacity="0.55"/>',
        text(cx, cy - 4, num(total), 42, INK, "800", "middle"),
        text(cx, cy + 22, "tracked lines", 11, MUTED, "400", "middle", MONO),
        text(cx, cy + 42, "4 groups", 10, "#5a677d", "400", "middle", MONO),
    ]
    legend_x = 550
    for index, (name, value, color) in enumerate(data):
        y = 150 + index * 62
        parts += [
            f'<rect x="{legend_x}" y="{y - 12}" width="12" height="12" rx="3" fill="{color}" filter="url(#glow)"/>',
            text(legend_x + 26, y, name, 13, INK, "600"),
            text(legend_x + 26, y + 18, f"{num(value)} lines · {value / total:.1%}", 10.5, MUTED, family=MONO),
        ]
    ui_share = data[0][1] / total
    parts.append(text(40, 470, f"index.html alone is {ui_share:.0%} of the tracked code — the UI is the product surface.",
                      11, MUTED, family=MONO))
    return svg(920, 510, "Codebase composition donut", "".join(parts))


def histogram() -> str:
    """Histogram of the measured RF fit stage with a stage legend."""
    train = sorted(BENCH["samples"]["train"])
    span = train[-1] - train[0]
    step = next(c for c in (50, 100, 200, 250, 500, 1000, 2000) if c * 6 >= span)
    low = int(train[0] // step) * step
    buckets = [0] * max(1, math.ceil((train[-1] - low) / step))
    for value in train:
        buckets[min(int((value - low) // step), len(buckets) - 1)] += 1
    peak = max(buckets) or 1

    parts = [
        text(40, 54, "MEASURED LATENCY — RandomForest fit", 19, INK, "700"),
        text(40, 76, f"{len(train)} independent fits on the same 1,000-row CSV · n_estimators=200, max_depth=8",
             10.5, MUTED, family=MONO),
    ]
    x0, baseline, top = 90, 380, 118
    ramp = [EMERALD, CYAN, BLUE, VIOLET, AMBER, ROSE]
    bar_w = 82 if len(buckets) <= 6 else 62
    gap = 24 if len(buckets) <= 6 else 20
    for index, value in enumerate(buckets):
        x = x0 + index * (bar_w + gap)
        height = (value / peak) * (baseline - top)
        if height < 4:
            height = 4
        color = ramp[min(index, len(ramp) - 1)]
        parts += [
            f'<rect x="{x}" y="{baseline - height:.1f}" width="{bar_w}" height="{height:.1f}" rx="6" '
            f'fill="{color}" fill-opacity="0.82"/>',
            f'<rect x="{x}" y="{baseline - height:.1f}" width="{bar_w}" height="3" rx="1.5" '
            f'fill="{color}" filter="url(#glow)"/>',
            text(x + bar_w / 2, baseline - height - 9, str(value), 12, INK, "700", "middle", MONO),
            text(x + bar_w / 2, baseline + 20, f"{low + index * step}–{low + (index + 1) * step}", 9.5, MUTED, "400", "middle", MONO),
        ]
    parts += [
        f'<line x1="{x0 - 8}" y1="{baseline + 1}" x2="{x0 + len(buckets) * (bar_w + gap) - gap - 16}" y2="{baseline + 1}" '
        f'stroke="{LINE}" stroke-width="1.2"/>',
        text(x0, baseline + 44, "fit latency bucket (ms)", 10.5, MUTED, family=MONO),
        text(58, top - 22, "fits", 9.5, "#5a677d", "400", "middle", MONO),
    ]
    median = BENCH["stages"]["train"]["median_ms"]
    mean = BENCH["stages"]["train"]["mean_ms"]
    parts += [
        text(40, 452, f"mean {num(mean)} ms · median {num(median)} ms · min {num(BENCH['stages']['train']['min_ms'])} ms"
                      f" · max {num(BENCH['stages']['train']['max_ms'])} ms · {len(train)} runs",
             11, INK, "600", family=MONO),
    ]
    legend = [
        ("engine spawn + CSV write", BENCH["stages"]["engine"]["median_ms"], CYAN),
        ("pandas load + clean", BENCH["stages"]["load_clean"]["median_ms"], EMERALD),
        ("Python fallback generator", BENCH["stages"]["fallback"]["median_ms"], BLUE),
        ("RandomForest fit", BENCH["stages"]["train"]["median_ms"], AMBER),
        ("compile (once, at build)", BENCH["compile"]["ms"], ROSE),
    ]
    parts.append(text(700, 128, "STAGE MEDIANS", 10, "#5a677d", "700", spacing=2, family=MONO))
    for index, (name, value, color) in enumerate(legend):
        y = 158 + index * 40
        parts += [
            f'<circle cx="708" cy="{y - 4}" r="4.5" fill="{color}" filter="url(#glow)"/>',
            text(724, y, name, 10.5, INK, "500"),
            text(724, y + 15, f"{value:,.1f} ms", 10.5, color, "700", family=MONO),
        ]
    parts.append(text(700, 372, "Speed ramp: emerald → cyan → blue → violet → amber → rose.", 9.5, MUTED, family=MONO))
    parts.append(text(40, 494, "Windows 11 · Python 3.14.5 · pandas 3.0.3 · scikit-learn 1.8.0 · 12 runs.",
                      10, MUTED, family=MONO))
    return svg(1100, 520, "Measured RandomForest fit latency histogram", "".join(parts))


def repo_tree() -> str:
    """Glowing file tree with a one-line purpose note per node."""
    nodes = [
        ("data_engine.cpp", "114", "seeded generator: structs, distributions, fixed-point CSV", CYAN),
        ("model_pipeline.py", "99", "load → clean → split → fit → print MAE / R²", CYAN),
        ("data_gen_fallback.py", "88", "Python mirror for hosts without g++", BLUE),
        ("app.py", "49", "Streamlit shell that full-bleeds index.html", VIOLET),
        ("index.html", "1,399", "4 views, canvas observatory, three.js river", VIOLET),
        ("design-system.html", "557", "tokens + component reference, standalone", VIOLET),
        ("synthetic_housing_data.csv", "1,001", "committed artefact · byte-stable · md5 39a0d36a", EMERALD),
        ("Dockerfile", "20", "python:3.11-slim, compiles and runs the engine at build", AMBER),
        ("docker-compose.yml", "7", "one service, port 7860", AMBER),
        ("render.yaml", "7", "free-tier Docker web service + health check", AMBER),
        (".github/workflows/build-check.yml", "51", "9 steps: compile → generate → train → smoke → docker", ROSE),
        ("requirements.txt", "4", "unpinned: streamlit, pandas, scikit-learn, plotly", ROSE),
        ("docs/assets/generate.py", "—", "renders all six SVGs, no browser needed", EMERALD),
        ("docs/assets/bench.py", "—", "re-measures the pipeline into bench_result.json", EMERALD),
    ]
    parts = [
        text(40, 54, "REPOSITORY MAP", 19, INK, "700"),
        text(40, 76, f"{len(nodes)} relevant paths · line counts from wc -l", 10.5, MUTED, family=MONO),
        f'<path d="M74 118 V{118 + (len(nodes) - 1) * 40}" stroke="{LINE}" stroke-width="1.4"/>',
    ]
    for index, (path, lines, note, color) in enumerate(nodes):
        y = 118 + index * 40
        parts += [
            f'<path d="M74 {y} H100" stroke="{LINE}" stroke-width="1.4"/>',
            f'<circle cx="74" cy="{y}" r="3" fill="{color}" filter="url(#glow)"/>',
            text(112, y + 4, path, 11.5, INK, "600", family=MONO),
            text(372, y + 4, lines, 10.5, color, "700", "start", MONO),
            text(430, y + 4, note, 10.5, MUTED),
        ]
    parts.append(text(40, 726, "Sizes are physical lines (wc -l). SVGs and the generated JSON are intentionally omitted.",
                      10.5, MUTED, family=MONO))
    return svg(1100, 750, "Repository map", "".join(parts))


def main() -> None:
    """Render every figure and print the written paths."""
    figures = {
        "banner.svg": banner(),
        "architecture.svg": architecture(),
        "pipeline.svg": pipeline(),
        "donut.svg": donut(),
        "histogram.svg": histogram(),
        "repo-tree.svg": repo_tree(),
    }
    for name, markup in figures.items():
        path = ASSETS / name
        path.write_text(markup, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}  {len(markup):,} bytes")
    print(f"totals: {sum(len(m) for m in figures.values()):,} bytes across {len(figures)} figures")


if __name__ == "__main__":
    main()
