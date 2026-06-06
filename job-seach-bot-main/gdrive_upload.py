"""
gdrive_upload.py — Uploads/updates job_tracker.xlsx to Google Drive
"""

import os
import json
from dotenv import load_dotenv
load_dotenv()

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES         = ["https://www.googleapis.com/auth/drive"]
TRACKER_FILE   = "job_tracker.xlsx"
DRIVE_FILENAME = "Job Tracker"


def _get_service():
    if os.path.exists("service_account.json"):
        creds = service_account.Credentials.from_service_account_file(
            "service_account.json", scopes=SCOPES
        )
        print("[gdrive] Using service_account.json")
    else:
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sa_json:
            raise Exception(
                "No Google credentials found — "
                "add service_account.json locally or set "
                "GOOGLE_SERVICE_ACCOUNT_JSON env var on Railway"
            )
        info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        print("[gdrive] Using GOOGLE_SERVICE_ACCOUNT_JSON env var")
    return build("drive", "v3", credentials=creds)


def _find_existing_file(service, folder_id: str) -> str | None:
    # Check with .xlsx extension
    results = service.files().list(
        q=f"name='Job Tracker.xlsx' and '{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    # Check without extension (Drive sometimes strips it)
    results2 = service.files().list(
        q=f"name='Job Tracker' and '{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    files2 = results2.get("files", [])
    return files2[0]["id"] if files2 else None


def upload_to_drive() -> None:
    """Upload job_tracker.xlsx to Google Drive, overwriting if it already exists."""
    if not os.path.exists(TRACKER_FILE):
        print("[gdrive] No tracker file to upload yet.")
        return

    folder_id = os.getenv("GDRIVE_FOLDER_ID", "")
    if not folder_id:
        print("[gdrive] GDRIVE_FOLDER_ID not set — skipping upload.")
        return

    try:
        service = _get_service()
        media = MediaFileUpload(
            TRACKER_FILE,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=False,
        )

        existing_id = _find_existing_file(service, folder_id)

        if existing_id:
            service.files().update(
                fileId=existing_id,
                media_body=media,
            ).execute()
            print(f"[gdrive] ✓ Updated '{DRIVE_FILENAME}' in Drive")
        else:
            metadata = {
                "name": DRIVE_FILENAME,
                "parents": [folder_id],
            }
            service.files().create(
                body=metadata,
                media_body=media,
                fields="id",
            ).execute()
            print(f"[gdrive] ✓ Created '{DRIVE_FILENAME}' in Drive")

    except Exception as e:
        print(f"[gdrive] ✗ Upload failed: {e}")


if __name__ == "__main__":
    upload_to_drive()