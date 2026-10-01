from __future__ import annotations

from ..config import get_settings


class GeminiServiceError(RuntimeError):
    pass


class GeminiService:
    """Small service layer around the current Google GenAI Python SDK."""

    def __init__(self, api_key: str | None = None, workout_model: str | None = None, tip_model: str | None = None):
        settings = get_settings()
        key = api_key or settings.gemini_api_key
        self.workout_model = workout_model or settings.gemini_workout_model
        self.tip_model = tip_model or settings.gemini_tip_model
        self.client = None
        if key:
            try:
                from google import genai
                self.client = genai.Client(api_key=key)
            except ImportError as exc:
                raise GeminiServiceError(
                    "The google-genai package is not installed. Run: pip install -r requirements.txt"
                ) from exc

    def _generate(self, model: str, prompt: str, max_tokens: int = 5000) -> str:
        if not self.client:
            raise GeminiServiceError(
                "GEMINI_API_KEY is not configured. Add it to your .env file."
            )

        from google.genai import types
        import time

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=max_tokens,
                    ),
                )

                text = (response.text or "").strip()

                if not text:
                    raise GeminiServiceError("Gemini returned an empty response.")

                return text

            except GeminiServiceError:
                raise

            except Exception as exc:
                error_message = str(exc)

                if (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                    or "429" in error_message
                    or "RESOURCE_EXHAUSTED" in error_message
                ):
                    if attempt < max_attempts:
                        time.sleep(2 * attempt)
                        continue

                raise GeminiServiceError(
                    f"Gemini request failed: {exc}"
                ) from exc

        raise GeminiServiceError("Gemini request failed after multiple attempts.")
    def generate_workout(self, user: dict) -> str:
        prompt = f"""
You are FitBuddy, a conservative wellness planning assistant.
Create a structured 7-day general fitness plan for an adult user unless the profile age is under 18.
User profile:
- Name: {user['username']}
- Age: {user['age']}
- Weight: {user['weight']} kg
- Goal: {user['goal']}
- Preferred intensity: {user['intensity']}
- Experience: {user['experience']}
- Requested training days: {user['days_per_week']}

Safety rules:
- Do not diagnose, treat, or claim medical outcomes.
- Do not prescribe extreme calorie restriction, fasting, supplements, dehydration, or unsafe challenges.
- Do not encourage exercise through pain, dizziness, fainting, or injury.
- Include rest/recovery and a short warm-up/cool-down.
- If age is under 18, do not frame the plan around weight loss, calorie restriction, or changing body size. Use age-appropriate general activity and wellness language and encourage support from a parent/guardian, coach, or qualified professional when appropriate.

Return exactly seven labeled days. For each day include: Focus, Warm-up, Main activity with simple sets/reps or duration, Rest/Recovery. Keep the plan practical and readable.
"""
        return self._generate(self.workout_model, prompt, max_tokens=6000)

    def generate_tip(self, user: dict) -> str:
        prompt = f"""
Give one concise nutrition or recovery tip for a FitBuddy user.
Goal: {user['goal']}
Age: {user['age']}
Intensity: {user['intensity']}
Experience: {user['experience']}

Use ordinary food, hydration, sleep, recovery, and balanced-meal guidance.
Do not prescribe supplements, extreme diets, calorie targets, or weight-loss tactics for minors.
Maximum 120 words. End with one short safety reminder when relevant.
"""
        return self._generate(self.tip_model, prompt, max_tokens=300)

    def update_workout(self, user: dict, original_plan: str, feedback: str) -> str:
        prompt = f"""
Update the FitBuddy 7-day fitness plan below using the user's feedback.

User: {user['username']}, age {user['age']}, goal {user['goal']}, intensity {user['intensity']}, experience {user['experience']}.

Original plan:
{original_plan}

Feedback:
{feedback}

Keep the same seven-day structure, incorporate the feedback where reasonable, preserve rest/recovery,
and avoid medical claims, extreme dieting, unsafe exercise, or exercising through pain.
If the feedback requests something unsafe, replace it with a safer general alternative.
"""
        return self._generate(self.workout_model, prompt, max_tokens=6000)
