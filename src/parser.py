"""Parser for ZwiftInsider Climb Portal schedule HTML."""

import re
from datetime import date, datetime
from typing import List, Optional
from bs4 import BeautifulSoup

from .models import ClimbEvent

CATEGORY_INFO = {
    "366": {
        "name": "Climb of the Month",
        "world": "France",
    },
    "370": {
        "name": "Climb of the Week",
        "world": "France",
    },
    "363": {
        "name": "Daily Climb",
        "world": "Watopia",
    },
    "364": {
        "name": "Daily Climb",
        "world": "Watopia",
    },
    "365": {
        "name": "Daily Climb",
        "world": "Watopia",
    },
}

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_schedule_html(html_content: str, default_year: Optional[int] = None, default_month: Optional[int] = None) -> List[ClimbEvent]:
    """
    Parses Spiffy Calendar HTML from ZwiftInsider into ClimbEvent objects.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Determine Year and Month from calendar heading
    month_td = soup.find("td", class_="calendar-month")
    year = default_year
    month = default_month

    if month_td and month_td.text.strip():
        heading_text = month_td.text.strip() # e.g. "September 2026"
        try:
            dt = datetime.strptime(heading_text, "%B %Y")
            year = dt.year
            month = dt.month
        except ValueError:
            pass

    if year is None or month is None:
        today = date.today()
        year = year or today.year
        month = month or today.month

    # 2. Extract day cells
    # Cells with dates typically have class 'day-with-date'
    day_cells = soup.find_all("td", class_=lambda c: c and "day-with-date" in c)
    events: List[ClimbEvent] = []

    for cell in day_cells:
        # Day number
        day_num_elem = cell.find("span", class_=lambda c: c and "day-number" in c)
        if not day_num_elem:
            # Fallback: check class 'spiffy-day-XX'
            day_match = re.search(r"spiffy-day-(\d+)", " ".join(cell.get("class", [])))
            if day_match:
                day = int(day_match.group(1))
            else:
                continue
        else:
            try:
                day = int(day_num_elem.text.strip())
            except ValueError:
                continue

        event_date = date(year, month, day)

        # Find all event items (span with class containing 'calnk')
        event_spans = cell.find_all("span", class_=lambda c: c and "calnk" in c and "category_" in c)

        for sp in event_spans:
            classes = sp.get("class", [])
            cat_id = ""
            for cls in classes:
                m = re.match(r"category_(\d+)", cls)
                if m:
                    cat_id = m.group(1)
                    break

            # Find title element
            title_elem = sp.find("span", class_="spiffy-title")
            raw_title = title_elem.text.strip() if title_elem else ""
            if not raw_title:
                continue

            # Check if there is a link
            link_elem = sp.find("a", href=True)
            url = link_elem["href"].strip() if link_elem else ""

            # Check for extra info such as '(500 XP)' in title
            extra_info = ""
            xp_match = re.search(r"\(([^)]*XP)\)", raw_title)
            if xp_match:
                extra_info = xp_match.group(1).strip()
                # Clean title
                clean_title = re.sub(r"\s*\([^)]*XP\)", "", raw_title).strip()
            else:
                clean_title = raw_title

            info = CATEGORY_INFO.get(cat_id, {
                "name": "Climb Portal",
                "world": "Zwift",
            })

            event = ClimbEvent(
                date=event_date,
                climb_name=clean_title,
                category_id=cat_id or "default",
                category_name=info["name"],
                world=info["world"],
                url=url,
                extra_info=extra_info
            )
            events.append(event)

    # Sort events chronologically, then by category
    events.sort(key=lambda e: (e.date, e.category_id))
    return events


def extract_month_links(html_content: str) -> dict:
    """
    Extracts previous and next month URL parameters from the calendar heading.
    Returns e.g. {'prev': '/climb-portal-schedule/?grid-list-toggle=grid&month=aug&yr=2026', 'next': ...}
    """
    soup = BeautifulSoup(html_content, "html.parser")
    result = {}
    prev_a = soup.find("td", class_="calendar-prev")
    if prev_a and prev_a.find("a"):
        result["prev"] = prev_a.find("a").get("href", "")

    next_a = soup.find("td", class_="calendar-next")
    if next_a and next_a.find("a"):
        result["next"] = next_a.find("a").get("href", "")

    return result
