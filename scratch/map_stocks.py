import json
import pandas as pd
import os
import re

with open('IN-FINews  Dataset.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

# Get 45 tickers
data_dir = 'data'
tickers = [f.split('.')[0] for f in os.listdir(data_dir) if f.endswith('.csv') and f != 'processed_dataset.csv']

print(f"Loaded {len(tickers)} tickers.")

# Mapping common names to tickers
company_map = {
    'adani ports': 'ADANIPORTS',
    'asian paints': 'ASIANPAINT',
    'asian paint': 'ASIANPAINT',
    'axis bank': 'AXISBANK',
    'bajaj auto': 'BAJAJ-AUTO',
    'bajaj finserv': 'BAJAJFINSV',
    'bajaj finance': 'BAJFINANCE',
    'bharti airtel': 'BHARTIARTL',
    'airtel': 'BHARTIARTL',
    'bpcl': 'BPCL',
    'bharat petroleum': 'BPCL',
    'britannia': 'BRITANNIA',
    'cipla': 'CIPLA',
    'coal india': 'COALINDIA',
    'dr reddy': 'DRREDDY',
    "dr reddy's": 'DRREDDY',
    'eicher': 'EICHERMOT',
    'gail': 'GAIL',
    'grasim': 'GRASIM',
    'hcl tech': 'HCLTECH',
    'hero moto': 'HEROMOTOCO',
    'hindalco': 'HINDALCO',
    'hindustan unilever': 'HINDUNILVR',
    'hul': 'HINDUNILVR',
    'icici': 'ICICIBANK',
    'indusind': 'INDUSINDBK',
    'infosys': 'INFY',
    'infy': 'INFY',
    'ioc': 'IOC',
    'indianoil': 'IOC',
    'indian oil': 'IOC',
    'itc': 'ITC',
    'jsw steel': 'JSWSTEEL',
    'kotak': 'KOTAKBANK',
    'larsen & toubro': 'LT',
    'l&t': 'LT',
    'maruti': 'MARUTI',
    'nestle': 'NESTLEIND',
    'ntpc': 'NTPC',
    'ongc': 'ONGC',
    'powergrid': 'POWERGRID',
    'power grid': 'POWERGRID',
    'reliance': 'RELIANCE',
    'sbi': 'SBIN',
    'state bank of india': 'SBIN',
    'shree cement': 'SHREECEM',
    'sun pharma': 'SUNPHARMA',
    'tata steel': 'TATASTEEL',
    'tcs': 'TCS',
    'tata consultancy services': 'TCS',
    'tech mahindra': 'TECHM',
    'titan': 'TITAN',
    'ultratech': 'ULTRACEMCO',
    'upl': 'UPL',
    'vedanta': 'VEDL',
    'vedl': 'VEDL',
    'wipro': 'WIPRO',
    'zeel': 'ZEEL',
    'zee entertainment': 'ZEEL'
}

mapped_records = 0
stock_counts = {t: 0 for t in tickers}
unmatched_records = 0

for item in data:
    text_to_search = (item['Title'] + " " + item['Keywords']).lower()
    matched = False
    
    # Simple regex based matching
    for name, ticker in company_map.items():
        if re.search(r'\b' + re.escape(name) + r'\b', text_to_search):
            stock_counts[ticker] += 1
            matched = True
            
    if matched:
        mapped_records += 1
    else:
        unmatched_records += 1

with open('scratch/mapping_output.txt', 'w') as out:
    out.write(f"Total Records: {len(data)}\n")
    out.write(f"Mapped Records: {mapped_records}\n")
    out.write(f"Unmatched Records: {unmatched_records}\n")
    out.write("\nCoverage per stock:\n")
    for t in sorted(tickers):
        out.write(f"{t}: {stock_counts[t]}\n")
