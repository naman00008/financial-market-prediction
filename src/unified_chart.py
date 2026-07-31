"""Advanced unified chart visualization with toggleable technical indicators"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional
import numpy as np


def build_unified_technical_chart(
    df: pd.DataFrame,
    ticker: str,
    selected_indicators: List[str] = None,
    chart_type: str = "Candle"
) -> go.Figure:
    """
    Render a unified professional chart with live price and toggleable indicators.
    
    Args:
        df: Stock data DataFrame
        ticker: Stock ticker symbol
        selected_indicators: List of indicators to display
    """
    if df.empty:
        raise ValueError("No data available for chart")

    if selected_indicators is None:
        selected_indicators = ["Volume"]

    fig = go.Figure()

    # Main price trace
    if chart_type == "Candle" and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350',
            hovertext=[f"<b>{ticker}</b><br>Date: {date.strftime('%Y-%m-%d %H:%M')}<br>Open: ₹{op:.2f}<br>High: ₹{hi:.2f}<br>Low: ₹{lo:.2f}<br>Close: ₹{cl:.2f}" 
                      for date, op, hi, lo, cl in zip(df['Date'], df['Open'], df['High'], df['Low'], df['Close'])],
            hoverinfo='text',
            yaxis='y1'
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Close Price",
            line=dict(color="#1f77b4", width=2),
            yaxis='y1'
        ))

    # Overlay technical indicators and volume on the same chart
    if "Volume" in selected_indicators and 'Volume' in df.columns:
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color='rgba(158,158,158,0.25)',
            opacity=0.35,
            hovertemplate='<b>Volume</b><br>Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>',
            yaxis='y3'
        ))

    if "Bollinger Bands" in selected_indicators and all(col in df.columns for col in ["BBL_20_2.0", "BBU_20_2.0", "BBM_20_2.0"]):
        if df["BBU_20_2.0"].notna().any():
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["BBU_20_2.0"],
                name="BB Upper",
                line=dict(color="#2196f3", width=1, dash="dot"),
                hovertemplate='<b>BB Upper</b><br>Date: %{x}<br>Value: ₹%{y:.2f}<extra></extra>',
                yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["BBL_20_2.0"],
                name="BB Lower",
                line=dict(color="#2196f3", width=1, dash="dot"),
                fill='tonexty',
                fillcolor='rgba(33, 150, 243, 0.1)',
                hovertemplate='<b>BB Lower</b><br>Date: %{x}<br>Value: ₹%{y:.2f}<extra></extra>',
                yaxis='y1'
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["BBM_20_2.0"],
                name="BB Middle",
                line=dict(color="#ff9800", width=1, dash="dash"),
                hovertemplate='<b>BB Middle</b><br>Date: %{x}<br>Value: ₹%{y:.2f}<extra></extra>',
                yaxis='y1'
            ))

    if "RSI" in selected_indicators and "RSI_14" in df.columns and df["RSI_14"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["RSI_14"],
            name="RSI (14)",
            line=dict(color="#636efa", width=2, dash="dash"),
            hovertemplate='<b>RSI (14)</b><br>Date: %{x}<br>RSI: %{y:.2f}<extra></extra>',
            yaxis='y2'
        ))

    if "MACD" in selected_indicators and "MACD_12_26_9" in df.columns and df["MACD_12_26_9"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["MACD_12_26_9"],
            name="MACD",
            line=dict(color="#00cc96", width=2, dash="dash"),
            hovertemplate='<b>MACD</b><br>Date: %{x}<br>MACD: %{y:.4f}<extra></extra>',
            yaxis='y2'
        ))
        if "MACDs_12_26_9" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"],
                y=df["MACDs_12_26_9"],
                name="Signal",
                line=dict(color="#ff6692", width=1, dash="dot"),
                hovertemplate='<b>Signal</b><br>Date: %{x}<br>Signal: %{y:.4f}<extra></extra>',
                yaxis='y2'
            ))

    if "Stochastic" in selected_indicators and "STOCHk_14_3_3" in df.columns and df["STOCHk_14_3_3"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["STOCHk_14_3_3"],
            name="%K",
            line=dict(color="#ab63fa", width=2, dash="dash"),
            hovertemplate='<b>Stochastic %K</b><br>Date: %{x}<br>%K: %{y:.2f}<extra></extra>',
            yaxis='y2'
        ))
        if "STOCHd_14_3_3" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["STOCHd_14_3_3"],
                name="%D",
                line=dict(color="#ffa15a", width=1, dash="dot"),
                hovertemplate='<b>Stochastic %D</b><br>Date: %{x}<br>%D: %{y:.2f}<extra></extra>',
                yaxis='y2'
            ))

    if "Williams %R" in selected_indicators and "WILLR_14" in df.columns and df["WILLR_14"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["WILLR_14"],
            name="Williams %R",
            line=dict(color="#636efa", width=2, dash="dash"),
            hovertemplate='<b>Williams %R</b><br>Date: %{x}<br>%R: %{y:.2f}<extra></extra>',
            yaxis='y2'
        ))

    fig.update_layout(
        title=dict(text=f"{ticker} - Live Chart with Technical Analysis", font=dict(size=18, color='#f8fafc')),
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=700,
        margin=dict(l=80, r=120, t=80, b=80),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(30,41,59,0.7)',
            bordercolor='rgba(255,255,255,0.1)',
            borderwidth=1,
            font=dict(color='#f8fafc')
        ),
        yaxis=dict(
            title={"text": 'Price (₹)', "font": {"color": '#60a5fa'}},
            tickfont={"color": '#60a5fa'},
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis2=dict(
            title={"text": 'Indicators', "font": {"color": '#94a3b8'}},
            tickfont={"color": '#94a3b8'},
            overlaying='y',
            side='right',
            position=0.92,
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=False,
            showline=True,
            linecolor='rgba(255,255,255,0.2)'
        ),
        xaxis=dict(
            title={"text": 'Date', "font": {"color": '#94a3b8'}},
            tickfont={"color": '#94a3b8'},
            gridcolor='rgba(255,255,255,0.1)',
            showline=True,
            linecolor='rgba(255,255,255,0.2)'
        )
    )

    # Ensure a single main x-axis for the whole chart (keeps Date under the main plot)
    fig.update_layout(xaxis=dict(title={"text": 'Date', "font": {"color": 'white'}}, color='white', gridcolor='rgba(255,255,255,0.08)', domain=[0, 1]))

    return fig


def render_unified_technical_chart(
    df: pd.DataFrame,
    ticker: str,
    selected_indicators: List[str] = None,
    chart_type: str = "Candle"
) -> None:
    fig = build_unified_technical_chart(df, ticker, selected_indicators, chart_type)
    st.plotly_chart(fig, width='stretch', key=f"unified_chart_{ticker}")


def render_unified_analysis_section(ticker: str, df: pd.DataFrame, all_tickers: List[str]):
    """
    Render unified Overview + Technical Analysis section with indicator toggles.
    
    Args:
        ticker: Stock ticker symbol
        df: Stock data DataFrame
        all_tickers: List of all available tickers
    """
    # Display current price information
    try:
        from src.live_data import live_stock_data
        current_info = live_stock_data.get_current_price(ticker)
        
        if 'current_price' in current_info and current_info['current_price'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Current Price",
                    f"₹{current_info['current_price']:.2f}",
                    delta=None,
                    delta_color="normal"
                )
            
            with col2:
                change = current_info['current_price'] - current_info.get('previous_close', current_info['current_price'])
                change_pct = (change / current_info.get('previous_close', current_info['current_price']) * 100) if current_info.get('previous_close', 1) != 0 else 0
                st.metric("Change", f"₹{change:.2f}", delta=f"{change_pct:.2f}%")
            
            with col3:
                st.metric("Day High", f"₹{current_info.get('day_high', 0):.2f}")
            
            with col4:
                st.metric("Day Low", f"₹{current_info.get('day_low', 0):.2f}")
        else:
            st.info("Current price information not available")
    except Exception as e:
        st.warning(f"Could not fetch current price: {e}")
    
    chart_type = st.radio(
        "Chart Type",
        ["Line", "Candle"],
        index=0,
        horizontal=True,
        key=f"{ticker}_chart_type"
    )

    chart_placeholder = st.empty()

    st.markdown("---")
    
    # Indicator selection controls
    st.subheader("Analysis Indicators")
    st.markdown("Select technical indicators to display on the chart above:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    selected_indicators = []
    
    with col1:
        show_volume = st.checkbox("Volume", value=True, key=f"{ticker}_volume")
        if show_volume:
            selected_indicators.append("Volume")
    
    with col2:
        show_rsi = st.checkbox("RSI (14)", value=False, key=f"{ticker}_rsi")
        if show_rsi:
            selected_indicators.append("RSI")
    
    with col3:
        show_macd = st.checkbox("MACD", value=False, key=f"{ticker}_macd")
        if show_macd:
            selected_indicators.append("MACD")
    
    with col4:
        show_bb = st.checkbox("Bollinger Bands", value=False, key=f"{ticker}_bb")
        if show_bb:
            selected_indicators.append("Bollinger Bands")
    
    col5, col6 = st.columns(2)
    
    with col5:
        show_stoch = st.checkbox("Stochastic", value=False, key=f"{ticker}_stoch")
        if show_stoch:
            selected_indicators.append("Stochastic")
    
    with col6:
        show_williams = st.checkbox("Williams %R", value=False, key=f"{ticker}_williams")
        if show_williams:
            selected_indicators.append("Williams %R")
    
    fig = build_unified_technical_chart(df, ticker, selected_indicators, chart_type)
    chart_placeholder.plotly_chart(fig, width='stretch', key=f"unified_chart_{ticker}")
    
    st.markdown("---")
    
    # Show indicator descriptions
    with st.expander("Indicator Descriptions", expanded=False):
        st.markdown("""
        **Volume**: Shows trading volume to indicate trading intensity.
        
        **RSI (14)**: Relative Strength Index - Measures momentum. Values above 70 indicate overbought, below 30 indicate oversold.
        
        **MACD**: Moving Average Convergence Divergence - Shows trend direction and momentum. Green MACD above signal line indicates uptrend.
        
        **Bollinger Bands**: Shows volatility and potential support/resistance levels using 20-period moving average and 2 standard deviations.
        
        **Stochastic**: Compares closing price to price range. %K above 80 indicates overbought, below 20 indicates oversold.
        
        **Williams %R**: Shows overbought/oversold levels. Above -20 is overbought, below -80 is oversold.
        """)
    
    # Display current indicator values
    st.subheader("Current Indicator Values")
    
    indicator_data = {}
    
    if "RSI_14" in df.columns and pd.notna(df["RSI_14"].iloc[-1]):
        indicator_data["RSI (14)"] = f"{df['RSI_14'].iloc[-1]:.2f}"
    
    if "MACD_12_26_9" in df.columns and pd.notna(df["MACD_12_26_9"].iloc[-1]):
        macd_val = df["MACD_12_26_9"].iloc[-1]
        signal_val = df["MACDs_12_26_9"].iloc[-1] if "MACDs_12_26_9" in df.columns else 0
        indicator_data["MACD"] = f"{macd_val:.4f} (Signal: {signal_val:.4f})"
    
    if "STOCHk_14_3_3" in df.columns and pd.notna(df["STOCHk_14_3_3"].iloc[-1]):
        indicator_data["Stochastic %K"] = f"{df['STOCHk_14_3_3'].iloc[-1]:.2f}"
    
    if "WILLR_14" in df.columns and pd.notna(df["WILLR_14"].iloc[-1]):
        indicator_data["Williams %R"] = f"{df['WILLR_14'].iloc[-1]:.2f}"
    
    if indicator_data:
        # Display in columns
        cols = st.columns(len(indicator_data))
        for col, (ind_name, ind_value) in zip(cols, indicator_data.items()):
            with col:
                st.metric(ind_name, ind_value)
    else:
        st.info("No indicator values available yet. Add technical indicators above.")
