# IN-FINews Dataset Audit

## Overview
- **Number of records**: 3,348
- **Date range**: 2025-02-07 to 2025-08-21
- **Unique dates**: 173

## Schema
- **Title** (`str`): Headline of the news article.
- **Date** (`str`): Publication date in `YYYY-MM-DD` format.
- **Description** (`str`): Short description or snippet of the article.
- **Author** (`str`): Author or source publisher of the news.
- **Content** (`str`): The full text body of the news article.
- **Keywords** (`str`): Comma-separated list of keywords, often containing company names, tickers, and topics.
- **URL** (`str`): Link to the original source (moneycontrol.com).

## Fields Audit
- **Timestamp field(s)**: NOT PRESENT. The dataset only provides calendar dates (e.g., `2025-07-08`). Publication time and timezone are unavailable.
- **Stock/company field**: NOT PRESENT as a standardized individual field. The `Keywords` field contains entities, but it mixes company names, general topics, and phrases like "share price".
- **Ticker/symbol field**: NOT PRESENT.
- **Headline/title field**: `Title`.
- **Article text/body field**: `Content`.
- **Source/publisher**: Present in `Author` (e.g., "Bloomberg", "Moneycontrol News") and the `URL`.
- **Sentiment-related fields**: NONE.

## Data Quality
- **Duplicate records**: 0
- **Missing values**: 0 in all fields.
- **Company/ticker coverage**: Needs to be inferred from `Keywords` and `Title`.
- **Number of unique dates**: 173.
- **Percentage of records with usable stock identifiers**: Depends on keyword matching, but every record has a `Keywords` field.

## Sample Record
```json
{
    "Title": "Bharti Airtel share price falls 1.53%; stock among top losers on Nifty 50",
    "Date": "2025-07-18",
    "Description": "With the stock currently trading at Rs 1,900.40, Bharti Airtel is experiencing a downturn, influenced by broader market dynamics.",
    "Author": "Alpha Desk",
    "Content": "Shares of Bharti Airtel were trading lower at Rs 1,900.40...",
    "Keywords": "Bharti Airtel, shares, stock price, Nifty 50, top losers, financial performance, revenue, net profit, EPS, dividend, corporate actions",
    "URL": "https://www.moneycontrol.com/news/business/stocks/bharti-airtel-share-price-falls-1-53-stock-among-top-losers-on-nifty-50-alpha-article-13295017.html"
}
```
