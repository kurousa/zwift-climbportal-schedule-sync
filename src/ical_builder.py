"""iCalendar (.ics) generator for Zwift Climb Portal schedules."""

from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from typing import List, Literal
from icalendar import Calendar, Event, vDate

from .models import ClimbEvent


def generate_icalendar(
    events: List[ClimbEvent],
    mode: Literal["individual", "consolidated"] = "individual",
    calendar_name: str = "Zwift Climb Portal Schedule",
) -> bytes:
    """
    Generates iCalendar (.ics) byte data from a list of ClimbEvents.

    :param events: List of ClimbEvent objects.
    :param mode: 'individual' (3 events per day) or 'consolidated' (1 summary event per day).
    :param calendar_name: Name of the calendar.
    :return: iCalendar file content as bytes.
    """
    cal = Calendar()
    cal.add("prodid", "-//Zwift Climb Portal Schedule Sync//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", calendar_name)
    cal.add("x-wr-caldesc", "Zwift Climb Portal scheduled climbs scraped from ZwiftInsider.")
    cal.add("method", "PUBLISH")

    now = datetime.now(timezone.utc)

    if mode == "individual":
        for ev in events:
            vevent = Event()
            vevent.add("summary", ev.event_title)
            vevent.add("description", ev.event_description)
            vevent.add("dtstamp", now)
            # All-day event: DTSTART is start date, DTEND is start date + 1 day
            vevent.add("dtstart", vDate(ev.date))
            vevent.add("dtend", vDate(ev.date + timedelta(days=1)))
            vevent.add("uid", ev.uid)
            vevent.add("categories", ["Zwift", "Cycling", ev.category_name])
            if ev.url:
                vevent.add("url", ev.url)
            cal.add_component(vevent)

    elif mode == "consolidated":
        # Group by date
        grouped = defaultdict(list)
        for ev in events:
            grouped[ev.date].append(ev)

        for event_date, day_events in sorted(grouped.items()):
            vevent = Event()

            # Titles summary
            climbs_summary = " / ".join(e.climb_name for e in day_events)
            summary = f"[Zwift Climb Portal] {climbs_summary}"

            # Description details
            desc_lines = [f"Zwift Climb Portal - {event_date.strftime('%Y-%m-%d')}"]
            for e in day_events:
                badge = f" ({e.extra_info})" if e.extra_info else ""
                desc_lines.append(f"\n• {e.category_name} ({e.world}):")
                desc_lines.append(f"  {e.climb_name}{badge}")
                if e.url:
                    desc_lines.append(f"  {e.url}")

            desc_lines.append("\nSchedule source: https://zwiftinsider.com/climb-portal-schedule/")

            vevent.add("summary", summary)
            vevent.add("description", "\n".join(desc_lines))
            vevent.add("dtstamp", now)
            vevent.add("dtstart", vDate(event_date))
            vevent.add("dtend", vDate(event_date + timedelta(days=1)))
            vevent.add("uid", f"zwift-climb-consolidated-{event_date.strftime('%Y%m%d')}@climbportal")
            vevent.add("categories", ["Zwift", "Cycling"])
            cal.add_component(vevent)

    return cal.to_ical()
