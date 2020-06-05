from time import strftime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now
from django.db import IntegrityError

from listings.models import Listing, StaticValue

import feedparser

ETAG_KEY = "jobs_rss__etag"
MODIFIED_KEY = "jobs_rss__modified"


class Command(BaseCommand):
    help = "Scrape data from SeasonalJobs RSS feed in to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            nargs=1,
            type=int,
            help="Max number of entries to process, defaults to all",
        )

        parser.add_argument(
            "--skip_update",
            action="store_true",
            help="Skip updating existing records if found?",
        )

    def handle(self, *args, **options):
        if not settings.JOBS_RSS_FEED_URL:
            raise CommandError("RSS feed URL must be set")

        max_records = None
        if options["max"]:
            max_records = options["max"][0]

        update = True
        if "skip_update" in options and options["skip_update"]:
            update = False

        # Check for saved etag and modified keys
        try:
            etag = StaticValue.objects.get(key=ETAG_KEY).value
        except StaticValue.DoesNotExist:
            etag = None

        try:
            modified = StaticValue.objects.get(key=MODIFIED_KEY).value
        except StaticValue.DoesNotExist:
            modified = None

        rss_entries = feedparser.parse(
            settings.JOBS_RSS_FEED_URL, etag=etag, modified=modified
        )

        if rss_entries.get("bozo", False):
            # Error code from feed scraper
            self.stdout.write(
                self.style.ERROR(
                    f"Error pulling RSS Feed {rss_entries.get('bozo_exception', '')}"
                )
            )
            return

        elif rss_entries.get("status", False) not in [200, 301]:
            # Error code from feed scraper
            self.stdout.write(
                self.style.ERROR(
                    f"RSS Feed status code: {rss_entries.get('status', False)}, not 200"
                )
            )
            return

        elif rss_entries.get("version", "") == "":
            self.stdout.write(self.style.SUCCESS(f"RSS fetched, but no new entries"))
            return

        processed_count = 0
        for entry in rss_entries.get("entries", []):
            processed_count += 1
            if max_records and processed_count > max_records:
                break

            dol_id = str(entry.get("link", "")).replace(
                "http://seasonaljobs.dol.gov/jobs/", ""
            )
            pub_date = strftime("%Y-%m-%d", entry.get("published_parsed", ""))
            if not dol_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"Invalid entry with link {entry.get('link', 'N/A')}"
                    )
                )
                continue

            defaults = {
                "link": entry.get("link", ""),
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "pub_date": pub_date,
                "last_seen": now(),
            }
            if update:
                l, _ = Listing.objects.update_or_create(
                    dol_id=dol_id, defaults=defaults
                )

            else:
                _ = True
                try:
                    Listing.objects.create(dol_id=dol_id, **defaults)
                except IntegrityError:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{processed_count} skipped updating entry with title {defaults['title']} and id {dol_id}"
                        )
                    )
                    continue

            operation = "Created" if _ else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{processed_count} - {operation} entry with title {defaults['title']} and id {dol_id}"
                )
            )

        # Assuming scrape was successful, save etag and last_modified.
        if rss_entries.get("etag", False):
            StaticValue.objects.update_or_create(
                key=ETAG_KEY, defaults={"value": rss_entries.get("etag", "")}
            )

        if rss_entries.get("modified", False):
            StaticValue.objects.update_or_create(
                key=MODIFIED_KEY, defaults={"value": rss_entries.get("modified", "")}
            )
