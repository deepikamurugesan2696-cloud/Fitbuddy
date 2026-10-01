from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import BASE_DIR, get_settings
from .database import get_db
from .models import User
from .schemas import FeedbackRequest, PlanResponse, UserInput
from .services.gemini_service import GeminiService, GeminiServiceError
from .services.plan_service import create_plan, get_latest_plan, update_plan, user_to_dict


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter()


def get_ai() -> GeminiService:
    return GeminiService()


def render_error(request: Request, message: str, code: int = 500):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"message": message},
        status_code=code,
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    experience: str = Form("beginner"),
    days_per_week: int = Form(4),
    db: Session = Depends(get_db),
    ai: GeminiService = Depends(get_ai),
):
    try:
        data = UserInput(
            username=username, user_id=user_id, age=age, weight=weight,
            goal=goal, intensity=intensity, experience=experience,
            days_per_week=days_per_week,
        )
        user, plan = create_plan(db, data, ai)
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={"user": user, "plan": plan, "message": None},
        )
    except GeminiServiceError as exc:
        return render_error(request, str(exc), 503)
    except ValueError as exc:
        return render_error(request, str(exc), 400)
    except Exception as exc:
        return render_error(request, f"Could not generate the plan: {exc}", 500)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
    ai: GeminiService = Depends(get_ai),
):
    try:
        feedback_data = FeedbackRequest(feedback=feedback)
        user, plan = update_plan(db, user_id, feedback_data.feedback, ai)
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={"user": user, "plan": plan, "message": "Your plan was updated successfully."},
        )
    except GeminiServiceError as exc:
        return render_error(request, str(exc), 503)
    except ValueError as exc:
        return render_error(request, str(exc), 404)
    except Exception as exc:
        return render_error(request, f"Could not update the plan: {exc}", 500)


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    if settings.admin_token:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={},
        )
    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={"users": users},
    )


@router.post("/admin", response_class=HTMLResponse)
def admin_login(request: Request, token: str = Form(...), db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.admin_token or token != settings.admin_token:
        return render_error(request, "Invalid admin token.", 401)
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users})


@router.get("/api/v1/users", response_model=list[dict])
def api_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {
            "id": u.id, "user_id": u.user_id, "username": u.username, "age": u.age,
            "weight": u.weight, "goal": u.goal, "intensity": u.intensity,
            "experience": u.experience, "days_per_week": u.days_per_week,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/api/v1/users/{user_id}")
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    plan = get_latest_plan(db, user_id)
    return {
        "user": user_to_dict(user),
        "plan": None if not plan else {
            "original_plan": plan.original_plan,
            "updated_plan": plan.updated_plan,
            "feedback": plan.feedback,
            "nutrition_tip": plan.nutrition_tip,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        },
    }


@router.post("/api/v1/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def api_generate_plan(data: UserInput, db: Session = Depends(get_db), ai: GeminiService = Depends(get_ai)):
    try:
        user, plan = create_plan(db, data, ai)
    except GeminiServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PlanResponse(
        user_id=user.user_id, username=user.username, goal=user.goal,
        intensity=user.intensity, experience=user.experience,
        workout_plan=plan.original_plan, nutrition_tip=plan.nutrition_tip,
    )


@router.post("/api/v1/plans/{user_id}/feedback", response_model=object)
def api_update_plan(
    user_id: str,
    data: FeedbackRequest,
    db: Session = Depends(get_db),
    ai: GeminiService = Depends(get_ai),
):
    try:
        user, plan = update_plan(db, user_id, data.feedback, ai)
    except GeminiServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "user_id": user.user_id,
        "username": user.username,
        "feedback": data.feedback,
        "updated_plan": plan.updated_plan,
        "nutrition_tip": plan.nutrition_tip,
    }
