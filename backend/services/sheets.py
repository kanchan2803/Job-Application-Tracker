import json
import gspread
import re
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

class SheetsService:
    def __init__(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Check if individual env variables exist (Render production)
        client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
        private_key = os.getenv("GOOGLE_PRIVATE_KEY")
        
        if client_email and private_key:
            # Reconstruct newline characters in private key if needed
            formatted_key = private_key.replace("\\n", "\n")
            
            creds_dict = {
                "type": "service_account",
                "client_email": client_email,
                "private_key": formatted_key,
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            self.credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        else:
            # Local development fallback
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
            self.credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
            
        self.client = gspread.authorize(self.credentials)
    def extract_sheet_id(self, url: str) -> str:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        return match.group(1) if match else None

    def append_job(self, sheet_url: str, job_data: dict):
        sheet_id = self.extract_sheet_id(sheet_url)
        if not sheet_id:
            raise ValueError("Invalid Google Sheets URL")
            
        sheet = self.client.open_by_key(sheet_id).sheet1
        
        # Format matching your requested columns
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"), # Date Saved
            job_data.get("company", ""),
            job_data.get("role", ""),
            job_data.get("location", ""),
            job_data.get("employmentType", ""),
            job_data.get("deadline", ""),
            ", ".join(job_data.get("skills", []) or []),
            job_data.get("experience", ""),
            job_data.get("batch", ""),
            job_data.get("salary", ""),
            job_data.get("jobLink", ""),
            job_data.get("jobID", ""),
            job_data.get("status", "Saved"),
            "", # Referral (Manual)
            "", # Resume Version (Manual)
            job_data.get("notes", ""),
            ""  # Prep Links (Manual)
        ]
        
        sheet.append_row(row)
        return job_data

    def get_latest_jobs(self, sheet_url: str, limit=10):
        sheet_id = self.extract_sheet_id(sheet_url)
        if not sheet_id:
            return []
        sheet = self.client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        return list(reversed(records))[:limit]