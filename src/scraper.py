"""Scraper for fetching Zwift Climb Portal schedule pages from ZwiftInsider."""

import logging
from typing import List, Optional
import requests

from .models import ClimbEvent
from .parser import parse_schedule_html, extract_month_links

logger = logging.getLogger(__name__)

BASE_URL = "https://zwiftinsider.com/climb-portal-schedule/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class ScheduleScraper:
    """Fetches and parses schedule pages from ZwiftInsider."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
        })

    def fetch_page(self, url: str) -> str:
        """Fetches a single page HTML given a full URL."""
        logger.info(f"Fetching URL: {url}")
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def fetch_month(self, month_abbr: Optional[str] = None, year: Optional[int] = None) -> (str, List[ClimbEvent]):
        """
        Fetches schedule for a specific month (e.g. month_abbr='sep', year=2026).
        If both are None, fetches the default/current schedule page.
        """
        if month_abbr and year:
            url = f"{BASE_URL}?grid-list-toggle=grid&month={month_abbr.lower()}&yr={year}"
        else:
            url = BASE_URL

        html = self.fetch_page(url)
        events = parse_schedule_html(html)
        return html, events

    def fetch_multiple_months(self, months_ahead: int = 1) -> List[ClimbEvent]:
        """
        Fetches current month and optionally subsequent months by following the 'next' links.
        months_ahead: 0 = current month only, 1 = current + next month, etc.
        """
        all_events: List[ClimbEvent] = []
        visited_urls = set()

        # Step 1: fetch base page
        current_url = BASE_URL
        for step in range(months_ahead + 1):
            if current_url in visited_urls:
                break
            visited_urls.add(current_url)

            html = self.fetch_page(current_url)
            events = parse_schedule_html(html)
            logger.info(f"Step {step}: parsed {len(events)} events from {current_url}")
            all_events.extend(events)

            if step < months_ahead:
                links = extract_month_links(html)
                next_href = links.get("next")
                if not next_href:
                    logger.warning("No next month link found in calendar.")
                    break
                if next_href.startswith("/"):
                    current_url = f"https://zwiftinsider.com{next_href}"
                elif next_href.startswith("http"):
                    current_url = next_href
                else:
                    current_url = f"https://zwiftinsider.com/{next_href}"

        # Deduplicate events by (date, category_id, climb_name)
        unique_events = {}
        for ev in all_events:
            key = (ev.date, ev.category_id, ev.climb_name)
            unique_events[key] = ev

        sorted_events = sorted(unique_events.values(), key=lambda e: (e.date, e.category_id))
        return sorted_events
