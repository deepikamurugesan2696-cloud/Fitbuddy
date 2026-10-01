"""Compatibility wrapper matching the function name in the project documentation."""
from .services.gemini_service import GeminiService


def generate_workout_gemini(user: dict) -> str:
    return GeminiService().generate_workout(user)
