import unittest
from datetime import date
from src.models import ClimbEvent
from src.ical_builder import generate_icalendar


class TestICalBuilder(unittest.TestCase):

    def setUp(self):
        self.events = [
            ClimbEvent(
                date=date(2026, 9, 1),
                climb_name="Col du Galibier (Valloire)",
                category_id="366",
                category_name="Climb of the Month",
                world="France",
                url="https://zwiftinsider.com/portal/col-du-galibier-valloire/",
                extra_info=""
            ),
            ClimbEvent(
                date=date(2026, 9, 1),
                climb_name="Cipressa",
                category_id="363",
                category_name="Daily Climb",
                world="Watopia",
                url="https://zwiftinsider.com/portal/cipressa/",
                extra_info=""
            ),
            ClimbEvent(
                date=date(2026, 9, 1),
                climb_name="Col de Peyresourde (Avajan)",
                category_id="370",
                category_name="Climb of the Week",
                world="France",
                url="https://zwiftinsider.com/portal/col-de-peyresourde-avajan/",
                extra_info="500 XP"
            ),
        ]

    def test_individual_mode(self):
        ical_bytes = generate_icalendar(self.events, mode="individual")
        content = ical_bytes.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("END:VCALENDAR", content)
        # Should have 3 VEVENTs
        self.assertEqual(content.count("BEGIN:VEVENT"), 3)
        self.assertIn("SUMMARY:[Zwift Climb] Cipressa - Daily Climb (Watopia)", content)
        self.assertIn("500 XP", content)
        self.assertIn("DTSTART:20260901", content)
        self.assertIn("DTEND:20260902", content)

    def test_consolidated_mode(self):
        ical_bytes = generate_icalendar(self.events, mode="consolidated")
        content = ical_bytes.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", content)
        # Should have 1 VEVENT
        self.assertEqual(content.count("BEGIN:VEVENT"), 1)
        self.assertIn("[Zwift Climb Portal]", content)
        self.assertIn("Col du Galibier (Valloire)", content)
        self.assertIn("Cipressa", content)
        self.assertIn("Col de Peyresourde (Avajan)", content)


if __name__ == "__main__":
    unittest.main()
