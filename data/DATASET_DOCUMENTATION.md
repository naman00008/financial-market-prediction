# Dataset Documentation & Data Quality Report

**Dataset Name:** NSE Top Equities 5-Year Daily OHLCV Collection  
**Acquisition Date:** 2026-10-01  
**Data Source:** Yahoo Finance (via yfinance)  
**Frequency:** Daily  
**Period Covered:** 2021-10-04 to 2026-10-01  

---

## 1. Executive Summary & Inventory

- **Acquired Stock Universe:** 45 NSE-listed equities (out of 47 candidate universe)
- **Excluded Symbols:** `MM` and `TATAMOTORS` (Yahoo Finance `.NS` data unavailable at collection time)
- **Total Raw OHLCV Records:** 55,800
- **Total Prepared ML Sample Rows:** 55,755 (after removing final row per symbol with unknown next-day return)
- **Target Distribution:**
  - **Class 1 (UP):** 28,259 (50.68%)
  - **Class 0 (DOWN / Non-Positive):** 27,496 (49.32%)

---

## 2. Feature & Schema Definition

| Column Name | Type | Description | Unit / Range |
|---|---|---|---|
| `Date` | Timestamp | Trading day date (YYYY-MM-DD) | Calendar trading days |
| `Open` | Continuous | Opening price of trading day | INR (₹) |
| `High` | Continuous | Highest price reached during trading day | INR (₹) |
| `Low` | Continuous | Lowest price reached during trading day | INR (₹) |
| `Close` | Continuous | Official closing price of trading day | INR (₹) |
| `Volume` | Discrete | Total shares traded | Integer count |
| `Target` | Binary Label | 1 if `Close_{t+1} > Close_t`, else 0 | {0, 1} |

---

## 3. Data Quality Audit Results

- **Missing Values in Required OHLCV Fields:** 0
- **Duplicate Trading Dates:** 0
- **Invalid / Unparseable Dates:** 0
- **Negative or Zero Prices:** 0
- **Price Inconsistencies (`High < Low` or `High < Close` or `Low > Close`):** 0
- **Missing Trading Days:** Standard weekend and NSE trading holiday gaps expected and preserved; chronological order strictly strictly validated.

---

## 4. Per-Stock Inventory

| Ticker | Raw Rows | Prepared Rows | Min Date | Max Date | UP Count | DOWN Count | UP % |
|---|---:|---:|---|---|---:|---:|---:|
| `ADANIPORTS` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 634 | 605 | 51.17% |
| `ASIANPAINT` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 625 | 614 | 50.44% |
| `AXISBANK` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 632 | 607 | 51.01% |
| `BAJAJ-AUTO` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 657 | 582 | 53.03% |
| `BAJAJFINSV` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 615 | 624 | 49.64% |
| `BAJFINANCE` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 628 | 611 | 50.69% |
| `BHARTIARTL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 637 | 602 | 51.41% |
| `BPCL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 615 | 624 | 49.64% |
| `BRITANNIA` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 641 | 598 | 51.74% |
| `CIPLA` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 615 | 624 | 49.64% |
| `COALINDIA` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 646 | 593 | 52.14% |
| `DRREDDY` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 629 | 610 | 50.77% |
| `EICHERMOT` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 613 | 626 | 49.48% |
| `GAIL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 628 | 611 | 50.69% |
| `GRASIM` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 641 | 598 | 51.74% |
| `HCLTECH` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 619 | 620 | 49.96% |
| `HEROMOTOCO` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 646 | 593 | 52.14% |
| `HINDALCO` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 665 | 574 | 53.67% |
| `HINDUNILVR` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 591 | 648 | 47.7% |
| `ICICIBANK` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 636 | 603 | 51.33% |
| `INDUSINDBK` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 627 | 612 | 50.61% |
| `INFY` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 607 | 632 | 48.99% |
| `IOC` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 641 | 598 | 51.74% |
| `ITC` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 618 | 621 | 49.88% |
| `JSWSTEEL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 630 | 609 | 50.85% |
| `KOTAKBANK` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 620 | 619 | 50.04% |
| `LT` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 634 | 605 | 51.17% |
| `MARUTI` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 618 | 621 | 49.88% |
| `NESTLEIND` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 620 | 619 | 50.04% |
| `NTPC` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 636 | 603 | 51.33% |
| `ONGC` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 634 | 605 | 51.17% |
| `POWERGRID` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 628 | 611 | 50.69% |
| `RELIANCE` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 626 | 613 | 50.52% |
| `SBIN` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 660 | 579 | 53.27% |
| `SHREECEM` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 610 | 629 | 49.23% |
| `SUNPHARMA` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 644 | 595 | 51.98% |
| `TATASTEEL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 627 | 612 | 50.61% |
| `TCS` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 593 | 646 | 47.86% |
| `TECHM` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 616 | 623 | 49.72% |
| `TITAN` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 630 | 609 | 50.85% |
| `ULTRACEMCO` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 645 | 594 | 52.06% |
| `UPL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 626 | 613 | 50.52% |
| `VEDL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 661 | 578 | 53.35% |
| `WIPRO` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 605 | 634 | 48.83% |
| `ZEEL` | 1,240 | 1,239 | 2021-10-04 | 2026-10-01 | 590 | 649 | 47.62% |
