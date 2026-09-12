from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ClimbEvent:
    """Represents a single scheduled climb in Zwift Climb Portal."""
    date: date
    climb_name: str
    category_id: str
    category_name: str
    world: str
    url: str = ""
    extra_info: str = ""

    @property
    def uid(self) -> str:
        """Unique ID for iCalendar / Google Calendar deduplication."""
        return f"zwift-climb-{self.date.strftime('%Y%m%d')}-{self.category_id}@climbportal"

    @property
    def event_title(self) -> str:
        """Formatted title for individual calendar event."""
        badge = f" ({self.extra_info})" if self.extra_info else ""
        return f"[Zwift Climb] {self.climb_name}{badge} - {self.category_name} ({self.world})"

    @property
    def event_description(self) -> str:
        """Formatted description for calendar event."""
        lines = [
            f"Zwift Climb Portal: {self.climb_name}",
            f"Type: {self.category_name}",
            f"World: {self.world}",
        ]
        if self.extra_info:
            lines.append(f"Bonus: {self.extra_info}")
        if self.url:
            lines.append(f"More info: {self.url}")
        lines.append("\nSchedule source: https://zwiftinsider.com/climb-portal-schedule/")
        return "\n".join(lines)
