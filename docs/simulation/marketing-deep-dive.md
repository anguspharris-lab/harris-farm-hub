# First Day at The Hub — Marketing Team Deep-Dive

*Assessment of marketing team readiness: asset access, content creation, data connectivity, board rubric*
*Generated 2026-02-22*

---

## Executive Summary

The Hub serves the marketing team as a **brand asset library and first-draft content tool** but fails as a **marketing intelligence platform**. The gap is fundamental: The Hub's data layer covers operational performance (sales, products, supply chain) but contains zero marketing performance data (ROAS, CPA, email rates, brand health, LTV cohorts).

**Overall Marketing Readiness: 4.5/10 — Rethink before marketing rollout.**

---

## 1. Asset Access Assessment

### What Exists
- **Marketing Assets page** (`/marketing-assets`): 19 curated files across 6 categories
- **Brand category:** HFM Brand Guidelines 2016 v3 (33 MB PDF), HFM Logo (PNG)
- **Campaign categories:** Amazon Ads, eCommerce, Weekend Specials (Feb 2026), OOH/DOOH signage, Butcher Campaign photography
- **Filtering:** Category and file type filters
- **Downloads:** Direct download buttons per asset
- **Video placeholders:** 2 butcher campaign videos (108 MB total) — Google Drive links pending

### What Works
- Centralised access to brand guidelines (first time this exists digitally in one place)
- Campaign creative browsable by category with image previews
- Download functionality works reliably
- Clean file naming (spaces removed, consistent format)

### What's Missing
- **No version control** — no way to distinguish current vs archived vs draft assets
- **No approval workflow** — no "approved for use" badge or manager sign-off
- **No upload capability** — marketing team can't add new assets themselves (requires developer intervention)
- **No search within assets** — can't search by campaign name, date range, or product
- **No image editing or template overlay** — still need Canva for asset customisation
- **No brand voice document** — guidelines PDF covers visual identity but tone-of-voice isn't extracted as a configurable resource

### Persona Scores (Asset Accessibility Dimension)
| Persona | Score | Notes |
|---------|:---:|---|
| Sophie (CMO) | 7 | Found assets, useful but expected more (intelligence, not just files) |
| Megan (Brand Mgr) | 8 | Strong — brand guidelines centralised for first time |
| Josh (Digital CRM) | 7 | Found campaign imagery, but disconnected from Prompt Engine |
| Liam (Analyst) | 6 | N/A for his role — he needs data, not creative files |
| Tilly (Content) | 7 | Good for downloads, needs cropping/template tools |

---

## 2. Content Creation Workflow Assessment

### What Exists
- **Prompt Engine** (`/prompt-builder`): 20 role-filtered task templates, multi-model AI (Claude, ChatGPT, Grok)
- **Rubric scoring** (`/the-rubric`): 8-criteria standard + 5-tier advanced evaluation
- **PtA workflow**: Generate > Score > Iterate > Annotate > Submit > Approve
- **Knowledge Base**: 543 articles for AI context (but only 7 in "Finance & Marketing" category)

### What Works
- AI-generated first drafts save 60-70% of writing time for structured content (email templates, analysis briefs)
- Rubric scoring forces quality iteration — educational for the team
- Multiple AI model selection (Claude tends to produce higher-quality output for this use case)

### What's Missing
- **No brand voice configuration** — AI generates generic retail copy, not Harris Farm copy. The warmth, community focus, "For The Greater Goodness" ethos isn't embedded.
- **Creative content scoring is wrong** — Rubric penalises social captions for lacking data citations. A creative rubric variant is needed.
- **Prompt Engine and Marketing Assets are disconnected** — you can't reference a campaign creative while writing copy for it.
- **No social media-specific templates** — current templates are analytical (Store Performance, Product Trend). Marketing needs: Social Caption, Email Subject Line, Campaign Brief, Brand Story.
- **No content calendar integration** — can't plan, schedule, or track content production.

### The Brand Voice Gap (Critical)

Current AI output example:
> "Check out our amazing weekend specials! Fresh produce at unbeatable prices. Visit your local Harris Farm Markets today!"

What it should sound like:
> "This weekend, the stone fruit is singing. Luscious white peaches from the Riverina, nectarines so ripe they're blushing, and our growers' finest cherries. Pop in, grab a brown bag, and taste what summer's really about. For The Greater Goodness."

**The fix:** Create a `brand_voice.txt` system prompt that the Prompt Engine prepends to every marketing request. Include: tone (warm, community, family), vocabulary (growers not suppliers, fresh not cheap, community not customers), structure (storytelling over selling), and examples.

---

## 3. Data Connectivity Assessment

### What Exists (Available to Marketing)
| Data Source | Location | Marketing Relevance |
|-------------|----------|-------------------|
| Market Share (CBAS) | Customer Hub | High — postcode-level competitive intelligence for campaign targeting |
| Weekly Sales | Sales Dashboard | Medium — product performance for promotional planning |
| PLU Intelligence | PLU Intel | Medium — product trends for content creation |
| Product Trends | Trending | High — what's selling now for social content |
| Customer Count | Customer Hub | Low — aggregate, not segmented |
| KB Articles | Learning Centre | Low — 7 articles in Finance & Marketing |

### What's Missing (The Marketing Data Desert)

| Data Needed | Current Source | Hub Status |
|-------------|---------------|-----------|
| ROAS by channel | Meta Ads Manager, Google Ads | NOT IN HUB |
| CPA tracking | Meta Ads Manager, Google Ads | NOT IN HUB |
| A/B test results | Klaviyo, ad platforms | NOT IN HUB |
| Email open/click rates | Klaviyo | NOT IN HUB |
| Loyalty active members (90-day) | Loyalty platform | NOT IN HUB |
| Customer LTV cohorts | Klaviyo + POS crossmatch | NOT IN HUB |
| Brand health / sentiment | Brand tracking survey | NOT IN HUB |
| Share of Voice vs Coles/Woolworths | Media monitoring | NOT IN HUB |
| Social engagement metrics | Meta, TikTok, Instagram | NOT IN HUB |
| Website traffic / conversion | Google Analytics | NOT IN HUB |

**Verdict: 0 out of 10 marketing-specific data sources are connected to The Hub.**

---

## 4. Board Rubric Readiness Assessment

Sophie (CMO) presents to the board quarterly on these criteria:

### Brand Health & Awareness (Board Target: Score 1-3)

| Sub-Metric | Hub Status | Gap |
|------------|-----------|-----|
| Brand awareness (prompted/unprompted) | NOT IN HUB | Need brand tracking survey integration |
| Share of Voice vs Coles/Woolworths | NOT IN HUB | Need media monitoring tool integration |
| Net sentiment score | NOT IN HUB | Need social listening tool integration |
| Community partnership reach | NOT IN HUB | Manual tracking — could add to Hub as input form |

**Hub score: 0/3. The Hub cannot support Brand Health reporting.**

### Campaign ROI & Attribution (Board Target: Score 1-3)

| Sub-Metric | Hub Status | Gap |
|------------|-----------|-----|
| Blended ROAS (target: 4x) | NOT IN HUB | Need Meta Ads + Google Ads API |
| CPA by channel | NOT IN HUB | Need ad platform integration |
| Campaign attribution (last-touch/multi-touch) | NOT IN HUB | Requires cross-platform data stitching |
| A/B test win rates | NOT IN HUB | Need Klaviyo + ad platform integration |

**Hub score: 0/3. The Hub cannot support Campaign ROI reporting.**

### Digital & CRM Performance (Board Target: Score 1-2)

| Sub-Metric | Hub Status | Gap |
|------------|-----------|-----|
| Email open rate (target: 28%+) | NOT IN HUB | Need Klaviyo API |
| Loyalty active members (90-day) | NOT IN HUB | Need loyalty platform API |
| LTV cohort analysis | PARTIAL — customer count exists, LTV does not | Need Klaviyo + POS crossmatch |
| Website conversion rate | NOT IN HUB | Need Google Analytics API |

**Hub score: 0/2. The Hub cannot support Digital & CRM reporting.**

### B-Corp & Values Brand Integration (Board Target: Score 1-2)

| Sub-Metric | Hub Status | Gap |
|------------|-----------|-----|
| B-Corp messaging templates | PARTIAL — Greater Goodness page exists | Need messaging template library |
| Community partnership content | NOT IN HUB | Need content repository |
| ESG PR tracking | NOT IN HUB | Need PR monitoring tool integration |
| Sustainability metric visibility | PARTIAL — "100% renewable" on P1 intro page | Other metrics are "Coming Soon" |

**Hub score: 0.5/2. Minimal B-Corp presence but not actionable for board reporting.**

### Overall Board Rubric Readiness: 0.5 out of 10

---

## 5. Recommendations for Marketing

### Phase 1: Quick Wins (This Sprint)
1. **Brand voice configuration** — create `brand_voice.txt` system prompt for Prompt Engine
2. **Marketing-specific templates** — add 4 templates: Social Caption, Email Campaign, Campaign Brief, Brand Story
3. **Creative content rubric** — new scoring variant in `pta_rubric.py` for non-analytical content
4. **Connect Prompt Engine to Marketing Assets** — show relevant brand assets alongside AI-generated copy

### Phase 2: Data Foundation (Next Sprint)
5. **Manual marketing metrics input** — add a simple form where marketing team enters weekly ROAS, email rates, etc. Display on a new Marketing Dashboard.
6. **Klaviyo API integration** — email open/click rates, loyalty active members, subscriber growth
7. **Meta Ads API integration** — ROAS by campaign, CPA, impression/click data

### Phase 3: Full Marketing Intelligence (Backlog)
8. **Google Ads + Analytics integration** — website traffic, conversion, search campaign data
9. **Brand health survey integration** — quarterly brand tracking data
10. **Marketing Dashboard for board** — single page covering all 4 board rubric criteria with live data

### What to Tell Sophie (CMO) Now
"The Hub currently provides competitive intelligence (market share data) and content creation tools (Prompt Engine + Marketing Assets), but it does not yet have marketing performance data. We're building the data connections now. For this quarter's board presentation, you'll need to pull ROAS from Meta Ads Manager and email metrics from Klaviyo directly. By next quarter, we aim to have those feeds connected to The Hub."

**Honest. Specific. No overpromise.**
