# Deploying PrepPilot AI

Live stack: **Render** (backend + Postgres) + **Vercel** (frontend). Both have free tiers — no credit card required for an initial portfolio deployment.

---

## Prerequisites

- GitHub account with this repo pushed to it (public or private both work)
- [Render account](https://render.com) — sign up free
- [Vercel account](https://vercel.com) — sign up free, connect your GitHub

---

## Step 1 — Push the repo to GitHub

```bash
cd preppilot-ai
git init                          # skip if already a git repo
git add .
git commit -m "feat: deploy config"
gh repo create preppilot-ai --public --source=. --push
# or: git remote add origin https://github.com/twix07/preppilot-ai.git && git push -u origin main
```

---

## Step 2 — Deploy backend + database on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect your GitHub account and select the `preppilot-ai` repo
3. Render detects `render.yaml` automatically and shows two resources:
   - `preppilot-backend` (web service)
   - `preppilot-db` (PostgreSQL)
4. Click **Apply** — Render provisions the DB, builds the Docker image, runs `alembic upgrade head`, and starts the API.
5. Wait ~3–5 min for the first build. Check the logs tab — you should see:
   ```
   PrepPilot API up. LLM=MOCK model=claude-sonnet-5 db=postgresql+asyncpg
   ```
6. Note your backend URL — it will look like:
   ```
   https://preppilot-backend-x6xc.onrender.com
   ```
7. Verify: `curl https://preppilot-backend-x6xc.onrender.com/health`
   Expected: `{"status":"ok","llm_mode":"mock"}`

### Optional — enable live Claude (costs ~$0.08/interview)

In Render dashboard → `preppilot-backend` → **Environment** → add:
```
ANTHROPIC_API_KEY = sk-ant-...
```
The service redeploys automatically. Health check will then return `"llm_mode":"live"`.

---

## Step 3 — Deploy frontend on Vercel

1. Go to [vercel.com/new](https://vercel.com/new) → **Import Git Repository** → select `preppilot-ai`
2. Set **Root Directory** to `frontend`
3. Framework: **Next.js** (auto-detected)
4. Under **Environment Variables**, add:
   ```
   NEXT_PUBLIC_API_URL = https://preppilot-backend-x6xc.onrender.com
   ```
5. Click **Deploy**. Vercel builds and gives you a URL like:
   ```
   https://preppilot-ai-blond.vercel.app
   ```

---

## Step 4 — Wire CORS (connect them)

Back in Render dashboard → `preppilot-backend` → **Environment** → set:
```
FRONTEND_ORIGIN = https://preppilot-ai-blond.vercel.app
```
If you have multiple domains (e.g. a custom domain too), use comma-separated values:
```
FRONTEND_ORIGIN = https://preppilot-ai-blond.vercel.app,https://preppilot.yourdomain.com
```
Save — Render redeploys in ~30 seconds.

---

## Step 5 — Smoke test

1. Open `https://preppilot-ai-blond.vercel.app`
2. Sign in with **dev login**: email `demo@preppilot.ai` (no password needed)
3. You should see the seeded dashboard with a readiness trend
4. Start a mock interview — it runs fully in mock mode, no API key needed

---

## Seed demo data (optional but recommended for demos)

The Docker startup does not auto-seed. To add the 5 demo sessions:

```bash
# one-off: run via Render Shell (dashboard → preppilot-backend → Shell tab)
python -m app.seed
```

This populates `demo@preppilot.ai` with a realistic upward readiness trend — looks much better on a live demo.

---

## Custom domain (optional)

- **Vercel:** Settings → Domains → add your domain, follow the DNS instructions
- **Render:** Settings → Custom Domain → add your domain

Update `FRONTEND_ORIGIN` on Render to include your custom domain after DNS propagates.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend shows "Service Unavailable" on first visit | Free tier spins down after 15 min inactivity — just wait 30–60s for cold start |
| CORS error in browser console | Check `FRONTEND_ORIGIN` on Render matches your Vercel URL exactly (no trailing slash) |
| `alembic upgrade head` fails in logs | Usually a DB connection timing issue on first deploy — click Manual Deploy to retry |
| Frontend shows "Network Error" | Confirm `NEXT_PUBLIC_API_URL` in Vercel env vars points to your Render URL, not localhost |
| `demo@preppilot.ai` login fails | Confirm `ALLOW_DEV_LOGIN=true` is set on Render (it is by default in render.yaml) |

---

## Cost summary

| Resource | Plan | Cost |
|---|---|---|
| Render backend | Free | $0 (sleeps after 15 min inactivity) |
| Render PostgreSQL | Free | $0 (90-day trial, then $7/mo) |
| Vercel frontend | Hobby | $0 |
| Anthropic Claude | Pay-per-use | ~$0.08/interview (optional — mock mode is free) |

For an always-on portfolio demo, the Render free tier is fine. The 30-second cold start is acceptable for interviewers clicking a link.
