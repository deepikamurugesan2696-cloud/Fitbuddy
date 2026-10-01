# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite web application that uses Google Gemini models to generate a structured 7-day workout plan, a concise nutrition/recovery tip, and an updated plan from user feedback.

## Architecture

Browser → FastAPI routes → Gemini service layer + SQLAlchemy → SQLite → Jinja2 templates

The implementation follows the supplied project documentation while using Google's current `google-genai` Python SDK instead of the legacy `google-generativeai` package.

## Features

- User profile form: name, user ID, age, weight, goal, intensity, experience and days/week.
- AI-generated 7-day plan.
- AI-generated nutrition/recovery tip.
- Feedback-based plan regeneration.
- SQLite persistence of users, original plans and updated plans.
- Admin dashboard.
- JSON REST endpoints for API testing.
- Health endpoint.
- Mockable Gemini service for automated tests.
- Friendly error handling when the API key is missing or Gemini is unavailable.

## Safety note

This is an educational software project, not medical care. Generated plans are general information. The app deliberately avoids prescribing extreme dieting, supplements, unsafe exercises, or diagnosis/treatment. For a real deployment, add authentication, authorization, rate limiting, audit logging, privacy controls, and professional review.

## Quick start (Windows / VS Code)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `GEMINI_API_KEY`.

Run:

```powershell
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users

## macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Test

```bash
pytest -q
```

The automated tests do not call Gemini; they inject a fake AI service so tests are repeatable and do not consume API quota.

## REST API

### Generate a plan

`POST /api/v1/plans`

JSON example:

```json
{
  "username": "Demo User",
  "user_id": "demo001",
  "age": 22,
  "weight": 65,
  "goal": "general wellness",
  "intensity": "medium",
  "experience": "beginner",
  "days_per_week": 4
}
```

### Update a plan

`POST /api/v1/plans/{user_id}/feedback`

```json
{
  "feedback": "Make the sessions shorter and include more mobility work."
}
```

### Get users

`GET /api/v1/users`

### Get a user

`GET /api/v1/users/{user_id}`

### Health

`GET /health`

## Model configuration

The defaults are configurable in `.env`:

- `GEMINI_WORKOUT_MODEL=gemini-2.5-pro`
- `GEMINI_TIP_MODEL=gemini-3.8-flash`

The current Gemini API uses the `google-genai` client and `client.models.generate_content(...)`. See Google's current Gemini API documentation for supported model IDs.
