---
title: HE awarding gap extract WORKING
format: xlsx
author: erra-measurine
created: 1052-10-03
modified: 1052-10-11
label: null
sensitive: false
site: planning
library: pi-working
path: Awarding gap
storylines: [awarding-gap]
skills: [2, 9]
---

```sheet:README
Note
NOT YET QA'd. Working extract for PI-1052-039 (Faculty awarding gap by programme for Council). Started 1052-10-03. Paused 1052-10-11 for NSS deep dive.
Source: good honours extract 1052-10-03. Graduating years 1049 to 1052.
Programme sheet is incomplete: suppression not yet applied. Do not circulate.
E.M.
```

```sheet:Faculty
Graduating year,Graduates,Elf good honours pct,Dwarf good honours pct,Gap pp,QA
1049,{{ he_graduates_1049 }},{{ he_good_degree_rate_elf_1049 }},{{ he_good_degree_rate_dwarf_1049 }},{{ he_good_degree_gap_1049 }},ok
1050,{{ he_graduates_1050 }},{{ he_good_degree_rate_elf_1050 }},{{ he_good_degree_rate_dwarf_1050 }},{{ he_good_degree_gap_1050 }},ok
1051,{{ he_graduates_1051 }},{{ he_good_degree_rate_elf_1051 }},{{ he_good_degree_rate_dwarf_1051 }},{{ he_good_degree_gap_1051 }},ok
1052,{{ he_graduates_1052 }},{{ he_good_degree_rate_elf_1052 }},{{ he_good_degree_rate_dwarf_1052 }},{{ he_good_degree_gap_1052 }},check vs annual report
```

```sheet:Programme
Programme,Graduates 1052,Elf pct,Dwarf pct,Gap,Suppress?,Note
Somatic Wellbeing Enquiry,,,,,,see he_good_honours_by_programme_species_5yr.csv
Occupational Therapy,,,,,,no graduates in extract?? check with Quality
Pharmacy,,,,,,no graduates in extract?? check
Physiotherapy,,,,,,no graduates in extract?? check
Social Work,,,,,,no graduates in extract?? check
Nursing and Care,0,,,,Y,two-year programme
Midwifery,0,,,,Y,two-year programme
Education Studies,0,,,,Y,two-year programme
```

```sheet:Todo
Item,Done
Apply suppression rule (n lt 20),
Check why only SWE has graduates in the extract. Record system issue or genuine?,
Reconcile 1052 faculty figure with annual report draft,
Add SES and prior education breakdown,
Send to Quorin,
```
