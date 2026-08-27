# ROADMAP — Port Berth Planning Application

This file holds the implementation plan: how the work was split into steps, the order of
those steps and their dependencies, and the scope of each one (what is included and what
is deliberately left out). Whenever development departed from the plan, a "what changed /
why" entry was added to the **Change Log** at the bottom.

---

## 1. Overview

A full-stack web application that **automatically** produces a berthing plan for a port's
operations team: it assigns incoming ships to berths under a set of rules while reasonably
reducing total waiting time.

**Technology and architecture decisions (summary):**

- **Frontend:** Next.js (App Router). Data-heavy screens such as listings are Server
  Components; forms and interactive visualisation are Client Components.
- **Backend:** FastAPI with a layered architecture — **Controller → Service → Repository**.
- **Domain core:** the scheduling algorithm is written as a **pure `planner` module**,
  completely independent of infrastructure (DB / HTTP / framework), so that it stays
  deterministic and unit-testable.
- **Database:** PostgreSQL (managed). Generated plans are **persisted** (retrospective
  review is a requirement), which is why a `Plan` aggregate is used.
- **Deployment:** frontend to Vercel, backend and Postgres to Railway (alternative: Render).

**Core rules the algorithm must respect:**

1. Only one ship may occupy a berth at a time.
2. Ship length ≤ berth length.
3. Ship draft ≤ berth depth.
4. A ship cannot be assigned before its estimated time of arrival (ETA).
5. Consecutive assignments on the same berth are separated by a **manoeuvring buffer**.

**Optimisation objective:** `waiting = start_time − ETA`; the plan is produced so as to
reduce the total waiting of assigned ships. Not optimal — a reasonable and defensible
heuristic is the target.

---

## 2. Phase plan

Phases are listed in dependency order. Each states its scope (in / out), dependencies and
output.

### Phase 0 — Project skeleton and repository setup
- **In:** monorepo layout (`frontend/`, `backend/`), base dependencies, linter/formatter
  (ruff + black, eslint + prettier), `.gitignore`, `.env.example`, an empty README and this
  ROADMAP.
- **Out:** business logic, data model.
- **Depends on:** —
- **Output:** a working empty skeleton; `uvicorn` and `next dev` both start.

### Phase 1 — Data model and migrations (backend)
- **In:** SQLAlchemy models (`Ship`, `Berth`, `Plan`, `Assignment`, `UnassignedEntry`);
  Alembic setup and the first migration; Pydantic schemas (request/response DTOs); reading
  settings from the environment via `pydantic-settings` (`DATABASE_URL`).
- **Out:** endpoints, planning logic.
- **Depends on:** Phase 0
- **Output:** a schema applicable to Postgres with `alembic upgrade head`.

### Phase 2 — Ship and berth CRUD (Repository → Service → Controller)
- **In:** layered CRUD for ships and berths (create, edit, list, delete); input validation
  (rejecting negative lengths and depths, and so on).
- **Out:** planning.
- **Depends on:** Phase 1
- **Output:** working `/api/ships` and `/api/berths` endpoints, testable through Swagger.

### Phase 3 — Planning core (pure `planner` domain module)
- **In:** a greedy algorithm — order ships by ETA; for each ship, among the berths that fit
  physically (length + draft), pick the one where it can **start earliest**
  (`start = max(ETA, end of last job on that berth + buffer)`); if no berth fits, add the
  ship to the unassigned list **with a reason**. The buffer is a **parameter**. Result: an
  in-memory `PlanResult { assignments, unassigned, total_waiting_min }`. Deterministic
  **unit tests**.
- **Out:** any dependency on DB, HTTP or framework — this module imports none of them.
- **Depends on:** only the plain domain types from Phase 1; being infrastructure-free, it
  can in fact be written in parallel with Phase 2.
- **Output:** a tested, isolated, pure planner.

### Phase 4 — Plan generation and persistence service and endpoints
- **In:** `SchedulingService` — loads ships and berths from the repositories, calls the pure
  planner and **persists** the result as a `Plan` (plus `Assignment` and `UnassignedEntry`).
  Endpoints: `POST /api/plans` (generate + persist), `GET /api/plans` (history),
  `GET /api/plans/{id}`.
- **Out:** advanced optimisation, manual editing.
- **Depends on:** Phase 2 + Phase 3
- **Output:** end-to-end, persisted plan generation.

### Phase 5 — Frontend: data management screens
- **In:** `/ships` and `/berths` pages; listings as Server Components, create/edit forms as
  Client Components; backend API integration.
- **Out:** visualisation.
- **Depends on:** Phase 2
- **Output:** ship and berth data manageable from the UI.

### Phase 6 — Frontend: plan visualisation (the main experience)
- **In:** the `/plan` page; a "Generate plan" action; a **Gantt / timeline** visualisation
  (rows = berths, horizontal axis = time, bars = assignments, gaps = buffer); an
  **unassigned ships panel** with a reason for each; viewing plan history.
- **Out:** drag-and-drop manual editing.
- **Depends on:** Phase 4 + Phase 5
- **Output:** the main screen an operations employee will use.

### Phase 7 — Sample data (seed)
- **In:** a seed script producing a realistic set of ships and berths, including
  **deliberately unassignable** examples (ships longer or deeper than any berth) so the
  "unassigned + reason" flow is visible in a demo.
- **Out:** —
- **Depends on:** Phase 1
- **Output:** demo-ready data in a single command.

### Phase 8 — Deployment
- **In:** frontend to Vercel; backend and Postgres to Railway. Configuration: the Vercel
  domain in FastAPI's `CORSMiddleware`; the `NEXT_PUBLIC_API_URL` (frontend) and
  `DATABASE_URL` (backend) environment variables; `alembic upgrade head` on release.
- **Out:** a CI/CD pipeline, scaling.
- **Depends on:** Phase 4 (and preferably Phase 6)
- **Output:** a live, reachable application link.

### Phase 9 — Documentation and presentation
- **In:** README (setup, project structure, **Problem approach**, **AI process note**); a
  short presentation.
- **Depends on:** all phases.
- **Output:** a deliverable package.

---

## 3. Dependency summary

```
Phase 0
  +- Phase 1
       +- Phase 2 ---------------+
       +- Phase 3 (parallel) ----+
       |                         +- Phase 4 --+
       +- Phase 7 (seed)                      |
       |                                      +- Phase 6 - Phase 8 - Phase 9
       +- Phase 5 ---------------------------+
```

Critical path: **0 → 1 → 2/3 → 4 → 6 → 8 → 9**. Phases 3 and 5 can proceed in parallel
alongside the critical path.

---

## 4. Schedule (2 days)

- **Day 1:** phases 0–4 (backend working end to end) plus phase 7 (seed).
- **Day 2:** phases 5–6 (frontend) → phase 8 (deployment) → phase 9 (documentation and
  presentation).

Under time pressure the priority is: a working backend, the algorithm, and basic
visualisation. Visual polish (colours, animation) is the last thing, only if time allows.

---

## 5. Deliberately out of scope

- **Authentication / authorisation** — not requested in the brief.
- **An optimal solution (ILP, OR-Tools and similar)** — a greedy heuristic is sufficient;
  the rationale is explained in the README's "Problem approach" section.
- **Real-time updates / WebSockets.**
- **Manual drag-and-drop plan editing** — a worthwhile nice-to-have, only if time allows.
- **Multiple ports / role management.**

---

## 6. Assumptions

- Times are stored in UTC; handling time and the manoeuvring buffer are in **minutes**.
- The **manoeuvring buffer** is taken as a fixed **60 minutes**. Rationale: the buffer
  represents one **unberthing plus one berthing** manoeuvre between consecutive ships on the
  same berth; since a single tug-assisted manoeuvre is on the order of 30 minutes, roughly
  30 + 30 makes 60 a reasonable floor. `handling_time` is the time a ship occupies the berth
  for cargo work; manoeuvres sit outside it, in the buffer. The value is kept as a
  **parameter rather than a constant**: the point is to make the safety versus
  berth-utilisation trade-off adjustable through one setting. It could later become a
  function of vessel size (LOA) or tonnage (GT).
- A ship becomes unassignable only for **physical** reasons (no berth long or deep enough);
  a time constraint never makes a ship unassignable, it only delays its start.
- Each plan run works on a snapshot of all ship and berth data at that moment.

---

## 7. Change Log

Departures from the plan are recorded here as they happen. Format:

- `YYYY-MM-DD` — **What changed:** … — **Why:** …

- `2026-08-27` — **What changed:** the seed script now offers two scenarios, selected with
  a flag: `python -m app.seed` loads a light day (11 ships) and `python -m app.seed --busy`
  a congested one (27 ships). Both share the same quay and the same three unassignable
  ships. — **Why:** the measurements showed that the choice of scheduling rule is invisible
  below roughly one unit of load, and the original seed sat exactly there: six berths
  absorbed eight ships with almost no queuing, so the timeline never showed the buffer
  costing berth time or the priority rule doing anything. The busy scenario runs the quay at
  roughly 85-90% utilisation, uses all six berths including the long-shallow and
  short-deep ones, and makes the waiting lanes and buffer gaps legible.


- `2026-08-27` — **What changed:** an upper bound was added to the manoeuvring buffer
  (`le=1440`, i.e. 24 hours) and the frontend input was aligned with the backend
  (`min="1" max="1440"`; it was previously `min="0"`, and entering 0 made the backend
  return 422).

- `2026-08-27` — **What changed:** of the four tools promised in phase 0, only **ruff**
  (the Python linter) was added; black, eslint and prettier were not. Phase 0 was also never
  run as a separate step, being folded into phase 1. — **Why:** both departures were noticed
  during the pre-submission review, having been promised in the ROADMAP but never carried
  out.

  **ruff:** measured before deciding to adopt it. With the default rules it reported 30
  findings; on inspection 17 were B008 false positives triggered by FastAPI's Depends(),
  and 9 concerned SQLAlchemy's Mapped["Ship"] form (the quotes are **required**, since those
  classes are imported only under TYPE_CHECKING; applying UP037's suggested fix breaks
  mapper configuration). That left 4 genuine findings: two missing "raise ... from None"
  clauses and two ambiguous variable names. All four were fixed, a `ruff.toml` was written
  (silencing the false positives with stated reasons) and `ruff check` now passes clean.

  **eslint:** installation was attempted but the project lives under OneDrive, which held
  file locks on `node_modules` (ENOTEMPTY) and the install never completed. That is an
  environment problem rather than a code problem. Rather than commit a configuration that
  could not be verified, the partial install was reverted. Note that `next build` already
  type-checks the frontend and compiles cleanly, so the frontend is not unchecked.

  **black / prettier:** deliberately left out of scope. Adding a formatter immediately
  before submission would reformat the entire codebase and produce a large, meaningless
  diff to review. A linter, which finds errors, is valuable at this stage; a formatter,
  which enforces style, is not.

- `2026-08-27` — **What changed:** the SQLite foreign-key PRAGMA branch was removed from
  `core/database.py`. — **Why:** the project uses SQLite in no environment at all:
  PostgreSQL in Docker for development, no database whatsoever in the tests (the planner is
  pure, so the unit tests need none), and Railway PostgreSQL in production. The code was
  marked `# pragma: no cover`, its own admission that it never runs. Carrying defensive code
  for an unused database left readers with the impression that SQLite was supported.

- `2026-08-27` — **What changed:** the planner's priority rule was switched from FCFS
  (arrival order) to **HRRN** (Highest Response Ratio Next), and `plan()` became a
  **dispatch** loop that decides at every step instead of a sort-then-place loop. —
  **Why:** the ordering decision carried no justification in the ROADMAP, so it was measured
  before submission. For each configuration 20 random datasets were generated and compared
  (load = handling demand divided by berths times arrival window):

  | Rule | Total waiting gain | Worst-case waiting cost | Parameter |
  |---|---:|---:|---|
  | SPT (no aging) | +16.5% | +9 to +70% | none |
  | Aging a=0.25 | +12% | +0.6 to +1.4% | a |
  | Aging a=0.5 | +7 to 8% | -1.4 to -1.9% | a |
  | **HRRN** | **+12 to 14%** | **+2.6 to +9.5%** | **none** |

  Findings: (1) at low load, for example 6 berths and 8 ships where our seed data sits,
  there is no measurable difference between the rules; (2) plain SPT reduces total waiting
  but starves long ships; (3) aging removes most of that cost. HRRN was chosen because it
  delivers aging's benefit **without a constant to tune**: the value of `a` that preserves
  fairness shifts between 0.25 and 0.5 depending on the load regime and has no physical
  meaning, and there is already one constant requiring justification (the 60-minute buffer)
  so a second was not wanted. HRRN normalises the ratio against the ship's own handling
  time, so it adapts to load by itself.

  **Known limitation:** HRRN bounds starvation, it does not eliminate it. Short ships that
  have waited the same amount of time grow their ratio faster and may be served before a
  long one; the +2.6 to +9.5% worst-case cost in the table is the price of that.
  `test_hrrn_rescues_a_long_ship_from_starvation` pins the behaviour, and the same test
  fails under plain SPT.

  **Cost:** the change never left `domain/planner.py` (+47/-18 lines); services, schemas,
  the API and the frontend were untouched. None of the existing 12 tests broke; only
  `test_greedy_orders_by_eta` was renamed to `test_ship_cannot_start_before_its_eta`,
  because its name had become misleading. This is the concrete payoff of the pure domain
  layer decision.

- `2026-08-27` — **What changed:** an `eta` column was added to `Assignment`; an
  assignment's waiting time is now computed from that stored copy rather than from the live
  `Ship.eta`. The waiting rule (waiting = start minus ETA) was reduced to a single source,
  `domain/types.waiting_minutes`, which the ORM model now calls instead of re-implementing.
  — **Why:** during the pre-submission code review it turned out the rule was written
  separately in both the pure domain and `models/assignment.py`, and that the ORM version
  read the live ship record. As a result, editing a ship's ETA after a plan had been
  generated made the stored `Plan.total_waiting_min` contradict the per-row waiting values.
  Since `Plan` was already designed as a record of the moment it was generated, and
  `buffer_min` was already copied on the same logic, not copying the ETA contradicted that
  design. The denormalisation was accepted deliberately: at this scale it costs nothing, and
  in exchange historical plans genuinely stop changing. Existing rows were backfilled from
  the ships' ETAs inside the migration.

- `2026-08-26` — **What changed:** a third value was added to the non-assignment reasons,
  `NO_SUITABLE_BERTH`. — **Why:** the initial design had only length and depth reasons.
  However, a ship may find a berth that satisfies its length and *another* that satisfies
  its draft, yet no single berth satisfying both. Reporting that combined case honestly
  required its own reason.

- `2026-08-26` — **What changed:** `DATABASE_URL` normalisation (`postgres://` to
  `postgresql+psycopg://`) and comma-separated `CORS_ORIGINS` support were added to the
  config; the Dockerfile runs `alembic upgrade head` before starting. — **Why:** platforms
  such as Railway hand out the DB URL in `postgres://` form and supply the environment
  themselves, so that deployment works without manual intervention.

- `2026-08-26` — **What changed:** the `UnassignedReason` enum was moved out of `app/models`
  into the pure `app/domain/types`. — **Why:** to keep the planner core independent of
  infrastructure (SQLAlchemy); the model now imports the enum from the domain, giving it a
  single source.
