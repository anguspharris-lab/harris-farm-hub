"""
Harris Farm Hub — Competitor Map Dashboard
Competitor locations, density analysis, and competitive landscape
by catchment area.

Placeholder — will integrate Coles, Woolworths, Aldi, IGA location data
and competitive density scoring.
"""

import streamlit as st

from shared.styles import render_header, render_footer

user = st.session_state.get("auth_user")

render_header(
    "Competitor Map",
    "Competitive landscape — Coles, Woolworths, Aldi, IGA locations & density",
    goals=["G1", "G3"],
    strategy_context=(
        "Understanding competitor density helps identify under-served markets "
        "and avoid over-saturated catchments."
    ),
)

st.info(
    "**Coming soon** — competitor location mapping, density analysis, "
    "and competitive saturation scoring by catchment."
)

st.markdown("---")

st.subheader("What This Page Will Include")
with st.container(border=True):
    st.markdown("""
**Data Sources (planned):**
- Coles, Woolworths, Aldi, IGA store locations (geocoded)
- Independent grocer locations
- Specialty food retailers

**Key Views:**
- Interactive map: all competitors within 5km/10km of each HFM store
- Competitor density score by postcode
- Cross-shop analysis: where HFM customers also shop (from CBAS data)
- Competitive saturation vs HFM market share
- Gap analysis: suburbs with grocery demand but limited competition

**Integration:**
- Links to Market Share (share vs competition density)
- Links to Whitespace Analysis (competition scoring component)
- Links to Store Network (competitor cross-shop by store)
""")

st.caption(
    "Some competition is healthy — it validates the market. "
    "Too much compresses share and margin. The sweet spot is "
    "moderate competition in affluent catchments."
)

# ── Cross-links ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("**Related**")
_pages = st.session_state.get("_pages", {})
c1, c2, c3 = st.columns(3)
if "market-share" in _pages:
    c1.page_link(_pages["market-share"], label="Market Share", icon="\U0001f4ca")
if "store-network" in _pages:
    c2.page_link(_pages["store-network"], label="Store Network", icon="\U0001f3ec")
if "whitespace" in _pages:
    c3.page_link(_pages["whitespace"], label="Whitespace Analysis", icon="\U0001f5fa\ufe0f")

render_footer("Competitor Map", "Placeholder — competitor data integration pending", user=user)
