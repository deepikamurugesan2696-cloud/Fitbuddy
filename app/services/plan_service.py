from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Plan, User
from ..schemas import UserInput
from .gemini_service import GeminiService


def user_to_dict(data: UserInput | User) -> dict:
    return {
        "username": data.username,
        "user_id": data.user_id,
        "age": data.age,
        "weight": data.weight,
        "goal": data.goal,
        "intensity": data.intensity,
        "experience": data.experience,
        "days_per_week": data.days_per_week,
    }


def save_or_update_user(db: Session, data: UserInput) -> User:
    user = db.scalar(select(User).where(User.user_id == data.user_id))
    if user is None:
        user = User(**user_to_dict(data))
        db.add(user)
    else:
        for key, value in user_to_dict(data).items():
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def create_plan(db: Session, data: UserInput, ai: GeminiService) -> tuple[User, Plan]:
    user = save_or_update_user(db, data)
    profile = user_to_dict(data)
    original = ai.generate_workout(profile)
    tip = ai.generate_tip(profile)
    plan = Plan(user_id=user.user_id, original_plan=original, nutrition_tip=tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return user, plan


def get_latest_plan(db: Session, user_id: str) -> Plan | None:
    return db.scalar(
        select(Plan).where(Plan.user_id == user_id).order_by(Plan.created_at.desc())
    )


def update_plan(db: Session, user_id: str, feedback: str, ai: GeminiService) -> tuple[User, Plan]:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    plan = get_latest_plan(db, user_id)
    if not plan:
        raise ValueError("No workout plan exists for this user")

    profile = user_to_dict(user)
    base = plan.updated_plan or plan.original_plan

    revised = ai.update_workout(profile, base, feedback)

    plan.updated_plan = revised
    plan.feedback = feedback
    plan.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(plan)

    return user, plan
    

