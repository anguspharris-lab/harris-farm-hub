"""
Harris Farm Hub — Greater Goodness Dashboard

Pillar 1: For The Greater Goodness
Our purpose, sustainability achievements, community impact, and the good
things we do every day. This is the heart of who we are.

"We've believed in something greater than just selling fresh food.
 We've believed in nature itself." — Harris Farm Markets
"""

import os

import requests
import streamlit as st

from shared.styles import render_footer
from shared.voice_realtime import render_voice_data_box

API_URL = os.getenv("API_URL", "http://localhost:8000")


@st.cache_data(ttl=3600, show_spinner=False)
def _load_sustainability_kpis():
    """Fetch sustainability KPIs from backend."""
    try:
        resp = requests.get(f"{API_URL}/api/sustainability/kpis", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("kpis", [])
    except Exception:
        pass
    return []

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='background:linear-gradient(135deg, #0F1D35 0%, #132240 50%, #1A2D50 100%);border:1px solid rgba(46,204,113,0.2);border-top:3px solid #2ECC71;"
    "color:white;padding:36px 32px;border-radius:14px;margin-bottom:24px;'>"
    "<div style='font-size:2.2em;font-weight:800;margin-bottom:8px;'>"
    "For The Greater Goodness</div>"
    "<div style='font-size:1.15em;opacity:0.95;max-width:800px;line-height:1.6;'>"
    "We've believed in something greater than just selling fresh food. "
    "We've believed in nature itself. Since 1971, our family has been committed to "
    "doing things right — for our customers, our farmers, our people, and our planet."
    "</div>"
    "<div style='margin-top:16px;font-size:0.9em;opacity:0.8;'>"
    "Pillar 1 of our Fewer, Bigger, Better strategy &mdash; "
    "Led by Kate Haselhoff &amp; Darren Weir</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# WHAT WE'VE ACHIEVED
# ---------------------------------------------------------------------------

st.markdown("## What We've Achieved")
st.markdown("*These are the things we've already done. Real progress, real impact.*")

achieved_cols = st.columns(3)

achievements = [
    {
        "icon": "\u26a1",
        "title": "100% Renewable Energy",
        "desc": "Every Harris Farm store, our warehouse, and our support office "
                "run on 100% renewable energy. Done.",
        "color": "#2ECC71",
    },
    {
        "icon": "\U0001f4dc",
        "title": "Modern Slavery Statement",
        "desc": "We've published our Modern Slavery Statement — transparent about "
                "our supply chain and committed to ethical sourcing.",
        "color": "#2ECC71",
    },
    {
        "icon": "\U0001f30d",
        "title": "FY25 Climate Disclosure",
        "desc": "Full climate disclosure published. We're honest about our footprint "
                "and open about our path to reduce it.",
        "color": "#2ECC71",
    },
    {
        "icon": "\U0001f3d8\ufe0f",
        "title": "Neighbourhood Goodness",
        "desc": "Year-on-year growth in community impact — local partnerships, food rescue, "
                "and supporting the neighbourhoods we serve.",
        "color": "#2ECC71",
    },
    {
        "icon": "\U0001f4ca",
        "title": "Sustainability KPIs for ELT",
        "desc": "Our executive leadership team now has sustainability targets baked into "
                "their scorecards. Purpose isn't optional — it's measured.",
        "color": "#2ECC71",
    },
    {
        "icon": "\U0001f3af",
        "title": "Purpose Definition Complete",
        "desc": "'For The Greater Goodness' is defined, aligned across Pillars 2 & 3, "
                "and ready to roll out to every Harris Farmer.",
        "color": "#2ECC71",
    },
]

for i, a in enumerate(achievements):
    with achieved_cols[i % 3]:
        st.markdown(
            f"<div style='background:rgba(46,204,113,0.08);border:1px solid rgba(46,204,113,0.2);"
            f"border-radius:10px;padding:18px;margin-bottom:12px;min-height:180px;'>"
            f"<div style='font-size:1.8em;'>{a['icon']}</div>"
            f"<div style='font-weight:700;color:#2ECC71;font-size:1.05em;margin:6px 0;'>"
            f"{a['title']}</div>"
            f"<div style='font-size:0.88em;color:#B0BEC5;line-height:1.5;'>{a['desc']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("")

# ---------------------------------------------------------------------------
# WHAT WE'RE WORKING ON
# ---------------------------------------------------------------------------

st.markdown("## What We're Working On Right Now")
st.markdown("*Progress in motion. Every one of these is actively being delivered.*")

wip_items = [
    {
        "icon": "\U0001f3c5",
        "title": "B Corp Certification",
        "status": "Board approval Feb/Mar 2026",
        "desc": "We've submitted our B-Impact Assessment and we're aiming to become "
                "a certified B Corp — joining the global movement of businesses that "
                "balance purpose and profit. The Top 100 will have scorecards to maintain it.",
    },
    {
        "icon": "\U0001f4e3",
        "title": "Purpose Activation — 'Greater Goodness' Manifesto",
        "status": "Compass Studio engaged, final presentation Mar 4",
        "desc": "Working with Compass Studio ($60K) to bring our purpose to life — "
                "internal and external comms so every Harris Farmer and every customer "
                "knows what we stand for. Rollout by March 20, 2026.",
    },
    {
        "icon": "\u267b\ufe0f",
        "title": "50% Landfill Diversion",
        "status": "In progress across all stores",
        "desc": "Halving the waste that goes to landfill from every store. "
                "Composting, recycling, food rescue partnerships, and smarter packaging.",
    },
    {
        "icon": "\U0001f34e",
        "title": "20% Wastage Reduction",
        "status": "Target FY26",
        "desc": "Imperfect Picks was just the start. We're using AI-driven demand forecasting, "
                "better ordering, and the Too Good To Go partnership to cut food waste by 20%. "
                "Every Harris Farmer plays a role in this.",
    },
    {
        "icon": "\U0001f4e6",
        "title": "ARL on All Harris Farm Packaging",
        "status": "Due December 2026",
        "desc": "Australasian Recycling Labels on every piece of Harris Farm branded packaging. "
                "Clear, honest recycling guidance for our customers.",
    },
    {
        "icon": "\U0001f91d",
        "title": "Supplier Engagement Sessions",
        "status": "1-1 meetings in progress",
        "desc": "Sitting down with our key suppliers to build stronger, more sustainable "
                "partnerships. Responsible sourcing policy shared, workshops being planned.",
    },
    {
        "icon": "\U0001f321\ufe0f",
        "title": "Scope 3 Decarbonisation Plan",
        "status": "Due April 2026",
        "desc": "Going beyond our own operations to understand and reduce emissions across "
                "our entire supply chain. Updated transition and decarbonisation plan in progress.",
    },
    {
        "icon": "\U0001f465",
        "title": "Inclusive Hiring & WGEA Gender Targets",
        "status": "YOY growth tracked",
        "desc": "Growing our commitment to diverse, inclusive teams. "
                "Tracking progress against WGEA gender targets because representation matters.",
    },
    {
        "icon": "\U0001f6e1\ufe0f",
        "title": "10% Reduction in Team & Customer Incidents",
        "status": "In progress",
        "desc": "Making our stores safer for everyone — team members and customers alike. "
                "Because looking after people is Greater Goodness in action.",
    },
]

for item in wip_items:
    st.markdown(
        f"<div style='border-left:4px solid #2ECC71;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-left:4px solid #2ECC71;"
        f"padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:10px;"
        f"box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"<span style='font-size:1.6em;'>{item['icon']}</span>"
        f"<div>"
        f"<div style='font-weight:700;color:white;font-size:1.05em;'>"
        f"{item['title']}</div>"
        f"<div style='font-size:0.78em;color:#2ECC71;font-weight:600;'>"
        f"{item['status']}</div>"
        f"</div></div>"
        f"<div style='font-size:0.9em;color:#B0BEC5;margin-top:8px;line-height:1.5;'>"
        f"{item['desc']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# THE GOODNESS WE DO EVERY DAY
# ---------------------------------------------------------------------------

st.markdown("## The Goodness We Do Every Day")
st.markdown("*This isn't just strategy — it's who we are in every store, every shift.*")

daily_cols = st.columns(2)

with daily_cols[0]:
    st.markdown(
        "<div style='background:rgba(241,196,15,0.08);border:1px solid rgba(241,196,15,0.2);"
        "border-radius:10px;padding:20px;min-height:200px;'>"
        "<div style='font-size:1.5em;margin-bottom:8px;'>\U0001f34b</div>"
        "<div style='font-weight:700;color:#F1C40F;font-size:1.1em;'>Imperfect Picks</div>"
        "<div style='font-size:0.9em;color:#B0BEC5;margin-top:8px;line-height:1.5;'>"
        "Ugly fruit and veg deserve love too. Our Imperfect Picks program rescues "
        "produce that doesn't meet cosmetic standards but tastes just as good. "
        "Less waste, more value, greater goodness."
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(
        "<div style='background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);"
        "border-radius:10px;padding:20px;min-height:200px;'>"
        "<div style='font-size:1.5em;margin-bottom:8px;'>\U0001f33e</div>"
        "<div style='font-weight:700;color:#3B82F6;font-size:1.1em;'>We're for Aussie Farmers</div>"
        "<div style='font-size:0.9em;color:#B0BEC5;margin-top:8px;line-height:1.5;'>"
        "We build real relationships with Australian farmers and producers. "
        "When something's in season, we buy more and pass the savings on. "
        "When times are tough, we back our farmers. That's how a family business works."
        "</div></div>",
        unsafe_allow_html=True,
    )

with daily_cols[1]:
    st.markdown(
        "<div style='background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.2);"
        "border-radius:10px;padding:20px;min-height:200px;'>"
        "<div style='font-size:1.5em;margin-bottom:8px;'>\U0001f3e0</div>"
        "<div style='font-weight:700;color:#EC4899;font-size:1.1em;'>Neighbourhood Goodness</div>"
        "<div style='font-size:0.9em;color:#B0BEC5;margin-top:8px;line-height:1.5;'>"
        "Every Harris Farm store is part of its community. Food rescue partnerships, "
        "local sponsorships, and showing up when it matters. "
        "We're not just in the neighbourhood — we're for the neighbourhood."
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(
        "<div style='background:rgba(46,204,113,0.08);border:1px solid rgba(46,204,113,0.2);"
        "border-radius:10px;padding:20px;min-height:200px;'>"
        "<div style='font-size:1.5em;margin-bottom:8px;'>\U0001f30f</div>"
        "<div style='font-weight:700;color:#2ECC71;font-size:1.1em;'>If It's In Season, Seize It</div>"
        "<div style='font-size:0.9em;color:#B0BEC5;margin-top:8px;line-height:1.5;'>"
        "Nature knows best. We let seasonal abundance drive our pricing and our range. "
        "When mangoes are at their peak, we fill the stores. When stone fruit is bursting, "
        "everyone benefits. It's fresher, cheaper, and better for the planet."
        "</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# PURPOSE-LED DECISIONS
# ---------------------------------------------------------------------------

st.markdown("## Purpose-Led Decisions")
st.markdown(
    "*Every decision at Harris Farm — big or small — should pass through the "
    "Greater Goodness lens. Our decision framework is ready and rolling out to the ELT "
    "(Feb 25) and Top 100 (Mar 12).*"
)

framework_cols = st.columns(3)

with framework_cols[0]:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.05);border:2px solid #2ECC71;border-radius:10px;"
        "padding:18px;text-align:center;min-height:140px;'>"
        "<div style='font-size:1.4em;margin-bottom:6px;'>\U0001f9ed</div>"
        "<div style='font-weight:700;color:#2ECC71;'>Governance Principles</div>"
        "<div style='font-size:0.85em;color:#8899AA;margin-top:6px;'>"
        "Purpose-Led Governance Principles defined. "
        "Board Governance Charter developed. "
        "Board skills matrix complete.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with framework_cols[1]:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.05);border:2px solid #2ECC71;border-radius:10px;"
        "padding:18px;text-align:center;min-height:140px;'>"
        "<div style='font-size:1.4em;margin-bottom:6px;'>\U0001f4cb</div>"
        "<div style='font-weight:700;color:#2ECC71;'>Decision Matrix</div>"
        "<div style='font-size:0.85em;color:#8899AA;margin-top:6px;'>"
        "Decision Matrix Templates developed. "
        "Does this decision serve Greater Goodness? "
        "Framework presenting to ELT Feb 25, Top 100 Mar 12.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with framework_cols[2]:
    st.markdown(
        "<div style='background:rgba(255,255,255,0.05);border:2px solid #2ECC71;border-radius:10px;"
        "padding:18px;text-align:center;min-height:140px;'>"
        "<div style='font-size:1.4em;margin-bottom:6px;'>\U0001f3c5</div>"
        "<div style='font-weight:700;color:#2ECC71;'>B Corp</div>"
        "<div style='font-size:0.85em;color:#8899AA;margin-top:6px;'>"
        "B-Impact Assessment submitted. "
        "Board education session underway. "
        "Targeting certification Feb/Mar 2026.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# TGTG & INNOVATION
# ---------------------------------------------------------------------------

st.markdown("## Innovation for Good")

st.markdown(
    "<div style='background:linear-gradient(135deg, rgba(46,204,113,0.08) 0%, rgba(46,204,113,0.04) 100%);"
    "border:1px solid rgba(46,204,113,0.2);border-radius:12px;padding:24px;margin-bottom:16px;'>"
    "<div style='font-size:1.2em;font-weight:700;color:#2ECC71;margin-bottom:10px;'>"
    "\U0001f4f1 Too Good To Go Partnership</div>"
    "<div style='font-size:0.95em;color:#B0BEC5;line-height:1.6;'>"
    "We're trialling date-check software in stores through our partnership with "
    "Too Good To Go. Scoping with IT is complete and the enterprise agreement is "
    "under review. This tech helps us rescue food that's still perfectly good "
    "but nearing its date — turning potential waste into meals for our community."
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div style='background:linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(59,130,246,0.04) 100%);"
    "border:1px solid rgba(59,130,246,0.2);border-radius:12px;padding:24px;margin-bottom:16px;'>"
    "<div style='font-size:1.2em;font-weight:700;color:#3B82F6;margin-bottom:10px;'>"
    "\U0001f916 AI for Waste Reduction</div>"
    "<div style='font-size:0.95em;color:#B0BEC5;line-height:1.6;'>"
    "The Hub's demand forecasting and weather integration help buyers order "
    "smarter — reducing over-ordering and food waste. When we know a heatwave "
    "is coming, we adjust. When rain is forecast, we scale back outdoor produce. "
    "AI working for Greater Goodness."
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown("")

# ---------------------------------------------------------------------------
# OUR STORY
# ---------------------------------------------------------------------------

st.markdown("## Our Story")

st.markdown(
    "<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:12px;"
    "padding:28px;'>"
    "<div style='font-size:1.3em;font-weight:700;color:white;margin-bottom:12px;'>"
    "Family owned since 1971</div>"
    "<div style='font-size:0.95em;color:#B0BEC5;line-height:1.7;'>"
    "<p>David and Cathy Harris opened our first store in <strong>Villawood in 1971</strong>. "
    "What started with a simple love of fresh food has grown into <strong>30+ stores "
    "across NSW, Queensland, and the ACT</strong>, employing over 3,000 Harris Farmers.</p>"
    "<p>For more than fifty years, we've stayed <strong>100% family-owned</strong>. "
    "That means we answer to our customers and our community — not shareholders. "
    "It means we can make long-term decisions. It means we can choose to do the right thing, "
    "even when it costs more.</p>"
    "<p>Today, led by brothers <strong>Angus and Luke Harris</strong>, we're on a mission to become "
    "<strong>Australia's most loved fresh food retailer — inside and out</strong> by 2030. "
    "Our strategy is <strong>Fewer, Bigger, Better</strong>: streamline what we do, "
    "scale what works, and never stop raising the bar.</p>"
    "<p>The Greater Goodness isn't a marketing slogan. It's how we make decisions. "
    "It's why we back Australian farmers, rescue imperfect produce, run on renewable energy, "
    "and invest in our people. It's the thread that connects everything we do.</p>"
    "<p style='font-style:italic;color:#2ECC71;font-weight:600;margin-top:16px;'>"
    "\"We're for good food and the good things it does for people.\" — David Harris</p>"
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown("")

# ---------------------------------------------------------------------------
# HOW YOU CAN CONTRIBUTE
# ---------------------------------------------------------------------------

st.markdown("## How Every Harris Farmer Contributes")
st.markdown("*Greater Goodness isn't just leadership's job — it's everyone's.*")

role_cols = st.columns(3)

with role_cols[0]:
    st.markdown(
        "<div style='background:rgba(46,204,113,0.08);border-radius:10px;padding:18px;min-height:180px;'>"
        "<div style='font-weight:700;color:#2ECC71;'>\U0001f3ea In Store</div>"
        "<ul style='font-size:0.88em;color:#B0BEC5;margin-top:8px;'>"
        "<li>Reduce waste — check dates, rotate stock, use Imperfect Picks</li>"
        "<li>Save energy — lights off when not needed, doors closed</li>"
        "<li>Be the community — welcome customers, support local events</li>"
        "<li>Speak up — if you see a better way, share it</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )

with role_cols[1]:
    st.markdown(
        "<div style='background:rgba(59,130,246,0.08);border-radius:10px;padding:18px;min-height:180px;'>"
        "<div style='font-weight:700;color:#3B82F6;'>\U0001f69a In the Warehouse</div>"
        "<ul style='font-size:0.88em;color:#B0BEC5;margin-top:8px;'>"
        "<li>Handle with care — less damage means less waste</li>"
        "<li>Sort smarter — recycling and composting at every step</li>"
        "<li>Report issues — if something's off, flag it early</li>"
        "<li>Look after each other — safety is goodness too</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )

with role_cols[2]:
    st.markdown(
        "<div style='background:rgba(241,196,15,0.08);border-radius:10px;padding:18px;min-height:180px;'>"
        "<div style='font-weight:700;color:#F1C40F;'>\U0001f4bc In Support Office</div>"
        "<ul style='font-size:0.88em;color:#B0BEC5;margin-top:8px;'>"
        "<li>Use the Decision Matrix — does it serve Greater Goodness?</li>"
        "<li>Buy responsibly — consider the full supply chain</li>"
        "<li>Use AI to find waste and efficiency — that's what The Hub is for</li>"
        "<li>Champion purpose — bring it into every meeting and decision</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# SUSTAINABILITY TARGETS
# ---------------------------------------------------------------------------

st.markdown("## FY26 Sustainability Scorecard")
st.markdown("*Tracking our progress. Honest, transparent, no greenwashing.*")

kpis = _load_sustainability_kpis()
if not kpis:
    # Fallback if API unavailable
    kpis = [
        {"kpi_name": "100% Renewable Energy", "current_value": 100, "status": "completed", "category": "Energy", "notes": ""},
        {"kpi_name": "B Corp Certification", "current_value": 75, "status": "in_progress", "category": "Governance", "notes": ""},
        {"kpi_name": "Modern Slavery Statement", "current_value": 100, "status": "completed", "category": "Governance", "notes": ""},
    ]

completed = sum(1 for k in kpis if k["status"] == "completed")
avg_progress = sum(k["current_value"] for k in kpis) / len(kpis) if kpis else 0

k1, k2, k3 = st.columns(3)
k1.metric("KPIs Tracked", len(kpis))
k2.metric("Completed", f"{completed}/{len(kpis)}")
k3.metric("Avg Progress", f"{avg_progress:.0f}%")

st.markdown("")

for kpi in kpis:
    pct = int(kpi["current_value"])
    achieved = kpi["status"] == "completed"
    col_label, col_bar = st.columns([1, 2])
    with col_label:
        icon = " \u2705" if achieved else ""
        st.markdown(f"**{kpi['kpi_name']}**{icon}")
        if kpi.get("notes"):
            st.caption(kpi["notes"])
    with col_bar:
        st.progress(pct / 100, text=f"{pct}%")

st.markdown("")

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.markdown(
    "<div style='background:linear-gradient(135deg, #0F1D35 0%, #132240 100%);border:1px solid rgba(46,204,113,0.2);border-top:3px solid #2ECC71;"
    "color:white;padding:20px 24px;border-radius:10px;margin:20px 0;text-align:center;'>"
    "<div style='font-size:1.3em;font-weight:700;'>For The Greater Goodness</div>"
    "<div style='font-size:0.9em;opacity:0.9;margin-top:6px;'>"
    "Every choice we make, every product we sell, every person we hire — "
    "it all comes back to this. We're building something bigger than a grocery store. "
    "We're building a business the world needs more of.</div>"
    "<div style='margin-top:10px;font-size:0.8em;opacity:0.7;'>"
    "Harris Farm Markets — Family owned since '71</div>"
    "</div>",
    unsafe_allow_html=True,
)

render_voice_data_box("general")

render_footer("Greater Goodness", "Pillar 1 — For The Greater Goodness")
