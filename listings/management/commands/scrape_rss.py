from time import strftime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now
from django.db import IntegrityError

from listings.models import Listing

import feedparser


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

        rss_entries = feedparser.parse(settings.JOBS_RSS_FEED_URL)

        processed_count = 0
        for entry in rss_entries.entries:
            processed_count += 1
            if max_records and processed_count > max_records:
                break

            dol_id = str(entry.link).replace("http://seasonaljobs.dol.gov/jobs/", "")
            pub_date = strftime("%Y-%m-%d", entry.published_parsed)
            if not dol_id:
                self.stdout.write(
                    self.style.WARNING(f"Invalid entry with link {entry.link}")
                )
                continue

            defaults = {
                "link": entry.link,
                "title": entry.title,
                "description": entry.description,
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
                            f"{processed_count} skipped updating entry with title {entry.title} and id {dol_id}"
                        )
                    )
                    continue

            operation = "Created" if _ else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{processed_count} - {operation} entry with title {entry.title} and id {dol_id}"
                )
            )
