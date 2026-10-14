# Django + Angular 21 Assessment

Please complete **Setup** and the **setup check** before your interview, so the session can start
straight away on the problem.

## Setup

You only need [uv](https://docs.astral.sh/uv/). It brings the right Python version with it, and the
setup below also downloads Node.js if yours is missing or older than 20.19. Nothing needs admin rights.

**1. Install uv** (skip if `uv --version` already works)

macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then open a **new** terminal so `uv` is on your PATH.

**2. Clone the repo and run the setup check**

```bash
git clone https://github.com/vivek-ottimate/django-angular-boilerplate.git
cd django-angular-boilerplate
uv run dev.py check
```

The check installs everything (Python packages, frontend packages, Antigravity CLI, and Node.js if
needed), then starts both servers once to confirm they work. The first run takes a few minutes. It
ends with **All set**, or tells you exactly what to fix.

**3. Sign in to Antigravity CLI**

[Antigravity CLI](https://antigravity.google/) (`agy`) is Google's free AI coding agent for the
terminal. Start it from the repo root:

```bash
uv run dev.py agy
```

It prints a Google sign-in link. Open it, sign in and approve. A **personal Gmail account** is
simplest, since a work or school account may be blocked by its admin. No credit card is needed.
`agy` usually notices the sign-in by itself; if it keeps waiting, the page shows a code starting
`4/0`: copy it and paste it into the terminal where `agy` is waiting.

Then quit `agy` (Ctrl+C) and run `uv run dev.py check` once more; it should show Antigravity CLI as
signed in.

If you already have `agy` installed, plain `agy` works too. The free plan has a weekly allowance per
model family; if the Gemini models run out, switch to a Claude model with `/model`.

## Start the project

```bash
uv run dev.py
```

This starts Django on `http://localhost:8000` and Angular on `http://localhost:4200` in one terminal.
**Ctrl+C** stops both. Django reloads when you change Python files, and Angular when you change
frontend files. Open `http://localhost:4200` and click **Ping Backend** to see them talk.

Use a second terminal for `agy` and anything else.

## No local setup? Use GitHub Codespaces

1. Click **Code → Codespaces → Create codespace on main** on the GitHub repo page
2. Wait a few minutes for the environment to build
3. In the terminal, run `uv run dev.py`, then open the forwarded port `4200` when prompted
4. In a second terminal, run `uv run dev.py agy` and sign in as above, pasting the `4/0…` code
   from the sign-in page if `agy` keeps waiting

## Interview problem

Your interviewer will give you codes during the session. From the repo root:

```bash
uv run interview/run.py <start-code>     # writes problem/BRIEF.md and problem/seed.json
uv run interview/run.py <check-code>     # runs the automated checks against your backend
```

The checks call Django directly at `http://127.0.0.1:8000`, so keep `uv run dev.py` running, with
the seed data freshly loaded. Keep the `DATABASES` settings in `backend/backend/settings.py` as they
are; the checks rely on them.

The database is `backend/db.sqlite3`. To start from an empty one, stop the servers, delete that
file, and run `uv run dev.py` again; it creates the tables on start.

## Everyday commands

| Task | Command |
| --- | --- |
| Start both servers | `uv run dev.py` |
| Django management commands | `cd backend` then `uv run manage.py <command>` (e.g. `makemigrations`) |
| Add a Python package | `uv add <package>` |
| Django tests | `cd backend` then `uv run manage.py test` |
| Angular tests | `uv run dev.py npm test` |
| Add a frontend package | `uv run dev.py npm install <package>` |

`uv run dev.py npm ...` runs npm in `frontend/` with the project's Node.js. If your own Node.js is
20.19 or newer, plain `npm` inside `frontend/` works the same.

## Project structure

```
├── backend/          # Django project
│   ├── api/          # Example app — models, views, tests
│   └── backend/      # Django settings and URLs
├── frontend/         # Angular 21 app
│   └── src/app/      # Components and services
├── interview/        # Problem runner and locked problem data
├── dev.py            # Setup, setup check and server runner
└── pyproject.toml    # Python version and packages (used by uv)
```
