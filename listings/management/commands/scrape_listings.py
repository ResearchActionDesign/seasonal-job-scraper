from time import strftime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.db import IntegrityError

from listings.models import Listing

import requests


class Command(BaseCommand):
    help = "Scrape data from SeasonalJobs RSS feed in to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            type=int,
            help="Max number of entries to process, defaults to 1",
            default=1,
        )

    def handle(self, *args, **options):
        if not settings.JOBS_API_URL or not settings.JOB_ORDER_BASE_URL:
            raise CommandError("JOBS_API_URL and JOB_ORDER_BASE_URL must be set")
        if not settings.JOBS_API_KEY:
            raise CommandError("Jobs API Key must be set")

        max_records = options.get("max", None)

        unscraped_listings = Listing.objects.filter(scraped=False)[:max_records]

        if len(unscraped_listings) == 0:
            self.stdout.write(self.style.SUCCESS("No listings left to scrape!"))
            return

        scraped_count = 0
        for listing in unscraped_listings:
            if scraped_count >= max_records:
                break

            payload = {
                "searchFields": "case_number",
                "search": listing.dol_id,
                "top": 1,
            }
            api_response = requests.post(
                settings.JOBS_API_URL,
                json=payload,
                headers={"api-key": settings.JOBS_API_KEY},
                timeout=30,
            )
            if api_response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(
                        f"API call failed for listing ID {listing.dol_id} with status code {api_response.status_code}"
                    )
                )
                continue

            try:
                listing.scraped_data = api_response.json()["value"]
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"Invalid JSON for {listing.dol_id}")
                )
                continue

            listing.scraped = True
            listing.save()
            scraped_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{scraped_count} - Saved data for listing ID {listing.dol_id}"
                )
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:77.0) Gecko/20100101 Firefox/77.0"
            }
            job_order_pdf = requests.get(
                f"{settings.JOB_ORDER_BASE_URL}{listing.dol_id}",
                headers=headers,
                timeout=30,
            )

            if job_order_pdf.status_code in (200, 301):
                listing.pdf = ContentFile(
                    job_order_pdf.content, name=f"{listing.dol_id}.pdf"
                )
                listing.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{scraped_count} - Saved job order PDF for listing ID {listing.dol_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"{scraped_count} - Failed job order PDF request for listing ID {listing.dol_id}"
                    )
                )
