from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility", "endurance"]
Intensity = Literal["low", "medium", "high"]
Experience = Literal["beginner", "intermediate", "advanced"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=0, le=500)
    goal: Goal
    intensity: Intensity
    experience: Experience = "beginner"
    days_per_week: int = Field(default=4, ge=1, le=7)

    @field_validator("username")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class FeedbackRequest(BaseModel):
    feedback: str = Field(min_length=3, max_length=1000)


class PlanResponse(BaseModel):
    user_id: str
    username: str
    goal: str
    intensity: str
    experience: str
    workout_plan: str
    nutrition_tip: str


class FeedbackResponse(PlanResponse):
    feedback: str
    updated_plan: str
