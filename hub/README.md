# Stonegrove Hub

A simulated institutional SharePoint estate for Stonegrove University: a downloadable folder tree of realistic, messy institutional documents, browsed through a SharePoint-style explorer on the public site, for learners to practise using AI safely. The full brief is in [`docs/SHAREPOINT_BRIEF.md`](../docs/SHAREPOINT_BRIEF.md).

**Status: phase 0 (bible) complete, awaiting review. Nothing in-world has been written yet.**

## Layout

```
hub/
  README.md                this file: design note, source schema, rules, commands
  bible/                   OUT OF WORLD. Never shipped.
    cast.yaml              people, students, providers, contact details
    sites.yaml             sites, libraries, folder skeletons, budgets, transcripts
    storylines.md          the nine threads and where their traces are
    classification.yaml    the three-label scheme and the planted sensitive items
    mess_rules.yaml        the deliberate chaos, declared, with named lineages
    planted_errors.yaml    in-world AI-generated files and what is wrong in them
    off_brand.yaml         brand rules and the planted off-brand files
    hand_supplied.yaml     files the build copies but never regenerates
    filename_rules.yaml    Windows-safe naming, enforced by the linter
  source/                  one authored file per estate document (phase 1 onwards)
    <site folder>/<library folder>/<path>/<name>.md
  build/                   phase 1 onwards
    build_estate.py        source -> real files in a tree + manifest.json
    renderers/             md->docx, table->xlsx, outline->pptx, transcript->vtt, mail->eml, pdf
    make_mess.py           applies mess_rules.yaml deterministically
    lint_filenames.py      enforces filename_rules.yaml
    make_zips.py           estate, per-site and per-library zips, each with README.txt
  output/                  generated; gitignored except what ships
scripts/
  make_hub_extracts.py     dataset -> Planning and Insight extracts + values.yaml (phase 1)
docs/hub/                  the explorer and Learner Guide (phase 1 onwards)
```

## How it works

1. **Authored source.** Every document in the estate is a Markdown file with YAML front-matter in `hub/source/`, at the path it will occupy in the estate. Minutes, policies, transcripts and letters are written by hand so they read right. Routine volume (meeting series, forms, provider letters) uses templates.
2. **Build.** `build_estate.py` reads every source file, renders it to its real format (docx, xlsx, pptx, pdf, txt, csv, vtt, eml), copies in hand-supplied files, and writes `manifest.json` describing every file: path, title, author, modified, label, size, ground truth, lineage, storyline tags, skills, and which mess rule (if any) produced it.
3. **Mess.** `make_mess.py` applies `mess_rules.yaml` with the build seed: stale versions, copies, junk folders, litter, missing labels. Every derived file is recorded in the manifest with `derived_from` and `mess_rule`. The truth is always recoverable.
4. **Lint.** `lint_filenames.py` fails the build on any name or path that breaks `filename_rules.yaml`.
5. **Zip.** `make_zips.py` produces the whole-estate zip and one per site (and per library where the explorer needs it), each with a `README.txt` at the root saying what this is, that it is synthetic, and the licence.
6. **Explorer.** `docs/hub/index.html` reads `manifest.json` and renders a SharePoint-style explorer with downloads at estate, site, library and folder level, and a hints overlay. `docs/hub/guide.html` is the Learner Guide.

### Data linkage

`scripts/make_hub_extracts.py` reads `data/relational/` and writes two things into `hub/source/`: the Planning and Insight data extracts (small csv and xlsx files) and `hub/source/values.yaml`, a dictionary of named figures. Source documents quote figures as `{{ key }}` and the renderer fills them at build time. `build_relational_outputs.py` calls the script at the end, so a pipeline run with a new seed regenerates the extracts and every quoted figure. Deliberately wrong figures (the Dean's draft) are expressed as wrong *keys* or template operations, never literals, so they stay wrong in the right way.

Keys the bible already depends on (phase 1 defines them properly):

| Key | Meaning |
|---|---|
| `he_good_degree_gap_1052`, `_1051`, `_1050`, `_1049`, `_1048` | Faculty Elf minus Dwarf good honours rate, pp, by graduating year |
| `faculty_good_degree_rate_dwarf_1052`, `_elf_1052` | Faculty good honours rate by species |
| `health_good_degree_rate_dwarf_1052`, `_elf_1052` | Department of Health likewise |
| `education_good_degree_rate_dwarf_1052`, `_elf_1052` | Department of Education likewise |
| `education_nss_overall_1052`, `_1051` | Department of Education NSS overall satisfaction, mean 1 to 5 |
| `health_nss_overall_1052`, `_1051` | Department of Health likewise |
| `nursing_enrolled_1052` | Nursing and Care enrolments 1052-53 |
| `he_enrolled_1052` | Faculty enrolments 1052-53 |
| `nursing_withdrawal_rate_1052` | Nursing and Care withdrawal rate |

### Dates

In-world dates use ordinary month names and in-world years: `14 March 1053`. The dataset's academic years run `1046-47` to `1052-53`; the snapshot is **14 April 1053**. File metadata (Modified) is stored in-world in the manifest. For zip timestamps, which need real dates, the build maps in-world year Y to real year Y + 973 (so 1053 becomes 2026) keeping month and day. The mapping is internal; nothing in-world shows a real year.

## Source file schema

Each source file is `<name>.md` where `<name>` is the final filename without extension (the extension comes from `format`). Front-matter:

```yaml
---
title: Placement Allocation 1052-53        # display title; usually equals filename stem
format: xlsx                                # docx | xlsx | pptx | pdf | txt | csv | vtt | eml | md | png | jpg
author: halden-bridgeglen                   # cast id
modified_by: hesta-gracestone               # cast id; defaults to author
created: 1052-08-20
modified: 1053-01-20
label: Internal                             # Public | Internal | Confidential | null (none shown)
sensitive: false                            # ground truth, independent of label
site: pst                                   # sites.yaml id
library: pst-placements                     # sites.yaml library id
path: Allocation                            # folder path within the library; "" for root
storylines: [placements]
skills: [3, 9]
lineage:                                    # optional
  root: true                                # this is the lineage root for version_sprawl
  true_latest: true                         # or false if a sibling supersedes it
  of: <source path>                         # for a hand-authored version of another file
date_in_name: false                         # let filename_dates reformat a date in the name
mess:                                       # optional per-file overrides
  exempt: [copy_of, numbered_dup]
planted: P01                                # optional: classification.yaml id
planted_error: E02                          # optional: planted_errors.yaml id
off_brand: B01                              # optional: off_brand.yaml id
hand_supplied: false                        # true: build copies, never regenerates
---
```

The body depends on `format`:

- **docx, pdf, md, txt**: Markdown. Headings, lists, tables, bold. `{{ key }}` for figures from `values.yaml`. A `::: letterhead old` or `::: letterhead current` directive at the top selects the header (for the off-brand plantings).
- **xlsx, csv**: one or more fenced blocks tagged with the sheet name, containing CSV. Formulas as `=SUM(B2:B14)` are passed through for xlsx.
- **pptx**: Markdown with `---` between slides; first heading is the slide title. A `::: theme jaskel` directive selects the off-brand theme.
- **vtt**: a transcript DSL, one line per utterance: `[00:12:41] halden-bridgeglen: No worries, I'll sort it.` The renderer resolves display names, applies the per-transcript name-mangling map, and emits WebVTT and a docx version.
- **eml**: `From:`, `To:`, `Cc:`, `Date:`, `Subject:` headers, a blank line, the body in plain text, then optional `attachments:` listing other source paths to embed.

## Filename rules (summary; `bible/filename_rules.yaml` is authoritative)

Letters, digits, space, hyphen, underscore, full stop, round brackets. ASCII only. No leading or trailing space or dot, no double dots or spaces. One lowercase extension from the allowed list. No two names in one folder differing only by case. Every zip path under 180 characters. No Windows reserved names. Tilde and dollar forbidden unless phase 1 proves the `~$` lock-file prefix survives a Windows extraction.

## Contact details

Email `forename.surname@stonegrove.ac.example`. Landlines `01632 960000` to `960999`. Mobiles `07700 900000` to `900999`. External organisations use `.example` domains. The build lints for anything else.

## Writing rules for in-world content

British English. UK HE register. "Species", never "race". No real people, institutions, products or places. No em dashes anywhere. No stock AI phrasing. Characters are allowed to be verbose, pompous or chaotic in a human way; see the voice notes in `cast.yaml` and keep the tells consistent. Sensitive material about fictional students is written with the right texture and lives only where `classification.yaml` says.

## Commands (phase 1 onwards)

```bash
python scripts/make_hub_extracts.py                 # also called by build_relational_outputs.py
python hub/build/build_estate.py --seed 42          # render, mess, lint, manifest
python hub/build/make_zips.py                       # zips into docs/hub/downloads/
```

## Adding a document (phase 1 onwards)

1. Pick the site, library and path from `sites.yaml`. Check the library's budget.
2. Create `hub/source/<site folder>/<library folder>/<path>/<name>.md` with the front-matter above.
3. Make the name pass `filename_rules.yaml` before you write anything else.
4. If it names a student or carries personal data, set `sensitive: true` and decide the label deliberately. If the label is wrong on purpose, add it to `classification.yaml`.
5. If it quotes a figure from the dataset, use a `values.yaml` key, never a literal.
6. Rebuild. The linter will tell you if the name is wrong.

## Phases

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Bible (this folder) | Done, awaiting review |
| 1 | Vertical slice: Governance complete, one faculty library, T3, build + lint + manifest, explorer, whole-estate zip, Windows extraction test, extracts wired into pipeline | |
| 2 | Breadth: all sites, all transcripts, storylines threaded, additional-skill seeds, Communications with placeholders, off-brand plantings | |
| 3 | Mess and sensitivity pass; StoneShare library; planted items and errors recorded | |
| 4 | Learner Guide, hints overlay, per-site and folder downloads, nav link, CLAUDE.md and README updates, slop pass, QA by attempting every skill | |
