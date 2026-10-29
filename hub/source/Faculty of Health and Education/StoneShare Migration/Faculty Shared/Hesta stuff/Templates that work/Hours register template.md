---
title: Hours register template
format: xlsx
author: hesta-gracestone
created: 1050-09-10
modified: 1050-09-10
label: null
sensitive: false
site: faculty
library: fac-stoneshare
path: Faculty Shared/Hesta stuff/Templates that work
storylines: [stoneshare, placements]
skills: [4, 3]
---

```sheet:Hours
Student ID,Surname,Forename,Placement,Required hours,Week 1,Week 2,Week 3,Week 4,Week 5,Week 6,Total,Shortfall,Make-up arranged,Confirmed by provider
,,,,225,,,,,,,=SUM(F2:K2),=E2-L2,,
,,,,225,,,,,,,=SUM(F3:K3),=E3-L3,,
,,,,225,,,,,,,=SUM(F4:K4),=E4-L4,,
```

```sheet:Notes
Note
One row per student per placement. Hours from the provider's signed record each week. Shortfall must be zero before the examination board.
Do not add columns. If you need to record something else, that is a different register.
Hesta
```
