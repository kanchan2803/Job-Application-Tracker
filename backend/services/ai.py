import json
import os
import httpx
from typing import Dict, Any

class AIService:
    def __init__(self):
        # Defaulting to Gemini for this example, can be swapped via env variables.
        self.api_key = os.getenv("AI_API_KEY")
        self.provider = os.getenv("AI_PROVIDER", "gemini") 

    async def extract_job_details(self, text: str) -> Dict[str, Any]:
        prompt = f"""
        Extract the following job details from the text below. 
        Return ONLY a valid JSON object with these exact keys (use null if missing): 
        "company", "role", "location", "employmentType", "deadline", "skills" (array of strings), 
        "experience", "batch", "salary", "jobLink", "status" (default to "Saved"), "notes" (any extra useful info).
        
        Text:
        {text}
        """

        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        # Add elif self.provider == "openai": ... here later
        
        return {}

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            try:
                content = data['candidates'][0]['content']['parts'][0]['text']
                return json.loads(content)
            except (KeyError, json.JSONDecodeError):
                return {}