#!/usr/bin/env python3
"""
Generate the templated-volume source documents for the Stonegrove Hub.

    python hub/build/generate_sources.py            # all generators
    python hub/build/generate_sources.py providers  # one generator

Hand-authored documents live in hub/source/ and are written by people. The
routine volume (thirty provider letters, the 14-tab placement workbook, the
applicant tracker, exam board marks tables, routine support plans, the Brand
Compliance Log) is generated here from the bible and the data extracts, with
a fixed seed, into the same hub/source/ tree. Every generated source carries
`generated: true` in its front-matter and is overwritten on each run, so do
not hand-edit them: edit the generator or the bible.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
PROJECT = HUB.parent
SOURCE = HUB / "source"
BIBLE = HUB / "bible"
REL = PROJECT / "data" / "relational"
SEED = 42

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def fm(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=None).strip() + "\n---\n\n"


def write(rel: str, meta: dict, body: str) -> Path:
    p = SOURCE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    meta = dict(meta)
    meta["generated"] = True
    p.write_text(fm(meta) + body, encoding="utf-8", newline="\n")
    return p


def longdate(y: int, m: int, d: int) -> str:
    return f"{d} {MONTHS[m - 1]} {y}"


def load_cast() -> dict:
    return yaml.safe_load((BIBLE / "cast.yaml").read_text(encoding="utf-8"))


def nc_students(year: str = "1052-53") -> pd.DataFrame:
    st = pd.read_csv(REL / "dim_students.csv")
    en = pd.read_csv(REL / "fact_enrollment.csv")
    nc = en[(en["programme_code"] == "4_2_7") & (en["academic_year"] == year)]
    d = nc.merge(st[["student_id", "forename", "surname", "species", "clan", "disabilities"]], on="student_id")
    d["display_id"] = d["student_id"].map(lambda i: f"1052-NC-{int(i) % 10000:04d}")
    return d.sort_values(["programme_year", "surname", "forename"]).reset_index(drop=True)


# =====================================================================
# Provider correspondence: thirty letters and emails, skill 7
# =====================================================================

LETTER_TEMPLATES = [
    # (format, template). Fields: {name} {contact} {uni_contact} {date} {capacity} {conditions} {year} {sem}
    ("docx", """::: letterhead none

**{name}**
{address}

{date}

{uni_contact}
Programme Support Team, Nursing and Care
Stonegrove University

Dear {uni_first}

**Re: Student placements, {year}**

Thank you for your letter of last month. I am writing to confirm the arrangements for Stonegrove students for the coming year.

We are able to offer **{capacity_sentence}** We would ask that {conditions_sentence}

Our contact for all placement matters remains {contact}, who can be reached on {phone} or at {email}. Please do not send student details to the general enquiries address.

{extra_para}

We look forward to welcoming your students again.

Yours sincerely

{contact}
{role}
{name}
"""),
    ("eml", """From: {email}
To: halden-bridgeglen
Cc: hesta-gracestone
Date: {iso}
Subject: {subject}

Hi Halden

{opening}

For {year}: {capacity_sentence} {conditions_sentence_short}

{extra_para}

Best
{contact_first}

{contact}, {role}
{name}
{phone}
"""),
    ("pdf", """# {name}

## Placement agreement: Stonegrove University, Nursing and Care, {year}

Date: {date}

| | |
|---|---|
| Provider | {name} |
| Provider contact | {contact}, {role} |
| Telephone | {phone} |
| Email | {email} |
| University contact | Halden Bridgeglen, Placements Coordinator |

### Places offered

{capacity_sentence}

### Conditions

{conditions_sentence}

### Other

{extra_para}

Signed for the provider: {contact}

Signed for the University: ____________________
"""),
    ("docx", """::: letterhead none

{date}

Dear Mr Bridgeglen

I write on behalf of {name} regarding student placements for the academic year {year}.

{opening}

Following discussion with my colleagues, {capacity_sentence_lower} I should add that {conditions_sentence_lower}

{extra_para}

Should you need to discuss any of this, I am on {phone}. Email reaches me more reliably: {email}.

Kind regards

{contact}
{role}, {name}
"""),
]

EXTRAS = [
    "We had a very positive experience with your students last year and two have since applied to join us on qualification.",
    "One of your students last year arrived without occupational health clearance and had to be sent home, which was awkward for everyone. Please could the University check this before the first day.",
    "We have a new car park arrangement; students should use the overflow car park and allow fifteen minutes to walk across.",
    "Please note our mentor for the autumn, who your students will know, is retiring in December. We are arranging cover.",
    "We would be grateful if students could be reminded that photographs are not permitted anywhere on the premises, including of their own documentation.",
    "Our induction now includes a half day on record-keeping. Students should attend this even if they have had similar training elsewhere.",
    "We can take an additional student at short notice if another provider withdraws, provided we have a week's notice.",
    "We are unable to offer placements in the two weeks either side of the midwinter festival.",
    "Students should bring their own lunch; the canteen is for staff only and the nearest shop is some distance.",
    "Please send the student names and start dates only. We do not need, and would rather not hold, any other information about them.",
    "We have changed our telephone number since last year; the number above is correct.",
    "Last year's paperwork arrived in three separate emails from three different people. One point of contact at the University would help us a great deal.",
]

ROLES = ["Practice Manager", "Placement Lead", "Senior Nurse", "Clinical Educator", "Service Manager", "Lead Practitioner", "Education Lead", "Ward Manager"]


def gen_providers() -> int:
    rng = random.Random(SEED + 7)
    cast = load_cast()
    providers = cast["providers"]
    uni_contacts = ["Halden Bridgeglen", "Hesta Gracestone"]
    count = 0
    for i, p in enumerate(providers):
        # Two letters for a few providers (changed capacity), one for the rest
        years = ["1052-53"] if i % 6 else ["1051-52", "1052-53"]
        for yi, year in enumerate(years):
            tpl_fmt, tpl = LETTER_TEMPLATES[(i + yi) % len(LETTER_TEMPLATES)]
            cap_note = p["capacity_note"]
            cap_text, _, cond_text = cap_note.partition(",")
            cap_text = cap_text.strip()
            cond_text = cond_text.strip() or "students follow the usual professional requirements"
            if yi == 0 and len(years) == 2:
                # earlier year, different capacity
                import re as _re
                m = _re.match(r"(\d+)", cap_text)
                if m:
                    n = max(1, int(m.group(1)) - rng.choice([1, 2]))
                    cap_text = _re.sub(r"^\d+", str(n), cap_text)
            y = int(year[:4]) + (0 if yi == 0 and len(years) == 2 else 0)
            month = rng.choice([6, 7, 8, 9]) if yi == len(years) - 1 else rng.choice([6, 7, 8])
            day = rng.randint(1, 28)
            yy = int(year[:4])
            ctx = dict(
                name=p["name"], contact=p["contact"], contact_first=p["contact"].split()[-2] if p["contact"].split()[0] in ("Dr", "Sister", "Matron") else p["contact"].split()[0],
                role=ROLES[i % len(ROLES)], phone=p["phone"], email=p["email"],
                address=f"{p['name'].split(',')[0]}, {rng.choice(['Greywater Vale', 'The Vale Road', 'Lower Stonegrove', 'Ashen Reach', 'Palm Coast', 'Cragburrow'])}",
                date=longdate(yy, month, day), iso=f"{yy}-{month:02d}-{day:02d}", year=year,
                uni_contact=uni_contacts[i % 2], uni_first=uni_contacts[i % 2].split()[0],
                capacity_sentence=f"{cap_text[0].upper() + cap_text[1:]}.",
                capacity_sentence_lower=f"we can offer {cap_text}.",
                conditions_sentence=f"{cond_text[0].upper() + cond_text[1:]}.",
                conditions_sentence_lower=f"{cond_text}.",
                conditions_sentence_short=f"Conditions: {cond_text}.",
                extra_para=EXTRAS[(i * 3 + yi) % len(EXTRAS)],
                opening=rng.choice(["Hope you are well and the term has started gently.", "Thanks for chasing, sorry for the delay, it has been a month.",
                                    "Good to see you at the providers' forum.", "Quick one as promised."]),
                subject=rng.choice([f"Placements {year}", f"RE: RE: student numbers {year}", f"Stonegrove students next year", f"FW: placement capacity {year}"]),
            )
            body = tpl.format(**ctx)
            short = p["name"].replace(",", "").replace("'", "").replace("&", "and")
            fname_stem = {
                0: f"{short} letter {year}",
                1: f"RE {short} placements {year}",
                2: f"{short} placement agreement {year}",
                3: f"Letter from {short} {MONTHS[month - 1]} {yy}",
            }[(i + yi) % 4]
            meta = dict(
                title=fname_stem, format=tpl_fmt, author="halden-bridgeglen",
                created=f"{yy}-{month:02d}-{day:02d}", modified=f"{yy}-{month:02d}-{min(day + 2, 28):02d}",
                label="Internal", sensitive=False, site="pst", library="pst-providers", path=year,
                storylines=["placements"], skills=[7], provider=p["id"],
            )
            if tpl_fmt == "eml":
                meta["author"] = "halden-bridgeglen"
            write(f"Programme Support Team Nursing and Care/Provider Correspondence/{year}/{fname_stem}.md", meta, body)
            count += 1
    return count


# =====================================================================
# The placement allocation workbook, 14 tabs
# =====================================================================

def gen_placement_workbook() -> int:
    rng = random.Random(SEED + 11)
    cast = load_cast()
    providers = cast["providers"]
    students = nc_students()
    y1 = students[students["programme_year"] == 1]
    y2 = students[students["programme_year"] == 2]

    def csv_rows(rows):
        import csv as _csv, io as _io
        s = _io.StringIO()
        w = _csv.writer(s)
        for r in rows:
            w.writerow(r)
        return s.getvalue().strip("\n")

    sheets = []
    # 1 Providers
    rows = [["Provider", "Contact", "Phone", "Email", "Places", "Notes", "Agreement signed?", "Last contacted"]]
    for p in providers:
        import re as _re
        m = _re.match(r"(\d+)", p["capacity_note"])
        rows.append([p["name"], p["contact"], p["phone"], p["email"], int(m.group(1)) if m else "", p["capacity_note"],
                     rng.choice(["Y", "Y", "Y", "N", "?", "see email"]), rng.choice(["Sep 1052", "Aug 1052", "Jul 1052", "last year", "", "ring H"])])
    sheets.append(("Providers", rows))

    # 2 Y2 Sem1 allocation, 3 Y2 Sem2 allocation, 4 Y1 intro placement
    def alloc(df, label, sem, start):
        rows = [["Student ID", "Surname", "Forename", "Pathway", "Provider", "Mentor", "Start", "End", "OH cleared", "Mandatory training", "Adjustments?", "Notes"]]
        provs = [p for p in providers]
        for _, s in df.iterrows():
            p = rng.choice(provs)
            oh = rng.choice(["Y", "Y", "Y", "Y", "pending", "N", "Y (letter)", "y"])
            rows.append([s["display_id"], s["surname"], s["forename"], rng.choice(["Adult", "Adult", "Community", "Mental health"]), p["name"],
                         rng.choice([p["contact"], "", "tbc", p["contact"].split()[-1]]), start, "", oh,
                         rng.choice(["complete", "complete", "2 outstanding", "", "done"]),
                         rng.choice(["", "", "", "Y see Wellbeing", "yes - no nights wk 1-2", "Y"]),
                         rng.choice(["", "", "", "swap requested (no)", "lives near Palm Coast", "repeat placement", "travel bursary", "ring provider re start date"])])
        return (label, rows)
    sheets.append(alloc(y2, "Y2 S1 alloc", 1, "1052-10-06"))
    sheets.append(alloc(y2, "Y2 S2 alloc", 2, "1053-02-17"))
    sheets.append(alloc(y1, "Y1 intro", 2, "1053-03-03"))
    # 5 Capacity
    rows = [["Provider", "Places", "Y2 S1 used", "Y2 S2 used", "Y1 used", "Spare", "Check"]]
    for i, p in enumerate(providers):
        rows.append([p["name"], "=INDEX(Providers!E:E,MATCH(A{r},Providers!A:A,0))".replace("{r}", str(i + 2)),
                     f"=COUNTIF('Y2 S1 alloc'!E:E,A{i + 2})", f"=COUNTIF('Y2 S2 alloc'!E:E,A{i + 2})", f"=COUNTIF('Y1 intro'!E:E,A{i + 2})",
                     f"=B{i + 2}-MAX(C{i + 2}:E{i + 2})", f'=IF(F{i + 2}<0,"OVER","")'])
    sheets.append(("Capacity", rows))
    # 6 OH tracker (free text: the thing Hesta flagged)
    rows = [["Student ID", "Name", "OH status", "Detail", "Date", "Chased"]]
    for _, s in students.sample(min(40, len(students)), random_state=SEED).iterrows():
        rows.append([s["display_id"], f"{s['forename']} {s['surname']}", rng.choice(["Cleared", "Cleared", "Pending", "Cleared with restrictions", "Not started"]),
                     rng.choice(["", "", "awaiting vaccination record", "back problem - no heavy lifting per OH", "asthma, inhaler", "needle phobia - OH aware", "mental health - see Wellbeing", ""]),
                     rng.choice(["1052-09-12", "1052-10-01", "1052-11-20", "1053-01-15", ""]), rng.choice(["", "x", "xx", "xxx"])])
    sheets.append(("OH tracker", rows))
    # 7 Mandatory training
    rows = [["Student ID", "Name", "Moving and handling", "Infection control", "Safeguarding", "IG", "Complete?"]]
    for _, s in students.iterrows():
        vals = [rng.choice(["Y", "Y", "Y", "N"]) for _ in range(4)]
        rows.append([s["display_id"], f"{s['forename']} {s['surname']}"] + vals + ["Y" if all(v == "Y" for v in vals) else "N"])
    sheets.append(("Mand training", rows))
    # 8 Mentors
    rows = [["Provider", "Mentor", "Qualified mentor?", "Last update", "Notes"]]
    for p in providers:
        rows.append([p["name"], p["contact"], rng.choice(["Y", "Y", "?", "lapsed"]), rng.choice(["1052", "1051", "1050", ""]), rng.choice(["", "", "retiring Dec", "new", "prefers phone"])])
    sheets.append(("Mentors", rows))
    # 9 Travel bursary
    rows = [["Student ID", "Name", "Provider", "Form received", "Amount", "Paid"]]
    for _, s in y2.sample(min(12, len(y2)), random_state=SEED + 1).iterrows():
        rows.append([s["display_id"], f"{s['forename']} {s['surname']}", rng.choice(["Brinestep Coastal Clinic", "Cragburrow Mine Surgery", "Palm Coast Ambulance Station"]), rng.choice(["Y", "N", "Y"]), rng.choice([40, 60, 85, 120]), rng.choice(["Y", "N", ""])])
    sheets.append(("Travel", rows))
    # 10 Issues log
    rows = [["Date", "Student", "Provider", "Issue", "Action", "Closed"]]
    issues = [("1052-10-09", "wrong site", "Sent to main site not outpatients. Rang provider, sorted by 10am", "Y"),
              ("1052-10-15", "no OH clearance", "Sent home. OH chased. Restarted following week", "Y"),
              ("1052-11-02", "swap", "Two students swapped without telling us. Both placements pulled. Dagna spoke to them", "Y"),
              ("1052-11-14", "documentation error", "Medication documentation error, mentor reported. Referred to Nyssa (FtP). Student removed from placement pending", "N"),
              ("1052-11-28", "mentor off sick", "No mentor for 2 weeks. Provider found cover week 2", "Y"),
              ("1053-01-20", "storms", "Brinestep closed. 6 students reallocated to Greywater OPD at 3 days notice", "Y"),
              ("1053-02-03", "OH column", "Hesta says OH detail column should not have health notes in. Agreed. Not done yet", "N"),
              ("1053-02-24", "adjustments", "Mentor not told about student adjustments (no nights). Student did nights. Wellbeing involved", "N"),
              ("1053-03-10", "photo", "Student photographed drug chart. FtP referral", "N")]
    for d, iss, act, cl in issues:
        s = y2.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
        rows.append([d, f"{s['forename']} {s['surname']}", rng.choice(providers)["name"], iss, act, cl])
    sheets.append(("Issues", rows))
    # 11 Contacts (old)
    rows = [["Provider", "Old contact", "Old phone", "Replaced by", "When"]]
    for p in providers[:12]:
        rows.append([p["name"], rng.choice(["Bolrik Cragburrow", "Enna Frostmantle", "Orien Candletome", "Jessa Claydancer"]), "01632 960" + str(rng.randint(100, 999)), p["contact"], rng.choice(["1050", "1051", "1052", "?"])])
    sheets.append(("Contacts OLD", rows))
    # 12 Lookups
    sheets.append(("Lookups", [["Pathway"], ["Adult"], ["Community"], ["Mental health"], ["Children (Y2 S2 only)"]]))
    # 13 Notes
    sheets.append(("Notes", [["Note"], ["Tab 9 formulas broke when I inserted a column in Providers. Fixed? Check Capacity."], ["DO NOT sort Y2 S1 alloc by provider, it unlinks the mentor column (not actually linked, just looks wrong)"],
                             ["Hesta has a better version of the OH tracker in her folder. Use that."], ["Liora: colour coding is in the legend tab (tab 14). Green = done. Yellow = chase. Red = problem. Grey = I don't know."],
                             ["Handover: everything is in my head and in this file. Writing it down. H"], ["If Brinestep closes for storms ring Agda at Greywater FIRST, she can usually take 4-6 at short notice"]]))
    # 14 Legend
    sheets.append(("Legend", [["Colour", "Meaning"], ["Green", "Done"], ["Yellow", "Chase"], ["Red", "Problem"], ["Grey", "Unknown"], ["Blue", "Halden to do"], ["Purple", "Hesta did this"]]))

    body = "\n\n".join(f"```sheet:{name}\n{csv_rows(rows)}\n```" for name, rows in sheets)
    meta = dict(title="Placement Allocation 1052-53", format="xlsx", author="halden-bridgeglen", modified_by="hesta-gracestone",
                created="1052-08-20", modified="1053-01-20", label="Internal", sensitive=True,
                site="pst", library="pst-placements", path="Allocation", storylines=["placements"], skills=[3, 9, 5],
                lineage={"root": True, "true_latest": False},
                note="sensitive: true because the OH tracker holds free-text health notes (Advice Given 1053-02-03). Label Internal is the in-world label.")
    write("Programme Support Team Nursing and Care/Placements/Allocation/Placement Allocation 1052-53.md", meta, body)
    return 1


# =====================================================================
# Examination board marks tables (student IDs only), from the assessment facts
# =====================================================================

def gen_examboards() -> int:
    asm = pd.read_csv(REL / "fact_assessment.csv")
    en = pd.read_csv(REL / "fact_enrollment.csv")
    pr = pd.read_csv(REL / "dim_programmes.csv")
    mods = pd.read_csv(REL / "dim_modules.csv")
    hep = pr[(pr["faculty"] == "Health & Education") & (pr["department"] == "Health")]
    e = en[(en["academic_year"] == "1052-53") & (en["programme_code"].isin(hep["programme_code"]))]
    a = asm[(asm["academic_year"] == "1052-53")].merge(e[["student_id", "programme_code", "programme_year"]], on="student_id")
    a = a.merge(mods[["module_code", "module_title"]], on="module_code", how="left").merge(hep[["programme_code", "programme_name"]], on="programme_code")
    count = 0
    for yr in (2, 3):
        sub = a[a["programme_year"] == yr]
        if sub.empty:
            continue
        piv = sub.pivot_table(index=["programme_name", "student_id"], columns="component_code", values="assessment_mark", aggfunc="mean").reset_index()
        piv["student_id"] = piv["student_id"].map(lambda i: f"1052-HE-{int(i) % 100000:05d}")
        sheets = []
        for prog, g in piv.groupby("programme_name"):
            rows = [["Student number", "MIDTERM", "FINAL", "Combined (0.4/0.6)", "Outcome"]]
            for _, r in g.iterrows():
                mid, fin = r.get("MIDTERM", float("nan")), r.get("FINAL", float("nan"))
                comb = round(0.4 * mid + 0.6 * fin, 1) if pd.notna(mid) and pd.notna(fin) else ""
                rows.append([r["student_id"], "" if pd.isna(mid) else round(mid, 1), "" if pd.isna(fin) else round(fin, 1), comb,
                             "" if comb == "" else ("Pass" if comb >= 40 else "Refer")])
            sheets.append((prog[:31], rows))
        import csv as _csv, io as _io
        def csv_rows(rows):
            s = _io.StringIO(); w = _csv.writer(s)
            for r in rows: w.writerow(r)
            return s.getvalue().strip(chr(10))
        nl = chr(10)
        body = (nl + nl).join(f"```sheet:{n}{nl}{csv_rows(r)}{nl}```" for n, r in sheets)
        meta = dict(title=f"EB-1053 marks tables Health Year {yr} DRAFT", format="xlsx", author="erra-measurine", modified_by="ollir-greenquill",
                    created="1053-04-02", modified="1053-04-02", label="Confidential", sensitive=True, site="quality", library="q-examboards",
                    path="Health 1052-53", storylines=[], skills=[2, 5],
                    note="Student numbers only. Mean marks per component across the student's modules; draft cut for the June board.")
        write(f"Quality/Examination Boards/Health 1052-53/EB-1053 marks tables Health Year {yr} DRAFT.md", meta, body)
        count += 1
    return count


GENERATORS = {
    "providers": gen_providers,
    "placements": gen_placement_workbook,
    "examboards": gen_examboards,
}


def main(argv: list[str]) -> int:
    names = argv or list(GENERATORS)
    for n in names:
        count = GENERATORS[n]()
        print(f"  {n}: {count} source document(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
