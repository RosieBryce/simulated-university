# Storylines

OUT OF WORLD. Never shipped.

Nine threads that run across the estate. Each one leaves traces in several sites; none is announced inside the Hub. The explorer's hints overlay can point at them. Dates are in-world; the snapshot is **14 April 1053**, in academic year 1052-53.

Tags used in source front-matter: `awarding-gap`, `placements`, `revalidation`, `ai-policy`, `incident`, `stoneshare`, `nss-dip`, `admissions`, `rebrand`.

---

## 1. The awarding gap reaches Council  (`awarding-gap`)

**Summary.** The Elf to Dwarf good honours gap in Health and Education is the dataset's own headline. Council's Chair saw a line about it in the annual report and asked for "a short paper" for May. The Dean wants it to make the Faculty look serious. Planning and Insight will not sign off numbers without definitions. The Dean has written his own draft and the numbers in it are wrong.

**Timeline.**
- Oct 1052: Erra starts the Health and Education awarding gap extract; pulled onto the NSS dip; extract left at "Not yet QA'd".
- 21 Feb 1053: Council. Chair asks for a short paper on the gap for 22 May.
- 24 Feb: Dean emails Quorin from his mobile: "Need gap numbers for Council. By programme. Thoughts?"
- 3 Mar: Quorin replies with four caveats and a request for a definition of "gap".
- 19 Mar: FMG (T2) discusses it; decision unclear.
- 2 Apr: Dean dictates a draft; Elowen types it. "Deans thing v3 USE THIS.docx". Figures taken from last year's report and the Faculty figure used where the departmental one was meant.
- 9 Apr: Quorin declines to sign off. Email in Data Requests.
- 14 Apr (snapshot): paper is due in the May Council papers folder; it is not there.

**People.** cyranor-goldmantle, elowen-fogwhisper, quorin-deepmirror, erra-measurine, teylin-leafchant, aerion-crownweaver, thalira-everjudged.

**Where the traces are.**
- governance / Council / 1052-53 / 1053-02-21: minutes with the Chair's request; Chair's covering note.
- governance / Council / 1052-53 / 1053-05-22: empty "Papers" folder with a placeholder agenda listing the paper.
- faculty / Deans Office / Council and Senate / Awarding Gap Paper: three Elowen-named drafts; figures templated from `values.yaml` with the *wrong* keys deliberately (see Ground truth).
- planning / Data Requests: the Dean's request, Quorin's reply, Quorin's decline.
- planning / Working / Awarding gap: Erra's half-finished extract and notes.
- planning / Reports / 1051-52: last year's awarding gap report (the source of the Dean's stale figures).
- planning / Data Extracts: the generated tables a learner can do the analysis from.

**Ground truth for the wrong numbers.** The Dean's draft uses `he_good_degree_gap_1051` where `he_good_degree_gap_1052` is meant (last year's figure), and quotes `he_good_degree_rate_elf_1052` as the Dwarf rate (the species swapped). A learner who does the analysis from the extracts should be able to catch both. Note for authors: in the current dataset the Faculty's graduates all come from Somatic Wellbeing Enquiry, so programme-level comparisons are thin; keep in-world claims at Faculty level. Both keys come from `scripts/make_hub_extracts.py`, so a reseed keeps them wrong in the right way.

**Skills.** 2 (do the analysis), 6 (write the short paper), 8 (check the Dean's draft).

**Hint text.** "Council have asked for a short paper on the awarding gap for 22 May. The Dean's Office has a draft and Planning will not sign it off. The figures to check it against are in Data Extracts."

---

## 2. Placements on one spreadsheet  (`placements`)

**Summary.** Nursing and Care placements for 180 students a year run on a 14-tab workbook maintained by Halden, who goes on extended leave on 19 May 1053. Dagna has asked for it to be fixed since January. Digital Services declined a project request in 1051 for lack of a business case. Everything a learner needs to scope a small system is lying about in pieces.

**Timeline.**
- Jun 1051: Halden submits a Digital Services project request: "a placements database". Aug 1051: Fenn declines it: insufficient business case, no process documentation, resubmit via the intake process.
- Nov 1052: Firestride placement incident (see Storyline 6) exposes that nobody but Halden knows which students are where.
- Jan 1053: Dagna raises it at every PST meeting.
- Feb 1053: Halden's leave confirmed. Asked to "write it all down".
- 27 Mar: Handover planning meeting (T1). Actions: Halden to document the process (third attempt), Hesta to consolidate the FINAL files, Liora to list what providers need from us.
- 14 Apr (snapshot): process note is two pages and stops at tab 6. Seven files called FINAL.

**People.** halden-bridgeglen, hesta-gracestone, liora-lanternwake, dagna-chiselhand, fenn-gridforge, brekka-anvildancer.

**Where the traces are.**
- pst / Placements / Allocation: the workbook and its FINAL lineage.
- pst / Placements / Process: Halden's note, flowchart, unfinished handover.
- pst / Placements / Digital Services request: the 1051 request, the decline, the blank form, a business case template.
- pst / Programme Administration / Meetings: T1 and Hesta's minutes; earlier meeting notes with Dagna's complaints.
- pst / Provider Correspondence: what providers actually require (the real requirements).
- faculty / StoneShare Migration / Faculty Shared / Hesta stuff / Placements: Hesta's own process documents, better than Halden's, that nobody knows about.
- comms / Requests / Open: Dagna's "a poster about placements".

**Skills.** 3 (scope the app), 7 (extract provider requirements), 9 (which FINAL is current), 1 (T1).

**Hint text.** "Placements for Nursing and Care run on a spreadsheet that one person understands, and he goes on leave in May. If you wanted to build something better, the requirements are already here, in the complaints, the provider letters and a form Digital Services turned down two years ago."

---

## 3. The Occupational Therapy revalidation  (`revalidation`)

**Summary.** OT is up for periodic revalidation. Caerel has produced a 71-page self-evaluation document. The panel met on 12 March with an external, Marenel, who has made the same recommendation for three years. A reserved item concerned a named member of staff and must not appear in the open minutes.

**Timeline.**
- 1050, 1051, 1052: Marenel's external examiner reports each recommend reducing the assessment load in Year 2. Programme responses each say "noted; under review".
- Dec 1052: SED v1. Jan 1053: SED v2 (Brynja's comments). Feb 1053: SED v3 FINAL, 71 pages.
- 12 Mar 1053: Panel (T4). Conditions: reduce Year 2 assessment load; produce a student-facing EC guide. Reserved item: Marenel's concern about marking consistency by one named lecturer.
- 26 Mar: Ollir's open minutes and reserved minutes circulated.
- 14 Apr (snapshot): the programme's response to conditions is due 30 April; a draft exists in Caerel's folder.

**People.** caerel-candletome, brynja-cragshield, ollir-greenquill, marenel-boughwitness, hrogar-dourstone, anric-hearthbind, student-enia-chalkhaven.

**Where the traces are.**
- quality / Programme Revalidation / Occupational Therapy 1053: SED versions, panel papers, T4, open minutes, panel report.
- quality / Programme Revalidation / ... / Reserved: reserved minutes, Confidential.
- quality / Working / Ollir: his drafts, and a copy of the reserved minutes with no label (classification.yaml P07).
- quality / External Examiners: Marenel's three reports and three identical responses.
- quality / Academic Regulations / Guidance: Caerel's draft EC guide, which uses Enia's case by name and has inherited the folder's Public label (P09). The skill 10 target is to write the guide properly.
- faculty / Department of Health / Fitness to Practise / Panel Papers: Firestride case summary labelled Internal (P10).
- planning / Working / Teylin: auto-generated summary of Marenel's reports with planted errors (E03).
- faculty / Department of Health / Programme Documents / Occupational Therapy: SED copies.
- wellbeing / Support Plans: Enia's DSA letter (the EC claim mentioned at panel).

**Skills.** 1 (T4 with a reserved item), 5 (the reserved minutes copy), 6 (brief the Dean on 71 pages), 9 (SED versions), 10 (write the EC guide).

**Hint text.** "The Occupational Therapy revalidation left behind a 71-page self-evaluation, a transcript of the panel, and the minutes the clerk wrote up afterwards, including a reserved item that must not appear in the open version. The panel also asked for student guidance on extenuating circumstances, which nobody has written yet."

---

## 4. The AI policy nobody has caught up with  (`ai-policy`)

**Summary.** The AI Acceptable Use Policy was debated at Senate on 4 December 1052, approved on 5 February 1053, and is not yet understood. Hrogar dissented. Gudrik distrusts it. Bruk has already broken it. Most of the estate pre-dates it.

**Timeline.**
- Sep 1052: Elenna and Fenn draft the policy. Two drafts in circulation.
- 4 Dec 1052: Senate (T3). Hrogar: "we are legitimising a thing we do not understand". Elenna: "colleagues are already using it; the policy is how we make that safe." Referred back for a technical annex.
- 5 Feb 1053: Senate approves with annex. Gudrik's minutes record a dissent.
- 12 Feb: All-staff email. Decision tree published.
- Mar 1053: Bruk pastes an applicant's personal statement into a non-approved tool; asks Elenna afterwards whether that was all right. Logged in Advice Given.
- Apr 1053: Liora is the only person in PST who has read it. Asks "is there a process for" using the approved tool on provider letters.

**People.** elenna-dewscroll, fenn-gridforge, thalira-everjudged, gudrik-bannerstone, hrogar-dourstone, bruk-coaljaw, liora-lanternwake.

**Where the traces are.**
- governance / Policies and Procedures / Current / Digital: the policy, annex, decision tree, approved tools list.
- governance / Policies and Procedures / Superseded: two drafts that should not be there (skill 9).
- governance / Senate / 1052-12-04: T3, Gudrik's minutes, the paper, Hrogar's dissenting note.
- governance / Information Governance / Advice Given: Bruk's question and Elenna's answer.
- admissions / Cycle 1053 Entry / Tracker: Nelka Cobblecloak's row (the statement he pasted).
- pst / Programme Administration / Meetings: Liora's question in the notes.

**Skills.** 5 (the ruleset), 1 and 8 (T3 against minutes), 9 (three policy drafts).

**Hint text.** "The AI policy was approved in February and most people have not read it. It is in Governance. Once you have, you will start noticing who has already fallen foul of it."

---

## 5. The February incident  (`incident`)

**Summary.** On 19 February 1053 Caelio attached Grinna Dustshard's full support plan, instead of the one-page adjustments summary, to an email to the whole Nursing and Care Year 2 teaching team. He reported it within the hour. The incident was logged, reviewed and closed. The closure checklist says the file was removed from the teaching folder. It was not.

**Timeline.**
- 19 Feb 1053, 09:41: email sent to NC-Y2-Teaching list (14 staff). 10:30: Caelio self-reports to Elenna.
- 19 Feb, 14:00: Elenna's email to recipients: delete, confirm, do not forward.
- 20 Feb: Velra's email to the Dean. Short sentences.
- 26 Feb: Review meeting (T5). Actions: revise the sharing procedure; remove the file from the teaching folder; brief all advisers.
- 7 Mar: INC-0031 closed. Checklist ticked.
- 14 Apr (snapshot): "Grinna Dustshard support plan.docx" still in faculty / Teaching Nursing and Care / Year 2 / Staff only, labelled Internal.

**People.** caelio-driftfeather, velra-cinderwake, elenna-dewscroll, anric-hearthbind, cyranor-goldmantle, dagna-chiselhand, student-grinna-dustshard.

**Where the traces are.**
- wellbeing / Incident February 1053: self-report, Velra's email, T5, Velra's note, checklist, revised procedure draft.
- governance / Information Governance / Incident Log / 1053-02 INC-0031: report form, emails, closure note.
- wellbeing / Support Plans / 1052-53 / Health: the plan, correctly Confidential.
- faculty / Teaching Nursing and Care / Year 2 / Staff only: the leaked copy, Internal (classification.yaml P01), beside the correct one-page summary.
- wellbeing / Procedures and Guidance / Staff guidance: the sharing procedure the incident broke.

**Skills.** 5 (find the file an AI must not touch; check whether it touched it), 1 (T5), 10 (draft Velra's email better, or Caelio's apology).

**Hint text.** "An incident was closed on 7 March with 'file removed' ticked on the checklist. Start in the Incident folder and follow it to where the file actually is."

---

## 6. The StoneShare migration  (`stoneshare`)

**Summary.** The Faculty's old network drive, StoneShare, was full. Brekka asked for it to be migrated. Over the weekend of 8 and 9 November 1052 Digital Services copied everything into one library with no curation. Nothing is labelled. It contains a CV, photos, an unlabelled Fitness to Practise file, eight-deep folders, and Hesta's folder, which is the best-organised thing in the Faculty.

**Timeline.**
- Sep 1052: Brekka's request. Oct 1052: Fenn's one-line confirmation: "lift and shift, no cleanse, as requested".
- 8 and 9 Nov 1052: migration.
- Nov 1052: Brekka's "StoneShare Migration: next steps" note (1. 2. 3.). Nobody does them.
- Jan 1053: Liora makes a colour-coded index of what is in it and saves it in To sort.
- 14 Apr (snapshot): untouched otherwise.

**People.** brekka-anvildancer, fenn-gridforge, hesta-gracestone, liora-lanternwake, nyssa-memoryvault, hrogar-dourstone, student-kaelen-firestride.

**Where the traces are.**
- faculty / StoneShare Migration: all of it. See sites.yaml for the skeleton and mess_rules.yaml for what is applied.
- faculty / Deans Office / Faculty Management Group: Brekka's next-steps note as an FMG paper.
- governance / Policies and Procedures: the naming convention and retention schedule the learner uses as rules.
- faculty / StoneShare Migration / Faculty Shared / To sort: Liora's index (the starting point, itself misplaced).
- faculty / StoneShare Migration / Health / FtP: Firestride case notes, no label (classification.yaml P03).
- faculty / StoneShare Migration / Personal / CV: a CV (P05).

**Skills.** 4 (the exercise), 5 (what is in there that should not be), 9 (duplicates and versions).

**Hint text.** "This library is the old network drive, copied across in one go and never sorted. The naming convention and retention schedule in Governance tell you what it should look like. Somewhere in here are at least three things that should not be on a shared drive at all."

---

## 7. The NSS dip  (`nss-dip`)

**Summary.** NSS 1052 results (published in-world August 1052; academic year 1051-52 in the data) showed Assessment and Feedback slipping across the Faculty, with Occupational Therapy and Somatic Wellbeing Enquiry falling most. The Dean asked both departments for action plans. The Department of Education has no finalists (its programmes are two years) and therefore no NSS results of its own, which did not stop Saelith taking the Faculty figures personally and producing an action plan at midnight, five times. The action group's transcript mangles every name. Teylin's auto-generated summary of the NSS pack has errors. A focus-group participant disclosed more than he meant to and the referral note exists in two places with different labels.

**Timeline.**
- Aug 1052: results. Faculty Assessment and Feedback down (`values.yaml`: `he_nss_assessment_feedback_1052` and `_1051`; `ot_nss_overall_1052` and `_1051`; `swe_nss_overall_1052` and `_1051`).
- Oct 1052: Erra's deep dive (Reports). Action group (T6). Teylin's "Summary (auto-generated)" of the pack.
- Oct to Dec 1052: action plan v1 to v5, unmarked.
- Nov 1052: focus groups; Tivan Reefgrace's disclosure; referral to Wellbeing.
- 14 Apr (snapshot): action plan "final" dated Dec; progress unknown.

**People.** saelith-emberthorn, jaskel-doodlehook, teylin-leafchant, erra-measurine, student-tivan-reefgrace, caelio-driftfeather.

**Where the traces are.**
- faculty / Department of Education / NSS Response: action plan versions, T6, focus group notes including the unlabelled referral copy (P04).
- planning / Reports / 1052-53: Erra's deep dive, properly done.
- planning / Working / NSS: Teylin's auto-generated summary with planted errors (planted_errors.yaml E01).
- planning / Data Extracts: NSS by department.
- wellbeing / Case Notes / Open: Tivan's referral, Confidential.

**Skills.** 1 (T6), 2 (the NSS data: which programmes actually fell, and does Education have any results at all), 8 (Teylin's summary), 9 (five action plans).

**Hint text.** "When Education's satisfaction scores dropped, the department wrote its action plan five times, and someone had a tool summarise the results pack without reading the output. The deep dive in Planning's Reports library is the version to trust."

---

## 8. The Admissions conversion scare  (`admissions`)

**Summary.** For 1053 entry, offers are up and firm acceptances are down. Mira has three explanations (the open day date, the Faculty's slow interview turnaround, competitor bursaries) and has written each one up for a different audience. Quorin wants definitions. Bruk's applicant tracker holds date of birth, home address and health declarations and is labelled Internal; he pasted a personal statement into a non-approved tool.

**Timeline.**
- Oct 1052: open day moved to a clash with a rival's. Jan 1053: interview turnaround slips to 19 days. Feb 1053: competitor announces bursaries.
- 5 Mar 1053: huddle (T7). 
- Mar 1053: three papers. Request to Planning for conversion by clan; Quorin's careful reply about small numbers.
- 14 Apr (snapshot): June open day planning under way; banner request to Comms uses the old name.

**People.** mira-dealroot, bruk-coaljaw, quorin-deepmirror, javin-brickrelay, student-nelka-cobblecloak.

**Where the traces are.**
- admissions / Cycle 1053 Entry: tracker (P08), offer-making minutes, three conversion papers, T7, Mira's email note of it.
- admissions / Reports: weekly dashboard exports; request to Planning and reply.
- admissions / Open Days: June plan; Jaskel's deck.
- comms / Requests / Open: banner request with old name.
- governance / Information Governance / Advice Given: Bruk's question.

**Skills.** 2 (is any of the three explanations supported?), 5 (the tracker), 10 (applicant comms), 1 (T7).

**Hint text.** "Admissions have three different explanations for why acceptances are down, each written for a different reader. They also keep an applicant tracker with columns nobody should have added."

---

## 9. The rebrand that didn't take  (`rebrand`)

**Summary.** In September 1051 the institution rebranded from "Stonegrove College of the Vale" to "Stonegrove University" with a new guide, logo and palette. Eighteen months on, the Department of Health still uses "Department of Healing Arts" on old letterhead, Jaskel has his pencil tree, two corporate templates carry the old footer, Admissions templates use the old name, and Javin's social posts drift. Sorell logs every sighting. Rhialla is quietly losing.

**Timeline.**
- Sep 1051: launch. Rhialla's "one voice" email.
- 1051 to 1053: Sorell's Brand Compliance Log grows to 60 rows.
- Mar 1053: Hrogar's second request for Healing Arts letterhead, declined.
- Apr 1053: Rhialla's "lessons learned" from the rebrand, filed in Archive, unread.

**People.** rhialla-moondrift, sorell-inkthread, javin-brickrelay, hrogar-dourstone, jaskel-doodlehook, mira-dealroot.

**Where the traces are.**
- comms / Brand: the guide, assets, Compliance Log.
- comms / Requests: Hrogar's declined requests, Jaskel's "make this look nice".
- comms / Archive: old brand, rebrand project, lessons learned.
- Off-brand files across sites: see off_brand.yaml.

**Skills.** 11 (follow the guide; fix the off-brand files), 10 (Rhialla's gentle reminder, again).

**Hint text.** "There is a brand guide, and there is a spreadsheet of everyone who has ignored it since 1051. Give an AI the guide and ask it to do better than the people did."

---

## Cross-references

| Storyline | Sites touched | Transcripts | Planted sensitive items | Planted errors | Off-brand |
|---|---|---|---|---|---|
| awarding-gap | governance, faculty, planning | T2 | | E02, E04 | B08 |
| placements | pst, faculty, comms | T1 | | | |
| revalidation | quality, faculty, wellbeing, planning | T4 | P06, P07, P09, P10 | E03 | |
| ai-policy | governance, admissions, pst | T3 | P08 | | |
| incident | wellbeing, governance, faculty | T5 | P01, P02 | | |
| stoneshare | faculty, governance | | P03, P05, P11 | | B05 |
| nss-dip | faculty, planning, wellbeing | T6 | P04 | E01 | B02, B03 |
| admissions | admissions, planning, comms | T7 | P08 | | B06, B09 |
| rebrand | comms, faculty, governance, admissions | | | | B01 to B09 |
