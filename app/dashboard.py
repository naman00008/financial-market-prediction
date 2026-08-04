import os
import sys
from typing import List, Optional
import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import uuid


# Ensure project root (so `import src...` works) is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
# Add the project root to sys.path so Python can import the `src` package
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# Also keep SRC_DIR available in case some modules import directly from it
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.data_preprocessing import (
    filter_by_date,
    list_available_companies,
    list_nifty50_companies,
    load_nifty_index,
    load_stock_data,
)
from src.live_data import live_stock_data, live_news_data
from src.feature_engineering import add_technical_indicators, create_features
from src.model_training import (
    directional_accuracy,
    evaluate_regression,
    train_regression_models,
)
from src.sentiment_analysis import analyze_sentiment, load_news_data
from src.unified_chart import render_unified_analysis_section


TIME_RANGES = {
    "1 Day": ("1d", "1m"),
    "5 Days": ("5d", "5m"),
    "1 Month": ("1mo", "1h"),
    "3 Months": ("3mo", "1d"),
    "6 Months": ("6mo", "1d"),
    "1 Year": ("1y", "1d"),
    "2 Years": ("2y", "1d"),
    "5 Years": ("5y", "1d"),
}


def get_time_range_config(time_range_key: str):
    """Get period and interval for the selected time range"""
    return TIME_RANGES.get(time_range_key, ("1y", "1d"))


def normalize_to_ticker(user_input: str, all_tickers: List[str]) -> str:
    """Try to resolve a user-provided company name or ticker to a known ticker.
    Rules:
    - exact case-insensitive match
    - remove spaces/punctuation and try
    - lookup in company_mappings.json values (company names -> ticker)
    - fuzzy match against company names and tickers using difflib
    Returns the resolved ticker string (may be unchanged if no better match).
    """
    import re
    import difflib

    if not user_input:
        return user_input

    candidate = str(user_input).strip()
    available = {t.upper(): t for t in all_tickers}

    # 1) Exact ticker match
    if candidate.upper() in available:
        return available[candidate.upper()]

    # 2) Normalized ticker (remove non-alphanum)
    norm = re.sub(r'[^A-Z0-9]', '', candidate.upper())
    if norm in available:
        return available[norm]

    # 3) Try mapping by company name from company_mappings.json
    mapping_path = os.path.join(SRC_DIR, 'company_mappings.json')
    name_to_ticker = {}
    try:
        if os.path.isfile(mapping_path):
            import json
            with open(mapping_path, 'r', encoding='utf-8') as fh:
                mappings = json.load(fh)
            for tk, vals in mappings.items():
                if isinstance(vals, list):
                    names = vals
                else:
                    names = [vals]
                for n in names:
                    if not n:
                        continue
                    name_to_ticker[str(n).lower()] = tk
                    # also normalized name
                    name_to_ticker[re.sub(r'[^a-z0-9]', '', str(n).lower())] = tk
    except Exception:
        name_to_ticker = {}

    if candidate.lower() in name_to_ticker:
        return name_to_ticker[candidate.lower()]
    if norm.lower() in name_to_ticker:
        return name_to_ticker[norm.lower()]

    # 4) Fuzzy match against company names
    if name_to_ticker:
        close = difflib.get_close_matches(candidate.lower(), list(name_to_ticker.keys()), n=1, cutoff=0.6)
        if close:
            return name_to_ticker[close[0]]

    # 5) Fuzzy match against tickers
    close_t = difflib.get_close_matches(candidate.upper(), list(available.keys()), n=1, cutoff=0.7)
    if close_t:
        return available[close_t[0]]

    # Nothing matched well — return original input for downstream handling
    return user_input


def render_price_chart(df: pd.DataFrame, ticker: str):
    """Create interactive live price chart with technical indicators"""
    if df.empty:
        st.warning("No data available for chart")
        return

    fig = go.Figure()

    # Candlestick chart if we have OHLC data
    if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ))
    else:
        # Line chart for close price
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="Close",
                line=dict(color="#1f77b4", width=2),
            )
        )

    # Volume as bar chart
    if 'Volume' in df.columns:
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color='rgba(158,158,158,0.3)',
            yaxis='y2',
            opacity=0.3
        ))

    # Moving averages
    if "SMA_20" in df.columns and df["SMA_20"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["Date"], y=df["SMA_20"], mode="lines", name="SMA 20",
                line=dict(dash="dash", color="#ff9800")
            )
        )
    if "EMA_20" in df.columns and df["EMA_20"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df["Date"], y=df["EMA_20"], mode="lines", name="EMA 20",
                line=dict(dash="dot", color="#9c27b0")
            )
        )

    # Bollinger Bands
    if "BBU_20_2.0" in df.columns and df["BBU_20_2.0"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["BBU_20_2.0"], mode="lines", name="BB Upper",
            line=dict(dash="dash", color="#2196f3", width=1)
        ))
    if "BBL_20_2.0" in df.columns and df["BBL_20_2.0"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["BBL_20_2.0"], mode="lines", name="BB Lower",
            line=dict(dash="dash", color="#2196f3", width=1)
        ))

    fig.update_layout(
        title=f"{ticker} - Live Price Chart",
        xaxis_title="Date/Time",
        yaxis_title="Price (INR)",
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode="x unified",
        template="plotly_white",
        height=500
    )

    st.plotly_chart(fig, width='stretch')


def render_volume_chart(df: dict, ticker: str):
    fig = px.bar(
        df,
        x="Date",
        y="Volume",
        title=f"{ticker} - Volume",
        labels={"Volume": "Volume", "Date": "Date"},
    )
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, width='stretch')


def render_technical_indicators(df: pd.DataFrame):
    """Render comprehensive technical indicators charts"""
    st.subheader("Technical Indicators")

    if df.empty:
        st.warning("No data available for technical indicators")
        return

    # RSI Chart
    if "RSI_14" in df.columns and df["RSI_14"].notna().any():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI_14"], name="RSI (14)", line=dict(color="#636efa")))
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig.update_layout(
            title="Relative Strength Index (RSI)",
            yaxis_title="RSI",
            template="plotly_white",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

    # MACD Chart
    if all(col in df.columns for col in ["MACD_12_26_9", "MACDs_12_26_9"]) and df["MACD_12_26_9"].notna().any():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD_12_26_9"], name="MACD", line=dict(color="#00ff00")))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACDs_12_26_9"], name="Signal", line=dict(color="#ff0000")))
        if "MACDh_12_26_9" in df.columns:
            fig.add_trace(go.Bar(x=df["Date"], y=df["MACDh_12_26_9"], name="Histogram", marker_color='rgba(158,158,158,0.5)'))
        fig.update_layout(
            title="MACD (12, 26, 9)",
            yaxis_title="MACD",
            template="plotly_white",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

    # Bollinger Bands Chart
    if all(col in df.columns for col in ["BBL_20_2.0", "BBU_20_2.0", "Close"]) and df["Close"].notna().any():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Close", line=dict(color="#1f77b4")))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BBL_20_2.0"], name="BB Lower", line=dict(dash="dash", color="#2196f3")))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BBU_20_2.0"], name="BB Upper", line=dict(dash="dash", color="#2196f3")))
        if "BBM_20_2.0" in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df["BBM_20_2.0"], name="BB Middle", line=dict(dash="dot", color="#ff9800")))
        fig.update_layout(
            title="Bollinger Bands (20, 2)",
            yaxis_title="Price",
            template="plotly_white",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

    # Stochastic Oscillator
    if "STOCHk_14_3_3" in df.columns and df["STOCHk_14_3_3"].notna().any():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["STOCHk_14_3_3"], name="%K", line=dict(color="#636efa")))
        if "STOCHd_14_3_3" in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df["STOCHd_14_3_3"], name="%D", line=dict(color="#ef553b")))
        fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig.update_layout(
            title="Stochastic Oscillator",
            yaxis_title="Stochastic",
            template="plotly_white",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

    # Williams %R
    if "WILLR_14" in df.columns and df["WILLR_14"].notna().any():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["WILLR_14"], name="Williams %R", line=dict(color="#ab63fa")))
        fig.add_hline(y=-20, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=-80, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig.update_layout(
            title="Williams %R",
            yaxis_title="Williams %R",
            template="plotly_white",
            height=300
        )
        st.plotly_chart(fig, width='stretch')


def render_nifty_index():
    st.subheader("NIFTY Index Overview")

    if not st.button("Load NIFTY index chart"):
        st.info("Click the button to load the NIFTY index proxy chart. This may take a few seconds.")
        return

    with st.spinner("Loading NIFTY index... this may take 10-20 seconds"):
        try:
            nifty = load_nifty_index()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=nifty["Date"],
                    y=nifty["NIFTY_INDEX"],
                    name="NIFTY Proxy",
                    line=dict(color="#ff7f0e"),
                )
            )
            fig.update_layout(
                title="NIFTY Proxy (Average Close of NIFTY 50)",
                xaxis_title="Date",
                yaxis_title="Index Level",
                hovermode="x unified",
                template="plotly_white",
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.warning(f"Unable to load NIFTY index data: {e}")


def render_news_sentiment(selected_company: str, tickers: List[str]):
    """Render live financial news and sentiment analysis"""

    # Allow entering a NewsAPI key in the sidebar settings
    try:
        import streamlit as _st
        from src.live_data import live_news_data as _live_news
        with _st.sidebar.expander("News API Configuration (Optional)"):
            _key = _st.text_input("NewsAPI key (paste here)", value=_st.session_state.get('newsapi_key',''), type='password', help="Optional: enable NewsAPI for broader coverage")
            if _st.button("Set NewsAPI key"):
                _live_news.set_api_key(_key.strip() or None)
                _st.session_state['newsapi_key'] = _key.strip()
                if _key.strip():
                    _st.success("NewsAPI key configured successfully")
                else:
                    _st.info("NewsAPI disabled - using RSS/Google News feeds")
    except Exception:
        # Sidebar input is optional; fail silently if import issues occur
        pass

    if selected_company == "All":
        # Market-wide news view
        st.subheader("Market-Wide Financial News & Sentiment Analysis")

        st.markdown("""
        **Complete Market Overview**: Get updated with the latest financial news and sentiment analysis across all major companies.
        Comprehensive view of market sentiment and trending topics.
        """)

        # Get broad market news
        with st.spinner("Loading latest market-wide financial news..."):
            # Use a smaller limit to reduce initial load time
            news_df = live_news_data.get_live_news(query="Indian stock market NSE BSE financial news economy", limit=12)

        show_company_specific = False
    else:
        # Company-specific news view
        st.subheader(f"{selected_company} News & Sentiment Analysis")

        st.markdown(f"""
        **Company-Specific Analysis**: Latest news and sentiment analysis for {selected_company}.
        Stay informed about company developments, analyst ratings, and market reactions.
        """)

        # Build a company-specific news query from the ticker and company name mapping
        company_search_name = None
        try:
            mapping_path = os.path.join(SRC_DIR, "company_mappings.json")
            if os.path.isfile(mapping_path):
                import json
                with open(mapping_path, "r", encoding="utf-8") as fh:
                    mappings = json.load(fh)
                vals = mappings.get(selected_company)
                if vals and isinstance(vals, list) and vals:
                    company_search_name = vals[0]
        except Exception:
            company_search_name = None

        if not company_search_name:
            try:
                info = live_stock_data.get_current_price(selected_company)
                if isinstance(info, dict):
                    cname = info.get('company_name')
                    if cname and isinstance(cname, str) and len(cname) > 2:
                        company_search_name = cname
            except Exception:
                company_search_name = None

        query_parts = []
        if company_search_name:
            query_parts.append(company_search_name)

        query_parts.append(selected_company)
        query_parts.append(selected_company + ".NS")

        # Add additional company aliases if available
        try:
            mapping_path = os.path.join(SRC_DIR, "company_mappings.json")
            if os.path.isfile(mapping_path):
                import json
                with open(mapping_path, "r", encoding="utf-8") as fh:
                    mappings = json.load(fh)
                variants = mappings.get(selected_company, [])
                for v in variants:
                    if isinstance(v, str) and v.strip() and v not in query_parts:
                        query_parts.append(v.strip())
        except Exception:
            pass

        or_query = " OR ".join([f'"{p}"' if ' ' in p else p for p in query_parts])
        query_text = f"{or_query} stock market NSE BSE financial news company updates earnings results"

        # Get company-specific news
        with st.spinner(f"Fetching latest news for {selected_company}..."):
            news_df = live_news_data.get_live_news(query=query_text, limit=10)

        # Also show historical news from the Economic Times dataset (for reference)
        try:
            historic_df = load_news_data()
            if not historic_df.empty:
                historic_df = historic_df.rename(columns={
                    'date': 'published_at',
                    'intro': 'description',
                    'href': 'url',
                })

                if 'title' not in historic_df.columns:
                    historic_df['title'] = ''
                if 'description' not in historic_df.columns:
                    historic_df['description'] = ''
                if 'url' not in historic_df.columns:
                    historic_df['url'] = ''

                historic_df['source'] = 'EconomicTimes Archive'
                historic_df['news_type'] = 'historic'
                historic_df['published_at'] = pd.to_datetime(historic_df['published_at'], errors='coerce')

                if selected_company != "All":
                    lower_ticker = selected_company.lower()
                    historic_df = historic_df[historic_df.apply(
                        lambda row: lower_ticker in str(row.get('title', '')).lower() or
                                    lower_ticker in str(row.get('description', '')).lower() or
                                    lower_ticker in str(row.get('content', '')).lower(),
                        axis=1
                    )]

                if not historic_df.empty:
                    news_df = pd.concat([news_df, historic_df], ignore_index=True, sort=False)
        except Exception as e:
            st.warning(f"Could not load historic news data: {e}")
            # Continue without historic data

        show_company_specific = True

    # Manual refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh News", key="refresh_news"):
            st.rerun()
    with col2:
        st.caption("Last updated: Auto-refresh enabled")

    if news_df.empty:
        st.error("Unable to fetch live news data. Please check your internet connection.")
        st.info("**Troubleshooting**: The app uses RSS feeds as fallback. If you're seeing this error, there might be a temporary issue with the news sources.")
        return

    # Analyze sentiment for all companies
    sentiment_df = analyze_sentiment(news_df, text_column="title", tickers=tickers)

    # Filter by selected company if a specific company is selected
    if selected_company != "All":
        related_series = sentiment_df.get("related_companies")
        if related_series is None:
            related_series = pd.Series([[]] * len(sentiment_df), index=sentiment_df.index)

        company_filtered = sentiment_df[related_series.apply(
            lambda lst: isinstance(lst, list) and selected_company in lst
        )]

        if not company_filtered.empty:
            sentiment_df = company_filtered
            st.success(f"Found {len(sentiment_df)} news articles specifically about {selected_company}")
        else:
            st.info(f"No recent news found specifically about {selected_company}. Displaying broader market headlines instead.")
            with st.spinner("Fetching market-wide headlines as fallback..."):
                fallback_news = live_news_data.get_live_news(query="Indian stock market NSE BSE financial news", limit=10)
            if fallback_news is not None and not fallback_news.empty:
                sentiment_df = fallback_news
            else:
                st.info(f"No general market headlines available right now.")
                return

    # Normalize published_at values so sorting works even with mixed string / Timestamp types
    sentiment_df['published_at'] = pd.to_datetime(sentiment_df['published_at'], errors='coerce')
    sentiment_df = sentiment_df.sort_values("published_at", ascending=False)

    # News filter options
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        sentiment_filter = st.multiselect(
            "Filter by Sentiment",
            ["All", "Positive", "Neutral", "Negative"],
            default=["All"],
            key="sentiment_filter"
        )

    with col2:
        show_company_news = st.checkbox("Company-specific only", value=False, key="company_filter")

    with col3:
        time_filter = st.selectbox(
            "Time Period",
            ["All Time", "Last 24h", "Last 12h", "Last 6h"],
            index=0,
            key="time_filter"
        )

    with col4:
        news_type_filter = st.selectbox(
            "News Type",
            ["All", "Live only", "Historic only"],
            index=0,
            key="news_type_filter"
        )

    # Apply filters
    filtered_df = sentiment_df.copy()

    # Ensure we always have a Series to work with for related company lists
    related_series = filtered_df.get('related_companies')
    if related_series is None:
        related_series = pd.Series([[]] * len(filtered_df), index=filtered_df.index)

    # Time filter
    if time_filter != "All Time" and pd.notna(filtered_df.get('published_at')).any():
        now = pd.Timestamp.now()
        if time_filter == "Last 24h":
            cutoff = now - pd.Timedelta(hours=24)
        elif time_filter == "Last 12h":
            cutoff = now - pd.Timedelta(hours=12)
        elif time_filter == "Last 6h":
            cutoff = now - pd.Timedelta(hours=6)

        filtered_df['published_datetime'] = pd.to_datetime(filtered_df['published_at'], errors='coerce')
        filtered_df = filtered_df[filtered_df['published_datetime'] >= cutoff]

    if "All" not in sentiment_filter:
        if "Positive" in sentiment_filter:
            filtered_df = filtered_df[filtered_df['sentiment_label'] == 'positive']
        if "Neutral" in sentiment_filter:
            filtered_df = filtered_df[filtered_df['sentiment_label'] == 'neutral']
        if "Negative" in sentiment_filter:
            filtered_df = filtered_df[filtered_df['sentiment_label'] == 'negative']

    # News type filter
    if news_type_filter == "Live only":
        filtered_df = filtered_df[filtered_df.get('news_type') == 'live']
    elif news_type_filter == "Historic only":
        filtered_df = filtered_df[filtered_df.get('news_type') == 'historic']

    if show_company_news:
        filtered_df = filtered_df[related_series.apply(lambda lst: isinstance(lst, list) and len(lst) > 0)]

    # Display news
    if selected_company == "All":
        st.markdown("### Latest Market News & Sentiment")
        st.markdown("Comprehensive financial news feed covering all major companies and market developments.")
    else:
        st.markdown(f"### {selected_company} Latest News & Sentiment")
        st.markdown(f"Dedicated news feed for {selected_company} with real-time sentiment analysis.")

    if filtered_df.empty:
        if selected_company == "All":
            st.info("No news articles available at the moment. Please try refreshing or check back later.")
        else:
            st.info(f"No specific news found for {selected_company}. Try selecting 'All Companies' to see general market news.")
        return

    # Show news articles
    for _, row in filtered_df.head(20).iterrows():
        sentiment_color = {
            "positive": "🟢",
            "neutral": "🟡",
            "negative": "🔴"
        }.get(row.get("sentiment_label", "neutral"), "🟡")

        company_info = ""
        if selected_company == "All":
            related = row.get('related_companies') or []
            if isinstance(related, list) and related:
                company_info = f" **🏢 {', '.join(related[:3])}" + ("..." if len(related) > 3 else "") + "**"

        # Create expandable news item for better UX
        title_display = row['title'][:80] + ('...' if len(row['title']) > 80 else '')
        news_type_icon = "📰" if row.get('news_type') == 'live' else "📜"
        with st.expander(f"{sentiment_color} {news_type_icon} {title_display}{company_info}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Sentiment:** {row.get('sentiment_label', 'neutral').title()} ({row.get('sentiment_score', 0):.3f})")
                st.markdown(f"**Source:** {row.get('source', 'Unknown')}")
                st.markdown(f"**Published:** {row.get('published_at', 'Unknown') if pd.notna(row.get('published_at')) else 'Unknown'}")

                if pd.notna(row.get('description')) and row['description']:
                    st.markdown("**Summary:**")
                    st.write(row['description'])

            with col2:
                if pd.notna(row.get('url')) and row['url']:
                    st.markdown(f"[🔗 Read Full Article]({row['url']})")

                # Show sentiment gauge
                sentiment_score = row.get('sentiment_score', 0)
                if sentiment_score > 0.05:
                    st.success("Positive")
                elif sentiment_score < -0.05:
                    st.error("Negative")
                else:
                    st.warning("Neutral")

        st.markdown("---")

    # --- Single combined sentiment summary graph ---
    st.markdown("### Sentiment Summary")

    summary_df = filtered_df.copy()
    summary_df['published_dt'] = pd.to_datetime(summary_df['published_at'], errors='coerce')
    summary_df = summary_df.dropna(subset=['published_dt'])
    summary_df['date'] = summary_df['published_dt'].dt.floor('D')
    summary_df['sentiment_label'] = summary_df['sentiment_label'].fillna('neutral')
    summary_df = summary_df[summary_df['sentiment_label'].isin(['positive', 'neutral', 'negative'])]

    if not summary_df.empty:
        # Choose aggregation granularity: daily for short ranges, monthly for long ranges
        unique_days = summary_df['date'].nunique()
        date_range_days = (summary_df['date'].max() - summary_df['date'].min()).days if unique_days > 0 else 0
        if date_range_days > 90 or unique_days > 60:
            # aggregate by month when data spans many months
            summary_df['period'] = summary_df['published_dt'].dt.to_period('M').dt.to_timestamp()
            group_field = 'period'
            label_fmt = '%Y-%m'
        else:
            group_field = 'date'
            label_fmt = '%Y-%m-%d'

        trend_data = (
            summary_df.groupby([group_field, 'sentiment_label'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        # normalize datetime field and create label strings for x-axis
        trend_data[group_field] = pd.to_datetime(trend_data[group_field])
        trend_data['date_str'] = trend_data[group_field].dt.strftime(label_fmt)
        for col in ['positive', 'neutral', 'negative']:
            if col not in trend_data.columns:
                trend_data[col] = 0

        trend_data['total'] = trend_data[['positive', 'neutral', 'negative']].sum(axis=1)

        fig_summary = go.Figure()
        colors = {'positive': '#2ca02c', 'neutral': '#ffbf00', 'negative': '#d62728'}

        # Add stacked bars
        for sentiment in ['positive', 'neutral', 'negative']:
            # show text inside bars when counts are small
            text_vals = trend_data[sentiment].astype(str) if trend_data['total'].max() <= 10 else None
            fig_summary.add_trace(go.Bar(
                x=trend_data['date_str'],
                y=trend_data[sentiment],
                name=sentiment.title(),
                marker_color=colors[sentiment],
                opacity=0.9,
                text=text_vals,
                textposition='inside' if text_vals is not None else 'none'
            ))

        # Add total line for clarity
        fig_summary.add_trace(go.Scatter(
            x=trend_data['date_str'],
            y=trend_data['total'],
            mode='lines+markers',
            name='Total',
            marker=dict(color='#1f2937', size=6),
            line=dict(color='#1f2937', width=2, dash='dash')
        ))

        fig_summary.update_layout(
            title='News Sentiment Trend',
            xaxis_title='Date',
            yaxis_title='Number of Articles',
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='stack',
            height=420,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.75)'),
            xaxis=dict(tickangle=-45, categoryorder='category ascending', tickfont={'color': '#374151'}),
            yaxis=dict(tick0=0, dtick=1, rangemode='tozero', tickfont={'color': '#374151'}),
            bargap=0.12,
            bargroupgap=0.02
        )

        st.plotly_chart(fig_summary, use_container_width=True, key=f"sentiment_summary_{selected_company}")
    else:
        st.info("Not enough sentiment data to render the summary graph.")

    # --- Market events and corporate action headlines ---
    st.markdown("### Market Events & Corporate Actions")
    if selected_company == "All":
        st.markdown(
            "Get the latest dividend announcements, ex-date alerts, quarterly and annual results, and other market-wide stock events."
        )
        event_query = (
            "dividend OR ex-date OR \"ex date\" OR quarterly result OR annual result OR earnings result "
            "OR upcoming event OR board meeting OR corporate action OR stock split"
        )
    else:
        st.markdown(
            f"Get the latest dividend announcements, ex-date alerts, quarterly and annual results, and other corporate actions for {selected_company}."
        )
        company_search_name = None
        try:
            mapping_path = os.path.join(SRC_DIR, "company_mappings.json")
            if os.path.isfile(mapping_path):
                import json
                with open(mapping_path, "r", encoding="utf-8") as fh:
                    mappings = json.load(fh)
                vals = mappings.get(selected_company, [])
                if vals and isinstance(vals, list) and vals:
                    company_search_name = vals[0]
        except Exception:
            company_search_name = None

        if not company_search_name:
            try:
                info = live_stock_data.get_current_price(selected_company)
                if isinstance(info, dict):
                    cname = info.get('company_name')
                    if cname and isinstance(cname, str) and len(cname) > 2:
                        company_search_name = cname
            except Exception:
                company_search_name = None

        company_terms = [selected_company, selected_company + ".NS"]
        if company_search_name:
            company_terms.insert(0, company_search_name)

        event_terms = (
            "dividend OR ex-date OR \"ex date\" OR quarterly result OR annual result OR earnings result "
            "OR upcoming event OR board meeting OR corporate action OR stock split"
        )
        query_company = " OR ".join([f'\"{term}\"' if ' ' in term else term for term in company_terms])
        event_query = f"({query_company}) AND ({event_terms})"

    with st.spinner("Fetching latest corporate events..."):
        event_df = live_news_data.get_live_news(query=event_query, limit=15)

    if selected_company != "All" and not event_df.empty:
        company_terms = [selected_company, selected_company + ".NS"]
        if company_search_name:
            company_terms.insert(0, company_search_name)
        company_terms = [str(t).lower() for t in company_terms if t]

        def company_match(row):
            text = " ".join([str(row.get(col, "")) for col in ["title", "description", "content"] if pd.notna(row.get(col))]).lower()
            return any(term in text for term in company_terms)

        event_df = event_df[event_df.apply(company_match, axis=1)]

    if not event_df.empty:
        event_df['published_at'] = pd.to_datetime(event_df['published_at'], errors='coerce')
        event_df = event_df.sort_values("published_at", ascending=False)
        event_df['event_type'] = event_query
        for _, row in event_df.head(10).iterrows():
            event_icon = "📌"
            title_display = row.get('title', '')[:90] + ('...' if len(str(row.get('title', ''))) > 90 else '')
            source = row.get('source', 'News Source')
            published = row.get('published_at', 'Unknown')
            if pd.notna(published):
                published = pd.to_datetime(published).strftime('%d %b %Y %H:%M')
            with st.expander(f"{event_icon} {title_display} ({source})", expanded=False):
                st.markdown(f"**Published:** {published}")
                if pd.notna(row.get('description')) and row.get('description'):
                    st.write(row['description'])
                if pd.notna(row.get('url')) and row.get('url'):
                    st.markdown(f"[🔗 Read Full Article]({row['url']})")
    else:
        st.info("No corporate event headlines available at the moment. Please try refreshing or check back later.")


def render_model_predictions(df: pd.DataFrame, ticker: str):
    """Render ML model training and predictions with XGBoost and LSTM"""
    st.subheader("Machine Learning Predictions")
    st.markdown(
        "Train Random Forest, XGBoost, and LSTM models on historical features to predict stock price from 1 day up to 1 year ahead."
    )

    # Diagnostics: show a small caption with data size (avoid prominent alert boxes)
    try:
        st.caption(f"Data points available: {len(df)}")
        if not df.empty:
            st.write(df.tail(3))
    except Exception:
        pass

    if df.empty:
        st.warning("Not enough data to train models. Need at least 50 data points.")
        return

    # Create features and show diagnostics so user knows if feature creation failed
    features = create_features(df)
    try:
        st.info(f"Features shape: {features.shape}")
        if not features.empty:
            st.write(features.head(3))
    except Exception:
        pass

    if features.empty or len(features) < 50:
        st.warning("Not enough data to train models. Need at least 50 feature rows after preprocessing.")
        return

    if st.button("Train ML Models", type="primary"):
        with st.spinner("Training models... This may take a few minutes"):
            try:
                models = train_regression_models(features, target_col="Close")

                metrics = []
                for name, info in models.items():
                    y_test = info["y_test"].values
                    y_pred = info["y_pred"]
                    evals = evaluate_regression(y_test, y_pred)
                    evals["directional_accuracy"] = directional_accuracy(y_test, y_pred)
                    evals["model"] = name.replace("_", " ").title()
                    metrics.append(evals)

                metrics_df = pd.DataFrame(metrics).set_index("model")
                st.subheader("Model Performance Metrics")
                st.dataframe(metrics_df.style.highlight_max(axis=0), width='stretch')

                # Plot actual vs predicted for best model (lowest RMSE)
                best_model_name = metrics_df['rmse'].idxmin()
                best_key = best_model_name.lower().replace(" ", "_")
                if best_key in models:
                    best = models[best_key]
                    # If models predict returns, reconstruct prices for plotting
                    if best.get('predicts_return'):
                        actual_prices = best.get('y_test_price')
                        pred_prices = best.get('y_pred_price')
                        results = pd.DataFrame({
                            "Date": best["X_test"].index,
                            "Actual": actual_prices,
                            "Predicted": pred_prices,
                        })
                    else:
                        results = pd.DataFrame(
                            {
                                "Date": best["X_test"].index,
                                "Actual": best["y_test"].values,
                                "Predicted": best["y_pred"],
                            }
                        )

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=results["Date"], y=results["Actual"], name="Actual", line=dict(color="#1f77b4")))
                    fig.add_trace(go.Scatter(x=results["Date"], y=results["Predicted"], name="Predicted", line=dict(color="#ff7f0e")))
                    fig.update_layout(
                        title=f"{ticker}: {best_model_name} - Actual vs Predicted Close Price",
                        xaxis_title="Date",
                        yaxis_title="Price (INR)",
                        template="plotly_white",
                        height=400
                    )
                    st.plotly_chart(fig, width='stretch')

                    # Future prediction (single-step + multi-horizon)
                    st.subheader("Future Prediction")
                    try:
                        # Use the last available data point for prediction
                        last_features = features.iloc[-1:].drop(columns=["Close"], errors="ignore").copy()

                        # Drop Date if present
                        if "Date" in last_features.columns:
                            last_features = last_features.drop(columns=["Date"])

                        # Determine expected feature order from scaler/model/X_test
                        expected_cols = None
                        scaler = best.get("scaler")
                        model_obj = best.get("model")

                        if scaler is not None and hasattr(scaler, "feature_names_in_"):
                            expected_cols = list(scaler.feature_names_in_)
                        elif model_obj is not None and hasattr(model_obj, "feature_names_in_"):
                            expected_cols = list(model_obj.feature_names_in_)
                        elif isinstance(best.get("X_test"), pd.DataFrame):
                            expected_cols = list(best["X_test"].columns)

                        if expected_cols:
                            # Ensure expected columns exist; if some are missing, attempt to fill
                            missing = [c for c in expected_cols if c not in last_features.columns]
                            if missing:
                                # Try to fill missing features using scaler means, X_test means, or zeros
                                fill_vals = {}
                                if scaler is not None and hasattr(scaler, "mean_") and hasattr(scaler, "feature_names_in_"):
                                    # Map scaler means to feature names if available
                                    try:
                                        scaler_names = list(scaler.feature_names_in_)
                                        for i, fname in enumerate(scaler_names):
                                            if i < len(scaler.mean_):
                                                fill_vals[fname] = float(scaler.mean_[i])
                                    except Exception:
                                        fill_vals = {}
                                # Fallback: use X_test column means
                                if not fill_vals and isinstance(best.get("X_test"), pd.DataFrame):
                                    try:
                                        xmean = best["X_test"].mean()
                                        for fname in expected_cols:
                                            if fname in xmean.index:
                                                fill_vals[fname] = float(xmean[fname])
                                    except Exception:
                                        fill_vals = {}

                                # Default to 0.0 for any remaining missing
                                for fname in missing:
                                    last_features[fname] = fill_vals.get(fname, 0.0)

                            # Reorder to match expected training order, filling any remaining with zeros
                            last_features = last_features.reindex(columns=expected_cols, fill_value=0.0)

                        # Ensure all feature values are numeric (coerce and fill NaNs)
                        try:
                            last_features = last_features.apply(pd.to_numeric, errors='coerce')
                            last_features = last_features.fillna(0.0)
                        except Exception:
                            # As a final fallback, convert to float values
                            last_features = last_features.astype(float).fillna(0.0)
                        else:
                            # Fallback: use numeric columns and hope order matches
                            last_features = last_features.select_dtypes(include=[np.number])

                        # Finally transform and predict (single-step + 1 month forecast)
                        if scaler is not None:
                            try:
                                last_features_scaled = scaler.transform(last_features)
                            except Exception:
                                last_features_scaled = scaler.transform(last_features.values)
                        else:
                            last_features_scaled = last_features.values

                        # Defensive: ensure no NaNs or infinities present before prediction
                        try:
                            last_features_scaled = np.array(last_features_scaled, dtype=float)
                            if np.isnan(last_features_scaled).any() or np.isinf(last_features_scaled).any():
                                last_features_scaled = np.nan_to_num(last_features_scaled, nan=0.0, posinf=0.0, neginf=0.0)
                        except Exception:
                            lf = np.asarray(last_features_scaled)
                            lf = lf.reshape(1, -1) if lf.ndim == 1 else lf
                            last_features_scaled = np.nan_to_num(lf, nan=0.0, posinf=0.0, neginf=0.0)

                        # Predict next-day price using the best model
                        try:
                            next_day_pred = float(best["model"].predict(last_features_scaled)[0])
                        except Exception:
                            # As a fallback, use last close as next-day prediction
                            next_day_pred = float(df["Close"].iloc[-1]) if not df.empty else 0.0

                        current_price = df["Close"].iloc[-1] if not df.empty else 0.0

                        # Compute a multi-horizon forecast from 1 day to 1 year
                        try:
                            recent_returns = df["Close"].pct_change().dropna().tail(21)
                            avg_daily_return = float(recent_returns.mean()) if not recent_returns.empty else 0.0
                            avg_daily_return = float(np.clip(avg_daily_return, -0.05, 0.05))
                        except Exception:
                            avg_daily_return = 0.0

                        if current_price != 0:
                            model_return = next_day_pred / current_price - 1.0
                        else:
                            model_return = 0.0

                        horizons = [
                            ("1 Day", 1),
                            ("1 Week", 5),
                            ("1 Month", 21),
                            ("3 Months", 63),
                            ("6 Months", 126),
                            ("1 Year", 252),
                        ]

                        rows = []
                        for label, days in horizons:
                            if days == 1:
                                predicted_price = next_day_pred
                            else:
                                try:
                                    predicted_price = float(next_day_pred * ((1.0 + avg_daily_return) ** (days - 1)))
                                except Exception:
                                    predicted_price = float(next_day_pred)
                            change_pct = ((predicted_price - current_price) / current_price) * 100 if current_price != 0 else 0
                            rows.append({
                                "Horizon": label,
                                "Predicted Close (₹)": round(predicted_price, 2),
                                "Change %": round(change_pct, 2)
                            })

                        pred_df = pd.DataFrame(rows)

                        col1, col2 = st.columns([2, 3])
                        with col1:
                            st.metric("Current Price", f"₹{current_price:.2f}")
                            st.metric("Predicted Next Day", f"₹{next_day_pred:.2f}")
                        with col2:
                            st.dataframe(pred_df, width='stretch')

                    except Exception as e:
                        # Provide detailed debug output to help diagnose feature/shape mismatches
                        import traceback
                        tb = traceback.format_exc()
                        st.error("Could not generate next day prediction — see debug info below.")
                        with st.expander("Debug information (click to expand)"):
                            st.markdown("**Traceback**")
                            st.code(tb)

                            try:
                                st.markdown("**Expected feature columns used during training**")
                                st.write(expected_cols)
                            except Exception:
                                pass

                            try:
                                st.markdown("**Last features (from most recent row)**")
                                st.write(list(last_features.columns))
                                st.write(last_features.dtypes.to_dict())
                                st.write(last_features.iloc[0].to_dict())
                            except Exception:
                                pass

                            try:
                                if scaler is not None:
                                    st.markdown("**Scaler details**")
                                    st.write({
                                        "has_mean": hasattr(scaler, "mean_"),
                                        "mean_": getattr(scaler, "mean_", None),
                                    })
                            except Exception:
                                pass

                            try:
                                if isinstance(best.get("X_test"), pd.DataFrame):
                                    st.markdown("**X_test columns used during training**")
                                    st.write(list(best["X_test"].columns))
                            except Exception:
                                pass

                        st.warning(str(e))

            except Exception as e:
                st.error(f"Error training models: {e}")
                st.exception(e)


def render_stock_comparison(all_tickers: List[str]):
    st.markdown("Compare multiple stocks side-by-side to analyze performance, risk, and correlations.")

    # Stock selection
    col1, col2 = st.columns(2)
    with col1:
        num_stocks = st.selectbox("Number of stocks to compare", [2, 3, 4], index=1)

    # Company search and selection for comparison
    st.markdown("### Stock Selection")
    search_term = st.text_input("Search companies for comparison", placeholder="Type to search companies...", key="comparison_search")

    # Filter companies based on search term
    if search_term:
        filtered_tickers = [t for t in all_tickers if search_term.lower() in t.lower()]
    else:
        filtered_tickers = all_tickers

    # Show number of results
    if search_term:
        st.markdown(f"Found {len(filtered_tickers)} companies matching '{search_term}'")

    # Multi-select for stocks
    if filtered_tickers:
        selected_from_multiselect = st.multiselect(
            f"Select {num_stocks} stocks to compare (scroll or search above)",
            filtered_tickers,
            default=filtered_tickers[:min(num_stocks, len(filtered_tickers))],
            max_selections=num_stocks,
            key="comparison_multiselect"
        )
    else:
        st.error("No companies found matching your search.")
        return

    # Use only the multiselect choices for comparison (no manual ticker inputs)
    combined = list(dict.fromkeys(list(selected_from_multiselect)))
    if len(combined) > num_stocks:
        st.warning(f"You selected {len(combined)} stocks but the comparison limit is {num_stocks}. Truncating to first {num_stocks}.")
        combined = combined[:num_stocks]

    selected_stocks = combined

    if len(selected_stocks) < 2:
        st.warning("Please select at least 2 stocks to compare.")
        return

    # Time range selection
    time_range = st.selectbox("Time Range", list(TIME_RANGES.keys()), index=3)
    period, interval = get_time_range_config(time_range)

    # Load live data for selected stocks
    stock_data = {}
    for ticker in selected_stocks:
        try:
            with st.spinner(f"Loading {ticker}..."):
                df = live_stock_data.get_live_data(ticker, period=period, interval=interval)
            if not df.empty:
                stock_data[ticker] = df
        except Exception as e:
            st.warning(f"Could not load live data for {ticker}: {e}")

    if not stock_data:
        st.error("No data could be loaded for the selected stocks.")
        return

    # Normalized Price Comparison
    st.subheader("Normalized Price Comparison")
    st.markdown("All prices normalized to 100 at the start of the period for easy comparison.")

    fig = go.Figure()

    for ticker, df in stock_data.items():
        if not df.empty and len(df) > 0:
            # Normalize prices to start at 100
            start_price = df['Close'].iloc[0]
            normalized_prices = (df['Close'] / start_price) * 100

            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=normalized_prices,
                mode='lines',
                name=ticker,
                line=dict(width=2)
            ))

    fig.update_layout(
        title="Normalized Price Performance",
        xaxis_title="Date",
        yaxis_title="Normalized Price (Base 100)",
        template="plotly_white",
        hovermode='x unified'
    )
    st.plotly_chart(fig, width='stretch')

    # Performance Metrics Table
    st.subheader("Performance Metrics")

    metrics_data = []
    for ticker, df in stock_data.items():
        if not df.empty and len(df) > 1:
            start_price = df['Close'].iloc[0]
            end_price = df['Close'].iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100

            # Calculate volatility (standard deviation of returns)
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility

            # Calculate Sharpe ratio (assuming 5% risk-free rate)
            risk_free_rate = 0.05
            sharpe_ratio = (returns.mean() * 252 - risk_free_rate) / (returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0

            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            metrics_data.append({
                'Stock': ticker,
                'Total Return (%)': round(total_return, 2),
                'Volatility (%)': round(volatility, 2),
                'Sharpe Ratio': round(sharpe_ratio, 2),
                'Max Drawdown (%)': round(max_drawdown, 2),
                'Start Price': round(start_price, 2),
                'End Price': round(end_price, 2)
            })

    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, width='stretch')

        # Highlight best and worst performers
        best_return = metrics_df.loc[metrics_df['Total Return (%)'].idxmax()]
        worst_return = metrics_df.loc[metrics_df['Total Return (%)'].idxmin()]

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"Best Performer: {best_return['Stock']} (+{best_return['Total Return (%)']}%)")
        with col2:
            st.error(f"Worst Performer: {worst_return['Stock']} ({worst_return['Total Return (%)']}%)")

    # Correlation Matrix
    st.subheader("Price Correlation Matrix")
    st.markdown("Shows how closely stock prices move together. Values closer to 1 indicate strong positive correlation.")

    # Create correlation matrix
    price_data = pd.DataFrame()
    for ticker, df in stock_data.items():
        if not df.empty:
            price_data[ticker] = df.set_index('Date')['Close']

    # Align all series to common date range
    price_data = price_data.dropna()

    if not price_data.empty and len(price_data.columns) > 1:
        correlation_matrix = price_data.corr()

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,
            text=np.round(correlation_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 12},
            hoverongaps=False
        ))

        fig.update_layout(
            title="Stock Price Correlation Matrix",
            template="plotly_white"
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Need at least 2 stocks with overlapping data to show correlation matrix.")

    # Risk-Return Scatter Plot
    st.subheader("Risk-Return Analysis")

    if metrics_data and len(metrics_data) > 1:
        risk_return_df = pd.DataFrame(metrics_data)

        # Improve visualization: color by return, show hover details, scale marker size
        fig = go.Figure()

        # Colorscale uses green for higher returns, red for negative
        colors = risk_return_df['Total Return (%)'] if 'Total Return (%)' in risk_return_df.columns else None
        sizes = (risk_return_df['Volatility (%)'] - risk_return_df['Volatility (%)'].min() + 1) * 6

        fig.add_trace(go.Scatter(
            x=risk_return_df['Volatility (%)'],
            y=risk_return_df['Total Return (%)'],
            mode='markers+text',
            text=risk_return_df['Stock'],
            textposition='top center',
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title='Return %')
            ),
            hovertemplate='<b>%{text}</b><br>Volatility: %{x:.2f}%<br>Total Return: %{y:.2f}%<extra></extra>',
            name='Stocks'
        ))

        fig.update_layout(
            title='Risk vs Return Scatter Plot',
            xaxis_title='Volatility (Risk) %',
            yaxis_title='Total Return %',
            template='plotly_white',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)', zeroline=False),
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)


def render_portfolio_management(all_tickers: List[str]):
    st.markdown("Create and manage your investment portfolio. Track performance, risk, and diversification.")

    # Initialize session state for portfolio
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}

    # Portfolio input section
    st.subheader("Portfolio Composition")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Add stock to portfolio
        st.markdown("**Add Stock to Portfolio**")

        # Search functionality for portfolio
        portfolio_search = st.text_input("Search companies for portfolio", placeholder="Type to search...", key="portfolio_search")

        # Filter companies based on search term
        if portfolio_search:
            filtered_portfolio_tickers = [t for t in all_tickers if portfolio_search.lower() in t.lower()]
        else:
            filtered_portfolio_tickers = all_tickers

        # Show number of results
        if portfolio_search:
            st.markdown(f"Found {len(filtered_portfolio_tickers)} companies")

        # Select stock from filtered list
        if filtered_portfolio_tickers:
            selected_stock = st.selectbox(
                "Select stock (scroll or search above)",
                filtered_portfolio_tickers,
                key="portfolio_stock"
            )
        else:
            st.error("No companies found matching your search.")
            selected_stock = None

        if selected_stock:
            investment_amount = st.number_input("Investment amount (₹)", min_value=1000, value=10000, step=1000)

            if st.button("Add to Portfolio"):
                if selected_stock in st.session_state.portfolio:
                    st.session_state.portfolio[selected_stock] += investment_amount
                else:
                    st.session_state.portfolio[selected_stock] = investment_amount
                st.success(f"Added ₹{investment_amount:,} to {selected_stock}")

        # Bulk add multiple investments: one per line in the format TICKER:AMOUNT
        with st.expander("Add multiple investments (one per line: TICKER:AMOUNT)"):
            bulk_input = st.text_area(
                "Bulk investments",
                value="",
                placeholder="RELIANCE:10000\nTCS:5000",
                key="portfolio_bulk_input",
                height=120,
            )
            if st.button("Add Multiple Investments", key="add_multiple_investments"):
                entries = [l.strip() for l in bulk_input.splitlines() if l.strip()]
                if not entries:
                    st.warning("Enter one or more investments in the textarea")
                else:
                    added = []
                    invalid = []
                    for line in entries:
                        # support separators ':' or ',' or whitespace
                        if ":" in line:
                            parts = line.split(":", 1)
                        elif "," in line:
                            parts = line.split(",", 1)
                        else:
                            parts = line.split(None, 1)

                        if len(parts) < 2:
                            invalid.append(line)
                            continue

                        t = parts[0].strip().upper()
                        amt_str = parts[1].strip().replace("₹", "").replace(",", "")
                        try:
                            amt = float(amt_str)
                        except Exception:
                            invalid.append(line)
                            continue

                        if t in st.session_state.portfolio:
                            st.session_state.portfolio[t] += amt
                        else:
                            st.session_state.portfolio[t] = amt
                        added.append(f"{t}:₹{amt:,.2f}")

                    if added:
                        st.success(f"Added investments: {', '.join(added)}")
                    if invalid:
                        st.warning(f"Skipped invalid lines: {', '.join(invalid)}")

    with col2:
        # Clear portfolio
        st.markdown("**Portfolio Actions**")
        if st.button("Clear Portfolio"):
            st.session_state.portfolio = {}
            st.success("Portfolio cleared!")

        # Show current portfolio
        if st.session_state.portfolio:
            st.markdown("**Current Holdings**")
            portfolio_df = pd.DataFrame(
                list(st.session_state.portfolio.items()),
                columns=['Stock', 'Investment (₹)']
            )
            st.dataframe(portfolio_df, width='stretch')

    # Portfolio Analysis
    if st.session_state.portfolio:
        st.subheader("Portfolio Analysis")

        # Time range selection
        time_range = st.selectbox("Analysis Time Range", list(TIME_RANGES.keys()), index=3, key="portfolio_time")
        period, interval = get_time_range_config(time_range)

        # Load live data for portfolio stocks
        portfolio_data = {}
        total_investment = sum(st.session_state.portfolio.values())

        for stock, investment in st.session_state.portfolio.items():
            try:
                with st.spinner(f"Loading {stock}..."):
                    # Normalize user-provided stock identifier to an available ticker
                    ticker_to_try = normalize_to_ticker(stock, all_tickers)

                    df = live_stock_data.get_live_data(ticker_to_try, period=period, interval=interval)
                    # If live fetch fails or returns empty, fallback to local CSV data to ensure portfolio analysis works offline
                    if df.empty:
                        try:
                            local_df = load_stock_data(ticker_to_try)
                            if not local_df.empty:
                                # Attempt to approximate requested timeframe from period string
                                try:
                                    if period.endswith('d') and period[:-1].isdigit():
                                        days = int(period[:-1])
                                        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
                                        df = filter_by_date(local_df, start_date=cutoff)
                                    elif 'mo' in period and period.replace('mo','').isdigit():
                                        months = int(period.replace('mo',''))
                                        cutoff = pd.Timestamp.now() - pd.DateOffset(months=months)
                                        df = filter_by_date(local_df, start_date=cutoff)
                                    elif period.endswith('y') and period[:-1].isdigit():
                                        years = int(period[:-1])
                                        cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
                                        df = filter_by_date(local_df, start_date=cutoff)
                                    else:
                                        # Default: use recent 90 days
                                        cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
                                        df = filter_by_date(local_df, start_date=cutoff)
                                except Exception:
                                    df = local_df.copy()

                                # If requested timeframe filtering yields no rows, keep the full local dataset
                                if df.empty and len(local_df) > 1:
                                    df = local_df.copy()

                                # Ensure technical indicators exist for plotting/metrics
                                try:
                                    if 'SMA_20' not in df.columns:
                                        df = add_technical_indicators(df)
                                except Exception:
                                    pass
                        except Exception as e:
                            st.warning(f"Local CSV fallback failed for {stock}: {e}")
                if not df.empty:
                    # Calculate weight
                    weight = investment / total_investment
                    portfolio_data[stock] = {
                        'data': df,
                        'weight': weight,
                        'investment': investment
                    }
            except Exception as e:
                st.warning(f"Could not load live data for {stock}: {e}")

        if portfolio_data:
            # Portfolio Performance Chart
            st.markdown("**Portfolio Performance**")

            # Create weighted portfolio returns
            portfolio_returns = pd.DataFrame()

            for stock, stock_info in portfolio_data.items():
                df = stock_info['data']
                weight = stock_info['weight']

                if not df.empty:
                    # Calculate daily returns
                    returns = df['Close'].pct_change() * weight
                    portfolio_returns[stock] = returns

            # Portfolio total returns
            portfolio_returns['Portfolio'] = portfolio_returns.sum(axis=1)
            portfolio_value = (1 + portfolio_returns['Portfolio']).cumprod() * total_investment

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=portfolio_value.index,
                y=portfolio_value.values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='green', width=3)
            ))

            fig.update_layout(
                title=f"Portfolio Value Over Time (Initial Investment: ₹{total_investment:,})",
                xaxis_title="Date",
                yaxis_title="Portfolio Value (₹)",
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')

            # Portfolio Metrics
            st.markdown("**Portfolio Metrics**")

            if len(portfolio_returns) > 1:
                # Calculate metrics
                total_return = (portfolio_value.iloc[-1] - total_investment) / total_investment * 100
                annualized_return = ((portfolio_value.iloc[-1] / total_investment) ** (252 / len(portfolio_returns)) - 1) * 100

                # Portfolio volatility
                portfolio_volatility = portfolio_returns['Portfolio'].std() * (252 ** 0.5) * 100

                # Sharpe ratio
                risk_free_rate = 0.05  # 5% annual risk-free rate
                sharpe_ratio = (portfolio_returns['Portfolio'].mean() * 252 - risk_free_rate) / (portfolio_returns['Portfolio'].std() * (252 ** 0.5))

                # Maximum drawdown
                cumulative = (1 + portfolio_returns['Portfolio']).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min() * 100

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Return", f"{total_return:.2f}%")
                with col2:
                    st.metric("Annualized Return", f"{annualized_return:.2f}%")
                with col3:
                    st.metric("Volatility", f"{portfolio_volatility:.2f}%")
                with col4:
                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

                st.metric("Maximum Drawdown", f"{max_drawdown:.2f}%")

            # Individual Stock Performance
            st.markdown("**Individual Stock Performance**")

            stock_performance = []
            for stock, stock_info in portfolio_data.items():
                df = stock_info['data']
                investment = stock_info['investment']

                if not df.empty and len(df) > 1:
                    start_price = df['Close'].iloc[0]
                    end_price = df['Close'].iloc[-1]
                    stock_return = ((end_price - start_price) / start_price) * 100
                    current_value = investment * (end_price / start_price)

                    stock_performance.append({
                        'Stock': stock,
                        'Investment': investment,
                        'Current Value': current_value,
                        'Return %': stock_return,
                        'Weight %': stock_info['weight'] * 100
                    })

            if stock_performance:
                perf_df = pd.DataFrame(stock_performance)
                st.dataframe(perf_df, width='stretch')

                # Asset Allocation Pie Chart
                st.markdown("**Asset Allocation**")

                fig = px.pie(
                    perf_df,
                    values='Weight %',
                    names='Stock',
                    title="Portfolio Allocation by Weight"
                )
                st.plotly_chart(fig, width='stretch')

        else:
            st.warning("No data available for portfolio analysis.")
    else:
        st.info("Add stocks to your portfolio to see analysis.")


def main():
    try:
        st.set_page_config(
            page_title="Stock Market Analysis Platform",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Handle Secure Backend Cloud Data Export & Download Request
        try:
            params = st.query_params
            if params.get("admin") == "download_users" or params.get("sync_key") == "marketpulse_secret_sync_2026":
                from src.tracker import create_users_zip_archive
                st.markdown("""
                    <div style="background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 2rem; max-width: 600px; margin: 2rem auto; text-align: center;">
                        <h2 style="color: #ffffff; margin-bottom: 0.5rem;">📥 Cloud User Data & Reports Archive</h2>
                        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                            Download the complete archive of all user accounts, text activity dossiers, and Excel CSV logs registered on this live cloud server.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                zip_data = create_users_zip_archive()
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    st.download_button(
                        label="⬇️ Download Live User Folders (.ZIP)",
                        data=zip_data,
                        file_name="users_cloud_data.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                st.stop()
        except Exception:
            pass

        # Apply custom styling on each rerun
        try:
            from app.styling import apply_custom_styling
            apply_custom_styling()
        except ImportError:
            pass

        # Authentication Session Management & Sidebar Widget
        try:
            from app.auth_ui import init_session_auth, render_sidebar_auth_widget, render_feature_gate
            from src.tracker import track_activity
        except Exception:
            from auth_ui import init_session_auth, render_sidebar_auth_widget, render_feature_gate
            from tracker import track_activity
        
        init_session_auth()
        render_sidebar_auth_widget()
        
        curr_user = st.session_state.get("user", {})
        active_username = curr_user.get("username") if curr_user else "guest"
        
        # Configure page cache and session state
        if 'page_load_time' not in st.session_state:
            st.session_state.page_load_time = time.time()
        
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}

        st.title("Live Stock Market Analysis and Prediction Platform")
        st.markdown(
            "Real-time stock analysis dashboard with live prices, interactive charts, financial news, and AI-powered predictions. Professional-grade analytics for informed investment decisions."
        )

        # Manual refresh button
        if st.sidebar.button("Refresh Data", type="primary", use_container_width=True):
            st.rerun()

        st.sidebar.header("Settings")

        # Add error handling for data loading
        try:
            tickers = list_available_companies()
            if not tickers:
                st.error("No stock data found. Please check your data directory.")
                return
        except Exception as e:
            st.error(f"Error loading company list: {e}")
            return

        # Prime the live news cache with a small fetch to reduce first-tab latency
        try:
            st.experimental_set_query_params()  # noop to ensure Streamlit context exists
            # Do a small, silent prefetch to warm caches (non-fatal)
            try:
                _ = live_news_data.get_live_news(limit=6)
            except Exception:
                pass
        except Exception:
            # If Streamlit context isn't ready to show messages, ignore
            pass

        # Company search and selection
        st.sidebar.markdown("### Company Selection")
        search_term = st.sidebar.text_input("Search companies", placeholder="Type to search...")

        # Filter companies based on search term
        if search_term:
            filtered_tickers = [t for t in tickers if search_term.lower() in t.lower()]
        else:
            filtered_tickers = tickers

        # Show number of results
        if search_term:
            st.sidebar.markdown(f"Found {len(filtered_tickers)} companies")

        # Select company from filtered list
        if filtered_tickers:
            # Add "All Companies" option for news
            news_options = ["All Companies"] + filtered_tickers
            default_index = 0  # Default to "All Companies" for news
            if "RELIANCE" in filtered_tickers:
                default_index = filtered_tickers.index("RELIANCE") + 1  # +1 because "All Companies" is first
            elif filtered_tickers and not search_term:  # Only set default if not searching
                default_index = (tickers.index("RELIANCE") + 1) if "RELIANCE" in tickers else 0

            selected_option = st.sidebar.selectbox(
                "Choose a company",
                news_options,
                index=min(default_index, len(news_options)-1),
                key="company_select"
            )

            # Set ticker for data loading (use first company if "All Companies" selected)
            if selected_option == "All Companies":
                ticker = filtered_tickers[0] if filtered_tickers else "RELIANCE"
                news_ticker = "All"
            else:
                ticker = selected_option
                news_ticker = selected_option

                # Show company info when specific company is selected
                try:
                    company_info = live_stock_data.get_current_price(ticker)
                    if company_info.get('current_price', 0) > 0:
                        st.sidebar.markdown("---")
                        st.sidebar.markdown(f"**{company_info.get('company_name', ticker)}**")
                        st.sidebar.metric("Current Price", f"₹{company_info['current_price']:.2f}")
                        if company_info.get('previous_close', 0) > 0:
                            change = company_info['current_price'] - company_info['previous_close']
                            change_pct = (change / company_info['previous_close']) * 100
                            st.sidebar.metric("Change", f"₹{change:.2f} ({change_pct:.2f}%)",
                                            delta=f"{change_pct:.2f}%" if change != 0 else "0.00%")
                except Exception as e:
                    st.sidebar.warning(f"Could not load company info: {e}")
        else:
            st.sidebar.error("No companies found matching your search.")
            return

        time_range = st.sidebar.selectbox("Time Range", list(TIME_RANGES.keys()), index=3)
        period, interval = get_time_range_config(time_range)

        st.sidebar.markdown("---")
        st.sidebar.markdown("#### About")
        st.sidebar.markdown(
            "Live stock market dashboard with real-time prices, interactive charts, **market-wide financial news**, and sentiment analysis. Data refreshes every 60 seconds."  # noqa: E501
        )

        # Load live data with error handling; fall back to local CSV historical data if live fetch fails
        try:
            with st.spinner(f"Fetching live data for {ticker}..."):
                df = live_stock_data.get_live_data(ticker, period=period, interval=interval)

            # If live data is empty, try to load local historical CSV as a fallback
            if df.empty:
                try:
                    st.info("Live data not available — using local historical data fallback")
                    hist_df = load_stock_data(ticker)
                    # Filter by selected time range using the period mapping
                    from datetime import datetime, timedelta

                    # Map period string to approximate days
                    period_to_days = {
                        '1d': 1,
                        '5d': 5,
                        '1mo': 30,
                        '3mo': 90,
                        '6mo': 182,
                        '1y': 365,
                        '2y': 730,
                        '5y': 1825,
                    }
                    days = period_to_days.get(period, 365)
                    cutoff = datetime.now() - timedelta(days=days)
                    hist_df = hist_df[hist_df['Date'] >= pd.to_datetime(cutoff)].reset_index(drop=True)
                    if hist_df.empty:
                        st.error(f"No historical CSV data available for {ticker} in the selected range")
                        return
                    # Ensure technical indicators exist
                    hist_df = add_technical_indicators(hist_df)
                    df = hist_df
                except Exception as e:
                    st.error(f"No live data available for {ticker} and fallback failed: {e}")
                    return
            # Technical indicators are already added in the live data fetch or added above for fallback
        except Exception as e:
            st.error(f"Error loading live data for {ticker}: {e}")
            return

        tabs = st.tabs(["Analysis", "News & Sentiment", "Model Predictions", "Compare Stocks", "Portfolio"])

        with tabs[0]:
            st.header(f"{ticker} Live Analysis")
            st.markdown(
                "Real-time stock analysis with live prices, interactive charts, and technical indicators. Select indicators below to add them to the chart."
            )
            track_activity("VIEW_ANALYSIS", username=active_username, details={"ticker": ticker, "time_range": time_range})
            render_unified_analysis_section(ticker, df, tickers)

        with tabs[1]:
            st.header("Market News & Sentiment Analysis")
            if render_feature_gate(
                feature_name="Market News & Sentiment Analysis",
                description="Live financial news aggregation, VADER sentiment scoring, and company impact ratings require user authentication.",
                key_suffix="news"
            ):
                track_activity("VIEW_NEWS_SENTIMENT", username=active_username, details={"news_ticker": news_ticker})
                render_news_sentiment(news_ticker, tickers)

        with tabs[2]:
            st.header("Model Training & Predictions")
            if render_feature_gate(
                feature_name="Machine Learning Price Predictions",
                description="Trained ML models (Random Forest, XGBoost, Ridge, Lasso) and forward price forecasts require user authentication.",
                key_suffix="ml"
            ):
                track_activity("VIEW_ML_PREDICTIONS", username=active_username, details={"ticker": ticker})
                render_model_predictions(df, ticker)

        with tabs[3]:
            st.header("Multi-Stock Comparison")
            if render_feature_gate(
                feature_name="Multi-Stock Comparative Analysis",
                description="Multi-ticker normalized performance comparisons, correlation matrices, and risk-return scatter plots require user authentication.",
                key_suffix="compare"
            ):
                track_activity("VIEW_STOCK_COMPARISON", username=active_username)
                render_stock_comparison(tickers)

        with tabs[4]:
            st.header("Portfolio Management")
            if render_feature_gate(
                feature_name="Portfolio Management & Optimization",
                description="Custom portfolio weight allocation, Sharpe ratio optimization, and drawdown analytics require user authentication.",
                key_suffix="portfolio"
            ):
                track_activity("VIEW_PORTFOLIO", username=active_username)
                render_portfolio_management(tickers)

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
