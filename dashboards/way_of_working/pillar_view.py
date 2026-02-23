"""
Way of Working — Pillar View Tab
Per-pillar initiative breakdown with status donut and owner distribution.
"""

import pandas as pd
import streamlit as st

from shared.monday_connector import fetch_board_items, fetch_board_name, BOARD_IDS
from shared.pillar_data import get_all_pillars, get_pillar
from shared.styles import HFM_DARK


def render():
    pillars = get_all_pillars()

    selected_pid = st.selectbox(
        "Select Pillar",
        [p["id"] for p in pillars],
        format_func=lambda pid: "{} {}".format(
            get_pillar(pid).get("icon", ""),
            get_pillar(pid).get("name", pid),
        ),
        key="wow_pillar_select",
    )

    pillar = get_pillar(selected_pid)
    board_id = BOARD_IDS.get(selected_pid)
    if not board_id:
        st.warning("No board configured for this pillar.")
        return

    items = fetch_board_items(board_id)
    board_name = fetch_board_name(board_id)

    if not items:
        st.info("No initiatives found for {}.".format(
            pillar.get("short_name", selected_pid)))
        return

    df = pd.DataFrame(items)
    color = pillar.get("color", "#2ECC71")

    # ── Pillar header ──
    st.markdown(
        "<div style='border-left:4px solid {};padding:12px 16px;"
        "background:rgba(255,255,255,0.05);border-radius:0 8px 8px 0;"
        "margin-bottom:16px;'>"
        "<div style='font-size:1.3em;font-weight:700;color:{};'>"
        "{} {}</div>"
        "<div style='color:#8899AA;font-size:0.9em;font-style:italic;'>"
        "{}</div>"
        "</div>".format(
            color, HFM_DARK,
            pillar.get("icon", ""), board_name or pillar.get("name", ""),
            pillar.get("tagline", ""),
        ),
        unsafe_allow_html=True,
    )

    # ── KPIs ──
    total = len(df)
    done = len(df[df["status_category"] == "done"])
    ip = len(df[df["status_category"] == "in_progress"])
    stuck = len(df[df["status_category"] == "stuck"])
    ns = len(df[df["status_category"] == "not_started"])
    pct = int((done / total) * 100) if total > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total", total)
    k2.metric("Done", done)
    k3.metric("In Progress", ip)
    k4.metric("Stuck", stuck)
    k5.metric("Not Started", ns)

    # ── Charts row ──
    col_chart, col_owners = st.columns(2)

    with col_chart:
        st.markdown("**Status Breakdown**")
        try:
            import plotly.graph_objects as go
            # Use actual status labels (not categories) for richer view
            status_counts = df["status"].value_counts()
            status_colors = {
                "Done": "#2ECC71", "Complete": "#2ECC71",
                "Immediate requirements complete": "#059669",
                "Working on it": "#2563eb", "In Progress": "#3b82f6",
                "Stuck": "#dc2626", "Blocked": "#ef4444",
                "Future steps": "#8899AA", "Not Started": "#d1d5db",
            }
            labels = status_counts.index.tolist()
            values = status_counts.values.tolist()
            colors = [status_colors.get(s, "#8899AA") for s in labels]

            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                marker=dict(colors=colors),
                hole=0.45, textinfo="label+value",
            )])
            fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for status, count in status_counts.items():
                st.write("{}: {}".format(status, count))

    # ── Owner distribution ──
    with col_owners:
        st.markdown("**By Owner**")
        owners = df[df["owner"] != ""]["owner"].value_counts().head(10)
        if not owners.empty:
            for owner_name, count in owners.items():
                pct_bar = int((count / total) * 100)
                st.markdown(
                    "<div style='display:flex;align-items:center;gap:8px;"
                    "margin:4px 0;'>"
                    "<span style='font-size:0.85em;min-width:140px;"
                    "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                    "{}</span>"
                    "<div style='flex:1;background:rgba(255,255,255,0.1);border-radius:4px;"
                    "height:8px;'>"
                    "<div style='background:{};height:8px;border-radius:4px;"
                    "width:{}%;'></div></div>"
                    "<span style='font-size:0.8em;color:#8899AA;min-width:30px;"
                    "text-align:right;'>{}</span>"
                    "</div>".format(owner_name, color, pct_bar, count),
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No owner data available.")

    # ── Initiatives grouped by Outcome ──
    st.markdown("---")
    st.subheader("Initiatives by Outcome")

    groups = sorted(df["group"].unique())
    for group in groups:
        group_df = df[df["group"] == group]
        # Shorten long group names for display
        display_group = group if len(group) <= 80 else group[:77] + "..."
        with st.expander(
            "{} ({} initiatives)".format(display_group, len(group_df)),
            expanded=False,
        ):
            for _, row in group_df.iterrows():
                cat = row.get("status_category", "not_started")
                icon_map = {
                    "done": "\u2705",
                    "in_progress": "\U0001f7e1",
                    "stuck": "\U0001f534",
                    "not_started": "\u26aa",
                }
                status_icon = icon_map.get(cat, "\u26aa")

                owner_str = ""
                if row.get("owner"):
                    owner_str = " \u2014 {}".format(row["owner"])

                timeline_str = ""
                if row.get("timeline"):
                    timeline_str = " \u2014 \U0001f4c5 {}".format(row["timeline"])

                st.markdown(
                    "{} **{}** _{}_{}{}".format(
                        status_icon, row["name"],
                        row.get("status") or "Not Started",
                        owner_str, timeline_str,
                    )
                )
