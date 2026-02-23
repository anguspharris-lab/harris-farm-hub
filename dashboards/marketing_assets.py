"""
Marketing Assets Library
Browse and download Harris Farm marketing collateral.
"""

import json
import os
from pathlib import Path

import streamlit as st

from shared.styles import HFM_GREEN, HFM_DARK


_HUB_ROOT = Path(__file__).resolve().parent.parent
_CATALOGUE_PATH = _HUB_ROOT / "marketing-assets" / "index.json"

# Category display metadata
_CATEGORY_META = {
    "brand": {"label": "Brand", "icon": "\U0001f3a8", "color": HFM_GREEN},
    "campaigns/amazon": {"label": "Amazon Ads", "icon": "\U0001f6d2", "color": "#f59e0b"},
    "campaigns/ecomm": {"label": "eCommerce", "icon": "\U0001f4e6", "color": "#3b82f6"},
    "campaigns/weekend-specials": {"label": "Weekend Specials", "icon": "\u2b50", "color": "#ef4444"},
    "campaigns/ooh": {"label": "Out of Home", "icon": "\U0001f5bc\ufe0f", "color": "#8b5cf6"},
    "campaigns/butcher": {"label": "Butcher Campaign", "icon": "\U0001f969", "color": "#b91c1c"},
}

_TYPE_ICONS = {
    "pdf": "\U0001f4c4",
    "png": "\U0001f5bc\ufe0f",
    "jpg": "\U0001f5bc\ufe0f",
    "jpeg": "\U0001f5bc\ufe0f",
    "mov": "\U0001f3ac",
    "mp4": "\U0001f3ac",
}


def _load_catalogue():
    """Load asset catalogue from index.json."""
    if not _CATALOGUE_PATH.exists():
        return {"assets": [], "video_links": []}
    with open(_CATALOGUE_PATH) as f:
        return json.load(f)


def _render_asset_card(asset):
    """Render a single asset as a card with preview and download."""
    file_path = _HUB_ROOT / asset["path"]
    icon = _TYPE_ICONS.get(asset["type"], "\U0001f4c1")
    cat_meta = _CATEGORY_META.get(asset["category"], {})
    cat_label = cat_meta.get("label", asset["category"])
    cat_color = cat_meta.get("color", "#6b7280")

    col_preview, col_info, col_action = st.columns([1, 3, 1])

    with col_preview:
        if asset["type"] in ("jpg", "jpeg", "png") and file_path.exists():
            st.image(str(file_path), width=120)
        else:
            st.markdown(
                "<div style='width:120px;height:80px;background:rgba(255,255,255,0.05);"
                "border-radius:8px;display:flex;align-items:center;"
                "justify-content:center;font-size:2em;'>{}</div>".format(icon),
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown("**{}**".format(asset["title"]))
        badge = (
            "<span style='background:{};color:white;padding:2px 8px;"
            "border-radius:4px;font-size:0.75em;font-weight:600;'>"
            "{}</span>".format(cat_color, cat_label)
        )
        st.markdown(
            "{} &nbsp; {} &nbsp; {:.1f} MB".format(
                badge,
                asset["type"].upper(),
                asset["size_mb"],
            ),
            unsafe_allow_html=True,
        )
        st.caption(asset["description"])

    with col_action:
        if file_path.exists():
            with open(file_path, "rb") as fh:
                st.download_button(
                    "\u2b07 Download",
                    fh.read(),
                    file_name=asset["filename"],
                    key="dl_{}".format(asset["id"]),
                )
        else:
            st.caption("File not found")


def _render_video_links(video_links):
    """Render external video link placeholders."""
    if not video_links:
        return

    st.markdown("---")
    st.subheader("\U0001f3ac Video Assets")
    st.caption("Large video files hosted externally. Add Google Drive links to index.json to activate.")

    for v in video_links:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("**{}**".format(v["title"]))
            st.caption("{} \u2014 {} MB \u2014 {}".format(
                v["description"], v["size_mb"], v["type"].upper()
            ))
        with col2:
            url = v.get("external_url", "")
            if url:
                st.link_button("\U0001f517 Open", url)
            else:
                st.caption("\u23f3 Link pending")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='border-left:4px solid {};padding:12px 16px;"
    "background:rgba(255,255,255,0.05);border-radius:0 8px 8px 0;"
    "border:1px solid rgba(255,255,255,0.08);margin-bottom:20px;'>"
    "<div style='font-size:1.4em;font-weight:700;color:{};'>"
    "\U0001f4c1 Marketing Assets</div>"
    "<div style='color:#8899AA;font-size:0.9em;'>"
    "Harris Farm's centralised library of brand assets, campaign creatives, "
    "and marketing collateral.</div>"
    "</div>".format(HFM_GREEN, HFM_DARK),
    unsafe_allow_html=True,
)

catalogue = _load_catalogue()
assets = catalogue.get("assets", [])

if not assets:
    st.warning("No marketing assets found. Check marketing-assets/index.json.")
    st.stop()

# Category filter
categories = sorted(set(a["category"] for a in assets))
cat_labels = ["All"] + [
    _CATEGORY_META.get(c, {}).get("label", c) for c in categories
]
cat_lookup = {_CATEGORY_META.get(c, {}).get("label", c): c for c in categories}

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    selected_label = st.selectbox("Category", cat_labels, key="ma_category")
with f2:
    type_options = ["All"] + sorted(set(a["type"] for a in assets))
    selected_type = st.selectbox("File Type", type_options, key="ma_type")
with f3:
    st.metric("Total Assets", len(assets))

# Filter
filtered = assets
if selected_label != "All":
    target_cat = cat_lookup.get(selected_label, selected_label)
    filtered = [a for a in filtered if a["category"] == target_cat]
if selected_type != "All":
    filtered = [a for a in filtered if a["type"] == selected_type]

st.markdown("**{} asset{}** shown".format(
    len(filtered), "s" if len(filtered) != 1 else ""
))

# Render assets
for asset in filtered:
    _render_asset_card(asset)
    st.markdown("")

# Video links section
_render_video_links(catalogue.get("video_links", []))
