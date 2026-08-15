# Deployment & Setup Guide — WebGuardian AI

WebGuardian AI is built with two operational modes: a zero-dependency **Local Development / Demo Mode** and a production-grade **Docker Orchestrated Mode**.

---

## ⚡ 1. Local Development / Demo Mode (Recommended for Judges)

This mode runs both backend API engines and task workers in a single process using local SQLite databases, requiring no Redis, Celery, or database server configurations.

### Step 1: Clone and Scaffolding Setup
Ensure you are inside the repository workspace root:
```bash
# Set up a python virtual environment
python -m venv venv

# Activate venv (Windows)
.\venv\Scripts\activate
# Activate venv (macOS/Linux)
source venv/bin/activate

# Install python dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`. The defaults are pre-configured to use SQLite and Mock LLM simulation mode:
```ini
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./webguardian.db
LLM_PROVIDER=mock
LLM_MODEL=gpt-4o-mini
```
*Note: Keep API keys blank to run WebGuardian in simulated demo mode. To run on live sites, add `OPENAI_API_KEY`, `BRIGHT_DATA_API_KEY`, and change `LLM_PROVIDER=openai`.*

### Step 3: Launch Backend Control Plane
Run the FastAPI application:
```bash
python -m uvicorn apps.backend.app.main:app --reload
```
This triggers the server at `http://127.0.0.1:8000` and automatically starts our async local worker queue loops.

### Step 4: Launch Frontend SaaS Dashboard
Navigate to the frontend folder and install Next.js packages:
```bash
cd apps/frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser. Click **Enter Console** to view the Command Center and trigger Chaos Mode redesigns.

---

## 🐋 2. Production Docker Compose Deployment

For production deployments, WebGuardian separates backend APIs, database backends, cache queues, and background task workers.

### Step 1: Set Production variables in `.env`
Configure production database URLs and cache networks:
```ini
DATABASE_URL=postgresql://postgres:postgres@postgres_db:5432/webguardian
REDIS_URL=redis://redis_cache:6379/0
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
BRIGHT_DATA_API_KEY=your_key_here
BRIGHT_DATA_CUSTOMER_ID=your_id_here
```

### Step 2: Build and Launch Containers
Run Docker Compose in the root folder:
```bash
docker-compose up --build -d
```
This spins up:
*   `postgres_db`: PostgreSQL relational database storage.
*   `redis_cache`: Redis message broker and backend cache.
*   `backend_api`: FastAPI control plane endpoints.
*   `celery_worker`: Celery task worker listening to Redis queues.
*   `frontend_app`: Next.js production build web server.
