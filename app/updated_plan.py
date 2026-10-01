"""Compatibility wrapper matching the function name in the project documentation."""
from .services.gemini_service import GeminiService


def update_workout_plan(user: dict, original_plan: str, feedback: str) -> str:
    return GeminiService().update_workout(user, original_plan, feedback)
