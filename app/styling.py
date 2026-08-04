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

    /* Auth Page Hero Banner */
    .auth-hero-banner {
        text-align: center;
        padding: 2.5rem 1.5rem 1.8rem 1.5rem;
        background: radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.25) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid #1e3a8a;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }

    .auth-badge {
        display: inline-block;
        background: rgba(37, 99, 235, 0.2);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
    }

    .auth-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.25rem 0 0.75rem 0;
    }

    .auth-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Auth Feature Showcase Box */
    .auth-feature-box {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 1rem;
        padding: 1.75rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }

    .auth-feature-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 1.25rem;
    }

    .auth-feature-icon {
        font-size: 1.4rem;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #334155;
        padding: 6px 10px;
        border-radius: 8px;
    }

    /* Auth Card Form */
    .auth-card-container {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid #334155;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    /* Sidebar User Profile Card */
    .sidebar-user-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .user-avatar-circle {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.9rem;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4);
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