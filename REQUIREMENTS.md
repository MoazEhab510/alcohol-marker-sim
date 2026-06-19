# Project Requirements — Alcohol Marker Production Line Simulator

> **SRH Advanced Programming · Applied Mechatronics**
> Sources: the assignment PDF (`AdvancedProgramming_Project.pdf`) and the course
> site <https://advancedprogrammingsrh.github.io/>.
> **The PDF is the binding spec (what is graded). The course site is reference
> material** — the lecture uses a *ballpen + matplotlib* example; we are free to
> choose our own product (alcohol marker) and our own HMI (HTML), which we did.

## ⏰ Submission deadline
**June 20th, via email.** Subject line **and** PDF title: `StudentID_Lastname_AP`.
Email must contain:
1. The PDF document (use the **Project_Template**, ~7–10 pages).
2. A link to the **live website** hosting + describing the project (e.g. GitHub Pages).

Grade weighting (from the Module page): **70% project + 30% theory exam.**
The project itself is scored out of 100 across Tasks 1–4 below.

---

## Task 1 — Introduction (10 pts) · *documentation*
- [ ] Describe the **product**: alcohol marker = **tip → alcohol/ink fill → body → cap** (≥4 components).
- [ ] Describe the **production-line concept** (the 4 stages and what each does).
- [ ] Reuse the stage table + FSM diagram already in `README.md`.

## Task 2 — Program the production line (60 pts) · *code (mostly done)*
| Requirement | Status | Where |
|---|---|---|
| **Backend** — logic in Python; clearly marks a product **defective and why** | ✅ Done | `backend/main.py` (`run_stage`, fault reasons) |
| **Frontend / HMI** — **Start, Stop, Reset** buttons; show production state; display errors when faulted | ✅ Done | `frontend/index.html` |
| **Database** — InfluxDB | ✅ Done & fixed | bucket `markers`, measurement `production` |
| **Dashboard** — Grafana, send **≥1 parameter** and display it | ✅ Done | `grafana/provisioning/...` (state, parts, temperature, ethanol) |

- [x] **InfluxDB write bug fixed** — `PYTHONUNBUFFERED` + `logging`, and
  `WritePrecision.SECONDS` → `WritePrecision.S`. Verified: data lands in bucket `markers`.
- [ ] **Verify Grafana visually** — log in at <http://localhost:3000>, confirm panels populate
  (if `admin/admin` fails, run `docker compose down -v` to reset the volume).
- [ ] Capture screenshots of the HMI and Grafana for the docs/website.

**Optional modules** (the PDF lists these as optional; the lecture explains them —
good material to *mention* in the documentation even if not coded). *We chose to keep
the build minimal, so these are not implemented:*
- Quality Control (vision/AI defect detection)
- CMMS (maintenance management)
- SCADA
- Related lecture concepts worth citing: **SEMI E10 states**, **OEE = Availability × Performance × Quality**, **MES / ISA-95 levels**.

## Task 3 — Tools, version control & website (20 pts) · *infra + documentation*
- [x] **Git** repository initialised locally (`git init`, `.gitignore`, commits).
- [ ] **GitHub** — push to a remote repo (single repo for the whole project).
- [ ] **GitHub Pages** website — describe the project, **1–2 images**, **max 4 paragraphs**, link to repo.
      Scaffold ready at `docs/index.html` (replace the repo-URL placeholder, add screenshots).
- [ ] In the PDF, explain how you used: **Git/GitHub** (version control), **Docker / Docker Compose**, and **AI tools**.
- [ ] **Mandatory AI appendix** — include your most relevant prompts, the AI output, and the
      corrections you made (e.g. the InfluxDB buffering + `WritePrecision` fix). Discuss the benefits of the AI tool.

## Task 4 — Conclusion (10 pts) · *documentation*
- [ ] Discuss the solution: **weaknesses** (in-memory state, single line, no auth/persistence of counters),
      **what you like**, **where further development is needed** (real QC/CMMS/SCADA, multi-line, OEE).
- [ ] Consider **operation** of such a solution and the **requirements** that come into play
      (uptime, data retention, security, maintenance).

---

## Technology stack (as built)
| Tech | Port | Version | Role |
|---|---|---|---|
| Python / Flask | 5000 | 3.11 / Flask 3.0 | Backend FSM + REST API |
| HTML HMI | — | — | Operator panel (`frontend/index.html`) |
| InfluxDB | 8086 | 2.7 | Time-series DB (org `srh`, bucket `markers`) |
| Grafana | 3000 | 10.4 | Dashboards (auto-provisioned) |
| Docker Compose | — | — | Orchestrates all services |

## REST API
| Method | Endpoint | Description |
|---|---|---|
| GET | `/status` | Full machine state as JSON |
| POST | `/start` | IDLE → RUNNING |
| POST | `/stop` | RUNNING → IDLE |
| POST | `/reset` | FAULTED → IDLE (clears counters) |

## Parameters sent to InfluxDB / Grafana
`fsm_state`, `stage`, `parts_produced`, `parts_defective`, `temperature_c`,
`ethanol_pct`, `cycle_time_s` — measurement `production`, tag `machine=alcohol-marker-line-1`.

---

## Remaining checklist (in priority order for the deadline)
1. [ ] Push the single repo to GitHub + enable Pages (`main` / `docs`).
2. [ ] Replace repo URL placeholder in `docs/index.html`; add `docs/img/hmi.png` + `docs/img/grafana.png`.
3. [ ] Visually confirm Grafana shows live data; take the two screenshots.
4. [ ] Write the documentation PDF (Tasks 1–4 + AI appendix), titled `StudentID_Lastname_AP`.
5. [ ] Email the PDF + website link before the June 20th deadline.
