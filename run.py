#!/usr/bin/env python3
"""Market ML — Canonical Application Runner & Environment Verifier.

Usage:
    python run.py              # Launch the Market ML platform on 127.0.0.1:8000
    python run.py --check      # Validate runtime dependencies, data, and environment
    python run.py --help       # Display detailed CLI options and instructions

Dependencies:
    python -m pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

# Resolve repository root strictly relative to this script
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure working directory is repo root for consistent file access
os.chdir(REPO_ROOT)

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("jinja2", "jinja2"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("sklearn", "scikit-learn"),
    ("xgboost", "xgboost"),
    ("plotly", "plotly"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("vaderSentiment", "vaderSentiment"),
    ("yfinance", "yfinance"),
    ("requests", "requests"),
    ("feedparser", "feedparser"),
    ("psutil", "psutil"),
    ("shap", "shap"),
]


def check_environment() -> bool:
    """Validate runtime environment, dependencies, dataset integrity, and assets.

    Returns True if healthy; False if any critical check fails.
    """
    print("=" * 70)
    print("Market ML: System Environment & Health Diagnostic")
    print("=" * 70)
    print(f"Repository Root : {REPO_ROOT}")
    print(f"Python Runtime  : {sys.version.split()[0]} ({sys.executable})")

    # 1. Dependency Verification
    print("\n[1/5] Checking Required Dependencies...")
    missing = []
    installed_count = 0
    for import_name, pkg_name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            ver = getattr(mod, "__version__", "installed")
            installed_count += 1
            print(f"  [OK] {pkg_name:<18} ({ver})")
        except ImportError:
            missing.append(pkg_name)
            print(f"  [X]  {pkg_name:<18} [MISSING]")

    if missing:
        print("\nMISSING DEPENDENCIES DETECTED:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall all required dependencies using:")
        print("   python -m pip install -r requirements.txt\n")
        return False

    print(f"  All {installed_count} packages verified successfully.")

    # 2. Dataset Verification
    print("\n[2/5] Checking Dataset Integrity...")
    data_dir = REPO_ROOT / "data"
    if not data_dir.is_dir():
        print(f"  [X]  Data directory missing: {data_dir}")
        return False
    csv_count = len(list(data_dir.glob("*.csv")))
    print(f"  [OK] Data directory located ({csv_count} stock CSV files available)")
    if csv_count < 40:
        print(f"  [!]  Warning: Expected 45 stock CSV files; found {csv_count}.")

    # 3. Static & Template Assets
    print("\n[3/5] Checking Web Assets & Template Integrity...")
    template_file = REPO_ROOT / "app" / "templates" / "index.html"
    css_file = REPO_ROOT / "app" / "static" / "style_v3.css"
    js_file = REPO_ROOT / "app" / "static" / "script_v52.js"

    assets = [("Template (index.html)", template_file),
              ("CSS (style_v3.css)", css_file),
              ("JS (script_v52.js)", js_file)]
    assets_ok = True
    for name, path in assets:
        if path.is_file():
            print(f"  [OK] {name:<22} ({path.stat().st_size:,} bytes)")
        else:
            print(f"  [X]  {name:<22} [FILE NOT FOUND: {path}]")
            assets_ok = False
    if not assets_ok:
        return False

    # 4. Trained Model Artifacts
    print("\n[4/5] Checking Machine Learning Model Artifacts...")
    models_dir = REPO_ROOT / "models"
    if models_dir.is_dir():
        joblib_count = len(list(models_dir.glob("*.joblib")))
        meta_count = len(list(models_dir.glob("*_metadata.json")))
        print(f"  [OK] Model repository active: {joblib_count} bundles, {meta_count} metadata records")
    else:
        print(f"  [i]  Model directory absent. Models will train on first demand.")

    # 5. Results & Evaluation Artifacts
    print("\n[5/5] Checking Benchmark & Evaluation Results...")
    res_dir = REPO_ROOT / "results"
    exp_file = res_dir / "experiment_results.json"
    dq_file = res_dir / "data_quality.json"
    if exp_file.is_file() and dq_file.is_file():
        print(f"  [OK] Verified experiment results: {exp_file.stat().st_size:,} bytes")
        print(f"  [OK] Verified data quality report: {dq_file.stat().st_size:,} bytes")
    else:
        print("  [i]  Experiment results absent. Run: python scripts/run_experiments.py run")

    print("\n" + "=" * 70)
    print("SUCCESS: ENVIRONMENT READY - Market ML is fully configured to run.")
    print("=" * 70 + "\n")
    return True


def start_server(host: str, port: int, reload: bool) -> None:
    """Launch the FastAPI application server."""
    # Pre-flight check
    for mod_name in ("fastapi", "uvicorn"):
        try:
            importlib.import_module(mod_name)
        except ImportError:
            print(f"❌ Error: Required package '{mod_name}' is not installed.")
            print("Please install dependencies with: python -m pip install -r requirements.txt")
            sys.exit(1)

    import uvicorn

    print("=" * 70)
    print("Market ML: Cloud-Native Market Prediction & Risk Analysis Platform")
    print(f"Listening on  : http://{host}:{port}")
    print(f"Interactive UI: http://{host}:{port}/")
    print(f"API Health    : http://{host}:{port}/api/health")
    print("=" * 70)
    print("Press Ctrl+C to terminate the server gracefully.\n")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python run.py",
        description="Market ML: Execution runner and diagnostic verification tool.",
        epilog="Dependency Installation: python -m pip install -r requirements.txt",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run system diagnostic check and verify environment readiness.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host interface to bind (default: 127.0.0.1 or $HOST).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port number to bind (default: 8000 or $PORT).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for local development.",
    )

    args = parser.parse_args()

    if args.check:
        healthy = check_environment()
        sys.exit(0 if healthy else 1)

    start_server(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
