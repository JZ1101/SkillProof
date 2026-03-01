# SkillProof

AI-powered trade certification platform. Workers upload videos of tasks (tiling, painting & decorating), AI assesses technique, safety, and result quality — certificates in minutes, not weeks.

## Quick Start

```bash
# Backend (port 8000)
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (port 5173) — in a separate terminal
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## Tech Stack

- **Backend:** FastAPI + SQLite
- **Frontend:** React + Vite
- **AI:** Google Gemini (video assessment)
- **Package manager:** uv (Python), npm (JS)
