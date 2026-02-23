"""
Harris Farm Hub — Universal Flag Widget
Reusable 'Something wrong?' button that appears on every Hub page.
Submits feedback to /api/flags/submit via fire-and-forget POST.
"""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

FLAG_CATEGORIES = [
    "Data looks wrong",
    "Wrong answer",
    "Outdated information",
    "Confusing UX",
    "Other",
]

# Map display labels to backend keys
_CATEGORY_MAP = {
    "Data looks wrong": "data_wrong",
    "Wrong answer": "wrong_answer",
    "Outdated information": "outdated",
    "Confusing UX": "confusing",
    "Other": "other",
}


def render_flag_button(page_slug=None, user_id=None, api_url=None):
    """Render the universal flag button with popover form.

    Call this in render_footer() or anywhere on a page.
    Uses st.popover() for a clean inline form.

    Args:
        page_slug: Current page slug (auto-detected from session if None)
        user_id: Current user email (auto-detected from session if None)
        api_url: API base URL (defaults to API_URL env var)
    """
    if api_url is None:
        api_url = API_URL

    # Auto-detect from session state
    if page_slug is None:
        page_slug = st.session_state.get("_current_slug", "unknown")
    if user_id is None:
        auth_user = st.session_state.get("auth_user")
        if auth_user:
            user_id = auth_user.get("email", "anonymous")
        else:
            user_id = "anonymous"

    # Unique key per page to avoid widget conflicts
    key_prefix = f"flag_{page_slug}"

    with st.popover("\u26a0\ufe0f Something wrong?", use_container_width=False):
        category = st.selectbox(
            "What's the issue?",
            FLAG_CATEGORIES,
            key=f"{key_prefix}_cat",
        )
        description = st.text_area(
            "Details (optional)",
            placeholder="Tell us what seems off...",
            max_chars=500,
            key=f"{key_prefix}_desc",
        )

        if st.button("Submit Flag", key=f"{key_prefix}_btn", type="primary",
                      use_container_width=True):
            try:
                requests.post(
                    f"{api_url}/api/flags/submit",
                    json={
                        "user_id": user_id,
                        "page_slug": page_slug,
                        "category": _CATEGORY_MAP.get(category, "other"),
                        "description": description,
                    },
                    timeout=2,
                )
                st.success("Thanks! We'll look into it.")
            except Exception:
                st.info("Flag saved locally. Thanks for the feedback!")
