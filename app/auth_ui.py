"""
Authentication UI and Session Management Component
Provides modular feature-level gatekeeping, sidebar profile widgets,
and modal login/signup interfaces for protected financial terminal features.
"""

import streamlit as st
from typing import Optional, Dict, Any
from src.auth import authenticate_user, register_user, init_auth_db


def init_session_auth() -> None:
    """Initialize authentication keys in Streamlit session state."""
    init_auth_db()
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


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


def is_authenticated() -> bool:
    """Check if the current session has an authenticated user."""
    return bool(st.session_state.get("authenticated", False) and st.session_state.get("user"))


def render_sidebar_auth_widget() -> None:
    """
    Render authentication controls in the sidebar:
    - If authenticated: user avatar, name, tier badge, and Sign Out button.
    - If unauthenticated: compact Sign In / Register expander with one-click demo.
    """
    init_session_auth()
    user = st.session_state.get("user")

    if is_authenticated() and user:
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
                    <span style="color: #64748b; font-size: 0.72rem; font-weight: 500;">AUTHENTICATED</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.sidebar.button("Sign Out", use_container_width=True, help="End active session"):
            logout_user()
    else:
        st.sidebar.markdown("""
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px;">Session Status</div>
                <div style="color: #f1f5f9; font-size: 0.88rem; font-weight: 500;">Guest Visitor</div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 2px;">Sign in below to unlock advanced analytics.</div>
            </div>
        """, unsafe_allow_html=True)

        with st.sidebar.expander("Sign In / Register", expanded=False):
            side_tab_login, side_tab_reg = st.tabs(["Sign In", "Register"])
            
            with side_tab_login:
                with st.form("sidebar_login_form"):
                    s_user = st.text_input("Username / Email", key="sb_login_user")
                    s_pass = st.text_input("Password", type="password", key="sb_login_pass")
                    s_btn = st.form_submit_button("Sign In", use_container_width=True)
                    if s_btn:
                        if not s_user or not s_pass:
                            st.error("Enter username and password.")
                        else:
                            ok, msg, udata = authenticate_user(s_user, s_pass)
                            if ok and udata:
                                login_user(udata)
                            else:
                                st.error(msg)
                
                if st.button("Quick Demo Login", key="sb_demo_btn", use_container_width=True):
                    ok, msg, udata = authenticate_user("demo_user", "demo123")
                    if ok and udata:
                        login_user(udata)

            with side_tab_reg:
                with st.form("sidebar_reg_form"):
                    r_name = st.text_input("Full Name", key="sb_reg_name")
                    r_user = st.text_input("Username", key="sb_reg_user")
                    r_email = st.text_input("Email", key="sb_reg_email")
                    r_pass = st.text_input("Password", type="password", key="sb_reg_pass")
                    r_btn = st.form_submit_button("Register", use_container_width=True)
                    if r_btn:
                        if not r_user or not r_email or not r_pass:
                            st.error("Please fill in required fields.")
                        else:
                            reg_ok, reg_msg = register_user(r_user, r_email, r_pass, r_name, "pro")
                            if reg_ok:
                                _, _, udata = authenticate_user(r_user, r_pass)
                                if udata:
                                    login_user(udata)
                            else:
                                st.error(reg_msg)


def render_feature_gate(feature_name: str, description: str, key_suffix: str = "default") -> bool:
    """
    Modular Feature Gatekeeper:
    - If user is authenticated, returns True and allows rendering the feature content.
    - If user is not authenticated, displays an institutional locked-feature portal
      with integrated login/signup and demo buttons, and returns False.
    """
    init_session_auth()
    
    if is_authenticated():
        return True

    # Render embedded professional gatekeeper
    st.markdown(f"""
        <div class="auth-hero-banner" style="margin-top: 1rem; padding: 2rem 1.5rem 1.5rem 1.5rem;">
            <div class="auth-badge">AUTHENTICATION REQUIRED</div>
            <h2 class="auth-title" style="font-size: 1.8rem;">{feature_name}</h2>
            <p class="auth-subtitle">
                {description}
            </p>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 8px;">
                Please sign in with your account or register for free access to unlock this module.
            </p>
        </div>
    """, unsafe_allow_html=True)

    gate_col1, gate_col2, gate_col3 = st.columns([1, 2.2, 1])

    with gate_col2:
        st.markdown('<div class="auth-card-container">', unsafe_allow_html=True)
        gate_tab_login, gate_tab_signup = st.tabs(["Sign In", "Create Account"])

        # ==========================================
        # GATE LOGIN TAB
        # ==========================================
        with gate_tab_login:
            st.markdown("<h4 style='margin-top: 0; color: #f8fafc;'>Sign In to Unlock</h4>", unsafe_allow_html=True)
            
            with st.form(f"gate_login_form_{key_suffix}"):
                username_input = st.text_input("Username or Email", placeholder="demo_user or email@domain.com", key=f"gate_u_{key_suffix}")
                password_input = st.text_input("Password", type="password", placeholder="••••••••", key=f"gate_p_{key_suffix}")
                submitted = st.form_submit_button("Authenticate & Unlock", use_container_width=True)
                
                if submitted:
                    if not username_input or not password_input:
                        st.error("Please enter both username/email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            success, message, user_data = authenticate_user(username_input, password_input)
                            if success and user_data:
                                st.success("Access Granted. Loading terminal...")
                                login_user(user_data)
                            else:
                                st.error(message)

            st.markdown("<div style='height: 1px; background: #334155; margin: 1rem 0;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 6px;'>Instant Access</p>", unsafe_allow_html=True)
            
            if st.button("Unlock with Pro Trader Demo", key=f"gate_demo_btn_{key_suffix}", use_container_width=True):
                success, msg, user_data = authenticate_user("demo_user", "demo123")
                if success and user_data:
                    login_user(user_data)

        # ==========================================
        # GATE SIGN UP TAB
        # ==========================================
        with gate_tab_signup:
            st.markdown("<h4 style='margin-top: 0; color: #f8fafc;'>Register Free Account</h4>", unsafe_allow_html=True)
            
            with st.form(f"gate_signup_form_{key_suffix}"):
                new_fullname = st.text_input("Full Name", placeholder="e.g. Alex Sharma", key=f"gate_r_fn_{key_suffix}")
                new_username = st.text_input("Username", placeholder="e.g. asharma", key=f"gate_r_un_{key_suffix}")
                new_email = st.text_input("Email Address", placeholder="e.g. alex@domain.com", key=f"gate_r_em_{key_suffix}")
                new_password = st.text_input("Password (min 6 chars)", type="password", placeholder="••••••••", key=f"gate_r_pw_{key_suffix}")
                new_confirm_pwd = st.text_input("Confirm Password", type="password", placeholder="••••••••", key=f"gate_r_cp_{key_suffix}")
                
                signup_submitted = st.form_submit_button("Create Account & Unlock", use_container_width=True)
                
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
                                tier="pro"
                            )
                            if reg_ok:
                                auth_ok, auth_msg, user_data = authenticate_user(new_username, new_password)
                                if auth_ok and user_data:
                                    login_user(user_data)
                            else:
                                st.error(reg_msg)

        st.markdown('</div>', unsafe_allow_html=True)

    return False
