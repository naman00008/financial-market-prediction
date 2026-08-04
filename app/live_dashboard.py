import os
import sys
from typing import List, Optional, Dict
import time

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Ensure app and src modules are importable in both local and Streamlit Cloud execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.dirname(__file__)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if os.path.join(ROOT_DIR, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from live_data import live_stock_data, live_news_data, LiveStockData, LiveNewsData
from feature_engineering import create_features
from model_training import train_regression_models, evaluate_regression
from sentiment_analysis import analyze_sentiment
from dashboard import render_stock_comparison, render_portfolio_management
from src.data_preprocessing import list_available_companies


# Caching wrappers to avoid repeated blocking network/compute calls on each rerun
@st.cache_data(ttl=30)
def get_cached_live_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return live_stock_data.get_live_data(ticker, period=period, interval=interval)


@st.cache_data(ttl=30)
def get_cached_current_price(ticker: str) -> dict:
    return live_stock_data.get_current_price(ticker)


@st.cache_data(ttl=300)
def get_cached_news(query: str, limit: int = 15) -> pd.DataFrame:
    return live_news_data.get_live_news(query=query, limit=limit)


@st.cache_data(ttl=600)
def get_cached_hist_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return live_stock_data.get_live_data(ticker, period=period, interval=interval)


def get_trained_models(features_df: pd.DataFrame):
    """Train ML models without caching to avoid stale data issues."""
    if features_df is None or features_df.empty:
        return {}
    sample_df = features_df.copy()
    if len(sample_df) > 2000:
        sample_df = sample_df.tail(2000)
    try:
        return train_regression_models(sample_df)
    except Exception as e:
        return {}

# Page configuration
st.set_page_config(
    page_title="Live Stock Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh every 60 seconds
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .positive-change {
        color: #28a745;
        font-weight: bold;
    }
    .negative-change {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-header {
        font-size: 1.25rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = 'RELIANCE'

if 'time_range' not in st.session_state:
    st.session_state.time_range = '1M'

# Time range options
TIME_RANGES = {
    '1D': ('1d', '1m'),
    '5D': ('5d', '5m'),
    '1M': ('1mo', '1h'),
    '3M': ('3mo', '1d'),
    '6M': ('6mo', '1d'),
    '1Y': ('1y', '1d'),
    '2Y': ('2y', '1d')
}


def create_live_price_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Create interactive live price chart with technical indicators"""
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))

    # Volume bar chart
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='Volume',
        marker_color='rgba(158,158,158,0.8)',
        yaxis='y2',
        opacity=0.3
    ))

    # Moving averages
    if 'SMA_20' in df.columns and df['SMA_20'].notna().any():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['SMA_20'],
            line=dict(color='#ff9800', width=1.5),
            name='SMA 20'
        ))

    if 'SMA_50' in df.columns and df['SMA_50'].notna().any():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['SMA_50'],
            line=dict(color='#9c27b0', width=1.5),
            name='SMA 50'
        ))

    # Bollinger Bands
    if 'BB_Upper' in df.columns and df['BB_Upper'].notna().any():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['BB_Upper'],
            line=dict(color='#2196f3', width=1, dash='dash'),
            name='BB Upper'
        ))
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['BB_Lower'],
            line=dict(color='#2196f3', width=1, dash='dash'),
            name='BB Lower'
        ))

    # Update layout
    fig.update_layout(
        title=f'{ticker} - Live Price Chart',
        yaxis_title='Price (₹)',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title='Time',
        template='plotly_white',
        hovermode='x unified',
        height=500,
        showlegend=True
    )

    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)

    return fig


def create_technical_indicators_chart(df: pd.DataFrame, indicator: str) -> go.Figure:
    """Create technical indicator charts"""
    fig = go.Figure()

    if indicator == 'RSI':
        if 'RSI_14' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['RSI_14'],
                line=dict(color='#ff5722', width=2),
                name='RSI'
            ))
            # Add overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            fig.update_layout(title='Relative Strength Index (RSI)', yaxis_title='RSI')

    elif indicator == 'MACD':
        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['MACD'],
                line=dict(color='#2196f3', width=2),
                name='MACD'
            ))
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['MACD_Signal'],
                line=dict(color='#ff9800', width=2),
                name='Signal'
            ))
            if 'MACD_Hist' in df.columns:
                colors = ['red' if val < 0 else 'green' for val in df['MACD_Hist']]
                fig.add_trace(go.Bar(
                    x=df['Date'], y=df['MACD_Hist'],
                    marker_color=colors,
                    name='Histogram',
                    opacity=0.7
                ))
            fig.update_layout(title='MACD', yaxis_title='Value')

    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        height=300
    )

    return fig


def create_sentiment_charts(news_df: pd.DataFrame):
    """Create sentiment analysis visualizations"""
    if news_df.empty or 'sentiment_label' not in news_df.columns:
        return None, None, None

    # Sentiment distribution pie chart
    sentiment_counts = news_df['sentiment_label'].value_counts()
    pie_fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Sentiment Distribution',
        color=sentiment_counts.index,
        color_discrete_map={
            'positive': '#28a745',
            'neutral': '#ffc107',
            'negative': '#dc3545'
        }
    )
    pie_fig.update_layout(height=300)

    # Sentiment timeline
    news_df['published_at'] = pd.to_datetime(news_df['published_at'])
    timeline_data = news_df.groupby([pd.Grouper(key='published_at', freq='D'), 'sentiment_label']).size().reset_index(name='count')

    timeline_fig = px.line(
        timeline_data,
        x='published_at',
        y='count',
        color='sentiment_label',
        title='Sentiment Trend Over Time',
        color_discrete_map={
            'positive': '#28a745',
            'neutral': '#ffc107',
            'negative': '#dc3545'
        }
    )
    timeline_fig.update_layout(height=300)

    # Sentiment scores histogram
    hist_fig = px.histogram(
        news_df,
        x='sentiment_score',
        nbins=20,
        title='Sentiment Score Distribution',
        color_discrete_sequence=['#1f77b4']
    )
    hist_fig.update_layout(height=300)

    return pie_fig, timeline_fig, hist_fig


def display_price_metrics(current_data: Dict):
    """Display current price and key metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        current_price = current_data.get('current_price', 0)
        prev_close = current_data.get('previous_close', 0)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0

        st.metric(
            "Current Price",
            f"₹{current_price:,.2f}",
            f"{change:+,.2f} ({change_pct:+.2f}%)",
            delta_color="normal" if change >= 0 else "inverse"
        )

    with col2:
        st.metric("Day High", f"₹{current_data.get('day_high', 0):,.2f}")

    with col3:
        st.metric("Day Low", f"₹{current_data.get('day_low', 0):,.2f}")

    with col4:
        volume = current_data.get('volume', 0)
        st.metric("Volume", f"{volume:,.0f}")


def main():
    # Authentication Gatekeeper (Login / Sign Up)
    current_user = None
    try:
        from auth_ui import require_auth
        current_user = require_auth()
    except Exception:
        try:
            from app.auth_ui import require_auth
            current_user = require_auth()
        except Exception:
            pass

    if not current_user:
        return

    # Main header
    st.markdown('<h1 class="main-header">Live Stock Market Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Real-time stock prices, live charts, and financial news analysis")

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">Stock Selection</div>', unsafe_allow_html=True)

        # Company search
        search_term = st.text_input("Search companies", placeholder="Type company name...")

        # Common NSE stocks for selection
        common_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'HINDUNILVR',
            'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'BAJFINANCE',
            'BHARTIARTL', 'WIPRO', 'NESTLEIND', 'ULTRACEMCO', 'POWERGRID',
            'NTPC', 'GRASIM', 'JSWSTEEL', 'TATAMOTORS', 'ADANIPORTS'
        ]

        if search_term:
            filtered_stocks = [s for s in common_stocks if search_term.lower() in s.lower()]
        else:
            filtered_stocks = common_stocks

        selected_ticker = st.selectbox(
            "Select Stock",
            filtered_stocks,
            index=filtered_stocks.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in filtered_stocks else 0
        )

        st.session_state.selected_ticker = selected_ticker

        # Time range selection
        time_range = st.selectbox(
            "Time Range",
            list(TIME_RANGES.keys()),
            index=list(TIME_RANGES.keys()).index(st.session_state.time_range)
        )
        st.session_state.time_range = time_range

        period, interval = TIME_RANGES[time_range]

        # Auto-refresh indicator
        st.markdown("---")
        st.markdown("**Auto-refresh:** Every 60 seconds")
        st.markdown(f"**Last updated:** {time.strftime('%H:%M:%S')}")

        # Current price quick view
        st.markdown("---")
        st.markdown("**Market Snapshot**")
        try:
            current_data = get_cached_current_price(selected_ticker)
            if 'error' not in current_data:
                price = current_data.get('current_price', 0)
                change = price - current_data.get('previous_close', 0)
                change_pct = (change / current_data.get('previous_close', 1)) * 100

                color = "positive-change" if change >= 0 else "negative-change"
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{selected_ticker}</strong><br>
                    ₹{price:,.2f} <span class="{color}">({change_pct:+.2f}%)</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.write("Price data unavailable")

    # Main content
    try:
        # Get live stock data (cached wrappers to reduce blocking)
        with st.spinner(f"Loading live data for {selected_ticker}..."):
            df = get_cached_live_data(selected_ticker, period, interval)
            current_data = get_cached_current_price(selected_ticker)

        if df.empty:
            st.error(f"No data available for {selected_ticker}")
            return

        try:
            all_tickers = list_available_companies()
        except Exception:
            all_tickers = [selected_ticker]

        tabs = st.tabs([
            "Overview",
            "Technical",
            "News & Sentiment",
            "ML Predictions",
            "Compare Stocks",
            "Portfolio"
        ])

        with tabs[0]:
            st.subheader("Current Price & Metrics")
            display_price_metrics(current_data)
            st.subheader("Live Price Chart")
            chart = create_live_price_chart(df, selected_ticker)
            st.plotly_chart(chart, width='stretch')

        with tabs[1]:
            st.subheader("Technical Indicators")
            indicator_tabs = st.tabs(["RSI", "MACD"])
            with indicator_tabs[0]:
                rsi_chart = create_technical_indicators_chart(df, 'RSI')
                st.plotly_chart(rsi_chart, width='stretch')
            with indicator_tabs[1]:
                macd_chart = create_technical_indicators_chart(df, 'MACD')
                st.plotly_chart(macd_chart, width='stretch')

        with tabs[2]:
            st.subheader("Live Financial News & Sentiment")
            with st.spinner("Loading latest news..."):
                news_df = get_cached_news(selected_ticker, limit=15)

            if not news_df.empty:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("**Latest Headlines**")
                    for _, row in news_df.head(10).iterrows():
                        label = row.get('sentiment_label', 'neutral')
                        label_color = '#10b981' if label == 'positive' else '#ef4444' if label == 'negative' else '#94a3b8'
                        st.markdown(f"""
                        <div style="border-left: 3px solid {label_color}; padding-left: 10px; margin-bottom:10px;">
                            <strong>{row['title']}</strong><br>
                            <small>{row['source']} • {pd.to_datetime(row['published_at']).strftime('%d %b %Y, %H:%M')} • <span style="color: {label_color}; font-weight: 600;">{label.upper()}</span></small>
                        </div>
                        """, unsafe_allow_html=True)
                with col2:
                    pie_chart, timeline_chart, hist_chart = create_sentiment_charts(news_df)
                    if pie_chart:
                        st.plotly_chart(pie_chart, width='stretch')
                        st.plotly_chart(timeline_chart, width='stretch')
            else:
                st.info("No news available at the moment.")

        with tabs[3]:
            st.subheader("ML Price Predictions")
            try:
                hist_df = get_cached_hist_data(selected_ticker, period="2y", interval="1d")
                if not hist_df.empty and len(hist_df) > 100:
                    features = create_features(hist_df)
                    with st.spinner(f"Training ML models for {selected_ticker}..."):
                        results = get_trained_models(features)
                    
                    if results:
                        # Display model performance metrics
                        cols = st.columns(3)
                        for idx, (name, data) in enumerate(sorted(results.items(), key=lambda x: x[1].get('r2_score', 0), reverse=True)):
                            r2 = data.get('r2_score', 0)
                            with cols[idx]:
                                st.metric(f"{name.replace('_', ' ').title()}", f"R² = {r2:.4f}")
                        
                        # Get best model
                        best_model_name, best_model_data = max(results.items(), key=lambda x: x[1].get('r2_score', 0))
                        st.markdown(f"### Top Performing Model: **{best_model_name.replace('_', ' ').title()}**")
                        
                        # Extract predictions
                        y_pred = best_model_data.get('y_pred')
                        y_test = best_model_data.get('y_test')
                        x_test = best_model_data.get('X_test')
                        
                        if y_pred is not None and y_test is not None and x_test is not None:
                            try:
                                # Prepare plot data
                                x_idx = list(range(len(y_pred)))[-50:]
                                y_pred_plot = y_pred[-50:] if isinstance(y_pred, list) else y_pred[-50:].tolist()
                                y_test_plot = y_test.iloc[-50:].values if hasattr(y_test, 'iloc') else y_test[-50:]
                                
                                # Create comparison chart
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=x_idx,
                                    y=y_test_plot,
                                    mode='lines',
                                    name='Actual Price',
                                    line=dict(color='#1f77b4', width=2)
                                ))
                                fig.add_trace(go.Scatter(
                                    x=x_idx,
                                    y=y_pred_plot,
                                    mode='lines',
                                    name='Predicted Price',
                                    line=dict(color='#ff7f0e', width=2, dash='dash')
                                ))
                                fig.update_layout(
                                    title=f'{selected_ticker} - Actual vs Predicted Price (Last 50 Days)',
                                    xaxis_title='Day Index',
                                    yaxis_title='Price (₹)',
                                    template='plotly_white',
                                    height=450,
                                    hovermode='x unified'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Show residuals
                                residuals = y_test_plot - y_pred_plot if hasattr(y_test_plot, '__sub__') else [a - b for a, b in zip(y_test_plot, y_pred_plot)]
                                fig_residuals = go.Figure()
                                fig_residuals.add_trace(go.Scatter(
                                    x=x_idx,
                                    y=residuals,
                                    mode='markers',
                                    name='Residuals',
                                    marker=dict(color='#ff6b6b', size=6)
                                ))
                                fig_residuals.add_hline(y=0, line_dash="dash", line_color="gray")
                                fig_residuals.update_layout(
                                    title='Prediction Residuals (Actual - Predicted)',
                                    xaxis_title='Day Index',
                                    yaxis_title='Residual Value (₹)',
                                    template='plotly_white',
                                    height=300
                                )
                                st.plotly_chart(fig_residuals, use_container_width=True)
                            except Exception as plot_error:
                                st.error(f"Error plotting predictions: {plot_error}")
                        else:
                            st.error("Model prediction arrays are incomplete or missing.")
                    else:
                        st.info("Unable to train ML models. Please try a different stock or time range.")
                else:
                    st.info("Insufficient historical data for ML predictions (need >100 data points).")
            except Exception as e:
                st.error(f"ML prediction error: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

        with tabs[4]:
            st.header("Compare Stocks")
            if all_tickers:
                render_stock_comparison(all_tickers)
            else:
                st.warning("Unable to load stock list for comparison.")

        with tabs[5]:
            st.header("Portfolio Management")
            if all_tickers:
                render_portfolio_management(all_tickers)
            else:
                st.warning("Unable to load stock list for portfolio management.")

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()