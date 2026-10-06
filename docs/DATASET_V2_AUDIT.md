# Dataset V2 Audit

## 1. Summary
- Total Stocks: 45
- Successful: 45
- Failed: 0
- Total Raw Rows: 10912
- Global Date Range: 2025-10-06 to 2026-10-06

## 2. Issues Found
- **Missing OHLC:** API Endpoint (`historical_data?filter=default`) only returned `Price` (Close), `Volume`, `DMA50`, and `DMA200`. Open, High, and Low values are missing from this API natively.
- **API Missing Data:** Some tickers may not have data reaching back to 2005.

## 3. Stock-level Audit
| ticker     |   row_count | earliest   | latest     |   duplicate_dates | is_chronological   |   zero_negative_prices |   invalid_numeric | missing_ohlc   |
|:-----------|------------:|:-----------|:-----------|------------------:|:-------------------|-----------------------:|------------------:|:---------------|
| ADANIPORTS |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ASIANPAINT |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| AXISBANK   |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| BAJAJ-AUTO |           0 | N/A        | N/A        |                 0 | True               |                      0 |                 0 | Yes            |
| BAJAJFINSV |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| BAJFINANCE |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| BHARTIARTL |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| BPCL       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| BRITANNIA  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| CIPLA      |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| COALINDIA  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| DRREDDY    |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| EICHERMOT  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| GAIL       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| GRASIM     |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| HCLTECH    |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| HEROMOTOCO |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| HINDALCO   |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| HINDUNILVR |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ICICIBANK  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| INDUSINDBK |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| INFY       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| IOC        |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ITC        |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| JSWSTEEL   |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| KOTAKBANK  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| LT         |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| MARUTI     |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| NESTLEIND  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| NTPC       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ONGC       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| POWERGRID  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| RELIANCE   |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| SBIN       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| SHREECEM   |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| SUNPHARMA  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| TATASTEEL  |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| TCS        |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| TECHM      |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| TITAN      |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ULTRACEMCO |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| UPL        |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| VEDL       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| WIPRO      |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
| ZEEL       |         248 | 2025-10-06 | 2026-10-06 |                 0 | True               |                      0 |                 0 | Yes            |
