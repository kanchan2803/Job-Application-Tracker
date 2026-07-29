import json
import os
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger("uvicorn.error")


class AIService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        # Current GA model as of mid-2026. Override via env var if it changes again.
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    async def extract_job_details(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "AI_API_KEY is not set on the server. Add it in your backend's "
                "environment variables on Render."
            )

        prompt = f"""
        Extract the following job details from the text below.
        Return ONLY a valid JSON object with these exact keys (use null if missing):
        "company", "role", "location", "employmentType", "deadline", "skills" (array of strings),
        "experience", "batch", "salary", "jobLink","jobID", "status" (default to "Saved"), "notes" (any extra useful info).

        Text:
        {text}
        """

        if self.provider == "gemini":
            return await self._call_gemini(prompt)

        raise ValueError(f"Unsupported AI_PROVIDER: {self.provider}")

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
            raise ValueError(
                f"Gemini API rejected the request ({e.response.status_code}). "
                f"Details: {e.response.text[:200]}"
            )
        except httpx.RequestError as e:
            logger.error(f"Gemini network error: {e}")
            raise ValueError(f"Could not reach Gemini API: {e}")

        try:
            content = data['candidates'][0]['content']['parts'][0]['text']
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Gemini response parsing failed: {data}")
            raise ValueError(f"Gemini returned an unexpected response format: {e}")