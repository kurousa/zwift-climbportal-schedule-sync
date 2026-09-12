import os
import unittest
from datetime import date
from src.parser import parse_schedule_html, extract_month_links

TEST_CONTENT_PATH = "/home/takaryo/.gemini/antigravity-ide/brain/2222d811-ce11-4175-949d-1eb79b36b4a7/.system_generated/steps/7/content.md"


class TestParser(unittest.TestCase):

    def test_parse_real_html(self):
        if not os.path.exists(TEST_CONTENT_PATH):
            self.skipTest("Real content file not found.")

        with open(TEST_CONTENT_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        events = parse_schedule_html(html)
        self.assertGreater(len(events), 0)

        # In September 2026 there are 30 days * 3 events = 90 events
        self.assertEqual(len(events), 90)

        # Check day 1
        day1_events = [e for e in events if e.date == date(2026, 9, 1)]
        self.assertEqual(len(day1_events), 3)

        # Check climb of the month
        cotm = next(e for e in day1_events if e.category_name == "Climb of the Month")
        self.assertEqual(cotm.climb_name, "Col du Galibier (Valloire)")
        self.assertEqual(cotm.world, "France")

        # Check daily climb
        daily = next(e for e in day1_events if e.category_name == "Daily Climb")
        self.assertEqual(daily.climb_name, "Cipressa")
        self.assertEqual(daily.world, "Watopia")

        # Check climb of the week with XP
        cotw = next(e for e in day1_events if e.category_name == "Climb of the Week")
        self.assertEqual(cotw.climb_name, "Col de Peyresourde (Avajan)")
        self.assertEqual(cotw.extra_info, "500 XP")

        # Check navigation links
        links = extract_month_links(html)
        self.assertIn("prev", links)
        self.assertIn("next", links)
        self.assertIn("month=oct", links["next"])


if __name__ == "__main__":
    unittest.main()
