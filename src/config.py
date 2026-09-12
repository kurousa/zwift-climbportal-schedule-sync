"""Configuration management for Zwift Climb Portal Schedule Sync."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    output_ics_path: str = "dist/zwift_climb_portal.ics"
    event_mode: str = "individual"  # "individual" or "consolidated"
    months_ahead: int = 1           # 0 = current month, 1 = current + next month
    calendar_name: str = "Zwift Climb Portal"

    # Google Calendar settings
    google_calendar_id: Optional[str] = None
    google_service_account_file: Optional[str] = None
    google_client_secret_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Loads configuration from environment variables."""
        return cls(
            output_ics_path=os.getenv("OUTPUT_ICS_PATH", "dist/zwift_climb_portal.ics"),
            event_mode=os.getenv("EVENT_MODE", "individual"),
            months_ahead=int(os.getenv("MONTHS_AHEAD", "1")),
            calendar_name=os.getenv("CALENDAR_NAME", "Zwift Climb Portal"),
            google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID"),
            google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            google_client_secret_file=os.getenv("GOOGLE_CLIENT_SECRET_FILE"),
        )
