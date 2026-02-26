"""
Harris Farm Hub — User Management
Admin-only page for managing Hub users, roles, and access permissions.
"""

import streamlit as st
import os
import requests
from datetime import datetime
from shared.styles import (
    render_header, render_footer,
    GREEN, BLUE, GOLD, RED, ORANGE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    NAVY_CARD, BORDER,
)


def render_user_management():
    user = st.session_state.get("auth_user", {})

    # Admin check
    if not user or user.get("role") != "admin":
        st.warning("This page is only accessible to administrators.")
        return

    render_header(
        "User Management",
        "Manage Hub users, roles, and access permissions",
    )

    API_URL = os.getenv("API_URL", "http://localhost:8000")
    token = st.session_state.get("auth_token", "")
    headers = {"X-Auth-Token": token}

    # ------------------------------------------------------------------
    # Fetch users from backend
    # ------------------------------------------------------------------
    users_list = []
    fetch_error = None
    try:
        resp = requests.get(
            "{}/api/auth/admin/users".format(API_URL),
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            users_list = resp.json().get("users", [])
        else:
            fetch_error = "Failed to load users (HTTP {})".format(resp.status_code)
    except requests.exceptions.RequestException as e:
        fetch_error = "Could not connect to backend: {}".format(str(e))

    if fetch_error:
        st.error(fetch_error)

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    tab_active, tab_pending, tab_roles = st.tabs([
        "Active Users",
        "Pending Approvals",
        "Role Summary",
    ])

    # ==================================================================
    # Tab 1: Active Users
    # ==================================================================
    with tab_active:
        if not users_list:
            st.info("No users found.")
        else:
            st.markdown("### {} registered users".format(len(users_list)))
            st.markdown("")

            # Import role options for the hub_role selector
            try:
                from shared.role_config import get_all_roles
                role_options = get_all_roles()  # list of (key, display_name)
            except ImportError:
                role_options = [
                    ("user", "General"),
                    ("executive", "Executive"),
                    ("store_manager", "Store Manager"),
                    ("buyer", "Buyer / Procurement"),
                    ("marketing", "Marketing"),
                    ("people_culture", "People & Culture"),
                    ("finance", "Finance / Analyst"),
                    ("viewer", "Viewer"),
                ]

            role_keys = [k for k, _ in role_options]
            role_labels = [v for _, v in role_options]

            for idx, u in enumerate(users_list):
                uid = u.get("id", idx)
                u_name = u.get("name", "Unknown")
                u_email = u.get("email", "")
                u_role = u.get("role", "user")
                u_hub_role = u.get("hub_role", "user")
                u_active = u.get("active", 1)
                u_last_login = u.get("updated_at", u.get("created_at", "N/A"))
                status_label = "Active" if u_active else "Inactive"

                with st.expander("{} -- {} ({})".format(u_name, u_email, status_label)):
                    col_info, col_actions = st.columns([3, 2])

                    with col_info:
                        st.markdown("**Name:** {}".format(u_name))
                        st.markdown("**Email:** {}".format(u_email))
                        st.markdown("**System Role:** {}".format(u_role))
                        st.markdown("**Hub Role:** {}".format(u_hub_role))
                        st.markdown("**Status:** {}".format(status_label))
                        st.markdown("**Last Updated:** {}".format(u_last_login))

                    with col_actions:
                        # Hub role selector
                        current_idx = 0
                        if u_hub_role in role_keys:
                            current_idx = role_keys.index(u_hub_role)

                        new_role = st.selectbox(
                            "Hub Role",
                            options=role_keys,
                            format_func=lambda k: role_labels[role_keys.index(k)] if k in role_keys else k,
                            index=current_idx,
                            key="role_select_{}".format(uid),
                        )

                        # Update button
                        if st.button("Update Role", key="update_btn_{}".format(uid)):
                            try:
                                put_resp = requests.put(
                                    "{}/api/auth/admin/users/{}".format(API_URL, uid),
                                    headers=headers,
                                    json={"hub_role": new_role},
                                    timeout=10,
                                )
                                if put_resp.status_code == 200:
                                    st.success("Updated {} to role: {}".format(u_name, new_role))
                                    st.rerun()
                                else:
                                    st.error("Update failed (HTTP {})".format(put_resp.status_code))
                            except requests.exceptions.RequestException as e:
                                st.error("Request failed: {}".format(str(e)))

                        st.markdown("")

                        # Deactivate button (skip for current user)
                        current_user_id = user.get("id")
                        if uid != current_user_id and u_active:
                            if st.button("Deactivate User", key="deactivate_btn_{}".format(uid)):
                                try:
                                    del_resp = requests.delete(
                                        "{}/api/auth/admin/users/{}".format(API_URL, uid),
                                        headers=headers,
                                        timeout=10,
                                    )
                                    if del_resp.status_code == 200:
                                        st.success("Deactivated {}".format(u_name))
                                        st.rerun()
                                    else:
                                        st.error("Deactivation failed (HTTP {})".format(del_resp.status_code))
                                except requests.exceptions.RequestException as e:
                                    st.error("Request failed: {}".format(str(e)))

    # ==================================================================
    # Tab 2: Pending Approvals
    # ==================================================================
    with tab_pending:
        st.markdown("### Pending Approvals")
        st.info(
            "Approval workflow coming soon. "
            "Currently all signups are auto-approved."
        )
        st.markdown(
            "When the `approved` column is added to the users table, "
            "new signups will require admin approval before they can access the Hub."
        )

    # ==================================================================
    # Tab 3: Role Summary
    # ==================================================================
    with tab_roles:
        st.markdown("### Role Definitions")
        st.markdown("")

        try:
            from shared.role_config import ROLE_DEFINITIONS, get_role_pages
        except ImportError:
            st.error("Could not load role_config module.")
            render_footer("User Management", user=user)
            return

        # Count users per role from the fetched users list
        role_counts = {}
        for u in users_list:
            r = u.get("hub_role", u.get("role", "user"))
            role_counts[r] = role_counts.get(r, 0) + 1

        # Build summary data
        rows = []
        for role_key, role_def in ROLE_DEFINITIONS.items():
            display_name = role_def.get("display_name", role_key)
            description = role_def.get("description", "")
            allowed = role_def.get("allowed_slugs", [])
            if allowed == "all":
                page_count = "All"
            else:
                page_count = str(len(allowed))
            user_count = role_counts.get(role_key, 0)
            rows.append({
                "Role Key": role_key,
                "Display Name": display_name,
                "Description": description,
                "Pages": page_count,
                "Users": user_count,
            })

        # Display as a table
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No roles defined.")

        st.markdown("")
        st.caption(
            "Roles control which pages a user sees in the Hub navigation. "
            "Admin and General (user) roles have access to all pages."
        )

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    render_footer("User Management", user=user)


render_user_management()
