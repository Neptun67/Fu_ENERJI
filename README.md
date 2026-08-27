# Port Berth Planning

A full-stack web application that automatically produces a berthing plan: it assigns
incoming ships to berths under a set of physical rules while reducing total waiting time,
for a port's operations team.

| | |
|---|---|
| **Live application** | https://fu-enerji.vercel.app |
| **API / Swagger** | https://fuenerji-production.up.railway.app/docs |
| **Source** | https://github.com/Neptun67/Fu_ENERJI |

Related documents: [ROADMAP.md](ROADMAP.md) (implementation plan and change log),
[DEPLOY.md](DEPLOY.md) (deployment steps).

---

## Contents

- [What it does](#what-it-does)
- [Technology](#technology)
- [Setup](#setup)
- [Project structure](#project-structure)
- [Architecture](#architecture)
- [Planning algorithm](#planning-algorithm)
- [Problem approach](#problem-approach)
- [AI process note](#ai-process-note)
- [Tests and code quality](#tests-and-code-quality)

---

## What it does

- **Ship and berth management** — create, edit, list, delete.
- **Automatic plan generation** — a plan that satisfies all five rules and reduces total
  waiting time.
- **Unassigned ships with reasons** — which physical constraint prevented each ship from
  being placed, shown in its own panel.
- **Timeline visualisation** — rows are berths, the horizontal axis is time, bars are
  assignments, and the gaps between them are the manoeuvring buffer.
- **Plan history** — every generated plan is persisted and can be reviewed later.

### Rules enforced

1. Only one ship may occupy a berth at a time.
2. Ship length must not exceed berth length.
3. Ship draft must not exceed berth depth.
4. A ship cannot be assigned before its ETA (estimated time of arrival).
5. Consecutive assignments on the same berth are separated by a manoeuvring buffer
   (60 min by default; rationale [below](#assumptions)).

---

## Technology

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, layered architecture plus a pure domain core |
| Database | PostgreSQL 16, SQLAlchemy 2.0 ORM, Alembic migrations |
| Deployment | Frontend to Vercel, backend and PostgreSQL to Railway |

---

## Setup

Requirements: **Python 3.11+**, **Node.js 18+**, **Docker** (for a local PostgreSQL).

### 1. PostgreSQL

```bash
docker run --name port-pg -e POSTGRES_USER=port -e POSTGRES_PASSWORD=port -e POSTGRES_DB=port_planning -p 5432:5432 -d postgres:16
```

On later sessions `docker start port-pg` is enough.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.seed
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

On Linux and macOS use `.venv/bin/` instead of `.venv/Scripts/`. The API serves on
`http://localhost:8000` and Swagger on `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

The application opens at `http://localhost:3000`.

### Environment variables

| Where | Variable | Local value |
|---|---|---|
| backend | `DATABASE_URL` | `postgresql+psycopg://port:port@localhost:5432/port_planning` |
| backend | `CORS_ORIGINS` | `http://localhost:3000` |
| frontend | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` |

`DATABASE_URL` is normalised: the `postgres://` form handed out by Railway and Heroku is
mapped to the psycopg v3 driver automatically. `CORS_ORIGINS` accepts a comma-separated
list and strips trailing slashes, because browsers send the `Origin` header without one.

### Sample data

`python -m app.seed` inserts six berths and eleven ships. Three ships are **deliberately
unassignable** so that all three variants of the "unassigned with a reason" flow are
visible in a demo:

| Ship | Problem |
|---|---|
| Titan Max (400 m) | No berth is long enough |
| Deep Diver (21 m draft) | No berth is deep enough |
| Odd Fit (300 m / 18 m) | No *single* berth satisfies both length and depth |

---

## Project structure

```
backend/
  app/
    controllers/     HTTP endpoints (FastAPI routers)
    services/        business logic, transaction boundary
    repositories/    data access (SQLAlchemy)
    models/          ORM models
    schemas/         Pydantic DTOs (request/response)
    domain/          PURE planning core - no infrastructure dependencies
    core/            config, database, exceptions
    seed.py          sample data
  alembic/versions/  migrations
  tests/             planner unit tests
  ruff.toml          linter configuration

frontend/
  app/               App Router pages (Server Components)
    ships/ berths/ plan/
  components/        Client Components and UI pieces
    plan/            gantt-chart, plan-workspace, unassigned-panel
  lib/               api client, types, date helpers
```

---

## Architecture

### Backend: Controller -> Service -> Repository, plus a pure domain

```
HTTP -> Controller -> Service -> Repository -> PostgreSQL
                         |
                         +--> domain/planner.py   (pure, infrastructure-free)
```

- **Controller** deals only with HTTP: routes, status codes, schema validation.
- **Service** owns the business logic and the **transaction boundary** (`commit` happens
  here).
- **Repository** encapsulates data access; it never commits, it only works on the session.
- **Domain** holds the scheduling algorithm and **imports no infrastructure at all** —
  no SQLAlchemy, no FastAPI, no pydantic.

That last claim can be verified:

```bash
cd backend
.venv/Scripts/python -c "import sys; b=set(sys.modules); import app.domain.planner; print([m for m in set(sys.modules)-b if m.split('.')[0] in {'sqlalchemy','fastapi','pydantic','psycopg'}] or 'pure')"
```

The practical payoff: the planner's 13 unit tests run **without a database, in about 0.05
seconds**. It also made changing the algorithm cheap — switching the priority rule from
FCFS to HRRN never left `domain/planner.py`. Services, schemas, the API and the frontend
were untouched, and no test broke.

The dependency direction is one-way: `models` -> `domain` (the `UnassignedReason` enum and
the `waiting_minutes` function live in the domain and the ORM uses them). The reverse is
forbidden.

### Frontend: Server / Client split

- **Server Components** — `app/ships/page.tsx`, `app/berths/page.tsx`, `app/plan/page.tsx`.
  They fetch on the server, handle the error case, and hand the result to a Client
  Component.
- **Client Components** — `ship-manager`, `berth-manager`, `plan-workspace`, `nav`.
  Form state, interaction and plan generation live here.

Pages are marked `dynamic = "force-dynamic"`: this is an operations tool, so serving stale
cached data is not acceptable.

### Data model

```
Ship --+                    +-- Assignment --> Berth
       +--> Plan -----------+
Berth -+                    +-- UnassignedEntry (+ reason)
```

A `Plan` is a **snapshot**: it stores the buffer value used at generation time
(`buffer_min`) and each assignment's ETA at that moment (`Assignment.eta`). Editing a ship
later therefore cannot change a past plan's waiting times. Ships and berths referenced by
a plan cannot be deleted (FK RESTRICT); attempting to do so returns 409.

---

## Planning algorithm

A dispatch loop that, at each step, picks from the ships that could start *right now*
using a **priority rule**:

1. Separate out ships that fit no berth at all, recording the reason.
2. Find the next decision point: the earliest time any remaining ship could start.
3. Among the ships that can start then, choose one via **HRRN**.
4. Place it on the least-wasteful feasible berth (best-fit) and mark that berth busy
   until end + buffer.

**HRRN (Highest Response Ratio Next):** priority = `(waiting + handling) / handling`.

### Why HRRN — the measurement

The ordering rule is the most debatable decision in this problem, so it was chosen by
measurement rather than intuition. For each configuration, 20 random datasets were
generated and averaged:

| Rule | Total waiting gain | Worst-case waiting cost | Constant to tune |
|---|---:|---:|---|
| FCFS (arrival order) | baseline | baseline | none |
| SPT (shortest first) | +16.5% | +9 … +70% | none |
| SPT + aging (a=0.25) | +12% | +0.6 … +1.4% | a |
| SPT + aging (a=0.5) | +7–8% | −1.4 … −1.9% | a |
| **HRRN** | **+12–14%** | **+2.6 … +9.5%** | **none** |

Three findings:

1. **At low load the rule does not matter.** For 6 berths and 8 ships — where our sample
   dataset sits — every rule lands within ±1%. The difference only appears under capacity
   pressure.
2. **Plain SPT causes starvation.** It lowers total waiting but pushes long ships to the
   back; worst-case waiting degrades by up to 70%. The classical SPT result assumes all
   jobs are available at time zero. Here ships have arrival times and waiting is measured
   from the ETA, so the theorem does not apply directly.
3. **Aging removes most of that cost.** Both HRRN and aged SPT keep most of SPT's gain
   while cutting the fairness penalty to a few percent.

HRRN was preferred over aged SPT because it has **no constant to tune**: the value of `a`
that preserves fairness shifts between 0.25 and 0.5 depending on load, it has no physical
meaning, and as a new plan parameter it would have to spread through the API, the database
and the UI. HRRN normalises the ratio against the ship's own handling time, so it adapts
to load on its own.

**Known limitation:** HRRN *bounds* starvation, it does not eliminate it. Short ships that
have waited the same amount of time grow their ratio faster and can still be served first;
the +2.6…+9.5% worst-case cost in the table is exactly that. The behaviour is pinned by
`test_hrrn_rescues_a_long_ship_from_starvation`, which fails under plain SPT.

---

## Problem approach

### How I framed the problem

A constrained resource-scheduling problem (berth allocation): each ship is a *job*, each
berth a *machine*. Jobs have a **release time** (ETA), a **processing time** (handling) and
**compatibility constraints** with the machine (length, draft). Consecutive jobs on the
same machine are separated by a **setup time** (the manoeuvring buffer).

Objective metric: `waiting = start_time − ETA`, and the plan should reduce the **total
waiting across assigned ships**.

The framing stayed constant throughout. The one thing that was refined was the model of
non-assignment: initially there were two reasons (length, draft), until the case of a ship
whose length fits one berth and whose draft fits *another*, but never both on the same
berth, was noticed. That added a third reason, `NO_SUITABLE_BERTH`.

### Assumptions

- Times are stored in **UTC**; handling time and the manoeuvring buffer are in **minutes**.
- **The manoeuvring buffer is 60 minutes.** It represents one *unberthing* plus one
  *berthing* manoeuvre between consecutive ships on the same berth; a single tug-assisted
  manoeuvre is on the order of 30 minutes, so roughly 30 + 30 makes 60 a reasonable floor.
  It is a **parameter**, not a constant: the point is to expose the safety versus
  berth-utilisation trade-off as one adjustable value. The accepted range is 1–1440
  minutes, since a buffer longer than a day is a data-entry error. It could later become a
  function of vessel size (LOA) or tonnage (GT).
- `handling_time` is the time a ship occupies the berth for cargo work; manoeuvres sit
  outside it, in the buffer.
- A ship becomes unassignable only for **physical** reasons. A time constraint never makes
  a ship unassignable, it only delays its start.
- Each plan run works on a snapshot of the ship and berth data at that moment.

### Constraints considered and not considered

**Considered:** the five rules from the brief, plus the integrity of historical plans
(records referenced by a plan cannot be deleted) and determinism of plan generation.

**Deliberately out of scope:**

| Out of scope | Rationale |
|---|---|
| Authentication | Explicitly not required by the brief |
| An optimal solution (ILP / OR-Tools) | Two-day scope; the brief does not expect optimality; a heuristic is explainable |
| Real-time updates / WebSockets | Unnecessary complexity for a single-operator tool |
| Drag-and-drop manual plan editing | A worthwhile nice-to-have; there was no time |
| Multiple ports / role management | Outside the problem definition |
| Tidal windows, tug and pilot availability, cargo-type to berth compatibility | Significant in real ports, but absent from the problem definition and the data model |

### Alternatives considered

| Alternative | Outcome |
|---|---|
| **Stateless plan** (generate, show, discard) | Rejected — retrospective review was wanted, so the plan is modelled as a persisted `Plan` aggregate |
| **SQLite** | Rejected — persistence plus deployment pointed to managed PostgreSQL |
| **Optimal solution via ILP / OR-Tools** | Rejected — two-day scope and explainability; the brief does not expect optimality |
| **FCFS, SPT, aged SPT** | Measured; HRRN chosen (table above) |
| **Render** for the backend | Railway was preferred; Render remains documented as an alternative in DEPLOY.md |

### Why this solution

- **A heuristic, not an optimum.** The brief does not expect an optimal solution. A
  dispatch heuristic is deterministic, fast and — most importantly — answerable when an
  operator asks *why was this ship put here*.
- **The priority rule was chosen by measurement**, not intuition: 20 random datasets across
  several load regimes.
- **The algorithm is isolated from infrastructure.** Being able to test the core without a
  database made changing the rule cheap: the move to HRRN stayed in one file and broke no
  test.
- **A plan is a record, not a live view.** Because it stores the parameters and ETAs from
  the moment it was generated, historical plans are unaffected by later edits.

---

## AI process note

I set out to build this project *together with* AI rather than have it handed to me, and
to keep the direction in my own hands throughout.

### Where in the process I used AI, and for what

I drove the sequencing: architecture and the data model first, then the ROADMAP, then the
implementation phase by phase, approving each one before moving on. Within that structure
I used Claude Code for the code-writing itself while I made the architectural calls.

AI did most of the work in three areas in particular:

- **Unit tests** for the planning core.
- **Sample datasets** — including the deliberately unassignable ships that make the
  "unassigned with a reason" flow visible.
- **Comparative experiments** on scheduling algorithms, which I directed and then used to
  decide (see the measurement table under [Planning algorithm](#planning-algorithm)).

The interface was written by AI throughout — layout, Tailwind, the colour palette, the
timeline component. For the first version I gave no styling direction and simply approved
what was proposed. The later redesign was different: I asked for it, set the brief (an
interface built on HCI principles, with some maritime character), reviewed the result and
sent parts of it back. What I found by using it is listed in the next section.

### What I changed or rejected in the AI output, and why

- **Persistent plans instead of a stateless design.** AI recommended starting stateless:
  generate a plan, display it, discard it. I chose to persist plans instead, because being
  able to review past plans matters for this kind of operations tool. That costs some
  database normalisation, but at this scale it is not a real risk — a judgement I made
  deliberately and repeated later when adding the ETA snapshot.

- **I refused to accept the manoeuvring buffer as a bare number.** AI produced the
  60-minute figure; I asked for it to be justified before it went into the plan. The
  unberthing-plus-berthing rationale in the [Assumptions](#assumptions) section exists
  because of that.

- **The ordering rule.** The initial implementation used FCFS with no stated reason. I had
  it compared against Shortest Job First across load regimes. The measurements showed SPT
  wins on total waiting under capacity pressure — where berths are few and ships many —
  while at low load the rules are indistinguishable. But SPT starved long ships. Rather
  than accept that trade-off, I asked for **aging**, the standard remedy for starvation, to
  be tested as well. Among the aged variants that were measured, HRRN was chosen because it
  delivers the benefit without a constant to tune. The experiments themselves were run by
  AI at my direction.

- **Snapshotting the ETA.** Presented with two options for a consistency defect found in
  review — copy the ETA onto each assignment, or document the limitation and leave it — I
  chose to copy it, again accepting denormalisation as the cheaper cost.

- **I dropped the decorative artwork I had asked for.** For the redesign I wanted a port
  and sea scene in the background. AI pushed back that decoration competes with dense data
  in an operations tool and proposed confining it to the landing page; I asked for it
  anyway, looked at the result, and concluded the objection was right. The illustration was
  removed and only a faint colour wash kept. Reversing my own request once I could see it
  was, in hindsight, the correct call.

- **Three defects I found by using the interface**, each of which had passed AI review:
  the landing page offered "Manage ships" but not berths, even though both are required
  before planning; the timeline caption described the buffer but never mentioned the
  waiting lane that had been added later, so the hatched area was undecodable; and "ETA"
  appeared throughout the UI and both documents without ever being spelled out. All three
  are the kind of thing that only surfaces when someone actually reads the screen.

- I do not recall rejecting an AI proposal outright beyond the artwork above.

### Which decisions are entirely my own

- **Scope:** deploying the application to a live environment was my decision, not a
  suggestion; so was persisting plans rather than discarding them.
- **Process:** planning the architecture and data model before any code, writing the
  ROADMAP before the implementation, and approving each phase individually.
- **Insisting that assumptions be argued rather than asserted.** I did not author the
  assumptions listed above, but the buffer value is justified rather than arbitrary because
  I required it to be.
- **Raising aging** as the answer to SPT's starvation problem, which changed the outcome of
  the algorithm comparison.
- **The denormalisation trade-off**, taken twice: persistent plans, and the ETA snapshot.
- **Commissioning the redesign and then cutting the decoration from it**, once seeing it
  made the argument against it concrete.

**For balance:** most of the internal engineering decisions in this project — the pure
domain layer, the layered architecture, PostgreSQL, the Gantt visualisation, the unit
tests — were AI proposals that I approved without objection. Two defects that surfaced
during development were caught by AI's own test runs rather than by me. My contribution was
concentrated in direction, scope and the decisions listed above, and in the pre-submission
review below.

### Independent pre-submission review

After development was finished the codebase was reviewed before submission. The issues
found and addressed — each recorded with its rationale in the
[ROADMAP.md](ROADMAP.md) change log:

| Finding | Decision |
|---|---|
| The rule `waiting = start − ETA` was written twice, once in the domain and once in the ORM; the ORM version read the live ship record, so editing a ship after a plan was generated made that plan inconsistent | Reduced to a single source; `Assignment.eta` added so a plan is a genuine snapshot |
| The ordering rule (FCFS) had no stated justification | Alternatives were measured; switched to HRRN |
| The linters promised in ROADMAP phase 0 had never been added | ruff added and passing; eslint, black and prettier documented as out of scope with reasons |
| `core/database.py` contained a SQLite code path that was never used | Removed |
| The manoeuvring buffer had no upper bound; 9000 min (~6 days) was silently accepted | Bounded to 1–1440 min and the frontend input aligned |
| The repository had no pytest configuration, so the `pytest` command failed | `pytest.ini` added |

---

## Tests and code quality

```bash
cd backend
.venv/Scripts/pytest
.venv/Scripts/ruff check app tests
```

13 unit tests, **no database required**, running in about 0.05 seconds. They cover each of
the five rules, all three non-assignment reasons, buffer application, determinism, the
waiting calculation (including clamping at zero) and HRRN's starvation behaviour.

**Out of scope:** there is no automated test infrastructure for the API layer;
controller and service behaviour was verified manually through Swagger. Given more time,
end-to-end API tests based on `TestClient` would be the first thing to add.

The ruff configuration ([backend/ruff.toml](backend/ruff.toml)) silences one false positive
with a stated reason: B008, which fires on FastAPI's use of `Depends()` in argument
defaults. UP037 is also disabled, because the quotes in `Mapped["Ship"]` are required —
those classes are imported only under `TYPE_CHECKING`, so removing the quotes breaks mapper
configuration.
