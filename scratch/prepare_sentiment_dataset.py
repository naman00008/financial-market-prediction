import json
import pandas as pd
import numpy as np
import os
import sys

# Append src to path so we can import sentiment_analysis
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.sentiment_analysis import analyze_sentiment

def main():
    print("Loading IN-FINews Dataset...")
    with open('IN-FINews  Dataset.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    news_df = pd.DataFrame(data)
    
    # 1. Map to tickers
    data_dir = 'data'
    tickers = [f.split('.')[0] for f in os.listdir(data_dir) if f.endswith('.csv') and f != 'processed_dataset.csv']
    
    company_map = {
        'adani ports': 'ADANIPORTS', 'asian paints': 'ASIANPAINT', 'asian paint': 'ASIANPAINT',
        'axis bank': 'AXISBANK', 'bajaj auto': 'BAJAJ-AUTO', 'bajaj finserv': 'BAJAJFINSV',
        'bajaj finance': 'BAJFINANCE', 'bharti airtel': 'BHARTIARTL', 'airtel': 'BHARTIARTL',
        'bpcl': 'BPCL', 'bharat petroleum': 'BPCL', 'britannia': 'BRITANNIA', 'cipla': 'CIPLA',
        'coal india': 'COALINDIA', 'dr reddy': 'DRREDDY', "dr reddy's": 'DRREDDY',
        'eicher': 'EICHERMOT', 'gail': 'GAIL', 'grasim': 'GRASIM', 'hcl tech': 'HCLTECH',
        'hero moto': 'HEROMOTOCO', 'hindalco': 'HINDALCO', 'hindustan unilever': 'HINDUNILVR',
        'hul': 'HINDUNILVR', 'icici': 'ICICIBANK', 'indusind': 'INDUSINDBK', 'infosys': 'INFY',
        'infy': 'INFY', 'ioc': 'IOC', 'indianoil': 'IOC', 'indian oil': 'IOC', 'itc': 'ITC',
        'jsw steel': 'JSWSTEEL', 'kotak': 'KOTAKBANK', 'larsen & toubro': 'LT', 'l&t': 'LT',
        'maruti': 'MARUTI', 'nestle': 'NESTLEIND', 'ntpc': 'NTPC', 'ongc': 'ONGC',
        'powergrid': 'POWERGRID', 'power grid': 'POWERGRID', 'reliance': 'RELIANCE',
        'sbi': 'SBIN', 'state bank of india': 'SBIN', 'shree cement': 'SHREECEM',
        'sun pharma': 'SUNPHARMA', 'tata steel': 'TATASTEEL', 'tcs': 'TCS',
        'tata consultancy services': 'TCS', 'tech mahindra': 'TECHM', 'titan': 'TITAN',
        'ultratech': 'ULTRACEMCO', 'upl': 'UPL', 'vedanta': 'VEDL', 'vedl': 'VEDL',
        'wipro': 'WIPRO', 'zeel': 'ZEEL', 'zee entertainment': 'ZEEL'
    }

    import re
    def get_tickers(row):
        text = (str(row['Title']) + " " + str(row['Keywords'])).lower()
        matched = []
        for name, tk in company_map.items():
            if re.search(r'\b' + re.escape(name) + r'\b', text):
                if tk not in matched:
                    matched.append(tk)
        return matched

    news_df['mapped_tickers'] = news_df.apply(get_tickers, axis=1)
    
    # Explode so each row is one ticker-article pair
    exploded_df = news_df.explode('mapped_tickers').dropna(subset=['mapped_tickers'])
    exploded_df = exploded_df.rename(columns={'mapped_tickers': 'Ticker', 'Date': 'News_Date'})
    
    print(f"Mapped articles: {len(exploded_df)}")
    
    # 2. Analyze Sentiment
    print("Running sentiment analysis...")
    exploded_df = exploded_df.rename(columns={'Title': 'title', 'Description': 'description', 'Content': 'content'})
    sent_df = analyze_sentiment(exploded_df, text_column='title', tickers=None)
    
    # 3. Timestamp Alignment (Strict Leakage Control)
    print("Aligning timestamps...")
    # Load official trading dates per ticker
    processed_path = 'data/processed_dataset.csv'
    off_df = pd.read_csv(processed_path, usecols=['Ticker', 'Date'])
    
    # We will map each News_Date to the NEXT available Trading_Date for that Ticker.
    # Trading_Date > News_Date (strict).
    merged_rows = []
    
    # Sort official dates
    off_df['Date'] = pd.to_datetime(off_df['Date'])
    sent_df['News_Date'] = pd.to_datetime(sent_df['News_Date'])
    
    for tk, group in sent_df.groupby('Ticker'):
        tk_trading_dates = off_df[off_df['Ticker'] == tk]['Date'].sort_values().values
        
        for _, row in group.iterrows():
            nd = row['News_Date'].to_datetime64()
            # Find first trading date strictly greater than news date
            valid_dates = tk_trading_dates[tk_trading_dates > nd]
            if len(valid_dates) > 0:
                target_date = valid_dates[0]
                merged_rows.append({
                    'Ticker': tk,
                    'Target_Date': target_date,
                    'sentiment_score': row['sentiment_score'],
                    'sentiment_label': row['sentiment_label']
                })
                
    mapped_sent_df = pd.DataFrame(merged_rows)
    print(f"Articles aligned to valid trading dates: {len(mapped_sent_df)}")
    
    # 4. Aggregation
    if len(mapped_sent_df) > 0:
        aggs = mapped_sent_df.groupby(['Ticker', 'Target_Date']).agg(
            News_Count=('sentiment_score', 'count'),
            Mean_Sentiment=('sentiment_score', 'mean'),
            Positive_News=('sentiment_label', lambda x: (x == 'positive').sum()),
            Negative_News=('sentiment_label', lambda x: (x == 'negative').sum()),
            Neutral_News=('sentiment_label', lambda x: (x == 'neutral').sum())
        ).reset_index()
        
        aggs['Positive_News_Proportion'] = aggs['Positive_News'] / aggs['News_Count']
        aggs['Negative_News_Proportion'] = aggs['Negative_News'] / aggs['News_Count']
        aggs['Neutral_News_Proportion'] = aggs['Neutral_News'] / aggs['News_Count']
        
        aggs = aggs.drop(columns=['Positive_News', 'Negative_News', 'Neutral_News'])
        aggs['Target_Date'] = aggs['Target_Date'].dt.strftime('%Y-%m-%d')
    else:
        aggs = pd.DataFrame(columns=['Ticker', 'Target_Date', 'News_Count', 'Mean_Sentiment', 
                                   'Positive_News_Proportion', 'Negative_News_Proportion', 'Neutral_News_Proportion'])
        
    # Save the aggregated sentiment features
    out_dir = 'data/v1_1_sentiment'
    os.makedirs(out_dir, exist_ok=True)
    aggs.to_csv(f"{out_dir}/IN_FINews_aggregated.csv", index=False)
    print(f"Aggregated features saved to {out_dir}/IN_FINews_aggregated.csv")
    
    # 5. Merge with V1 Dataset
    print("Merging with V1 Dataset...")
    full_df = pd.read_csv('data/processed_dataset.csv')
    
    # Drop old sentiment columns if they exist to replace them cleanly for the experiment
    if 'Sentiment_Score' in full_df.columns:
        full_df = full_df.drop(columns=['Sentiment_Score', 'News_Count'])
    if 'News_Count' in full_df.columns:
        full_df = full_df.drop(columns=['News_Count'])
        
    full_df = full_df.merge(
        aggs, 
        left_on=['Ticker', 'Date'], 
        right_on=['Ticker', 'Target_Date'], 
        how='left'
    )
    
    # Handle missing
    full_df['News_Count'] = full_df['News_Count'].fillna(0)
    full_df['Mean_Sentiment'] = full_df['Mean_Sentiment'].fillna(0)
    full_df['Positive_News_Proportion'] = full_df['Positive_News_Proportion'].fillna(0)
    full_df['Negative_News_Proportion'] = full_df['Negative_News_Proportion'].fillna(0)
    full_df['Neutral_News_Proportion'] = full_df['Neutral_News_Proportion'].fillna(0)
    
    full_df = full_df.drop(columns=['Target_Date'])
    
    os.makedirs(f"{out_dir}/processed", exist_ok=True)
    full_df.to_csv(f"{out_dir}/processed/processed_dataset.csv", index=False)
    
    print("\n--- Data Quality Audit After Merge ---")
    print(f"Original V1 Rows: {len(pd.read_csv('data/processed_dataset.csv'))}")
    print(f"Merged V1.1 Rows: {len(full_df)}")
    has_news = (full_df['News_Count'] > 0).sum()
    print(f"Rows with news: {has_news} ({(has_news/len(full_df))*100:.2f}%)")
    print(f"Rows with NO news: {len(full_df) - has_news} ({((len(full_df)-has_news)/len(full_df))*100:.2f}%)")
    print(f"Duplicates (Ticker+Date): {full_df.duplicated(subset=['Ticker', 'Date']).sum()}")

if __name__ == '__main__':
    main()
