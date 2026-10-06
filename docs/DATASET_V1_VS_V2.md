# Dataset V1 vs V2

| Property | V1 | V2 |
|---|---|---|
| Number of stocks | 45 | 45 |
| Earliest date | 2021-12-15 | 2025-10-06 |
| Latest date | 2026-09-30 | 2026-10-06 |
| Raw rows | 55800 (approx) | 10912 |
| Average rows/stock | 1190 | 242 |
| Missing values | 0 in processed | Open/High/Low are missing |
| Data source | Yahoo Finance | Indian Stock API |
| Collection date | Previous Phase | 2026-10-06 |

### Differences
- **Missing OHLC in V2:** V2 does not have Open, High, Low values natively returned by the historical endpoint.
- **Longer History:** V2 generally has data spanning back to ~2005, giving much more historical depth than V1's 2021 start date.
