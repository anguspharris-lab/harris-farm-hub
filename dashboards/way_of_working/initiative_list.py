"""
Way of Working — Initiative List Tab
Filterable table of all initiatives from all 5 Monday.com boards.
"""

import pandas as pd
import streamlit as st

from shared.monday_connector import fetch_board_items, BOARD_IDS
from shared.pillar_data import get_all_pillars


def _status_color(status):
    """Return a colour for a Monday.com status label."""
    colors = {
        "Done": "#2ECC71",
        "Complete": "#2ECC71",
        "Immediate requirements complete": "#2ECC71",
        "Working on it": "#2563eb",
        "In Progress": "#2563eb",
        "Stuck": "#dc2626",
        "Blocked": "#dc2626",
        "Future steps": "#9ca3af",
        "Not Started": "#9ca3af",
    }
    return colors.get(status, "#6b7280")


def render():
    pillars = get_all_pillars()

    # Fetch items from all boards
    all_items = []
    for pillar in pillars:
        pid = pillar["id"]
        board_id = BOARD_IDS.get(pid)
        if not board_id:
            continue
        items = fetch_board_items(board_id)
        for item in items:
            item["pillar"] = pillar["short_name"]
            item["pillar_id"] = pid
            item["pillar_icon"] = pillar["icon"]
        all_items.extend(items)

    if not all_items:
        st.info("No initiatives found. Check your Monday.com connection.")
        return

    df = pd.DataFrame(all_items)

    # ── Filters ──
    f1, f2, f3 = st.columns(3)
    with f1:
        pillar_options = ["All"] + [p["short_name"] for p in pillars]
        pillar_filter = st.selectbox("Pillar", pillar_options, key="wow_pillar_filter")
    with f2:
        status_vals = sorted(df["status"].unique().tolist())
        status_options = ["All"] + [s for s in status_vals if s]
        status_filter = st.selectbox("Status", status_options, key="wow_status_filter")
    with f3:
        owner_options = ["All"] + sorted(
            [o for o in df["owner"].unique().tolist() if o]
        )
        owner_filter = st.selectbox("Owner", owner_options, key="wow_owner_filter")

    # Apply filters
    filtered = df.copy()
    if pillar_filter != "All":
        filtered = filtered[filtered["pillar"] == pillar_filter]
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]
    if owner_filter != "All":
        filtered = filtered[filtered["owner"] == owner_filter]

    st.markdown(
        "**{} initiatives** shown (of {} total)".format(len(filtered), len(df))
    )

    # ── Table ──
    display_cols = ["pillar", "name", "status", "priority", "owner", "group", "timeline"]
    # Only include columns that exist in the dataframe
    available_cols = [c for c in display_cols if c in filtered.columns]

    display_labels = {
        "pillar": "Pillar",
        "name": "Initiative",
        "status": "Status",
        "priority": "Priority",
        "owner": "Owner",
        "group": "Outcome",
        "timeline": "Timeline",
    }

    if not filtered.empty:
        show_df = filtered[available_cols].rename(
            columns={c: display_labels.get(c, c) for c in available_cols}
        )
        st.dataframe(
            show_df,
            use_container_width=True,
            hide_index=True,
            height=min(600, 35 * len(show_df) + 38),
        )

        # ── Export ──
        csv = show_df.to_csv(index=False)
        st.download_button(
            "\U0001f4e5 Export to CSV",
            csv,
            file_name="harris_farm_initiatives.csv",
            mime="text/csv",
            key="wow_export_csv",
        )
    else:
        st.info("No initiatives match the selected filters.")
