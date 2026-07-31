"""Professional CSS styling for Streamlit dashboard"""

# Professional color palette for charts
CHART_COLORS = {
    "primary": "#2563eb",      # Blue
    "success": "#10b981",      # Green
    "danger": "#ef4444",       # Red
    "warning": "#f59e0b",      # Amber
    "secondary": "#8b5cf6",    # Purple
    "info": "#06b6d4",         # Cyan
}

SENTIMENT_COLORS = {
    "positive": "#10b981",     # Green
    "negative": "#ef4444",     # Red
    "neutral": "#6b7280",      # Gray
}

# Plotly template with dark theme and colors
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#0f172a",
        "plot_bgcolor": "#1e293b",
        "font": {"color": "#f8fafc", "family": "Arial"},
        "colorway": [
            "#3b82f6",  # Blue
            "#10b981",  # Green
            "#ef4444",  # Red
            "#f59e0b",  # Amber
            "#8b5cf6",  # Purple
            "#06b6d4",  # Cyan
            "#ec4899",  # Pink
            "#14b8a6",  # Teal
        ],
        "title": {"font": {"size": 18, "color": "#f8fafc"}},
        "xaxis": {
            "gridcolor": "rgba(255, 255, 255, 0.1)",
            "linecolor": "rgba(255, 255, 255, 0.2)",
            "tickfont": {"color": "#cbd5e1"},
        },
        "yaxis": {
            "gridcolor": "rgba(255, 255, 255, 0.1)",
            "linecolor": "rgba(255, 255, 255, 0.2)",
            "tickfont": {"color": "#cbd5e1"},
        },
    }
}

CUSTOM_CSS = """
<style>
    /* Main container styling */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    /* Professional header styling */
    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e293b;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] [data-baseweb="tab"] {
        background-color: #3b82f6;
        color: white;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }

    /* Metric styling */
    [data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 1px 8px rgba(0, 0, 0, 0.2);
        color: #f8fafc;
    }

    /* Button styling */
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        box-shadow: 0 1px 6px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    /* Input styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 0.75rem;
        border: 1px solid #475569;
        padding: 0.65rem 1rem;
        font-size: 0.95rem;
        background-color: #0f172a;
        color: #f8fafc;
    }

    .stTextInput > div > div > input::placeholder,
    .stSelectbox > div > div > select::placeholder,
    .stNumberInput > div > div > input::placeholder {
        color: #94a3b8;
    }

    /* Success/Error/Warning styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 0.75rem;
        padding: 1rem 1.5rem;
        border-left: 4px solid;
        background-color: rgba(30, 41, 59, 0.95);
        color: #f8fafc;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stSuccess {
        border-left-color: #22c55e;
    }

    .stError {
        border-left-color: #ef4444;
    }

    .stWarning {
        border-left-color: #f59e0b;
    }

    .stInfo {
        border-left-color: #3b82f6;
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
        color: #f8fafc;
    }

    .stSidebar [data-testid="stMarkdownContainer"] {
        padding-left: 1rem;
        color: #f8fafc;
    }

    /* Expander styling */
    .stExpander {
        border: 1px solid #334155;
        border-radius: 0.75rem;
        background-color: #1e293b;
    }

    .stExpander > div[role="button"] {
        background-color: #0f172a;
        padding: 1rem;
        font-weight: 600;
        color: #f8fafc;
    }

    /* DataFrame styling */
    [data-testid="dataframe"] {
        border-radius: 0.75rem;
        border: 1px solid #334155;
        overflow: hidden;
        background-color: #1e293b;
        color: #f8fafc;
    }

    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #334155;
        margin: 2rem 0;
    }

    /* Loading spinner */
    .stSpinner > div > div {
        border-color: #3b82f6;
    }

    /* Caption and small text */
    .stCaption {
        color: #94a3b8;
        font-size: 0.875rem;
    }

    /* Link styling */
    a {
        color: #60a5fa;
        text-decoration: none;
        font-weight: 500;
    }

    a:hover {
        text-decoration: underline;
    }
</style>
"""


def apply_custom_styling():
    """Apply custom CSS to Streamlit app"""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def apply_plotly_theme(fig):
    """Apply professional theme to Plotly figure"""
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


def get_sentiment_color(sentiment: str) -> str:
    """Get color for sentiment label"""
    sentiment_lower = str(sentiment).lower()
    if "positive" in sentiment_lower or "bullish" in sentiment_lower:
        return SENTIMENT_COLORS["positive"]
    elif "negative" in sentiment_lower or "bearish" in sentiment_lower:
        return SENTIMENT_COLORS["negative"]
    else:
        return SENTIMENT_COLORS["neutral"]


def get_chart_color_scale(n_colors: int = 7) -> list:
    """Get a color scale for multi-series charts"""
    return PLOTLY_TEMPLATE["layout"]["colorway"][:n_colors]