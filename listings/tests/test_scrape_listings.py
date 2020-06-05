from io import StringIO
import time
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone

from listings.models import Listing, StaticValue


class FakeResponse(object):
    # default response attributes
    status_code = 200
    content = "Some content"

    def json(self):
        return {"value": {"a_key": "a value"}}

    def invalid_json(self):
        raise ValueError


class TestScrapeListings(TestCase):
    def setUp(self):
        # currently just creates 1 listing
        for i in range(1, 2):
            Listing.objects.create(
                dol_id=f"H-{i}",
                link=f"http://seasonaljobs.dol.gov/jobs/H-{i}",
                title=f"Test title #{i}",
                description="Test description",
                pub_date=timezone.now(),
            )

    def test_fails_on_invalid_status_code(self):
        with patch("requests.post") as mock_request_post:
            mock_request_post.return_value = FakeResponse()
            mock_request_post.return_value.status_code = 403
            out = StringIO()
            call_command("scrape_listings", stdout=out)
            mock_request_post.assert_called_once()
            self.assertEqual(Listing.objects.filter(scraped=True).count(), 0)
            self.assertIn("403", out.getvalue())

    def test_fails_on_invalid_json(self):
        with patch("requests.post") as mock_request_post:
            mock_request_post.return_value = FakeResponse()
            mock_request_post.return_value.json = (
                mock_request_post.return_value.invalid_json
            )
            out = StringIO()
            call_command("scrape_listings", stdout=out, max=1)
            mock_request_post.assert_called_once()
            self.assertEqual(Listing.objects.filter(scraped=True).count(), 0)
            self.assertIn("Invalid JSON", out.getvalue())

    def test_successfully_scrapes_one_listing(self):
        with patch("requests.post") as mock_request_post, patch(
            "requests.get"
        ) as mock_request_get:
            mock_request_post.return_value = FakeResponse()
            mock_request_get.return_value = FakeResponse()
            out = StringIO()
            call_command("scrape_listings", stdout=out, max=1)
            mock_request_post.assert_called_once()
            mock_request_get.assert_called_once()
            self.assertIn("H-1", out.getvalue())
            self.assertEqual(Listing.objects.filter(scraped=True).count(), 1)
            l = Listing.objects.get(dol_id="H-1")
            self.assertTrue(l.scraped)
            self.assertIn("a_key", l.scraped_data)
            self.assertEqual(l.scraped_data["a_key"], "a value")

    def test_successfully_saves_pdf(self):
        # TODO
        pass
