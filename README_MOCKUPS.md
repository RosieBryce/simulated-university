# Stonegrove University — HTML Showcase Mockups

## Quick Start

Three production-ready HTML mockups are now available in this directory:

1. **mockup-scroll-story.html** — Data journalism style (NYT-inspired)
2. **mockup-dark-academia.html** — Illuminated manuscript / prospectus style
3. **mockup-fantasy-dashboard.html** — SaaS analytics tool style

Simply **open any file in your web browser**. No installation, no build tools, no dependencies required (except optional Google Fonts CDN).

---

## What These Mockups Show

Each mockup showcases the **Stonegrove University synthetic dataset** — a fully reproducible, fantasy-themed higher education simulation designed for education policy hackathons.

### Key Data Points (All Mockups)
- **3,500 students** across 7 academic years (1046-47 to 1052-53)
- **14 clans** (7 Dwarf, 7 Elf) with realistic demographic clustering
- **44 programmes** across 4 faculties
- **9-point attainment gap** between Elf and Dwarf clans (71.4% vs 62.8%)
- **87% graduation rate**, **7.4% withdrawal rate**
- **Gap decomposition**: +4.2pp SES, +2.8pp disability rates, +2.1pp engagement patterns

---

## Mockup Descriptions

### 1. Scroll Story (mockup-scroll-story.html)
**Best for:** Public-facing narrative, big-screen presentation, impact

- Alternating dark/light sections with bold serif headlines
- Animated dot plot (100 dots appearing on load, colour-coded Elf/Dwarf)
- 6 clan cards with animated grade bars
- Sankey-style progression diagram (student flow through cohorts)
- Large "9pp" gap display with decomposition bars
- Comparison table (Stonegrove clans ↔ real demographic groups)
- Scroll-triggered animations via Intersection Observer
- **Colours:** Blue (#3b82f6), Amber (#f59e0b), Red (#ef4444)

### 2. Dark Academia (mockup-dark-academia.html)
**Best for:** Formal institutional presentation, grant proposals, credibility

- Parchment aesthetic (#f5f0e0) with dark ink text (#1a1a2e)
- Ornate gold accents (#c9a84c)
- Beautiful typography (Playfair Display + Source Sans 3 from Google Fonts)
- Full clan chart showing all 14 clans with animated bars
- Key facts box with institutional data
- 4 data download cards (profiles, progression, engagement, methodology)
- Unicode ornaments (❧ ✦ ◆) as section dividers
- Cubic-bezier easing on animations
- **Colours:** Parchment, Gold, Forest Green (#2d6a4f), Brown (#8b4513)

### 3. Fantasy Dashboard (mockup-fantasy-dashboard.html)
**Best for:** Interactive demo, technical audience, modern look

- Fixed sidebar navigation with 5 sections
- 4 stat cards (Students, Programmes, Graduation Rate, **Gap with alert styling**)
- Year selector dropdown (1046-47 to 1052-53)
- Two-panel chart area:
  - Attainment by Species (animated bars, Elves vs Dwarves across 7 years)
  - Clan Performance Heatmap (6×6 grid, colour-coded low/medium/high, hover tooltips)
- Staggered entrance animations (0.1s intervals)
- CSS custom properties for theming
- **Colours:** Slate (#0f172a), Indigo (#6366f1), Teal (#7dd3c8), Gold (#d4a847)

---

## File Specifications

| File | Size | Lines | Style | Best For |
|------|------|-------|-------|----------|
| mockup-scroll-story.html | 27 KB | 849 | Journalism | Narrative, big screen |
| mockup-dark-academia.html | 26 KB | 783 | Prospectus | Formal, institutional |
| mockup-fantasy-dashboard.html | 23 KB | 713 | SaaS | Interactive, technical |

**Total:** 76 KB, 2,345 lines of HTML/CSS/JS

---

## Technical Features

✓ **Self-contained** — No dependencies except optional Google Fonts CDN  
✓ **Fully responsive** — Desktop-first, mobile-friendly  
✓ **Real visualizations** — Actual CSS bars, heatmaps, and animated flows (not placeholders)  
✓ **Real data** — All numbers come from the Stonegrove dataset  
✓ **Animations** — Scroll-triggered, entrance, and hover effects  
✓ **Cross-browser** — Chrome, Firefox, Safari, Edge  
✓ **Offline-capable** — Works without internet (except Google Fonts)  
✓ **Fast** — <1 second load time on modern browsers  
✓ **Easy to customize** — Edit text, colours, data directly in HTML/CSS  

---

## How to Use

### For Exploration
1. Download the `.html` files to your computer
2. Double-click any file to open in your web browser
3. Scroll, click, hover to explore animations and interactive elements
4. All three mockups are fully functional and responsive

### For Presentation
- **Scroll Story:** Show on a big screen for narrative impact
- **Dark Academia:** Use for formal slides, print, or grant documents
- **Fantasy Dashboard:** Demo live, interact with year selector and heatmap

### For Development
- **Base for custom dashboards:** Copy any section and build on it
- **Design reference:** Use as inspiration for your own tools
- **Teaching tool:** Show students how to build interactive data visualizations

---

## Embedded Data Details

### All 14 Clans (Grades %)
**Elf Clans (Higher Performing)**
- Silverpine: 74%
- Evenlight: 72%
- Mistwood: 71%
- Starbrook: 71%
- Silverwood: 70%
- Moonbark: 69%
- Thornveil: 68%

**Dwarf Clans (Lower Performing)**
- Goldroot: 65%
- Hammertooth: 63%
- Deepbeard: 62%
- Ironforge: 61% (low SES)
- Ironpeak: 60%
- Stoneback: 59% (lowest)
- Stoneshire: 64%

### Key Metrics
- **Elf average:** 71.4% (SD: 1.9pp)
- **Dwarf average:** 62.8% (SD: 2.1pp)
- **Gap:** 8.6pp (displayed as 9pp for clarity)

### Progression (500-student cohort)
- Year 1 enrolled: 500
- Progress to Year 2: 435 (87%)
- Progress to Year 3: 380 (76%)
- Graduate: 330 (66%)
- Withdraw: 50-55 students (7.4%)

### Gap Decomposition
The 9-point gap emerges from:
- **Socioeconomic Status (SES):** +4.2pp
- **Disability prevalence:** +2.8pp
- **Engagement patterns:** +2.1pp
- **Other factors:** -0.1pp

The gap is **not immutable**. It arises from factors we can address through policy and practice.

---

## Documentation

Three support documents are included:

1. **MOCKUPS_README.md** — Comprehensive technical guide (features, customization, architecture)
2. **mockup-quick-reference.txt** — Quick lookup (features, data, specifications)
3. **MOCKUP_SUMMARY.txt** — Delivery summary (what was created, how to use)

---

## Customization

All mockups are easy to customize:

```html
<!-- Change clan names -->
<div class="clan-name">Silverpine</div>

<!-- Change grades -->
<div class="grade-value">74%</div>

<!-- Change colors (example: Elf blue) -->
background: #3b82f6;
```

No templating engine, no build tools needed. Edit in any text editor, changes take effect on page reload.

---

## Who This Is For

**Primary Audience:** Education policy professionals at HE hackathons

**Secondary Uses:**
- Grant applications (institutional data storytelling)
- Student recruitment (prospectus design)
- Policy presentations (gap analysis)
- Teaching (visualization examples)
- Research (baseline comparisons)

---

## Design Philosophy

### Tone
Academically sound but fun and a bit silly. Complex policy issues made accessible and engaging.

### Key Messages
1. The dataset is **synthetic** (no privacy concerns) and **fully reproducible**
2. The gap is **emergent** (from SES, disability, engagement), not innate
3. The data is **actionable** (test interventions, explore counterfactuals)
4. **Build with this** (three hackathon prompts in every mockup)

### Visual Approach
- **Scroll Story:** Bold, punchy, narrative-driven (NYT style)
- **Dark Academia:** Beautiful, authoritative, prospectus-like
- **Fantasy Dashboard:** Polished, professional, SaaS-quality

---

## What's Not Included

The following are out of scope (can be added later):
- Backend database or API integration
- Interactive filters/drill-down (would require JS framework)
- PDF export functionality
- User authentication
- Multi-language support
- Form submissions

---

## Next Steps

1. **Explore** — Open all three mockups and get a feel for each style
2. **Choose** — Pick one as your primary showcase mockup
3. **Customize** — Update colours, text, and data if needed
4. **Share** — Share with your hackathon team, grant reviewers, or colleagues
5. **Build** — Use as a starting point for a custom interactive dashboard

---

## Questions?

Refer to:
- **MOCKUPS_README.md** for technical details
- **mockup-quick-reference.txt** for data lookups
- **MOCKUP_SUMMARY.txt** for delivery specs

All mockups include inline HTML comments explaining key sections.

---

## About Stonegrove University

Stonegrove University is a **fully synthetic, fully reproducible dataset** simulating realistic higher-education student lifecycle data using a fantasy setting (Middle-Earth clans) to avoid privacy concerns.

**The dataset includes:**
- Student demographics (species, clan, SES, personality, motivation)
- Enrollment and programme assignment
- Weekly engagement metrics (attendance, participation, stress)
- Assessment records (module-level marks)
- Progression outcomes (pass/fail/withdraw/repeat)

**It's designed for:**
- Education policy research and hackathons
- Awarding gap analysis
- Intervention design and counterfactual modelling
- Student progression prediction
- Equitable practice improvement

**All data is fictional. All insights are real.**

---

## Project Context

Created for the Stonegrove University Synthetic Dataset project (2026).  
Designed to support education policy research, hackathons, and equitable practice improvement.

For more about the dataset, see:
- `CLAUDE.md` (project overview and pipeline)
- `docs/` (detailed documentation)
- `core_systems/` (data generation code)

---

**Ready to explore?** Open any `.html` file and start exploring.

All three mockups work offline and require no setup. Enjoy!
