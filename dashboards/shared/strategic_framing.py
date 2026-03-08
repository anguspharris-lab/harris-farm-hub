"""
Harris Farm Hub — Strategic Framing Components
Reusable UI components for pillar intro pages and strategic storytelling.
"""

import streamlit as st

from shared.styles import HFM_GREEN, HFM_DARK


def pillar_hero(pillar, metrics=None):
    """Render a pillar hero banner with strategic question and optional metrics.

    Args:
        pillar: Dict from PILLAR_REGISTRY (must have name, icon, color,
                strategic_question, tagline).
        metrics: Optional list of dicts [{label, value, delta}] to show as KPI chips.
    """
    color = pillar.get("color", HFM_GREEN)
    icon = pillar.get("icon", "")
    name = pillar.get("name", "")
    tagline = pillar.get("tagline", "")
    question = pillar.get("strategic_question", "")

    metric_html = ""
    if metrics:
        chips = []
        for m in metrics:
            delta = m.get("delta", "")
            delta_html = ""
            if delta:
                delta_html = (
                    "<span style='font-size:11px;opacity:0.85;margin-left:4px;'>"
                    "{}</span>".format(delta)
                )
            chips.append(
                "<div style='background:rgba(0,0,0,0.12);"
                "padding:10px 16px;border-radius:8px;text-align:center;'>"
                "<div style='font-size:24px;font-weight:700;'>"
                "{}{}</div>"
                "<div style='font-size:12px;opacity:0.9;'>{}</div>"
                "</div>".format(m.get("value", ""), delta_html, m.get("label", ""))
            )
        metric_html = (
            "<div style='display:flex;gap:12px;flex-wrap:wrap;margin-top:16px;'>"
            + "".join(chips)
            + "</div>"
        )

    st.markdown(
        "<div style='background:linear-gradient(135deg, {c} 0%, {c}dd 100%);"
        "color:white;padding:32px 36px;border-radius:14px;margin-bottom:20px;'>"
        "<div style='font-size:12px;opacity:0.8;text-transform:uppercase;"
        "letter-spacing:0.1em;font-weight:600;'>{icon} {name}</div>"
        "<div style='font-size:16px;font-weight:500;margin:6px 0;'>{tagline}</div>"
        "<div style='font-size:24px;font-weight:700;margin-top:12px;"
        "font-style:italic;'>\u201c{question}\u201d</div>"
        "{metrics}"
        "</div>".format(
            c=color, icon=icon, name=name, tagline=tagline,
            question=question, metrics=metric_html,
        ),
        unsafe_allow_html=True,
    )


def coming_soon_card(title, description="Data source not yet connected."):
    """Render a placeholder card for metrics that don't have data yet."""
    st.markdown(
        "<div style='background:rgba(0,0,0,0.03);border:2px dashed rgba(0,0,0,0.08);"
        "border-radius:10px;padding:20px;text-align:center;min-height:100px;"
        "display:flex;flex-direction:column;justify-content:center;'>"
        "<div style='font-size:29px;margin-bottom:6px;'>\U0001f6a7</div>"
        "<div style='font-weight:700;color:#4A4A4A;font-size:16px;'>"
        "{title}</div>"
        "<div style='font-size:12px;color:#717171;margin-top:4px;'>"
        "{desc}</div>"
        "</div>".format(title=title, desc=description),
        unsafe_allow_html=True,
    )


def one_thing_box(text):
    """Render a highlighted 'One Thing to Remember' takeaway box."""
    st.markdown(
        "<div style='background:rgba(200,151,31,0.08);"
        "border-left:4px solid #C8971F;border:1px solid rgba(0,0,0,0.08);"
        "border-left:4px solid #C8971F;"
        "border-radius:0 10px 10px 0;"
        "padding:16px 20px;margin:16px 0;'>"
        "<div style='font-weight:700;color:#C8971F;font-size:13px;"
        "margin-bottom:4px;'>"
        "\U0001f4a1 One Thing to Remember</div>"
        "<div style='color:#4A4A4A;font-size:14px;'>{text}</div>"
        "</div>".format(text=text),
        unsafe_allow_html=True,
    )


def initiative_summary_card(summary):
    """Render a Monday.com initiative progress card.

    Args:
        summary: Dict with keys: total, done, in_progress, stuck, configured.
    """
    if not summary or not summary.get("configured"):
        return

    total = summary.get("total", 0)
    done = summary.get("done", 0)
    in_prog = summary.get("in_progress", 0)
    stuck = summary.get("stuck", 0)
    pct = int((done / total) * 100) if total > 0 else 0

    st.markdown(
        "<div style='background:#FFFFFF;"
        "border:1px solid rgba(0,0,0,0.08);"
        "border-radius:10px;padding:16px;'>"
        "<div style='font-weight:600;color:#1A1A1A;font-size:14px;"
        "margin-bottom:8px;font-family:-apple-system, BlinkMacSystemFont, &apos;Segoe UI&apos;, Roboto, Oxygen, sans-serif;'>"
        "\U0001f4cb Strategic Initiatives</div>"
        "<div style='display:flex;gap:16px;margin-bottom:10px;'>"
        "<div><span style='font-size:20px;font-weight:700;color:#1A1A1A;'>{total}</span>"
        " <span style='color:#4A4A4A;font-size:12px;'>Total</span></div>"
        "<div><span style='font-size:20px;font-weight:700;color:#2D6A2D;'>"
        "{done}</span>"
        " <span style='color:#4A4A4A;font-size:12px;'>Done</span></div>"
        "<div><span style='font-size:20px;font-weight:700;color:#1565C0;'>"
        "{ip}</span>"
        " <span style='color:#4A4A4A;font-size:12px;'>In Progress</span></div>"
        "<div><span style='font-size:20px;font-weight:700;color:#C0392B;'>"
        "{stuck}</span>"
        " <span style='color:#4A4A4A;font-size:12px;'>Stuck</span></div>"
        "</div>"
        "<div style='background:rgba(0,0,0,0.06);border-radius:6px;height:8px;'>"
        "<div style='background:#2D6A2D;height:8px;border-radius:6px;"
        "width:{pct}%;'></div></div>"
        "<div style='font-size:12px;color:#4A4A4A;text-align:right;"
        "margin-top:2px;'>{pct}% complete</div>"
        "</div>".format(
            dark=HFM_DARK, total=total, done=done, ip=in_prog,
            stuck=stuck, pct=pct,
        ),
        unsafe_allow_html=True,
    )


def growing_legends_banner():
    """Render a compact manifesto-aligned banner for Growing Legends pages.

    Used by Skills Academy, The Paddock, Prompt Engine, Learning Centre
    to create visual unity under the AI-First Manifesto.
    """
    st.markdown(
        "<div style='background:rgba(139,92,246,0.06);"
        "border:1px solid rgba(139,92,246,0.15);"
        "border-radius:12px;padding:20px 24px;margin-bottom:20px;'>"
        "<div style='font-size:12px;text-transform:uppercase;"
        "letter-spacing:0.15em;color:#7C3AED;font-weight:700;"
        "margin-bottom:8px;'>"
        "\U0001f331 Growing Legends</div>"
        "<div style='font-size:18px;font-weight:700;color:#1A1A1A;"
        "font-family:-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, sans-serif;margin-bottom:6px;'>"
        "AI is our brain partner. The prompt is our unlock.</div>"
        "<div style='font-size:13px;color:#4A4A4A;'>"
        "Every Harris Farmer who masters these tools doesn't just use AI "
        "&mdash; they lead with it. Same family. Same values. "
        "Radically better tools.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def sub_page_links(slugs, labels=None):
    """Render a grid of st.page_link() buttons for sub-pages within a pillar.

    Args:
        slugs: List of url_path slugs to link to.
        labels: Optional dict of slug→label overrides. If not provided,
                uses the page title from session state.
    """
    pages = st.session_state.get("_pages", {})
    valid = [(s, pages[s]) for s in slugs if s in pages]
    if not valid:
        return

    cols_per_row = min(4, len(valid))
    cols = st.columns(cols_per_row)
    for i, (slug, page) in enumerate(valid):
        with cols[i % cols_per_row]:
            label = page.title
            if labels and slug in labels:
                label = labels[slug]
            st.page_link(page, label="{} \u2192".format(label),
                         use_container_width=True)
