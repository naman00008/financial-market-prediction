import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

def ensure_dirs():
    dirs = [
        "data/v2_indianapi/raw",
        "data/v2_indianapi/processed",
        "data/v2_indianapi/metadata"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_tickers():
    df = pd.read_csv("data/processed_dataset.csv")
    return list(df["Ticker"].unique())

def main():
    load_dotenv()
    api_key = os.environ.get("INDIAN_API_KEY")
    if not api_key:
        print("API key missing!")
        return

    ensure_dirs()
    tickers = load_tickers()
    
    manifest_path = "data/v2_indianapi/download_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    else:
        manifest = {}

    print(f"Total tickers to process: {len(tickers)}")
    
    for ticker in tickers:
        if ticker in manifest and manifest[ticker].get("status") == "success":
            print(f"Skipping {ticker}, already downloaded.")
            continue
            
        print(f"Downloading {ticker}...")
        url = f"https://stock.indianapi.in/historical_data?stock_name={ticker}&period=max&filter=default"
        req = urllib.request.Request(url)
        req.add_header("x-api-key", api_key)
        
        success = False
        error_msg = ""
        raw_data = None
        status_code = None
        
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req) as response:
                    status_code = response.getcode()
                    raw_data = response.read().decode('utf-8')
                    success = True
                    break
            except urllib.error.HTTPError as e:
                status_code = e.code
                error_msg = str(e)
                print(f"Attempt {attempt+1} failed: {error_msg}")
                time.sleep(2)
            except Exception as e:
                error_msg = str(e)
                print(f"Attempt {attempt+1} failed: {error_msg}")
                time.sleep(2)
                
        # Parse data to get start/end dates and counts
        start_date = None
        end_date = None
        row_count = 0
        file_path = f"data/v2_indianapi/raw/{ticker}.json"
        
        if success and raw_data:
            try:
                parsed = json.loads(raw_data)
                # Find the price dataset
                datasets = parsed.get("datasets", [])
                price_data = None
                for ds in datasets:
                    if ds.get("metric") == "Price":
                        price_data = ds.get("values", [])
                        break
                
                if price_data:
                    row_count = len(price_data)
                    if row_count > 0:
                        start_date = price_data[0][0]
                        end_date = price_data[-1][0]
                
                with open(file_path, "w") as f:
                    f.write(raw_data)
            except Exception as e:
                success = False
                error_msg = f"JSON parsing failed: {str(e)}"
                
        manifest[ticker] = {
            "ticker": ticker,
            "status": "success" if success else "failed",
            "start_date_requested": "max",
            "end_date_requested": "today",
            "actual_earliest_date": start_date,
            "actual_latest_date": end_date,
            "number_of_rows": row_count,
            "http_status": status_code,
            "retry_count": attempt,
            "error_message": error_msg if not success else None,
            "download_timestamp": datetime.now().isoformat(),
            "raw_file_path": file_path if success else None
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)
            
        time.sleep(1) # respect rate limit

if __name__ == "__main__":
    main()
