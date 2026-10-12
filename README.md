# Django + Angular 21 Assessment

## Option A — GitHub Codespaces (recommended, no local setup)

1. Click **Code → Codespaces → Create codespace on main** on the GitHub repo page
2. Wait ~30 seconds for the environment to build and dependencies to install
3. Open two terminal tabs and start the servers:

**Terminal 1 — Django:**
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 — Angular:**
```bash
cd frontend
npm start
```

4. Codespaces will prompt you to open the forwarded port — click **Open in Browser** on port `4200`
5. Gemini CLI is already installed — see [AI assistant](#ai-assistant--gemini-cli) to start it

---

## Option B — Run locally

### Prerequisites
- Python 3.12+
- Node.js 22+ (or 20.19+)

### 1. Clone the repo

```bash
git clone https://github.com/vivek-ottimate/django-angular16-boilerplate.git
cd django-angular16-boilerplate
```

### 2. Backend

```bash
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
cd backend
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

Django runs at `http://localhost:8000`

### 3. Frontend

Open a second terminal tab:

```bash
cd frontend
npm install
npm start
```

Angular runs at `http://localhost:4200`

### 4. Gemini CLI

Open a third terminal tab and install it once (macOS, Linux and Windows):

```bash
npm install -g @google/gemini-cli
```

On Linux, if this fails with `EACCES`, your Node install needs `sudo` for global packages — either rerun with `sudo` or install Node via [nvm](https://github.com/nvm-sh/nvm). On macOS, `brew install gemini-cli` also works.

---

## AI assistant — Gemini CLI

From the repo root (not `backend/` or `frontend/`, so it can see the whole project):

```bash
gemini
```

On first run choose **Sign in with Google** and log in with a **personal Gmail account** — work or school accounts need extra Google Cloud setup. The free tier needs no credit card.

---

## Verify the connection

Open the Angular app and click **Ping Backend** — you should see a message and ping count returned from Django.

## Running tests

**Django:**
```bash
cd backend
python manage.py test
```

**Angular:**
```bash
cd frontend
npm test
```

## Project structure

```
├── backend/          # Django project
│   ├── api/          # Example app — models, views, tests
│   └── backend/      # Django settings and URLs
└── frontend/         # Angular 21 app
    └── src/app/      # Components and services
```
