"""
Admin Portal & User Activity Viewer Component
Renders an executive control panel directly in the Streamlit dashboard
allowing administrators/owners to visually inspect all user folders, profiles,
and real-time user movement logs without using a terminal.
"""

import json
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from src.tracker import (
    get_all_registered_user_folders,
    get_user_activity_history,
    GLOBAL_LOG_PATH,
    USERS_DIR
)


def render_admin_dashboard_section():
    """Render the full administrative control panel and user audit monitor."""
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: inline-block; background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 2px 8px; font-size: 0.72rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">
                BACKEND CONTROL CENTER
            </div>
            <h3 style="color: #ffffff; margin: 0.5rem 0 0.25rem 0; font-size: 1.5rem;">User Directory & Activity Audit Portal</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0;">
                Live monitor of all provisioned user folders (<code style="color: #38bdf8;">data/users/</code>) and real-time user actions.
            </p>
        </div>
    """, unsafe_allow_html=True)

    admin_tabs = st.tabs(["User Directories", "User Action Timeline", "Global Activity Stream", "Filesystem Browser"])

    # ----------------------------------------------------
    # TAB 1: User Directories
    # ----------------------------------------------------
    with admin_tabs[0]:
        st.subheader("Registered Users & Account Folders")
        user_list = get_all_registered_user_folders()
        
        if not user_list:
            st.info("No registered user directories found yet in data/users/.")
        else:
            table_data = []
            for u in user_list:
                table_data.append({
                    "Username": f"@{u.get('username', 'N/A')}",
                    "Full Name": u.get("full_name", "N/A"),
                    "Email": u.get("email", "N/A"),
                    "Tier": u.get("tier", "pro").upper(),
                    "Registered (UTC)": u.get("registered_at", "N/A"),
                    "Last Active (UTC)": u.get("last_active", "N/A"),
                    "Actions Logged": u.get("total_actions_recorded", 0)
                })
            
            df_users = pd.DataFrame(table_data)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.caption(f"Total Provisioned User Folders: {len(user_list)}")

    # ----------------------------------------------------
    # TAB 2: User Action Timeline
    # ----------------------------------------------------
    with admin_tabs[1]:
        st.subheader("Individual User Activity Timeline")
        user_list = get_all_registered_user_folders()
        
        if not user_list:
            st.info("No user accounts found.")
        else:
            usernames = [u.get("username") for u in user_list if u.get("username")]
            selected_user = st.selectbox("Select User Account to Audit", usernames)
            
            if selected_user:
                history = get_user_activity_history(selected_user, limit=50)
                if not history:
                    st.info(f"No actions logged yet for @{selected_user}.")
                else:
                    st.markdown(f"**Chronological Activity Feed for @{selected_user}** ({len(history)} recent events)")
                    
                    hist_data = []
                    for h in history:
                        hist_data.append({
                            "Timestamp": h.get("timestamp"),
                            "Action Performed": h.get("action"),
                            "Parameters & Details": json.dumps(h.get("details", {}))
                        })
                    
                    df_hist = pd.DataFrame(hist_data)
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    # ----------------------------------------------------
    # TAB 3: Global Activity Stream
    # ----------------------------------------------------
    with admin_tabs[2]:
        st.subheader("Live Global Activity Stream")
        st.caption("All user interactions across the entire web platform.")
        
        if os.path.exists(GLOBAL_LOG_PATH):
            raw_lines = []
            try:
                with open(GLOBAL_LOG_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            raw_lines.append(json.loads(line.strip()))
            except Exception:
                pass

            if not raw_lines:
                st.info("No global events recorded yet.")
            else:
                recent = raw_lines[-50:][::-1]
                feed_data = []
                for r in recent:
                    feed_data.append({
                        "Timestamp": r.get("timestamp"),
                        "User": f"@{r.get('username', 'guest')}",
                        "Action": r.get("action"),
                        "Details": json.dumps(r.get("details", {}))
                    })
                df_global = pd.DataFrame(feed_data)
                st.dataframe(df_global, use_container_width=True, hide_index=True)
        else:
            st.info("No activity stream generated yet.")

    # ----------------------------------------------------
    # TAB 4: Filesystem Structure
    # ----------------------------------------------------
    with admin_tabs[3]:
        st.subheader("Backend Directory Tree (`data/users/`)")
        
        tree_output = []
        if os.path.exists(USERS_DIR):
            for root, dirs, files in os.walk(USERS_DIR):
                rel_root = os.path.relpath(root, os.path.dirname(USERS_DIR))
                level = rel_root.count(os.sep)
                indent = "  " * level
                tree_output.append(f"{indent}📁 {os.path.basename(root)}/")
                for f in files:
                    tree_output.append(f"{indent}  📄 {f}")
        
        if tree_output:
            st.code("\n".join(tree_output), language="text")
        else:
            st.code("data/users/\n  (empty)", language="text")
