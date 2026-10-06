# IN-FINews Merge Audit

## Merge Strategy
- We used VADER sentiment analysis to compute sentiment scores for the matched IN-FINews articles.
- Sentiment was aggregated by mapping the `News_Date` to the first available `Trading_Date` where `Trading_Date > News_Date`. This enforces a strict lag of at least one day, guaranteeing no future information leakage.
- We aggregated the features: `News_Count`, `Mean_Sentiment`, `Positive_News_Proportion`, `Negative_News_Proportion`, `Neutral_News_Proportion`.
- Missing values (no news) were filled with 0 (no news count, neutral sentiment assumption).

## Row Integrity
- **Original V1 Rows**: 53,550
- **Merged V1.1 Rows**: 53,550
- **Rows lost during merge**: 0
- **Rows duplicated during merge**: 0
- **Duplicate Ticker-Date records**: 0 (The structure is exactly preserved).

## Coverage Statistics
- **Rows with news**: 1,381 (2.58%)
- **Rows with NO news**: 52,169 (97.42%)
- *Note: While the absolute coverage percentage is small across the entire multi-year historical dataset, this is expected for a small specific 6-month news dataset (Feb-Aug 2025).*

## Distribution Changes
- The target distribution and the underlying feature distributions are completely unchanged because the original V1 DataFrame was joined strictly using a left merge.
- Timestamp alignment verified successfully, ensuring no unexpected future dates were created. 

## Safe / Unsafe Features Audit
- **SAFE NEWS FEATURES**: 
  - `Title`, `Description`, `Content` (used for sentiment calculation)
  - `Date` (strictly lagged)
  - Derived features: `News_Count`, `Mean_Sentiment`, `Positive_News_Proportion`, `Negative_News_Proportion`, `Neutral_News_Proportion`.
- **UNSAFE / EXCLUDED FEATURES**:
  - The dataset contained no target-leakage features (like "future return", "target", "post-event outcome"). All original fields were purely text-based and thus naturally safe for NLP processing.

Dataset saved to: `data/v1_1_sentiment/processed/processed_dataset.csv`
