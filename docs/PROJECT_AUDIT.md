# Project Audit — Market ML (AUCML Semester V ESE)

Audit date: 2026-10-28. Every finding below was verified by reading the actual source and executing the test suite in the current environment (Python 3.14.7, pandas 3.0.6, scikit-learn 1.9.1).

## 1. Repository overview

- FastAPI single-page app (`main.py` + `app/` routes + vanilla JS dashboard) over a `src/` analytics layer.
- Data: 45 NSE equity daily OHLCV CSVs (`data/*.csv`, 2021-10-04 → 2026-10-01, documented in `data/DATASET_DOCUMENTATION.md` and `data/dataset_manifest.json`), plus per-ticker cached metric JSON in `cache/`.
- Tests: 9 pytest files; last full run: **13 passed, 3 failed, 1 collection error**.

## 2. Requirement-to-evidence matrix

| Capability | Files | Status | Evidence / notes |
|---|---|---|---|
| Data loading & standardization | `src/data_preprocessing.py` | Implemented and verified | Local CSV → yfinance fallback; lru_cache; unit tests pass |
| Leakage-free technical indicators | `src/feature_engineering.py` | Implemented, weakly tested | No bfill; rolling windows correct; test expects wrong column names (`RSI`, `BB_Upper`) |
| Next-day direction target | `src/dataset_builder.py` → imports `src/ml_dataset` | **Broken** | `src/ml_dataset.py` does not exist → ImportError; the honest classification dataset is never built |
| Chronological split / walk-forward | `src/validation.py` | Implemented but unused | Not called from any route or the frontend |
| Classification training | `src/model_training.py` | Implemented but crippled | RF/XGBoost use `n_estimators=2`; scaler fit only on train (good) |
| Regression training | `src/model_training.py` | Implemented but **leaky** | `create_features` keeps same-day Open/High/Low/Close; `train_regression_models(features, target_col="Close")` predicts Close from same-day OHLC |
| `/api/train/{ticker}` | `app/api_routes.py:134` | **Statistically invalid** | Trains on same-day features → near-perfect R²; "directional accuracy" formula compares `y_p[1:] − y_t[:-1]` (meaningless); retrains per request |
| `/api/backtest/{ticker}` | `app/api_routes.py:331` | **Leaky + invalid** | Model selected by test-set R²; signals = (same-day predicted Close > same-day Open); predicted Close used same-day High/Low |
| `/api/forecast/{ticker}` | `app/forecast_routes.py` | Partially valid | GBM Monte Carlo OK as a scenario tool; "AI trend" is a degree-2 polynomial extrapolation mislabeled as AI; not tied to the ML pipeline |
| `/api/explain/{ticker}` | `app/api_routes.py:371` | Implemented but leaky | Explains the leaky regression model on same-day OHLC features |
| Portfolio optimization | `app/portfolio_routes.py` | Implemented, approximately correct | Vectorized Dirichlet Monte-Carlo frontier (sampling, not a true optimizer — must be documented); annualization ×252 fine; discrete share logic fine |
| Risk metrics | `app/portfolio_routes.py` | Mostly correct | Parametric VaR (z=1.645) and ES (2.063σ) correct for normal assumption; stress scenarios use **fabricated** sector multipliers (must be labeled simulated) |
| Backtester | `src/backtest.py` | Implemented, correct core | Round-trip cost, equity curves, drawdown; debug prints left in production path; buys on signal==1 only (no shorting) |
| Explainability | `src/explainability.py` | Partially implemented | SHAP optional with fallback to `feature_importances_`; imports matplotlib at module load (hard dependency) |
| Auth | `src/auth.py`, `app/auth_routes.py` | Implemented with **security defects** | PBKDF2-100k + constant-time compare (good); tokens in-memory, no expiry; `/api/auth/me?username=` returns any user's profile **without a token** (bypass); login/registration audit logs store password hash + salt; `credentials.txt` plaintext dossier written per user; default password `MarketPulse123!` assigned to folder-derived users |
| Tracker | `src/tracker.py` | Implemented | Per-user folders + JSONL audit; benign but verbose |
| Live data / news | `src/live_data.py`, `src/sentiment_analysis.py` | Implemented, hard deps | Module-level `import yfinance`, `vaderSentiment` → app failed to import in a clean env (fixed by installing; graceful-import refactor recommended) |
| NIFTY proxy | `src/data_preprocessing.load_nifty_index` | **Misleading** | "Index" = mean of raw prices across 45 stocks (not value-weighted, uses bfill); should not be presented as NIFTY 50 |
| Tests | `tests/` | Partially valid | `test_market_ml_models` calls `train_regression_models(X, y)` (old signature); `test_technical_indicators` expects `RSI`/`BB_Upper`; `test_sentiment_engine` imports nonexistent `analyze_text_sentiment` |
| Docker | `Dockerfile`, `docker-compose.yml` | Implemented, unverified here | Multi-stage build is coherent; **not built in this environment**; README's AWS deployment claim is unverifiable |
| README claims | `README.md` | Overstated | "Institutional-grade", "Zero-Knowledge Cryptographic Authentication" (it is not zero-knowledge), "Deployed on AWS EC2" (unverified) |

## 3. Defects that can cause data leakage

1. **Same-day OHLC regression** (`/api/train`, `/api/explain`): features include the same day's Open/High/Low used to predict that day's Close. This is the single largest academic defect — R² ≈ 1 by construction.
2. **Backtest model selection on test R²** and **backtest signal** derived from same-day leakage.
3. `load_nifty_index` uses `bfill` (future data into the past) — only affects the proxy index, not the ML pipeline.
4. Scaler leakage is **already prevented** in classification (fit on train only).

## 4. Statistical validity issues

- The only classification trainer is crippled (`n_estimators=2`) and never wired into the app; the dashboard's "ML" numbers all come from the leaky regression path.
- No experiment produces a saved model artifact, so dashboard results are not traceable to a trained model.
- Walk-forward validation exists but is never executed.
- Directional accuracy in `/api/train` is mathematically wrong.
- Stress-test sector multipliers and recovery-day estimates are invented heuristics presented as analysis.

## 5. Security findings

1. `/api/auth/me` accepts `?username=` without any token → unauthenticated user enumeration.
2. Audit logs (`track_activity`) record password hash and salt on login/registration.
3. `credentials.txt` (human-readable hash dossier) written into each user folder — unnecessary exposure surface.
4. Sessions never expire; store is in-memory (acceptable for a classroom app, must be documented).
5. CORS `allow_origins=["*"]` together with `allow_credentials=True`.
6. Default password fallback `MarketPulse123!` for users restored from folders without stored hashes.

## 6. Reliability / demo risks

- Clean-env import failure (yfinance/vaderSentiment/matplotlib hard imports) — fixed by installing; graceful fallback still recommended for the sentiment/live paths.
- `/api/train`, `/api/backtest`, `/api/explain` retrain on every request (multi-second latency during a live demo).
- `profile_cache` unbounded; yfinance profile calls have no timeout.

## 7. What already works and must be preserved

- Data loading/caching layer and the documented 45-ticker dataset.
- Leakage-free feature engineering module (correct design).
- Chronological split + walk-forward generators (`src/validation.py`).
- FastAPI app structure, static dashboard, auth's PBKDF2 core.
- Portfolio/risk math core (frontier sampling, VaR/ES, discrete shares).
- Backtester engine (correct once fed honest signals).

## 8. Priority remediation order

1. Create `src/ml_dataset.py` (target definition) and repair `src/dataset_builder.py`.
2. Build the honest classification pipeline: drop same-day OHLC from model features, chronological split, real hyperparameters, persisted model + metadata.
3. Replace `/api/train` & `/api/explain` leakage paths; add `/api/ml/predict`; fix `/api/backtest` (no test-selected models, next-day-aligned signals).
4. Security fixes in auth (no unauthenticated `/me` fallback, no hash/salt in logs, no credentials.txt).
5. Fix broken tests; add leakage/chronology/quant tests.
6. Run the full experiment suite and generate real evaluation artifacts.
7. Documentation set (problem statement, dataset docs, evaluation, report, presentation, viva, rubric matrix).
