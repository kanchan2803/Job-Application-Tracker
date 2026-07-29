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

        client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
        private_key = os.getenv("GOOGLE_PRIVATE_KEY")

        if client_email and private_key:
            formatted_key = private_key.replace("\\n", "\n")
            creds_dict = {
                "type": "service_account",
                "client_email": client_email,
                "private_key": formatted_key,
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            self.credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        else:
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
            self.credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)

        self.client = gspread.authorize(self.credentials)

    def extract_sheet_id(self, url: str) -> str:
        if not url:
            return None
        url = url.strip()
        # Handles /d/ID/edit, /d/ID, /d/ID/view, with or without trailing params
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        return match.group(1) if match else None

    def append_job(self, sheet_url: str, job_data: dict):
        if not sheet_url or not sheet_url.strip():
            raise ValueError("Sheet URL is missing")

        sheet_id = self.extract_sheet_id(sheet_url)
        if not sheet_id:
            raise ValueError(
                "Could not read a Sheet ID from that URL. Make sure it looks like "
                "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
            )

        try:
            sheet = self.client.open_by_key(sheet_id).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            raise ValueError("Sheet not found. Double check the URL is correct.")
        except gspread.exceptions.APIError as e:
            raise ValueError(
                f"Google Sheets API error — make sure the sheet is shared with "
                f"the service account email ({e})"
            )

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
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
            "",  # Referral (Manual)
            "",  # Resume Version (Manual)
            job_data.get("notes", ""),
            ""   # Prep Links (Manual)
        ]

        sheet.append_row(row)
        return job_data

    def get_latest_jobs(self, sheet_url: str, limit=10):
        if not sheet_url or not sheet_url.strip():
            raise ValueError("Sheet URL is missing")

        sheet_id = self.extract_sheet_id(sheet_url)
        if not sheet_id:
            raise ValueError("Could not read a Sheet ID from that URL")

        sheet = self.client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        return list(reversed(records))[:limit]