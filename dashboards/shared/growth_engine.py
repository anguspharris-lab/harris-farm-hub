"""
Growth Engine — The Hub Homepage Section
Renders the four AI scaling lessons, gamification track,
workflow/approvals pipeline, and new ways of working.

Inserts between The 5 Goals and Quick Launch on the homepage.
"""

import streamlit as st


def render_growth_engine(user_level: str = "Seed", user_xp: int = 5, xp_to_next: int = 45):
    """
    Render the Growth Engine section.

    Args:
        user_level: Current user's gamification level (Seed/Sprout/Grower/Harvester/Cultivator/Legend)
        user_xp: Current user's XP points
        xp_to_next: XP needed to reach next level
    """

    # Calculate XP percentage for progress bar
    total_xp_for_level = user_xp + xp_to_next
    xp_pct = (user_xp / total_xp_for_level * 100) if total_xp_for_level > 0 else 0

    # Level config — matches academy_engine.py LEVEL_THRESHOLDS
    levels = [
        {"name": "Seed", "icon": "\U0001f331"},
        {"name": "Sprout", "icon": "\U0001f33f"},
        {"name": "Grower", "icon": "\U0001f33b"},
        {"name": "Harvester", "icon": "\U0001f9fa"},
        {"name": "Cultivator", "icon": "\U0001f333"},
        {"name": "Legend", "icon": "\U0001f3c6"},
    ]

    current_level_idx = next((i for i, l in enumerate(levels) if l["name"] == user_level), 0)

    # Build level track HTML
    level_pips_html = ""
    for i, level in enumerate(levels):
        state = "active" if i == current_level_idx else ("" if i < current_level_idx else "locked")
        level_pips_html += (
            f'<div class="ge-level-pip {state}">'
            f'<div class="ge-dot">{level["icon"]}</div>'
            f'<div class="ge-pip-label">{level["name"]}</div>'
            f'</div>'
        )
        if i < len(levels) - 1:
            wire_state = "done" if i < current_level_idx else ""
            level_pips_html += f'<div class="ge-level-wire {wire_state}"></div>'

    next_level_name = levels[min(current_level_idx + 1, len(levels) - 1)]["name"]

    html = f'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;0,9..144,700;0,9..144,900;1,9..144,300;1,9..144,400&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

    :root {{
        --ge-green-deep: #0B1628;
        --ge-green-rich: #132240;
        --ge-green-mid: #2ECC71;
        --ge-green-bright: #2ECC71;
        --ge-green-light: #2ECC71;
        --ge-green-pale: rgba(46,204,113,0.12);
        --ge-gold: #F1C40F;
        --ge-gold-light: #F1C40F;
        --ge-cream: #0B1628;
        --ge-cream-warm: #0F1D35;
        --ge-charcoal: #FFFFFF;
        --ge-slate: #B0BEC5;
        --ge-mist: #8899AA;
        --ge-white: #FFFFFF;
        --ge-purple: #8B5CF6;
        --ge-font-display: Georgia, 'Times New Roman', serif;
        --ge-font-body: 'Trebuchet MS', 'Segoe UI', sans-serif;
        --ge-ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
        --ge-ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
    }}

    .ge-container {{
        background: linear-gradient(178deg, #0F1D35 0%, #0B1628 40%, #0F1D35 100%);
        border: 1px solid rgba(255,255,255,0.08);
        position: relative;
        overflow: hidden;
        border-radius: 16px;
        margin: 24px 0;
        font-family: var(--ge-font-body);
        -webkit-font-smoothing: antialiased;
    }}

    .ge-container * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    .ge-container::before {{
        content: '';
        position: absolute;
        top: -200px; right: -150px;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(46,204,113,0.06) 0%, transparent 70%);
        animation: ge-float 25s ease-in-out infinite;
        pointer-events: none;
    }}

    @keyframes ge-float {{
        0%, 100% {{ transform: translate(0, 0) scale(1); }}
        50% {{ transform: translate(-40px, 30px) scale(1.1); }}
    }}

    /* Section Header */
    .ge-intro {{
        padding: 48px 40px 0;
        position: relative;
        z-index: 1;
    }}

    .ge-eyebrow {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--ge-green-mid);
        margin-bottom: 10px;
        opacity: 0;
        transform: translateY(12px);
        animation: ge-fadeUp 0.7s var(--ge-ease-out-expo) 0.1s forwards;
    }}

    .ge-eyebrow::before {{
        content: '';
        width: 24px; height: 2px;
        background: var(--ge-green-mid);
        border-radius: 1px;
    }}

    .ge-title {{
        font-family: var(--ge-font-display);
        font-size: clamp(26px, 3.5vw, 40px);
        font-weight: 900;
        line-height: 1.1;
        color: var(--ge-white);
        margin-bottom: 10px;
        opacity: 0;
        transform: translateY(12px);
        animation: ge-fadeUp 0.8s var(--ge-ease-out-expo) 0.2s forwards;
    }}

    .ge-title em {{
        font-style: italic;
        color: var(--ge-green-mid);
    }}

    .ge-subtitle {{
        font-size: 15px;
        line-height: 1.6;
        color: var(--ge-slate);
        max-width: 520px;
        opacity: 0;
        transform: translateY(12px);
        animation: ge-fadeUp 0.8s var(--ge-ease-out-expo) 0.35s forwards;
    }}

    @keyframes ge-fadeUp {{
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Four Lessons Journey */
    .ge-lessons {{
        padding: 36px 40px 0;
        position: relative;
        z-index: 1;
    }}

    .ge-journey {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        position: relative;
    }}

    .ge-journey::before {{
        content: '';
        position: absolute;
        top: 30px;
        left: 12%;
        right: 12%;
        height: 2px;
        background: linear-gradient(90deg, var(--ge-green-light), var(--ge-green-mid), var(--ge-green-rich), var(--ge-green-deep));
        z-index: 0;
        opacity: 0.4;
    }}

    .ge-card {{
        text-align: center;
        position: relative;
        z-index: 1;
        opacity: 0;
        transform: translateY(20px);
        animation: ge-cardIn 0.7s var(--ge-ease-out-expo) forwards;
    }}

    .ge-card:nth-child(1) {{ animation-delay: 0.4s; }}
    .ge-card:nth-child(2) {{ animation-delay: 0.6s; }}
    .ge-card:nth-child(3) {{ animation-delay: 0.8s; }}
    .ge-card:nth-child(4) {{ animation-delay: 1.0s; }}

    @keyframes ge-cardIn {{
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .ge-orb {{
        width: 52px; height: 52px;
        border-radius: 50%;
        margin: 0 auto 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: var(--ge-font-display);
        font-size: 18px;
        font-weight: 700;
        color: var(--ge-white);
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
        transition: transform 0.3s var(--ge-ease-out-back);
    }}

    .ge-card:hover .ge-orb {{ transform: scale(1.1); }}

    .ge-card:nth-child(1) .ge-orb {{ background: var(--ge-green-light); color: var(--ge-green-deep); }}
    .ge-card:nth-child(2) .ge-orb {{ background: var(--ge-green-mid); }}
    .ge-card:nth-child(3) .ge-orb {{ background: var(--ge-green-rich); }}
    .ge-card:nth-child(4) .ge-orb {{ background: var(--ge-green-deep); }}

    /* Visual tiles */
    .ge-vis {{
        width: 100%;
        max-width: 200px;
        aspect-ratio: 5/4;
        margin: 0 auto 14px;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.4s var(--ge-ease-out-expo), box-shadow 0.4s ease;
    }}

    .ge-card:hover .ge-vis {{
        transform: translateY(-3px);
        box-shadow: 0 14px 40px rgba(0,0,0,0.3);
    }}

    .ge-vis-simple {{ background: linear-gradient(135deg, #132240, #1A2D50); position: relative; }}
    .ge-vis-simple .ge-rays {{
        position: absolute; inset: -20px;
        background: radial-gradient(circle, rgba(255,235,59,0.25) 0%, transparent 65%);
        animation: ge-pulse 3.5s ease-in-out infinite;
    }}
    .ge-vis-simple .ge-bulb {{ font-size: 48px; position: relative; z-index: 1; filter: drop-shadow(0 3px 8px rgba(76,175,80,0.2)); }}

    @keyframes ge-pulse {{
        0%, 100% {{ opacity: 0.4; transform: scale(0.92); }}
        50% {{ opacity: 1; transform: scale(1.08); }}
    }}

    .ge-vis-bigger {{ background: linear-gradient(135deg, #132240, #1A2D50); position: relative; }}
    .ge-ring-set {{ position: relative; width: 100px; height: 100px; }}
    .ge-ring {{ position: absolute; border-radius: 50%; border: 2px solid var(--ge-green-mid); animation: ge-breathe 3.5s ease-in-out infinite; }}
    .ge-ring:nth-child(1) {{ inset: 34px; border-color: var(--ge-green-deep); background: rgba(45,90,63,0.1); }}
    .ge-ring:nth-child(2) {{ inset: 22px; opacity: 0.5; animation-delay: 0.25s; }}
    .ge-ring:nth-child(3) {{ inset: 10px; opacity: 0.3; animation-delay: 0.5s; }}
    .ge-ring:nth-child(4) {{ inset: -2px; opacity: 0.12; border-style: dashed; animation-delay: 0.75s; }}
    .ge-ring-core {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 24px; z-index: 1; }}

    @keyframes ge-breathe {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.06); }}
    }}

    .ge-vis-work {{ background: linear-gradient(135deg, #1A2D50, #132240); }}
    .ge-gear-cluster {{ position: relative; width: 90px; height: 72px; }}
    .ge-g {{ position: absolute; animation: ge-spin 5s linear infinite; }}
    .ge-g:nth-child(1) {{ top: 6px; left: 2px; font-size: 40px; }}
    .ge-g:nth-child(2) {{ top: 26px; left: 38px; font-size: 28px; animation-direction: reverse; animation-duration: 3.5s; }}
    .ge-g:nth-child(3) {{ top: 0; left: 50px; font-size: 22px; animation-duration: 2.8s; }}
    .ge-gear-out {{ margin-left: 10px; font-size: 18px; animation: ge-nudge 2.5s ease-in-out infinite; }}

    @keyframes ge-spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes ge-nudge {{
        0%, 100% {{ transform: translateX(0); opacity: 0.5; }}
        50% {{ transform: translateX(4px); opacity: 1; }}
    }}

    .ge-vis-scale {{
        background: linear-gradient(135deg, var(--ge-green-rich), var(--ge-green-deep));
        flex-direction: column;
        gap: 5px;
    }}
    .ge-block-grid {{ display: grid; grid-template-columns: repeat(6,1fr); gap: 3px; }}
    .ge-b {{
        width: 13px; height: 13px;
        background: var(--ge-green-light);
        border-radius: 2px;
        opacity: 0;
        animation: ge-pop 0.2s var(--ge-ease-out-back) forwards;
    }}
    .ge-b:nth-child(1){{animation-delay:1.4s}}.ge-b:nth-child(2){{animation-delay:1.44s}}.ge-b:nth-child(3){{animation-delay:1.48s}}.ge-b:nth-child(4){{animation-delay:1.52s}}.ge-b:nth-child(5){{animation-delay:1.56s}}.ge-b:nth-child(6){{animation-delay:1.6s}}
    .ge-b:nth-child(7){{animation-delay:1.62s}}.ge-b:nth-child(8){{animation-delay:1.64s}}.ge-b:nth-child(9){{animation-delay:1.66s}}.ge-b:nth-child(10){{animation-delay:1.68s}}.ge-b:nth-child(11){{animation-delay:1.7s}}.ge-b:nth-child(12){{animation-delay:1.72s}}
    .ge-b:nth-child(13){{animation-delay:1.73s}}.ge-b:nth-child(14){{animation-delay:1.74s}}.ge-b:nth-child(15){{animation-delay:1.75s}}.ge-b:nth-child(16){{animation-delay:1.76s}}.ge-b:nth-child(17){{animation-delay:1.77s}}.ge-b:nth-child(18){{animation-delay:1.78s}}

    @keyframes ge-pop {{ from {{ opacity:0; transform:scale(0); }} to {{ opacity:1; transform:scale(1); }} }}

    .ge-scale-tag {{
        font-size: 9px; font-weight: 600; letter-spacing: 0.1em;
        text-transform: uppercase; color: var(--ge-green-light); opacity: 0.7;
    }}

    .ge-lesson-title {{
        font-family: var(--ge-font-display);
        font-size: 16px; font-weight: 700; color: var(--ge-white);
        margin-bottom: 4px; line-height: 1.25;
    }}

    .ge-lesson-hook {{
        font-family: var(--ge-font-display);
        font-size: 12px; font-weight: 300; font-style: italic;
        color: var(--ge-green-mid); margin-bottom: 6px;
    }}

    .ge-lesson-body {{
        font-size: 12px; line-height: 1.6; color: var(--ge-slate);
        max-width: 210px; margin: 0 auto;
    }}

    .ge-lesson-cta {{
        display: inline-block;
        margin-top: 10px; font-size: 11px; font-weight: 600;
        color: var(--ge-green-mid);
    }}

    /* Three Pillars */
    .ge-pillars {{
        padding: 36px 40px 40px;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        position: relative;
        z-index: 1;
    }}

    .ge-pillar {{
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 28px 24px 24px;
        position: relative;
        overflow: hidden;
        transition: transform 0.4s var(--ge-ease-out-expo), box-shadow 0.4s ease;
        opacity: 0;
        transform: translateY(16px);
        animation: ge-cardIn 0.7s var(--ge-ease-out-expo) forwards;
    }}

    .ge-pillar:nth-child(1) {{ animation-delay: 1.0s; }}
    .ge-pillar:nth-child(2) {{ animation-delay: 1.2s; }}
    .ge-pillar:nth-child(3) {{ animation-delay: 1.4s; }}

    .ge-pillar:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 32px rgba(0,0,0,0.3);
    }}

    .ge-pillar::before {{
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
    }}

    .ge-pillar:nth-child(1)::before {{ background: linear-gradient(90deg, var(--ge-green-mid), var(--ge-green-light)); }}
    .ge-pillar:nth-child(2)::before {{ background: linear-gradient(90deg, var(--ge-purple), #A78BFA); }}
    .ge-pillar:nth-child(3)::before {{ background: linear-gradient(90deg, var(--ge-green-mid), var(--ge-green-light)); }}

    .ge-pillar-icon {{
        width: 42px; height: 42px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; margin-bottom: 14px;
    }}
    .ge-pillar:nth-child(1) .ge-pillar-icon {{ background: rgba(46,204,113,0.15); }}
    .ge-pillar:nth-child(2) .ge-pillar-icon {{ background: rgba(139,92,246,0.15); }}
    .ge-pillar:nth-child(3) .ge-pillar-icon {{ background: rgba(46,204,113,0.15); }}

    .ge-pillar-label {{
        font-size: 9px; font-weight: 600; letter-spacing: 0.1em;
        text-transform: uppercase; margin-bottom: 5px;
    }}
    .ge-pillar:nth-child(1) .ge-pillar-label {{ color: var(--ge-green-mid); }}
    .ge-pillar:nth-child(2) .ge-pillar-label {{ color: var(--ge-purple); }}
    .ge-pillar:nth-child(3) .ge-pillar-label {{ color: var(--ge-green-mid); }}

    .ge-pillar h3 {{
        font-family: var(--ge-font-display);
        font-size: 17px; font-weight: 700;
        color: var(--ge-white); margin-bottom: 8px; line-height: 1.25;
    }}

    .ge-pillar-desc {{
        font-size: 12px; line-height: 1.6; color: var(--ge-slate); margin-bottom: 16px;
    }}

    /* Gamification level track */
    .ge-level-track {{
        display: flex; align-items: center; gap: 2px; margin-bottom: 12px;
    }}
    .ge-level-pip {{
        display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1;
    }}
    .ge-dot {{
        width: 26px; height: 26px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; background: var(--ge-green-pale);
        border: 2px solid var(--ge-green-light);
        transition: transform 0.3s var(--ge-ease-out-back);
    }}
    .ge-level-pip.active .ge-dot {{
        background: var(--ge-green-mid); border-color: var(--ge-green-mid);
        box-shadow: 0 0 0 3px rgba(46,204,113,0.2); transform: scale(1.08);
    }}
    .ge-level-pip.locked .ge-dot {{ background: #1A2D50; border-color: rgba(255,255,255,0.1); opacity: 0.45; }}
    .ge-pip-label {{ font-size: 8px; font-weight: 600; color: var(--ge-mist); letter-spacing: 0.02em; }}
    .ge-level-pip.active .ge-pip-label {{ color: var(--ge-green-mid); font-weight: 700; }}
    .ge-level-wire {{ width: 100%; height: 2px; background: rgba(255,255,255,0.1); flex: 1; margin-top: -12px; }}
    .ge-level-wire.done {{ background: var(--ge-green-light); }}

    .ge-xp-bar {{ background: rgba(255,255,255,0.1); border-radius: 5px; height: 5px; overflow: hidden; margin-bottom: 5px; }}
    .ge-xp-fill {{ height: 100%; background: linear-gradient(90deg, var(--ge-green-light), var(--ge-gold)); border-radius: 5px; width: {xp_pct:.0f}%; }}
    .ge-xp-text {{ font-size: 10px; color: var(--ge-mist); }}
    .ge-xp-text strong {{ color: var(--ge-green-mid); font-weight: 700; }}

    /* Workflow pipeline */
    .ge-pipeline {{ display: flex; flex-direction: column; gap: 8px; }}
    .ge-pipe-step {{
        display: flex; align-items: center; gap: 8px;
        padding: 8px 10px; border-radius: 8px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        transition: background 0.2s;
    }}
    .ge-pipe-step:hover {{ background: rgba(139,92,246,0.08); }}
    .ge-pipe-num {{
        width: 22px; height: 22px; border-radius: 5px;
        display: flex; align-items: center; justify-content: center;
        font-size: 10px; font-weight: 700; color: var(--ge-white);
        background: var(--ge-purple); flex-shrink: 0;
    }}
    .ge-pipe-name {{ font-size: 12px; font-weight: 600; color: var(--ge-charcoal); line-height: 1.3; }}
    .ge-pipe-detail {{ font-size: 10px; color: var(--ge-mist); }}
    .ge-pipe-badge {{
        font-size: 8px; font-weight: 700; padding: 2px 6px;
        border-radius: 3px;
        letter-spacing: 0.04em; text-transform: uppercase; flex-shrink: 0; margin-left: auto;
    }}
    .ge-pipe-badge.rubric {{ background: rgba(139,92,246,0.15); color: #A78BFA; }}
    .ge-pipe-badge.auto {{ background: rgba(46,204,113,0.15); color: #2ECC71; }}
    .ge-pipe-badge.human {{ background: rgba(249,115,22,0.15); color: #F97316; }}

    /* New Ways */
    .ge-ways {{ display: flex; flex-direction: column; gap: 8px; }}
    .ge-way {{
        display: flex; gap: 10px; align-items: flex-start;
        padding: 8px 10px; border-radius: 8px;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        transition: background 0.2s;
    }}
    .ge-way:hover {{ background: rgba(46,204,113,0.08); }}
    .ge-way-icon {{
        width: 28px; height: 28px; border-radius: 7px;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; background: rgba(46,204,113,0.12); flex-shrink: 0; margin-top: 1px;
    }}
    .ge-way h4 {{ font-size: 12px; font-weight: 600; color: var(--ge-white); margin-bottom: 1px; }}
    .ge-way p {{ font-size: 10.5px; line-height: 1.5; color: var(--ge-mist); }}

    /* Method quote strip */
    .ge-method {{
        background: var(--ge-green-deep);
        padding: 32px 40px;
        text-align: center;
        border-radius: 0 0 16px 16px;
        position: relative;
        overflow: hidden;
    }}
    .ge-method::before {{
        content: '\\201C';
        position: absolute;
        top: -24px; left: 28px;
        font-family: var(--ge-font-display);
        font-size: 160px;
        color: rgba(255,255,255,0.025);
        line-height: 1;
        pointer-events: none;
    }}
    .ge-method-quote {{
        font-family: var(--ge-font-display);
        font-size: clamp(16px, 2.2vw, 22px);
        font-weight: 300; font-style: italic;
        color: var(--ge-white);
        max-width: 580px;
        margin: 0 auto 10px;
        line-height: 1.45;
        position: relative;
        z-index: 1;
    }}
    .ge-method-attr {{
        font-size: 11px; font-weight: 500;
        color: var(--ge-green-light); letter-spacing: 0.06em;
    }}

    /* Responsive */
    @media (max-width: 900px) {{
        .ge-journey {{ grid-template-columns: repeat(2, 1fr); gap: 24px; }}
        .ge-journey::before {{ display: none; }}
        .ge-pillars {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 600px) {{
        .ge-journey {{ grid-template-columns: 1fr; }}
        .ge-intro, .ge-lessons, .ge-pillars {{ padding-left: 20px; padding-right: 20px; }}
    }}
    </style>

    <div class="ge-container">

        <!-- HEADER -->
        <div class="ge-intro">
            <div class="ge-eyebrow">Growing Legends Academy</div>
            <div class="ge-title">Four lessons that change <em>everything.</em></div>
            <p class="ge-subtitle">Every Harris Farmer who masters these four ideas doesn't just use AI &mdash; they become a Legend. This is the Harris Farm Method.</p>
        </div>

        <!-- FOUR LESSONS -->
        <div class="ge-lessons">
            <div class="ge-journey">

                <div class="ge-card">
                    <div class="ge-orb">1</div>
                    <div class="ge-vis ge-vis-simple">
                        <div style="position:relative">
                            <div class="ge-rays"></div>
                            <div class="ge-bulb">\U0001f4a1</div>
                        </div>
                    </div>
                    <div class="ge-lesson-title">It's Simple When<br>You Get It</div>
                    <div class="ge-lesson-hook">The first habit that changes everything</div>
                    <div class="ge-lesson-body">When in doubt, ask AI. That's it. One habit, practised daily, unlocks everything that follows.</div>
                    <div class="ge-lesson-cta">\U0001f4a1 Open "When In Doubt"</div>
                </div>

                <div class="ge-card">
                    <div class="ge-orb">2</div>
                    <div class="ge-vis ge-vis-bigger">
                        <div class="ge-ring-set">
                            <div class="ge-ring"></div>
                            <div class="ge-ring"></div>
                            <div class="ge-ring"></div>
                            <div class="ge-ring"></div>
                            <div class="ge-ring-core">\U0001f52d</div>
                        </div>
                    </div>
                    <div class="ge-lesson-title">Think Bigger</div>
                    <div class="ge-lesson-hook">Expand what you believe is possible</div>
                    <div class="ge-lesson-body">Don't ask AI to fix a typo &mdash; ask it to rethink the process. The gap between beginners and leaders is the size of their questions.</div>
                    <div class="ge-lesson-cta">\U0001f31f Open Academy</div>
                </div>

                <div class="ge-card">
                    <div class="ge-orb">3</div>
                    <div class="ge-vis ge-vis-work">
                        <div class="ge-gear-cluster">
                            <div class="ge-g">\u2699\ufe0f</div>
                            <div class="ge-g">\u2699\ufe0f</div>
                            <div class="ge-g">\u2699\ufe0f</div>
                        </div>
                        <div class="ge-gear-out">\U0001f4ca</div>
                    </div>
                    <div class="ge-lesson-title">Make It Work<br>Hard for You</div>
                    <div class="ge-lesson-hook">Build prompts that compound your effort</div>
                    <div class="ge-lesson-body">Templates. Prompt chains. Repeatable workflows. One great prompt used 100 times beats 100 one-off questions.</div>
                    <div class="ge-lesson-cta">\u26a1 Open Prompt Engine</div>
                </div>

                <div class="ge-card">
                    <div class="ge-orb">4</div>
                    <div class="ge-vis ge-vis-scale">
                        <div class="ge-block-grid">
                            <div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div>
                            <div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div>
                            <div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div><div class="ge-b"></div>
                        </div>
                        <div class="ge-scale-tag">Autonomous at Scale</div>
                    </div>
                    <div class="ge-lesson-title">Claude Code.<br>Your Job, at Scale.</div>
                    <div class="ge-lesson-hook">Prompt the whole process, not one step</div>
                    <div class="ge-lesson-body">Don't ask a question &mdash; prompt the entire end-to-end process. Define the goal. Flood with context. Add a rubric. Let AI build it.</div>
                    <div class="ge-lesson-cta">\U0001f680 Open The Paddock</div>
                </div>

            </div>
        </div>

        <!-- THREE PILLARS -->
        <div class="ge-pillars">

            <!-- GAMIFICATION -->
            <div class="ge-pillar">
                <div class="ge-pillar-icon">\U0001f96c</div>
                <div class="ge-pillar-label">Harris Farming It</div>
                <h3>Grow from Seed to Legend</h3>
                <p class="ge-pillar-desc">Every action earns XP. Six levels track your mastery &mdash; visible to you and your team.</p>
                <div class="ge-level-track">
                    {level_pips_html}
                </div>
                <div class="ge-xp-bar"><div class="ge-xp-fill"></div></div>
                <div class="ge-xp-text"><strong>{user_xp} XP</strong> &middot; {xp_to_next} XP to {next_level_name}</div>
            </div>

            <!-- WORKFLOW & APPROVALS -->
            <div class="ge-pillar">
                <div class="ge-pillar-icon">\u2705</div>
                <div class="ge-pillar-label">Workflow & Approvals</div>
                <h3>Quality That Ships</h3>
                <p class="ge-pillar-desc">Every piece of work flows through a structured pipeline. The Rubric scores it. Nothing ships below an 8.</p>
                <div class="ge-pipeline">
                    <div class="ge-pipe-step">
                        <div class="ge-pipe-num">1</div>
                        <div><div class="ge-pipe-name">AI Generates Draft</div><div class="ge-pipe-detail">Autonomous agents build first pass</div></div>
                        <span class="ge-pipe-badge auto">Auto</span>
                    </div>
                    <div class="ge-pipe-step">
                        <div class="ge-pipe-num">2</div>
                        <div><div class="ge-pipe-name">Rubric Evaluation</div><div class="ge-pipe-detail">5-tier scoring &mdash; must reach 8+ to proceed</div></div>
                        <span class="ge-pipe-badge rubric">8+ to Ship</span>
                    </div>
                    <div class="ge-pipe-step">
                        <div class="ge-pipe-num">3</div>
                        <div><div class="ge-pipe-name">WATCHDOG Safety Check</div><div class="ge-pipe-detail">Seven immutable laws verified</div></div>
                        <span class="ge-pipe-badge auto">Auto</span>
                    </div>
                    <div class="ge-pipe-step">
                        <div class="ge-pipe-num">4</div>
                        <div><div class="ge-pipe-name">Human Approval</div><div class="ge-pipe-detail">Team lead reviews and approves</div></div>
                        <span class="ge-pipe-badge human">Human</span>
                    </div>
                </div>
            </div>

            <!-- NEW WAYS OF WORKING -->
            <div class="ge-pillar">
                <div class="ge-pillar-icon">\U0001f680</div>
                <div class="ge-pillar-label">New Ways of Working</div>
                <h3>The Harris Farm Method</h3>
                <p class="ge-pillar-desc">These aren't suggestions &mdash; they're how we operate now.</p>
                <div class="ge-ways">
                    <div class="ge-way">
                        <div class="ge-way-icon">\U0001f4ac</div>
                        <div><h4>When in doubt, ask AI first</h4><p>Before emailing, Slacking, or guessing &mdash; ask AI.</p></div>
                    </div>
                    <div class="ge-way">
                        <div class="ge-way-icon">\U0001f3af</div>
                        <div><h4>Prompt the whole process</h4><p>Don't automate one step. Describe the entire outcome.</p></div>
                    </div>
                    <div class="ge-way">
                        <div class="ge-way-icon">\U0001f4d0</div>
                        <div><h4>Nothing ships below an 8</h4><p>The Rubric is the standard. Score it. No exceptions.</p></div>
                    </div>
                    <div class="ge-way">
                        <div class="ge-way-icon">\U0001f331</div>
                        <div><h4>Grow every week</h4><p>Your level is public. Your XP is earned. Keep climbing.</p></div>
                    </div>
                </div>
            </div>

        </div>

        <!-- METHOD QUOTE -->
        <div class="ge-method">
            <p class="ge-method-quote">Create the Claude Code prompt. Think end-to-end, not one step. Prompt the whole process, let AI build it.</p>
            <p class="ge-method-attr">&mdash; The Harris Farm Method</p>
        </div>

    </div>
    '''

    # st.html() renders full HTML inline (not iframe), supports <style> tags,
    # CSS animations, pseudo-elements — unlike st.markdown(unsafe_allow_html=True)
    # which strips <style> blocks.
    st.html(html)
