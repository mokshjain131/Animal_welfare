# Setup Guide

This guide covers running the project locally and deploying it to Render + Netlify/Vercel.

---

## Prerequisites

- Python 3.13+
- Node.js 18+
- A [Supabase](https://supabase.com) project with the schema applied
- A [HuggingFace](https://huggingface.co/settings/tokens) account (free tier works)
- A [NewsAPI](https://newsapi.org) API key (free tier: 100 requests/day)

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/animal-welfare-tracker.git
cd animal-welfare-tracker
```

---

## 2. Supabase Schema

1. Create a new project at [supabase.com](https://supabase.com)
2. Open the **SQL Editor** in your Supabase dashboard
3. Run the contents of `backend/db/migrations/init.sql` — this creates all tables
4. Run `backend/db/migrations/supabase_rpc_functions.sql` — this creates the RPC functions used by the API
5. Copy your **Project URL** and **anon public key** from Project Settings → API

---

## 3. Backend — Local

### Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or with [uv](https://docs.astral.sh/uv/) (faster):

```bash
cd backend
uv sync
```

### Configure environment

Create `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
NEWSAPI_KEY=your-newsapi-key
HF_API_TOKEN=hf_your-token
```

### Run the server

```bash
# With uv
uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With pip
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On startup the server will:
1. Start the APScheduler (pipeline runs every 30 minutes)
2. Immediately run the ingestion pipeline in a background thread
3. Serve all API endpoints at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

> Set `SKIP_PIPELINE=1` in your environment to skip the pipeline on startup (useful for testing endpoints without waiting for ingestion).

---

## 4. Frontend — Local

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Run the dev server:

```bash
npm run dev
```

Dashboard available at `http://localhost:5173`

---

## 5. Deploy Backend to Render

1. Push the repository to GitHub
2. Go to [render.com](https://render.com) → New → **Web Service**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. Add environment variables under **Environment**:

| Key | Value |
|---|---|
| `SUPABASE_URL` | your Supabase project URL |
| `SUPABASE_KEY` | your Supabase anon key |
| `NEWSAPI_KEY` | your NewsAPI key |
| `HF_API_TOKEN` | your HuggingFace token |

6. Deploy. The backend will be live at `https://your-service.onrender.com`

> **Free tier note:** Render free services spin down after 15 minutes of inactivity. The first request after spin-down takes ~30 seconds. Use a cron job service (e.g. [cron-job.org](https://cron-job.org)) to ping `/overview/metrics` every 10 minutes to keep it warm.

---

## 6. Deploy Frontend to Netlify or Vercel

### Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → import your repository
2. Set **Root Directory** to `frontend`
3. Add environment variable: `VITE_API_URL` = `https://your-service.onrender.com`
4. Deploy

### Netlify

1. Go to [netlify.com](https://netlify.com) → Add new site → import from Git
2. Set **Base directory** to `frontend`, **Build command** to `npm run build`, **Publish directory** to `frontend/dist`
3. Under Site settings → Environment variables, add: `VITE_API_URL` = `https://your-service.onrender.com`
4. Deploy

---

## 7. Running Tests

```bash
cd backend

# Individual module verification scripts
uv run python tests/verify_module1.py
uv run python tests/verify_module2.py
uv run python tests/verify_module3.py
uv run python tests/verify_module4.py
uv run python tests/verify_module5.py
uv run python tests/verify_module6.py
uv run python tests/verify_module7.py
```

---

## 8. Keeping Dependencies Up to Date

When you change `pyproject.toml`, regenerate `requirements.txt` before pushing:

```bash
cd backend
uv export --format requirements-txt --no-dev --no-hashes -o requirements.txt
```

This keeps the Render pip install in sync with your local uv environment.
