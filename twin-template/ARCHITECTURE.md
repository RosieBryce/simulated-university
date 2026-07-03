# University Digital Twin — Abstract Architecture

This document abstracts the Stonegrove University simulation into a reusable architecture.
The goal: a repeatable method for building **digital twins of real UK universities** —
synthetic, privacy-free datasets that reproduce an institution's observable patterns —
runnable by any colleague from standard information collected when working with a partner.

The route there (see §10 for the full roadmap):

1. **Seed University** — a fictional but structurally realistic UK HE institution, built
   once from this architecture in a **new repo**, using real UK category systems
   (disaggregated ethnicities, IMD quintiles, HECoS-coded subjects, real academic
   calendar) and sector-typical statistics. This is the test case where we prove the
   model works as expected.
2. **Pilot twin** — test with a provider who trusts us; a real twin built as a parameter
   diff from the Seed. This is where we learn what the data request actually needs to
   contain and what accuracy each input tier buys.
3. **Blueprint** — the documented, colleague-runnable method, living in the same repo as
   the Seed.

The Stonegrove repo remains the **mechanism reference** — the code patterns every stage
follows. Its fantasy skin is cosmetic; nothing downstream should ever need to reason
about dwarves to build a twin.

---

## 1. The core design principle

> **Gaps emerge from distributions, never from direct group modifiers.**

No stage of the pipeline may say "students in group X get −5 marks". Instead, groups
differ in their *input distributions* — socio-economic status, prior educational
qualification, disability prevalence, subject preference — and outcome gaps (continuation,
attainment, employment) **emerge** from how those inputs flow through the causal chain.

This is the single most important property to preserve. It makes the data honest to
analyse (a researcher who controls for SES and prior attainment sees the gap shrink,
exactly as in real data), and it makes the ethics defensible: the simulation encodes
structural circumstance, not group essence. With real ethnicity labels this principle is
non-negotiable, and every distribution choice must be traceable to the real statistic it
was calibrated against — the blueprint records this provenance.

The second principle:

> **Publish only what a real institution could observe.**

The simulation runs on latent constructs (personality, motivation, stress, engagement
propensity). The published schema contains none of them — only their observable shadows:
attendance counts, VLE logins, marks, survey Likert responses, progression statuses.
The output-builder stage is the firewall.

---

## 2. Concept mapping

| Stonegrove concept          | Seed University concept                                                                                                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Clan (14)                   | **Disaggregated ethnicity** (e.g. Bangladeshi, Indian, Pakistani, Chinese, Black African, Black Caribbean, White British, White Other, Mixed White/Black Caribbean, …) — HESA/ONS categories, never collapsed into broad aggregates |
| Species (Dwarf/Elf)         | **Reporting hierarchy**: BAME / White at the top level, sub-grouped as Black, Asian, Other Minoritised Ethnicities (and White) — *reporting rollups only*; they carry **no distributions of their own**, everything hangs off the disaggregated category. One level more than Stonegrove's species/clan — implemented as two rollup columns on `dim_students` |
| Clan personality ranges     | Ethnicity-level latent trait distributions — calibrated so trait→engagement→outcome gradients reproduce the *residual* gap left after SES and entry-qualification effects                              |
| Clan SES distribution       | Ethnicity → IMD quintile / POLAR4 distribution (from HESA/OfS cross-tabs)                                                                                                                              |
| Clan health tendencies      | Ethnicity → disability declaration rates (per-condition Bernoulli, HESA categories)                                                                                                                    |
| Clan-programme affinities   | Ethnicity → subject-area preference weights (from HESA subject-of-study × ethnicity data), rebalanced against real per-programme student numbers where supplied (§5)                                   |
| Clan name pools             | Synthetic name pools per ethnicity, or fully random names — decide at Seed build                                                                                                                       |
| Education (3 categories)    | Entry route: A-levels / BTEC & other L3 / Access to HE / no formal L3 (UCAS end-of-cycle + HESA)                                                                                                       |
| 5 faculties / 55 programmes | Seed portfolio: faculties → programmes → modules (see §5)                                                                                                                                              |
| Academic years 1046-47…     | Real-format academic years, offset or clearly flagged as synthetic                                                                                                                                     |

**Why disaggregated ethnicities**: sector analysis shows patterns *within* broad groups
differ more than the groups differ from the sector average — Indian, Bangladeshi and
Pakistani attainment and progression trajectories are not interchangeable, and a twin
calibrated against broad-group averages would describe nobody. The clan mechanism
already handles 14 segments; the UK disaggregated ethnicity list is the same order of
magnitude.

---

## 3. The causal graph

```
ethnicity (disaggregated)
   ├─→ IMD/SES quintile ────────┐
   ├─→ entry route ─────────────┤
   ├─→ disability profile ──────┤
   ├─→ latent traits ───────────┤        (personality + motivation; hidden)
   └─→ programme choice         │
                                ▼
                     ENGAGEMENT (weekly)          ← module characteristics
                     attendance, VLE, participation, stress
                                │
                                ▼
                     ASSESSMENT (marks)           ← module difficulty, assessment mix
                                │
                                ▼
                     PROGRESSION                  ← traits (log-odds modifiers)
                     progress / repeat / withdraw / graduate
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
        next-year loop    DEGREE CLASS     SURVEYS (NSS, enrolment)
                                │
                                ▼
                        GRADUATE OUTCOMES
                        employment, salary band
```

Every arrow is a configurable modifier; every node writes an output table. The
longitudinal loop feeds progression back into next year's enrolment, and accumulated
history drives repeat-discouragement and degree classification.

---

## 4. Pipeline stages, abstracted

Each stage is an independent module with a `seed`, reading config, taking the previous
stage's DataFrame, returning its own. Strictly sequential.

### Stage 1 — Population generation

**Inputs**: cohort size, ethnicity intake shares, per-ethnicity distributions (IMD,
entry route, disability, latent traits, motivation), first-in-family model.
**Output**: one row per student with demographics + latent traits.
**Calibrate against**: intake profile (% by disaggregated ethnicity, IMD/POLAR,
disability declaration, entry qualification type, age on entry).

### Stage 2 — Programme enrolment

**Inputs**: the portfolio catalogue (§5), ethnicity-programme affinity weights,
trait-programme fit mapping, real per-programme student numbers where supplied.
**Output**: student × programme, with fixed module lists per programme year.
**Calibrate against**: per-programme/module intake counts (enhanced tier) or
subject-of-study × ethnicity cross-tabs (basic tier).

### Stage 3 — Engagement (weekly)

**Model**: per-student baseline from traits, shifted by disability/SES → per-module
adjustment → per-week AR(1) autocorrelated deviation + semester temporal arc (early
enthusiasm, midterm crunch, exam stress) + noise. Attendance rate → integer
attended/total sessions. VLE behaviour (login counts from a mixture model, resource
views, forum posts, login-hour distribution) generated alongside, deliberately only
*weakly* coupled to attendance so it retains independent predictive value.
**Calibrate against**: sector-typical attendance/VLE shapes (basic tier); the provider's
own attendance and VLE analytics norms (enhanced tier).

### Stage 4 — Assessment

**Model**: components per module weighted per the module's assessment mix. Mark = draw
from a multimodal base distribution × multiplicative modifiers (disability, entry route,
SES, module difficulty, engagement) + noise.
**Calibrate against**: mark distribution, % good honours per faculty/subject, and the
attainment gap sizes to reproduce.
**Known Stonegrove gap to fix at Seed build**: no persistent per-student ability term —
year-to-year mark autocorrelation is weaker than reality. The Seed should add one.

### Stage 5 — Progression

**Model**: pass rule over module marks (the Seed should include condonement/resits —
see Stonegrove backlog), then a **log-odds decision model**: base probabilities shifted
by traits, significant-disability flags, year-of-programme investment, prior-repeat
discouragement. Final-year pass → graduate.
**Calibrate against**: OfS continuation/completion rates overall and per ethnicity ×
IMD × entry route. This is the primary calibration target — ethnicity-level input
distributions are tuned until these rates emerge correctly.

### Stage 6 — Awards & graduate outcomes

**Model**: degree classification from weighted multi-year mark average; then outcome
type, professional level, sector (subject-mapped), salary band via log-odds models on
classification, SES, disability, traits. Survey non-response modelled explicitly and
non-uniformly.
**Calibrate against**: classification profile, Graduate Outcomes employment rates and
gaps (OfS progression measure).

### Stage 7 — Surveys

**Model**: theme scores = base + engagement signal + mark signal + demographic
adjustments + personality adjustment + correlated per-student bias + noise, clipped to
Likert 1–5. Non-respondents stay in the table with nulls (`survey_responded` flag).
**Calibrate against**: published NSS theme scores; response rates; internal survey
instruments and results where the provider shares them (enhanced tier).

### Stage 8 — Relational output builder (the firewall)

Assembles a star schema (dimensions: students, programmes, modules, academic years;
facts: enrolment, weekly engagement, assessment, progression, awards, outcomes,
surveys), **stripping every latent construct**. Also builds the distributable zip. A
validation script checks the outputs against the calibration targets.

---

## 5. The portfolio side — the twin is programmes, not just students

The digital twin must model the institution's **course portfolio** as a first-class
calibrated object: faculties, departments, programmes, modules, and each programme's
character. In Stonegrove this is the curriculum workbook plus two characteristics CSVs;
a twin needs the same artefacts built from real sources.

**Primary source (enhanced tier): the provider's curriculum management system.**
Expect a CSV export of real programme and module data — programme/module codes, titles,
diets per year, credit values — including **student numbers per programme and module**,
which directly balances the intake algorithm (Stage 2) instead of inferring intake
shares from subject-level statistics.

**On HECoS/CAH coding**: real universities treat this as *approximate* — there is
usually a mapping document somewhere associating real programmes with HECoS subjects,
rather than clean coding at source. So HECoS/CAH is the **linkage layer, not the
catalogue**: use the provider's mapping document (or build one) to connect their real
programmes to sector statistics (HESA subject data, Graduate Outcomes by subject, NSS
by subject) for calibration, while the portfolio itself comes from the curriculum
system export.

**Basic-tier fallback** (no provider data): reconstruct an approximate portfolio from
Discover Uni (Unistats) course records, prospectus module lists, and HESA subject-level
student numbers.

**Roughing out per-programme characteristics** (the analogue of
`programme_characteristics.csv` / `module_characteristics.csv`):

| Characteristic                          | Source / heuristic                                                                                  |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Practical/theoretical balance           | CAH group prior (nursing high-practical, philosophy high-theoretical) adjusted by Unistats assessment mix |
| Difficulty / mark severity              | Subject-level good-honours rates — some subjects systematically mark harder                            |
| Assessment mix per module               | Provider assessment records (enhanced) or Unistats course percentages distributed across the diet (basic) |
| Contact intensity (sessions/week)       | Provider timetable data (enhanced) or subject norms (basic)                                            |
| Career prospects                        | Graduate Outcomes professional-employment rate by CAH subject                                          |
| Stress level                            | Proxy from assessment load + subject-level NSS signals                                                 |
| Social intensity, creativity requirement| CAH group priors, hand-tuned                                                                           |
| PSRB constraints                        | Accredited programmes (nursing, social work, law, engineering) get progression rules closer to fitness-to-practise reality |

Either way the derivation of each value is recorded next to it, so it can be audited
and re-run.

**Seed portfolio shape**: a mid-size post-92-style institution profile is the most
useful default — broad portfolio (business, health, engineering/computing, arts &
design, social sciences, education), strong BTEC/vocational intake, diverse commuter
population — because that is where awarding-gap analysis matters most and where the
demographic machinery gets exercised hardest.

---

## 6. Inputs — two tiers

Be explicit about what we can source ourselves versus what the university must provide.
Each tier produces a twin; the tiers differ in how much of the institution's real
texture the twin carries. Accuracy percentages (~XX% / ~YY%) are placeholders to be
quantified during the pilot — measured as the share of validation targets hit within
tolerance, plus structural fidelity of the portfolio.

### Tier 1 — Basic twin (public + Heidi data only, ~XX% accurate)

Everything obtainable without the provider's involvement:

- **Heidi Plus / HESA**: intake profile by disaggregated ethnicity, IMD/POLAR, entry
  qualifications, disability, age; student numbers by subject area; qualifiers by
  classification.
- **OfS dashboards / APP data**: continuation, completion, progression and awarding
  gaps by demographic group — the calibration backbone.
- **NSS public results**: theme scores by provider and subject.
- **Graduate Outcomes**: employment rates by provider and subject.
- **Discover Uni (Unistats)**: course-level entry tariff, assessment mix, salaries.
- **Prospectus / course pages**: approximate portfolio and module diets.

Limits: portfolio is approximate (no real module codes or diets), intake balancing is
inferred from subject-level data, engagement/VLE shapes are sector-typical, academic
regulations are assumed.

### Tier 2 — Enhanced twin (Tier 1 + provider conversations, ~YY% accurate)

What we ask the partner for — this list becomes the standard data request in the
blueprint:

- **Curriculum management system export (CSV)**: real programmes, modules, diets,
  credit values, and student numbers per programme/module (§5).
- **HECoS mapping document**: their programme → HECoS/CAH associations.
- **Academic regulations**: condonement rules, resit caps, classification algorithm,
  progression board conventions.
- **Attendance / learning analytics norms**: real attendance rates, VLE usage
  distributions.
- **Internal intake statistics**: programme-level demographic profiles.
- **Internal survey instruments and results**: beyond NSS.
- **Timetable / contact hours**: per programme or module type.

Everything requested is aggregate or structural — the method never needs student-level
data, which is the point.

---

## 7. Partner data handling

The core move: **partner data never touches git**. Code lives in the repo; the
institution lives in the partner's folder.

- **The Seed repo** contains pipeline code, generic Seed config, and the blueprint —
  fully shareable with colleagues, never a partner number in it.
- **Each partner gets a folder on the PACT SharePoint site**, behind its existing
  access controls: the data request returns, the derived institution config, the
  provenance manifest, and validation reports. The derived config is as sensitive as
  the raw returns — it *is* their internal statistics restructured — so it lives in
  the partner zone, not the repo.
- **The pipeline takes a config-directory argument.** A colleague clones the Seed repo
  and points it at the partner's synced SharePoint folder. Nothing partner-specific is
  ever committed; the safe path is the lazy path. One-line mental model: *the repo is
  ours, the folder is theirs.*

### Engagement workflow

1. **Agreement** — a lightweight MoU naming the standard data request, storage
   location, retention, and access. No template currently exists — drafting one is
   part of the blueprint work.
2. **Aggregate-only, by design** — the data request never asks for student-level
   records; everything is structural (curriculum export) or aggregate (rates,
   distributions). This keeps GDPR largely out of scope and makes approval easy for a
   partner's data office. Partners apply their own rounding/suppression conventions
   before sending (HESA-style rounding is fine — calibration tolerances are ±1–2pp, so
   exact values were never needed; say so in the data request, it lowers perceived
   risk). If record-level data arrives by mistake: delete, re-request the aggregate.
3. **Collection** — partner uploads against the Tier 2 checklist; returns are
   versioned and dated.
4. **Translate → build → validate** — returns become institution config, with the
   provenance manifest citing a source document for every value; the calibrate–validate
   loop runs; the validation report (which contains their real targets) stays in the
   partner zone.
5. **Handover** — twin dataset + validation summary to the partner. **An enhanced-tier
   twin is not automatically publishable**, even though it's synthetic: it is
   calibrated to reproduce internal statistics that aren't public, so a good twin
   reveals approximations of them. Default: the twin belongs to the partner;
   publication needs their sign-off. A Tier 1 twin, built from public data only, is
   inherently publishable — the tiers are a governance distinction as well as an
   accuracy one.
6. **Genericise** — after each engagement, a deliberate lessons pass moves *process*
   learnings into the blueprint ("curriculum exports from System X come in this
   shape") under a hard rule: no numbers, no names, nothing structurally identifying.

---

## 8. Configuration surface

Two formats, one rule:

- **YAML** for hierarchical config: ethnicity specifications (trait ranges, disability
  prevalence), affinity matrices, progression rules, survey modifiers, outcome models.
- **CSV** for tabular config a human edits in Excel: module characteristics,
  programme characteristics, per-ethnicity SES/entry-route distributions — and the
  curriculum export slots in here as the portfolio source.

Every system takes a `seed`; a run writes `metadata.json` (seed, git commit, versions)
so any dataset is reproducible. All calibration numbers live in config, never in code —
the code is the *mechanism*, the config is the *institution*.

---

## 9. Calibration: from descriptive statistics to config

The data request supplies observed targets; the build must choose input distributions
that reproduce them. Working method, in order:

1. **Direct transcription** — intake shares, portfolio catalogue, response rates go
   straight into config.
2. **Backwards inference for gaps** — e.g. a 9pp continuation gap for a given ethnicity
   is achieved by shifting that group's IMD/entry-route mix and (secondarily) trait
   ranges, *not* by a group coefficient. Start from the real correlates: if the real
   gap shrinks by two-thirds when controlling for entry qualifications, then roughly
   two-thirds of the synthetic gap should flow through the entry-route distribution.
   OfS sector analyses publish exactly these decompositions.
3. **Iterate against the validation script** — run pipeline → compare emergent rates
   to targets → adjust distributions → re-run. Tolerances (e.g. ±1pp on continuation,
   ±2pp on awarding gap per group) belong in the validation config.

---

## 10. Roadmap — the actual workflow

1. **This document** — agree the abstraction. ← *you are here*
2. **Seed University build** — **new repo**, scaffolded from this architecture with
   Stonegrove as mechanism reference: real UK category systems throughout, a realistic
   portfolio (§5), sector-average calibration targets, and fixes for the known
   Stonegrove realism gaps (persistent ability term, condonement/resits, non-uniform
   survey response). **Design requirement**: the pipeline takes a config-directory
   argument (Stonegrove hardcodes `config/` paths), so a partner build can point at a
   SharePoint-synced folder and no partner data ever enters the repo (§7). Validate
   until sector-typical gaps emerge correctly.
3. **Pilot twin with a trusted provider** — build the first real twin as a parameter
   diff from the Seed. Learn what the data request actually needs to contain, where
   Tier 1 data falls short, and quantify the XX%/YY% accuracy claims.
4. **Blueprint** — written from what the pilot teaches us; lives **in the Seed repo**
   so any colleague can run it:
   - the **standard data request** — the Tier 1 checklist (what we gather ourselves)
     and Tier 2 pack (what we collect when working with a partner);
   - the **build runbook / generation prompt** — how to turn a completed data request
     into a validated twin, including the calibrate–validate loop and the provenance
     record for every distribution choice;
   - the **MoU template** for the agreement stage (§7) — none exists yet, draft from
     scratch during the pilot.

---

*Drafted 2026-07-03; revised same day: clans → disaggregated ethnicities; reporting
hierarchy BAME/White with Black, Asian, Other Minoritised Ethnicities sub-groups;
portfolio modelling and curriculum-system input added; input tiers added; partner data
handling added (§7); roadmap rewritten as Seed → pilot → blueprint.*
