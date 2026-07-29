from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from services.scraper import extract_text_from_url
from services.ai import AIService
from services.sheets import SheetsService
import re
import logging
import traceback

load_dotenv()

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="AI Job Tracker MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

        if re.match(r'^https?://', content) and len(content.split()) == 1:
            content = await extract_text_from_url(content)

        job_data = await ai_service.extract_job_details(content)

        if re.match(r'^https?://', request.input_text):
            job_data["jobLink"] = request.input_text

        sheets_service.append_job(request.sheet_url, job_data)

        return {"status": "success", "data": job_data}
    except ValueError as e:
        logger.warning(f"Handled error in /api/jobs: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unhandled error in /api/jobs: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


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
        logger.error(f"Unhandled error in GET /api/jobs: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)