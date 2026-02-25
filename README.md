# Billing Watch Monorepo

Unified repository for the Billing Watch dashboard and backend services.

## Structure
- `/frontend`: React + Vite dashboard application.
- `/backend`: FastAPI backend with PostHog and AWS integrations.

## Getting Started

### Backend
1. `cd backend`
2. `python -m uvicorn app.main:app --port 8001`

### Frontend
1. `cd frontend`
2. `npm run dev`
