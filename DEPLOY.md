# Deployment guide

Layout: **backend + PostgreSQL on Railway**, **frontend on Vercel**.

> **Order matters.** The backend and the frontend each need the other's URL, so:
> deploy the backend first and take its URL, then deploy the frontend with that URL,
> and finally update the backend's `CORS_ORIGINS` with the frontend URL.

Prerequisite: the project must be pushed to GitHub as a monorepo (`backend/` and
`frontend/` at the repository root).

---

## 1. Backend + PostgreSQL (Railway)

1. [railway.app](https://railway.app) then **New Project** -> **Deploy from GitHub repo**
   and pick the repository.
2. Set the service's **Settings -> Root Directory** to `backend`. Railway detects
   `backend/Dockerfile` automatically, and the Dockerfile runs `alembic upgrade head`
   before starting the server.
3. Add **New -> Database -> PostgreSQL** to the project. Then wire the connection up
   **manually** on the backend service via **Variables -> New Variable**:
   - Name `DATABASE_URL`, value `${{Postgres.DATABASE_URL}}`
   - Rather than typing it, use the **Add a Reference** button and pick `Postgres` ->
     `DATABASE_URL`.
   - Use `DATABASE_URL`, which goes over the private network, not `DATABASE_PUBLIC_URL`.

   > Adding Postgres to the same Railway project does **not** inject the variable into the
   > backend service automatically. Skip this step and the application falls back to the
   > local default in `config.py`, then crashes at startup with
   > `connection to server at "127.0.0.1", port 5432 failed`.
   - The URL comes in `postgres://...` form; the application converts it to the psycopg v3
     driver **automatically** (handled in code).
4. Backend service -> **Settings -> Networking -> Generate Domain**. You get a public URL,
   `https://<name>.up.railway.app`. **Note it down.**
5. Confirm in the deploy logs that the migration ran (`Running upgrade -> ... initial`).
6. `https://<name>.up.railway.app/health` should return `{"status":"ok"}`, and `/docs`
   (Swagger) should open.

## 2. Frontend (Vercel)

1. [vercel.com](https://vercel.com) then **Add New -> Project** and import the same
   repository.
2. Choose `frontend` as the **Root Directory**. Vercel detects Next.js automatically.
3. Add an **Environment Variable**:
   - `NEXT_PUBLIC_API_URL = https://<name>.up.railway.app/api` *(the trailing `/api`
     matters)*
4. **Deploy.** You get a URL, `https://<app>.vercel.app`. **Note it down too.**

## 3. Update the backend CORS setting

1. Railway -> backend service -> **Variables** -> new variable:
   - `CORS_ORIGINS = https://<app>.vercel.app`
2. The service redeploys automatically. Browser requests will now pass CORS.

## 4. Demo data (optional)

To fill the live database with sample data, run the seed script once:

- **With the Railway CLI:** `railway run --service <backend> python -m app.seed`
- **Or** from the Railway service shell (Deployments -> shell): `python -m app.seed`

This inserts 6 berths and 11 ships; generating a plan then yields 8 assignments and 3
unassigned ships covering three different reasons.

---

## Notes

- **Cold start:** on a free tier the backend may sleep while idle, so the first request can
  take a few seconds. Hit `/health` shortly before a demo to wake it up.
- **Environment variables at a glance:**
  | Where | Variable | Example |
  |---|---|---|
  | Railway (backend) | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` *(added manually as a reference)* |
  | Railway (backend) | `CORS_ORIGINS` | `https://app.vercel.app` |
  | Vercel (frontend) | `NEXT_PUBLIC_API_URL` | `https://backend.up.railway.app/api` |
- **Alternative (Render):** Render also works for the backend — the same Dockerfile applies.
  Add managed PostgreSQL, wire up `DATABASE_URL`, and the start command comes from the
  Dockerfile.
