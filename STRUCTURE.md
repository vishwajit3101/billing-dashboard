# Billing Watch — Project Structure

This file provides an overview of the actual project structure as of February 2026.

## Repo Root
- `backend/`: FastAPI backend and Lambda logic.
- `frontend/`: React dashboard frontend.
- `src/`: Shared frontend source code (standard Vite structure).
- `STRUCTURE.md`: This file.

## Backend Structure (`backend/`)
The backend is a consolidated FastAPI application designed to run on AWS Lambda.

- `app/`: Main application logic.
  - `main.py`: FastAPI entry point and dashboard API.
  - `lambda_handler.py`: Entry point for hourly data fetching tasks.
  - `posthog.py`: Integration with PostHog for real usage data.
  - `anthropic.py`, `aws_cost.py`, `tavily.py`, etc.: Tool-specific API integrations.
  - `calculations.py`: Risk scoring and alert generation logic.
  - `database.py`: PostgreSQL connection management.
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables (API keys, DB credentials).
- `seed_mock.py`: Utility script to seed the database with mock tools.
- `create_tables.py`: Utility script to initialize database tables.

## Frontend Structure
The frontend is a modern React application using Vite and Tailwind CSS.
- `src/components/dashboard/`: Core dashboard UI components (`AnthropicCard`, `AWSCard`, `ToolCard`, etc.).
- `src/hooks/`: Custom React hooks like `useDashboard`.
- `src/lib/`: API client and utility logic.

## Deployment & Infrastructure
- Infrastructure code (Terraform) is located in `infrastructure/`.
- Deployment scripts are located in `scripts/`.
- Automated EventBridge scheduler setup is identified as a future improvement.
