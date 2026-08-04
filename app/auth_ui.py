"""
Institutional Authentication UI & Feature Gatekeeper
Provides professional, secure single-point authentication and automated
user directory management. No shortcuts, demo bypasses, or playful elements.
"""

import streamlit as st
from typing import Optional, Dict, Any
from src.auth import authenticate_user, register_user, init_auth_db
from src.tracker import track_activity


def init_session_auth() -> None:
    """Initialize authentication state in Streamlit session."""
    init_auth_db()
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def logout_user() -> None:
    """Log out active session and record audit event."""
    user = st.session_state.get("user")
    uname = user.get("username") if user else "guest"
    track_activity("USER_LOGOUT", username=uname, details={"reason": "user_initiated"})
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def login_user(user_data: Dict[str, Any]) -> None:
    """Set active user session and trigger interface refresh."""
    st.session_state.authenticated = True
    st.session_state.user = user_data
    track_activity("SESSION_STARTED", username=user_data.get("username"), details={"tier": user_data.get("tier")})
    st.rerun()


def is_authenticated() -> bool:
    """Check if current session is authenticated."""
    return bool(st.session_state.get("authenticated", False) and st.session_state.get("user"))


def render_sidebar_auth_widget() -> None:
    """
    Render professional user profile in sidebar if authenticated.
    Keeps sidebar completely clean and unobtrusive for guests.
    """
    init_session_auth()
    user = st.session_state.get("user")

    if is_authenticated() and user:
        full_name = user.get("full_name", user.get("username", "User"))
        username = user.get("username", "user")
        tier = user.get("tier", "pro").upper()

        st.sidebar.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid #1e293b; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 6px; background: #0284c7; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.5px;">
                        {username[:2].upper()}
                    </div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="color: #f8fafc; font-weight: 600; font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {full_name}
                        </div>
                        <div style="color: #64748b; font-size: 0.75rem;">@{username}</div>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center;">
                    <span style="background: rgba(14, 165, 233, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 2px 6px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.5px;">
                        {tier} MEMBER
                    </span>
                    <span style="color: #10b981; font-size: 0.72rem; font-weight: 600;">ACTIVE</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.sidebar.button("Sign Out", use_container_width=True):
            logout_user()


def render_feature_gate(feature_name: str, description: str, key_suffix: str = "default") -> bool:
    """
    Institutional Feature Gatekeeper:
    - Returns True if user is authenticated.
    - If unauthenticated, renders a single high-contrast institutional sign-in card.
    - No demo bypass shortcuts. Requires registered user login.
    """
    init_session_auth()
    
    if is_authenticated():
        return True

    # Track that an unauthenticated user arrived at this gated feature
    track_activity("VIEW_GATED_FEATURE_PROMPT", username="guest", details={"feature": feature_name})

    # Render clean, sleek locked header
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 2rem 2rem 1.8rem 2rem; margin: 1.5rem auto 2rem auto; text-align: center; max-width: 800px; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
            <div style="display: inline-block; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 4px 12px; font-size: 0.72rem; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.75rem;">
                RESTRICTED ACCESS
            </div>
            <h2 style="color: #ffffff; font-size: 1.75rem; font-weight: 700; margin: 0.25rem 0 0.75rem 0; letter-spacing: -0.02em;">
                {feature_name}
            </h2>
            <p style="color: #94a3b8; font-size: 0.92rem; max-width: 620px; margin: 0 auto; line-height: 1.5;">
                {description}
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 2.2, 1])

    with col_center:
        st.markdown("""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 1.5rem; box-shadow: 0 15px 35px -10px rgba(0,0,0,0.6);">
        """, unsafe_allow_html=True)

        tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

        # ==========================================
        # SIGN IN TAB
        # ==========================================
        with tab_signin:
            st.markdown("<p style='color: #64748b; font-size: 0.82rem; margin: 0.5rem 0 1rem 0;'>Enter your authorized credentials to access this analytics engine.</p>", unsafe_allow_html=True)
            
            with st.form(f"gate_auth_form_{key_suffix}"):
                login_id = st.text_input("Username or Email", placeholder="your.name@company.com", key=f"gate_u_{key_suffix}")
                login_pwd = st.text_input("Password", type="password", placeholder="••••••••", key=f"gate_p_{key_suffix}")
                
                auth_btn = st.form_submit_button("Sign In & Access Module", use_container_width=True)
                
                if auth_btn:
                    if not login_id or not login_pwd:
                        st.error("Please provide both username/email and password.")
                    else:
                        with st.spinner("Verifying credentials..."):
                            success, message, user_data = authenticate_user(login_id, login_pwd)
                            if success and user_data:
                                st.success("Authorization confirmed. Loading workspace...")
                                login_user(user_data)
                            else:
                                st.error(message)

        # ==========================================
        # REGISTER TAB
        # ==========================================
        with tab_register:
            st.markdown("<p style='color: #64748b; font-size: 0.82rem; margin: 0.5rem 0 1rem 0;'>Register a private account. Your dedicated user repository and workspace will be provisioned automatically.</p>", unsafe_allow_html=True)
            
            with st.form(f"gate_reg_form_{key_suffix}"):
                r_fullname = st.text_input("Full Name", placeholder="e.g. Alex Sharma", key=f"gate_r_fn_{key_suffix}")
                r_username = st.text_input("Username", placeholder="e.g. asharma", key=f"gate_r_un_{key_suffix}")
                r_email = st.text_input("Work or Personal Email", placeholder="e.g. alex@company.com", key=f"gate_r_em_{key_suffix}")
                r_pwd = st.text_input("Password (min 6 characters)", type="password", placeholder="••••••••", key=f"gate_r_pw_{key_suffix}")
                r_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••", key=f"gate_r_cp_{key_suffix}")
                
                reg_btn = st.form_submit_button("Register & Initialize Workspace", use_container_width=True)
                
                if reg_btn:
                    if not r_username or not r_email or not r_pwd:
                        st.error("Please complete all required registration fields.")
                    elif r_pwd != r_confirm:
                        st.error("Password confirmation does not match.")
                    elif len(r_pwd) < 6:
                        st.error("Password must be at least 6 characters in length.")
                    else:
                        with st.spinner("Provisioning user environment..."):
                            reg_ok, reg_msg = register_user(
                                username=r_username,
                                email=r_email,
                                password=r_pwd,
                                full_name=r_fullname,
                                tier="pro"
                            )
                            if reg_ok:
                                auth_ok, _, user_data = authenticate_user(r_username, r_pwd)
                                if auth_ok and user_data:
                                    st.success("Account provisioned. Entering workspace...")
                                    login_user(user_data)
                            else:
                                st.error(reg_msg)

        st.markdown("</div>", unsafe_allow_html=True)

    return False
