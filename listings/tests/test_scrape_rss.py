from io import StringIO
import time
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command

from listings.models import Listing, StaticValue


class TestScrapeRSS(TestCase):
    def test_fails_on_bozo_error(self):
        with patch("feedparser.parse") as mock_parse:
            mock_parse.return_value = {"bozo": 1, "bozo_exception": "Test exception"}
            out = StringIO()
            self.assertFalse(call_command("scrape_rss", stdout=out))
            self.assertIn("Error", out.getvalue())
            self.assertIn("Test exception", out.getvalue())
            self.assertEqual(Listing.objects.count(), 0)

    def test_fails_on_invalid_status_code(self):
        with patch("feedparser.parse") as mock_parse:
            mock_parse.return_value = {
                "status": 403,
            }
            out = StringIO()
            call_command("scrape_rss", stdout=out)
            self.assertIn("403", out.getvalue())
            self.assertEqual(Listing.objects.count(), 0)

    def test_successfully_handles_no_new_entries(self):
        with patch("feedparser.parse") as mock_parse:
            mock_parse.return_value = {
                "status": 200,
                "version": "",
            }
            out = StringIO()
            call_command("scrape_rss", stdout=out)
            self.assertIn("no new entries", out.getvalue())
            self.assertEqual(Listing.objects.count(), 0)

    def test_successfully_scrapes_entries(self):
        with patch("feedparser.parse") as mock_parse:
            test_entries = [
                {
                    "link": f"http://seasonaljobs.dol.gov/jobs/H-{n}",
                    "title": f"Test title #{n}",
                    "description": "Test description",
                    "published_parsed": time.localtime(),
                }
                for n in range(1, 6)
            ]
            mock_parse.return_value = {
                "status": 200,
                "version": "test",
                "entries": test_entries,
            }
            out = StringIO()
            call_command("scrape_rss", stdout=out)
            self.assertIn("Test title #1", out.getvalue())
            self.assertIn("Test title #5", out.getvalue())
            self.assertEqual(Listing.objects.count(), 5)

    def test_saves_modified_date_and_etag(self):
        with patch("feedparser.parse") as mock_parse:
            mock_parse.return_value = {
                "status": 200,
                "version": "test",
                "entries": [],
                "etag": "6c132-941-ad7e3080",
                "modified": "Fri, 11 Jun 2012 23:00:34 GMT",
            }
            out = StringIO()
            call_command("scrape_rss", stdout=out)
            self.assertEqual(Listing.objects.count(), 0)
            etag = StaticValue.objects.get(key="jobs_rss__etag")
            modified = StaticValue.objects.get(key="jobs_rss__modified")
            self.assertEqual(etag.value, "6c132-941-ad7e3080")
            self.assertEqual(modified.value, "Fri, 11 Jun 2012 23:00:34 GMT")
