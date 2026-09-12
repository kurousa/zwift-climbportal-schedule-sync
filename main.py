#!/usr/bin/env python3
"""CLI Entrypoint for Zwift Climb Portal Schedule Sync."""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.config import Config
from src.scraper import ScheduleScraper
from src.ical_builder import generate_icalendar
from src.gcal_client import GoogleCalendarSync


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Zwift Climb Portal schedule from ZwiftInsider and sync to Google Calendar / iCalendar (.ics)."
    )
    parser.add_argument(
        "-o", "--output",
        default="dist/zwift_climb_portal.ics",
        help="Path to output iCalendar (.ics) file (default: dist/zwift_climb_portal.ics)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["individual", "consolidated"],
        default="individual",
        help="Calendar event mode: 'individual' (3 events/day) or 'consolidated' (1 summary event/day)"
    )
    parser.add_argument(
        "-n", "--months-ahead",
        type=int,
        default=1,
        help="Number of future months to scrape ahead (0 = current month only, 1 = current + next, default: 1)"
    )
    parser.add_argument(
        "--calendar-name",
        default="Zwift Climb Portal",
        help="Calendar title used in the iCalendar feed (default: 'Zwift Climb Portal')"
    )

    # Google Calendar API Options
    parser.add_argument(
        "--sync-gcal",
        action="store_true",
        help="Directly sync events to Google Calendar using Google Calendar API"
    )
    parser.add_argument(
        "--calendar-id",
        help="Target Google Calendar ID (e.g. primary or your_calendar@group.calendar.google.com)"
    )
    parser.add_argument(
        "--service-account",
        help="Path to Google Cloud Service Account credentials JSON file"
    )
    parser.add_argument(
        "--oauth-secret",
        help="Path to Google OAuth 2.0 client secrets JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without actually writing to Google Calendar"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger("main")

    config = Config.from_env()

    output_path = args.output or config.output_ics_path
    mode = args.mode or config.event_mode
    months_ahead = args.months_ahead if args.months_ahead is not None else config.months_ahead
    calendar_name = args.calendar_name or config.calendar_name

    logger.info("Starting Zwift Climb Portal scraper...")
    logger.info(f"Scraping current month + {months_ahead} months ahead...")

    scraper = ScheduleScraper()
    try:
        events = scraper.fetch_multiple_months(months_ahead=months_ahead)
    except Exception as e:
        logger.error(f"Failed to fetch schedule from ZwiftInsider: {e}", exc_info=args.verbose)
        sys.exit(1)

    if not events:
        logger.warning("No events were extracted from the schedule.")
        sys.exit(0)

    logger.info(f"Total events extracted: {len(events)} (Dates: {events[0].date} to {events[-1].date})")

    # 1. Generate iCalendar (.ics)
    if output_path:
        out_dir = Path(output_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        ical_bytes = generate_icalendar(events, mode=mode, calendar_name=calendar_name)
        with open(output_path, "wb") as f:
            f.write(ical_bytes)
        logger.info(f"Successfully generated iCalendar file: {output_path} ({len(ical_bytes):,} bytes)")

    # 2. Google Calendar API Direct Sync (Optional)
    calendar_id = args.calendar_id or config.google_calendar_id
    service_account_file = args.service_account or config.google_service_account_file
    oauth_secret_file = args.oauth_secret or config.google_client_secret_file

    if args.sync_gcal:
        if not calendar_id:
            logger.error("--calendar-id (or GOOGLE_CALENDAR_ID env var) is required for --sync-gcal.")
            sys.exit(1)

        gcal_client = None
        if service_account_file:
            logger.info(f"Authenticating with Service Account: {service_account_file}")
            gcal_client = GoogleCalendarSync.from_service_account(service_account_file)
        elif oauth_secret_file:
            logger.info(f"Authenticating with OAuth secret: {oauth_secret_file}")
            gcal_client = GoogleCalendarSync.from_oauth(oauth_secret_file)
        else:
            logger.error("Either --service-account or --oauth-secret is required for Google Calendar sync.")
            sys.exit(1)

        logger.info(f"Syncing {len(events)} events to Google Calendar '{calendar_id}' (dry_run={args.dry_run})...")
        stats = gcal_client.sync_events(calendar_id, events, dry_run=args.dry_run)
        logger.info(f"Sync completed: Created={stats['created']}, Updated={stats['updated']}, Skipped={stats['skipped']}")

    logger.info("Done!")


if __name__ == "__main__":
    main()
