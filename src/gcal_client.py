"""Google Calendar API integration for directly syncing Zwift Climb Portal events."""

import logging
from datetime import timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from .models import ClimbEvent

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarSync:
    """Handles synchronization of ClimbEvents to a Google Calendar via Google Calendar API."""

    def __init__(self, service):
        self.service = service

    @classmethod
    def from_service_account(cls, credentials_path: str):
        """Creates an instance using a Google Cloud service account JSON file."""
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google client libraries not found. "
                "Please run: pip install google-api-python-client google-auth google-auth-oauthlib"
            )
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        service = build("calendar", "v3", credentials=creds)
        return cls(service)

    @classmethod
    def from_oauth(cls, client_secret_path: str, token_path: str = "token.json"):
        """Creates an instance using OAuth 2.0 user credentials (browser flow)."""
        import os
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google client libraries not found. "
                "Please run: pip install google-api-python-client google-auth google-auth-oauthlib"
            )

        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)
        return cls(service)

    def sync_events(self, calendar_id: str, events: List[ClimbEvent], dry_run: bool = False) -> dict:
        """
        Syncs a list of ClimbEvents to the target Google Calendar.
        Prevents duplicates by searching via private extended properties or iCalUID.
        """
        stats = {"created": 0, "updated": 0, "skipped": 0}

        for ev in events:
            # Check if event already exists using private extendedProperties
            query_res = self.service.events().list(
                calendarId=calendar_id,
                privateExtendedProperty=f"uid={ev.uid}",
                maxResults=1
            ).execute()

            existing_items = query_res.get("items", [])

            event_body = {
                "summary": ev.event_title,
                "description": ev.event_description,
                "start": {
                    "date": ev.date.strftime("%Y-%m-%d"),
                },
                "end": {
                    "date": (ev.date + timedelta(days=1)).strftime("%Y-%m-%d"),
                },
                "extendedProperties": {
                    "private": {
                        "uid": ev.uid,
                        "source": "zwift-climbportal-schedule-sync"
                    }
                }
            }

            if existing_items:
                existing_event = existing_items[0]
                event_id = existing_event["id"]
                # Compare fields to check if update is needed
                if (existing_event.get("summary") == event_body["summary"] and
                    existing_event.get("description") == event_body["description"]):
                    logger.debug(f"Skipped (unchanged): {ev.event_title}")
                    stats["skipped"] += 1
                else:
                    if not dry_run:
                        self.service.events().update(
                            calendarId=calendar_id,
                            eventId=event_id,
                            body=event_body
                        ).execute()
                    logger.info(f"Updated: {ev.event_title}")
                    stats["updated"] += 1
            else:
                if not dry_run:
                    self.service.events().insert(
                        calendarId=calendar_id,
                        body=event_body
                    ).execute()
                logger.info(f"Created: {ev.event_title}")
                stats["created"] += 1

        return stats
