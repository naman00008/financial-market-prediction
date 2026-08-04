"""
Authentication UI and Session Management Component
Renders the professional login/signup portal, handles authentication flows,
and manages user session state in Streamlit.
"""

import streamlit as st
from typing import Optional, Dict, Any
from src.auth import authenticate_user, register_user, init_auth_db


def init_session_auth() -> None:
    """Initialize authentication keys in Streamlit session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"


def logout_user() -> None:
    """Log out the active user and reset session state."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def login_user(user_data: Dict[str, Any]) -> None:
    """Set active user session and trigger rerun."""
    st.session_state.authenticated = True
    st.session_state.user = user_data
    st.rerun()


def render_auth_page() -> None:
    """Render the executive Login and Sign Up landing experience."""
    init_auth_db()
    
    st.markdown("""
        <div class="auth-hero-banner">
            <div class="auth-badge">MARKET INTELLIGENCE TERMINAL</div>
            <h1 class="auth-title">Financial Market Prediction & Analytics</h1>
            <p class="auth-subtitle">
                Institutional-grade real-time market analytics, automated NLP sentiment scoring, 
                and machine learning price forecasting for Indian equities.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_hero, col_form = st.columns([1.1, 1], gap="large")

    with col_hero:
        st.markdown("""
            <div class="auth-feature-box">
                <h3 style="color: #38bdf8; margin-top: 0; font-size: 1.15rem; letter-spacing: 0.5px;">System Capabilities</h3>
                <div class="auth-feature-item">
                    <div style="width: 8px; height: 8px; background: #38bdf8; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></div>
                    <div>
                        <strong style="color: #f1f5f9;">Sub-Minute Real-Time Streaming:</strong>
                        <p style="color: #94a3b8; font-size: 0.88rem; margin: 2px 0 0 0; line-height: 1.4;">
                            Live NSE & BSE ticker prices, interactive candlesticks, and volume overlays.
                        </p>
                    </div>
                </div>
                <div class="auth-feature-item">
                    <div style="width: 8px; height: 8px; background: #38bdf8; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></div>
                    <div>
                        <strong style="color: #f1f5f9;">Machine Learning Price Forecasting:</strong>
                        <p style="color: #94a3b8; font-size: 0.88rem; margin: 2px 0 0 0; line-height: 1.4;">
                            Random Forest & XGBoost predictive models with directional accuracy hit rates.
                        </p>
                    </div>
                </div>
                <div class="auth-feature-item">
                    <div style="width: 8px; height: 8px; background: #38bdf8; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></div>
                    <div>
                        <strong style="color: #f1f5f9;">Financial News Sentiment Engine:</strong>
                        <p style="color: #94a3b8; font-size: 0.88rem; margin: 2px 0 0 0; line-height: 1.4;">
                            Live headline aggregation from news feeds with compound impact ratings.
                        </p>
                    </div>
                </div>
                <div class="auth-feature-item">
                    <div style="width: 8px; height: 8px; background: #38bdf8; border-radius: 50%; margin-top: 6px; flex-shrink: 0;"></div>
                    <div>
                        <strong style="color: #f1f5f9;">Portfolio Risk & Sharpe Optimization:</strong>
                        <p style="color: #94a3b8; font-size: 0.88rem; margin: 2px 0 0 0; line-height: 1.4;">
                            Multi-stock covariance matrix, efficient frontier mapping, and drawdown tracking.
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 10px; padding: 16px; margin-top: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Data Pipeline</span>
                        <div style="color: #10b981; font-weight: 600; font-size: 0.9rem; margin-top: 2px;">LIVE / CONNECTED</div>
                    </div>
                    <div>
                        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Refresh Rate</span>
                        <div style="color: #38bdf8; font-weight: 600; font-size: 0.9rem; margin-top: 2px;">60s Interval</div>
                    </div>
                    <div>
                        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Encryption</span>
                        <div style="color: #a855f7; font-weight: 600; font-size: 0.9rem; margin-top: 2px;">PBKDF2-SHA256</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown('<div class="auth-card-container">', unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        # ==========================================
        # LOGIN TAB
        # ==========================================
        with tab_login:
            st.markdown("<h3 style='margin-top: 0; color: #f8fafc; font-size: 1.2rem;'>Access Terminal</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 0.88rem; margin-bottom: 1rem;'>Enter credentials to authenticate session.</p>", unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                username_input = st.text_input("Username or Email", placeholder="demo_user or email@domain.com")
                password_input = st.text_input("Password", type="password", placeholder="••••••••")
                
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    if not username_input or not password_input:
                        st.error("Please enter both username/email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            success, message, user_data = authenticate_user(username_input, password_input)
                            if success and user_data:
                                st.success(f"{message}")
                                login_user(user_data)
                            else:
                                st.error(message)

            st.markdown("<div style='height: 1px; background: #334155; margin: 1.2rem 0;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px;'>Evaluation Accounts</p>", unsafe_allow_html=True)
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Pro Trader Demo", use_container_width=True, help="Authenticate as Pro Trader with ML and Portfolio access"):
                    success, msg, user_data = authenticate_user("demo_user", "demo123")
                    if success and user_data:
                        login_user(user_data)
            with btn_col2:
                if st.button("Administrator Demo", use_container_width=True, help="Authenticate with administrative privileges"):
                    success, msg, user_data = authenticate_user("admin", "admin123")
                    if success and user_data:
                        login_user(user_data)

        # ==========================================
        # SIGN UP TAB
        # ==========================================
        with tab_signup:
            st.markdown("<h3 style='margin-top: 0; color: #f8fafc; font-size: 1.2rem;'>Register Account</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 0.88rem; margin-bottom: 1rem;'>Create an account to access real-time market data.</p>", unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                new_fullname = st.text_input("Full Name", placeholder="e.g. Alex Sharma")
                new_username = st.text_input("Username", placeholder="e.g. asharma")
                new_email = st.text_input("Email Address", placeholder="e.g. alex@domain.com")
                new_password = st.text_input("Password (min 6 chars)", type="password", placeholder="••••••••")
                new_confirm_pwd = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                
                selected_tier = st.selectbox(
                    "Account Tier",
                    options=["pro", "free"],
                    format_func=lambda x: "Pro Tier (Full access: ML Forecasting, NLP Sentiment, Portfolio)" if x == "pro" else "Standard Tier (Market Data & Analytics)"
                )
                
                signup_submitted = st.form_submit_button("Register Account", use_container_width=True)
                
                if signup_submitted:
                    if not new_username or not new_email or not new_password:
                        st.error("Please fill in all required fields.")
                    elif new_password != new_confirm_pwd:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        with st.spinner("Creating account..."):
                            reg_ok, reg_msg = register_user(
                                username=new_username,
                                email=new_email,
                                password=new_password,
                                full_name=new_fullname,
                                tier=selected_tier
                            )
                            if reg_ok:
                                st.success(f"{reg_msg}")
                                auth_ok, auth_msg, user_data = authenticate_user(new_username, new_password)
                                if auth_ok and user_data:
                                    login_user(user_data)
                            else:
                                st.error(reg_msg)

        st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar_user_profile() -> None:
    """Render the logged in user profile and sign out controls in the sidebar."""
    user = st.session_state.get("user")
    if not user:
        return

    full_name = user.get("full_name", user.get("username", "User"))
    username = user.get("username", "user")
    tier = user.get("tier", "free").lower()

    tier_config = {
        "admin": ("ADMINISTRATOR", "#8b5cf6", "rgba(139, 92, 246, 0.15)"),
        "pro": ("PRO TIER", "#38bdf8", "rgba(56, 189, 248, 0.15)"),
        "free": ("STANDARD TIER", "#10b981", "rgba(16, 185, 129, 0.15)"),
    }
    badge_text, badge_color, badge_bg = tier_config.get(tier, tier_config["free"])

    st.sidebar.markdown(f"""
        <div class="sidebar-user-card">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="user-avatar-circle">{username[:2].upper()}</div>
                <div style="flex: 1; overflow: hidden;">
                    <div style="font-weight: 600; font-size: 0.92rem; color: #f8fafc; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">
                        {full_name}
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8;">@{username}</div>
                </div>
            </div>
            <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;">
                    {badge_text}
                </span>
                <span style="color: #64748b; font-size: 0.72rem; font-weight: 500;">ACTIVE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Sign Out", use_container_width=True, help="End active session"):
        logout_user()


def require_auth() -> Optional[Dict[str, Any]]:
    """
    Main authentication gatekeeper.
    Returns user dict if authenticated; otherwise displays auth screen and returns None.
    """
    init_session_auth()
    
    if not st.session_state.get("authenticated", False) or not st.session_state.get("user"):
        render_auth_page()
        return None
    
    render_sidebar_user_profile()
    return st.session_state.user
