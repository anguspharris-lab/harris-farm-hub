"""
Harris Farm Hub — User Management
Admin-only page for managing Hub users, roles, and access permissions.
"""

import streamlit as st
import os
import requests
from shared.styles import render_header, render_footer


def render_user_management():
    user = st.session_state.get("auth_user", {})

    # Admin check — allow both role and hub_role to match
    is_admin = (
        user.get("role") == "admin"
        or user.get("hub_role") == "admin"
    )
    if not user or not is_admin:
        st.warning("This page is only accessible to administrators.")
        return

    render_header(
        "User Management",
        "Manage Hub users, roles, and access permissions",
    )

    API_URL = os.getenv("API_URL", "http://localhost:8000")
    token = st.session_state.get("auth_token", "")
    headers = {"X-Auth-Token": token} if token else {}

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
            st.info("No users found. If running locally with AUTH_ENABLED=false, no users are stored in the local database.")
        else:
            st.markdown("### {} registered users".format(len(users_list)))
            st.markdown("")

            # Import role options for the hub_role selector
            try:
                from shared.role_config import get_all_roles
                role_options = get_all_roles()
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
            # Build a lookup dict for format_func (avoids closure issues)
            role_label_map = dict(role_options)

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
                            format_func=lambda k, m=role_label_map: m.get(k, k),
                            index=current_idx,
                            key="role_select_{}".format(uid),
                        )

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

    # ==================================================================
    # Tab 3: Role Summary
    # ==================================================================
    with tab_roles:
        st.markdown("### Role Definitions")
        st.markdown("")

        try:
            from shared.role_config import ROLE_DEFINITIONS
        except ImportError:
            st.error("Could not load role_config module.")
            render_footer("User Management", user=user)
            return

        role_counts = {}
        for u in users_list:
            r = u.get("hub_role", u.get("role", "user"))
            role_counts[r] = role_counts.get(r, 0) + 1

        rows = []
        for role_key, role_def in ROLE_DEFINITIONS.items():
            display_name = role_def.get("display_name", role_key)
            description = role_def.get("description", "")
            allowed = role_def.get("allowed_slugs", [])
            page_count = "All" if allowed == "all" else str(len(allowed))
            user_count = role_counts.get(role_key, 0)
            rows.append({
                "Role Key": role_key,
                "Display Name": display_name,
                "Description": description,
                "Pages": page_count,
                "Users": user_count,
            })

        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No roles defined.")

        st.markdown("")
        st.caption(
            "Roles control which pages a user sees in the Hub navigation. "
            "Admin and General (user) roles have access to all pages."
        )

    render_footer("User Management", user=user)


render_user_management()
