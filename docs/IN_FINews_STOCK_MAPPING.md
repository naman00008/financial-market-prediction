# IN-FINews Stock Mapping

## Overview
The goal was to align the news articles in the `IN-FINews Dataset.json` to the official V1 dataset, which contains a finalized 45-stock NSE universe. We mapped known company names/entities found in the `Title` and `Keywords` to the 45 NSE tickers using an exact regex keyword match.

## Mapping Summary
- **Total News Records**: 3,348
- **Mapped Records**: 1,470
- **Unmatched Records**: 1,878 (These belong to companies outside the 45-stock universe or macro news, and they will be excluded from the ML merge.)

## Matched Stocks & Coverage
The following tickers were successfully matched, showing the number of news records for each:
- **ADANIPORTS**: 37
- **ASIANPAINT**: 46
- **AXISBANK**: 55
- **BAJAJ-AUTO**: 42
- **BAJAJFINSV**: 34
- **BAJFINANCE**: 55
- **BHARTIARTL**: 177
- **BPCL**: 36
- **BRITANNIA**: 13
- **CIPLA**: 40
- **COALINDIA**: 36
- **DRREDDY**: 43
- **EICHERMOT**: 39
- **GAIL**: 7
- **GRASIM**: 27
- **HCLTECH**: 28
- **HEROMOTOCO**: 4
- **HINDALCO**: 51
- **HINDUNILVR**: 89
- **ICICIBANK**: 161
- **INDUSINDBK**: 67
- **INFY**: 82
- **IOC**: 44
- **ITC**: 75
- **JSWSTEEL**: 62
- **KOTAKBANK**: 55
- **LT**: 45
- **MARUTI**: 47
- **NESTLEIND**: 42
- **NTPC**: 63
- **ONGC**: 19
- **POWERGRID**: 35
- **RELIANCE**: 56
- **SBIN**: 149
- **SHREECEM**: 2
- **SUNPHARMA**: 38
- **TATASTEEL**: 71
- **TCS**: 141
- **TECHM**: 42
- **TITAN**: 43
- **ULTRACEMCO**: 53
- **UPL**: 9
- **VEDL**: 62
- **WIPRO**: 31
- **ZEEL**: 6

## Ambiguous / Unmatched Stocks
- 1,878 records were unmatched.
- These records cover macro topics (e.g., RBI rate cuts), broader indices (Nifty 50), or mid-cap/small-cap companies that are not part of the 45-stock universe (e.g., Aurobindo Pharma, HDB Financial, Tata Communications).
- Ambiguous mappings (e.g., "Tata" alone) were intentionally ignored. Only concrete, confident company names mapping exactly to the 45-ticker universe were used.

## Conclusion
If a company could not be mapped with high confidence to the 45-stock universe, it was entirely excluded from the merge to avoid polluting the dataset.
