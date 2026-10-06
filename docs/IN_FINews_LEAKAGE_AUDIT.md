# IN-FINews Leakage Audit

## Timestamp Availability
The `IN-FINews Dataset.json` dataset provides only the calendar date (`Date` field, formatted as `YYYY-MM-DD`) of publication.
It **does not provide**:
- Publication time
- Timezone
- Article creation timestamp
- Update timestamp

## Leakage Risk Analysis
The official ML task is to predict the stock return direction for trading day `t+1`, with the prediction being made at the end of trading day `t` (typically 3:30 PM IST). 

If a news article is published on day `t`, we only know the date, not the time. It could have been published at 10:00 AM (during market hours, available before the prediction point) or at 8:00 PM (after market close, strictly unavailable at the prediction point). 

If we were to merge day `t` news into the feature row for day `t`, we would be assuming the news was available by 3:30 PM. For after-market news (e.g., earnings releases at 5:00 PM), this would introduce look-ahead leakage because the model would be using information from 5:00 PM to make a prediction supposedly at 3:30 PM.

## Conservative Alignment Strategy
Since we cannot guarantee that news published on day `t` was available by the end of trading day `t`, we must apply a strict, conservative alignment rule to ensure zero look-ahead bias:

**Alignment Rule**: 
A news article published on calendar date `d` is only considered available for prediction at the end of trading day `t` if `d < t`.
Mathematically, the news features merged into the stock's feature row for trading day `t` will be aggregated from news articles published exactly on day `t-1`. 

(Note: To handle weekends/holidays, the safest robust logic is to aggregate news from the calendar days strictly between the previous trading day and the current trading day. But a simple, strict one-day shift—merging `News(t-1)` to `Trading_Day(t)`—is mathematically the safest baseline that guarantees no leakage.)

By strictly lagging the news by at least one calendar day relative to the trading day `t` feature row, we guarantee that all news information used was genuinely available before the prediction point at the end of day `t`.

## Conclusion
We will aggregate the sentiment of news published on date `d` and merge it with the market features of trading date `t = d + 1` (or the next available trading day). If we cannot safely align it, we will exclude the news. This strict lag ensures zero future information leakage.
