"""Compatibility wrapper matching the function name in the project documentation."""
from .services.gemini_service import GeminiService


def generate_nutrition_tip_with_flash(user: dict) -> str:
    return GeminiService().generate_tip(user)
