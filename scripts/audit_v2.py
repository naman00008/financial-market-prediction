import os
import json
import pandas as pd
from datetime import datetime

def generate_audit_and_freeze():
    manifest_path = "data/v2_indianapi/download_manifest.json"
    if not os.path.exists(manifest_path):
        print("Manifest not found.")
        return
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    audit_results = []
    
    total_raw_rows = 0
    earliest_global = "2100-01-01"
    latest_global = "1900-01-01"
    successful_stocks = 0
    failed_stocks = 0
    
    for ticker, info in manifest.items():
        if info["status"] != "success":
            failed_stocks += 1
            continue
            
        successful_stocks += 1
        raw_path = info["raw_file_path"]
        with open(raw_path, "r") as f:
            raw_data = json.load(f)
            
        datasets = raw_data.get("datasets", [])
        price_data = []
        volume_data = []
        
        for ds in datasets:
            if ds.get("metric") == "Price":
                price_data = ds.get("values", [])
            elif ds.get("metric") == "Volume":
                volume_data = ds.get("values", [])
                
        row_count = len(price_data)
        total_raw_rows += row_count
        
        dates = [r[0] for r in price_data]
        prices = [float(r[1]) for r in price_data]
        
        if row_count > 0:
            earliest = min(dates)
            latest = max(dates)
            if earliest < earliest_global: earliest_global = earliest
            if latest > latest_global: latest_global = latest
        else:
            earliest = "N/A"
            latest = "N/A"
            
        # Checks
        duplicate_dates = len(dates) - len(set(dates))
        is_chronological = dates == sorted(dates)
        zero_negative_prices = sum(1 for p in prices if p <= 0)
        invalid_numeric = sum(1 for p in prices if pd.isna(p))
        
        audit_results.append({
            "ticker": ticker,
            "row_count": row_count,
            "earliest": earliest,
            "latest": latest,
            "duplicate_dates": duplicate_dates,
            "is_chronological": is_chronological,
            "zero_negative_prices": zero_negative_prices,
            "invalid_numeric": invalid_numeric,
            "missing_ohlc": "Yes" # The API does not provide Open, High, Low
        })
        
    # Write Audit MD
    with open("docs/DATASET_V2_AUDIT.md", "w") as f:
        f.write("# Dataset V2 Audit\n\n")
        f.write("## 1. Summary\n")
        f.write(f"- Total Stocks: {len(manifest)}\n")
        f.write(f"- Successful: {successful_stocks}\n")
        f.write(f"- Failed: {failed_stocks}\n")
        f.write(f"- Total Raw Rows: {total_raw_rows}\n")
        f.write(f"- Global Date Range: {earliest_global} to {latest_global}\n\n")
        
        f.write("## 2. Issues Found\n")
        f.write("- **Missing OHLC:** API Endpoint (`historical_data?filter=default`) only returned `Price` (Close), `Volume`, `DMA50`, and `DMA200`. Open, High, and Low values are missing from this API natively.\n")
        f.write("- **API Missing Data:** Some tickers may not have data reaching back to 2005.\n\n")
        
        f.write("## 3. Stock-level Audit\n")
        df_audit = pd.DataFrame(audit_results)
        f.write(df_audit.to_markdown(index=False))
        f.write("\n")
        
    # Compare with V1
    df_v1 = pd.read_csv("data/processed_dataset.csv")
    v1_stocks = df_v1["Ticker"].nunique()
    v1_earliest = df_v1["Date"].min()
    v1_latest = df_v1["Date"].max()
    v1_rows = len(df_v1)
    
    with open("docs/DATASET_V1_VS_V2.md", "w") as f:
        f.write("# Dataset V1 vs V2\n\n")
        f.write("| Property | V1 | V2 |\n")
        f.write("|---|---|---|\n")
        f.write(f"| Number of stocks | {v1_stocks} | {successful_stocks} |\n")
        f.write(f"| Earliest date | {v1_earliest} | {earliest_global} |\n")
        f.write(f"| Latest date | {v1_latest} | {latest_global} |\n")
        f.write(f"| Raw rows | 55800 (approx) | {total_raw_rows} |\n")
        f.write(f"| Average rows/stock | {v1_rows/v1_stocks:.0f} | {total_raw_rows/max(1, successful_stocks):.0f} |\n")
        f.write(f"| Missing values | 0 in processed | Open/High/Low are missing |\n")
        f.write(f"| Data source | Yahoo Finance | Indian Stock API |\n")
        f.write(f"| Collection date | Previous Phase | {datetime.now().strftime('%Y-%m-%d')} |\n\n")
        
        f.write("### Differences\n")
        f.write("- **Missing OHLC in V2:** V2 does not have Open, High, Low values natively returned by the historical endpoint.\n")
        f.write("- **Longer History:** V2 generally has data spanning back to ~2005, giving much more historical depth than V1's 2021 start date.\n")
        
    # Freeze Dataset V2
    with open("data/v2_indianapi/DATASET_VERSION.md", "w") as f:
        f.write("# Dataset V2 (Indian Stock API)\n\n")
        f.write("- **Source:** `https://stock.indianapi.in/historical_data`\n")
        f.write(f"- **Acquisition date:** {datetime.now().isoformat()}\n")
        f.write(f"- **Exact stocks downloaded:** {successful_stocks} out of {len(manifest)} requested.\n")
        f.write(f"- **Exact date coverage:** {earliest_global} to {latest_global}\n")
        f.write(f"- **Row count:** {total_raw_rows} raw daily records.\n")
        f.write("- **Columns (Metrics):** `Price` (Close), `Volume`, `DMA50`, `DMA200`.\n")
        f.write("- **Known missing data:** Open, High, Low are completely missing from the API response.\n")
        f.write("- **Known limitations:** Without OHL, features like Volatility, True Range, and some candle patterns cannot be computed exactly as in V1.\n")
        f.write("- **API version:** v1 (implicit)\n")
        f.write("- **Files included:** `download_manifest.json`, and raw JSON responses in `raw/` folder.\n")
        
    print("Audit and Freeze complete.")

if __name__ == "__main__":
    generate_audit_and_freeze()
