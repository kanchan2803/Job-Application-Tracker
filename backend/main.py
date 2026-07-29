from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from services.scraper import extract_text_from_url
from services.ai import AIService
from services.sheets import SheetsService
import re

load_dotenv()

app = FastAPI(title="AI Job Tracker MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIService()
sheets_service = SheetsService()


class JobRequest(BaseModel):
    input_text: str
    sheet_url: str

    @field_validator("input_text", "sheet_url")
    @classmethod
    def not_blank(cls, v: str, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()


@app.post("/api/jobs")
async def save_job(request: JobRequest):
    try:
        content = request.input_text

        # If input is just a URL, scrape it
        if re.match(r'^https?://', content) and len(content.split()) == 1:
            content = await extract_text_from_url(content)

        # 1. Extract JSON via AI
        job_data = await ai_service.extract_job_details(content)

        # Preserve original link if input was a link
        if re.match(r'^https?://', request.input_text):
            job_data["jobLink"] = request.input_text

        # 2. Append to Sheet
        sheets_service.append_job(request.sheet_url, job_data)

        return {"status": "success", "data": job_data}
    except ValueError as e:
        # Known, user-facing errors (bad sheet URL, permissions, etc.)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def get_jobs(sheet_url: str = Query(..., description="The Google Sheet URL")):
    sheet_url = sheet_url.strip()
    if not sheet_url:
        raise HTTPException(status_code=400, detail="sheet_url cannot be empty")
    try:
        jobs = sheets_service.get_latest_jobs(sheet_url)
        return {"status": "success", "data": jobs}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)