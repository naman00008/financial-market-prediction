# Dataset V2 (Indian Stock API)

- **Source:** `https://stock.indianapi.in/historical_data`
- **Acquisition date:** 2026-10-06T10:44:57.985332
- **Exact stocks downloaded:** 45 out of 45 requested.
- **Exact date coverage:** 2025-10-06 to 2026-10-06
- **Row count:** 10912 raw daily records.
- **Columns (Metrics):** `Price` (Close), `Volume`, `DMA50`, `DMA200`.
- **Known missing data:** Open, High, Low are completely missing from the API response.
- **Known limitations:** Without OHL, features like Volatility, True Range, and some candle patterns cannot be computed exactly as in V1.
- **API version:** v1 (implicit)
- **Files included:** `download_manifest.json`, and raw JSON responses in `raw/` folder.
