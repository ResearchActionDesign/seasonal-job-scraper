from io import StringIO
import time
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.core.management import call_command
from django.utils import timezone

from listings.models import Listing, StaticValue


class TestListingModel(TestCase):
    def test_cleans_url(self):
        test_listing = Listing(scraped_data={"apply_url": "N/A"})
        test_listing.clean()
        self.assertEqual(test_listing.scraped_data["apply_url"], "")
        test_listing.scraped_data["apply_url"] = "https://http:www.twc.state.tx.us"
        test_listing.clean()
        self.assertEqual(
            test_listing.scraped_data["apply_url"], "https://www.twc.state.tx.us"
        )
        test_listing.scraped_data["apply_url"] = "https://test.com"
        test_listing.clean()
        self.assertEqual(test_listing.scraped_data["apply_url"], "https://test.com")
