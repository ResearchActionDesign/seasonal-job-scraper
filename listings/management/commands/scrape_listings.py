import random

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.base import ContentFile

from listings.models import Listing

import requests
import rollbar


class Command(BaseCommand):
    help = "Scrape data from SeasonalJobs RSS feed in to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            type=int,
            help="Max number of entries to process, defaults to 1",
            default=10,
        )

    def handle(self, *args, **options):
        if not (settings.JOBS_API_URL and settings.JOB_ORDER_BASE_URL):
            raise CommandError("JOBS_API_URL and JOB_ORDER_BASE_URL must be set")
        if not settings.JOBS_API_KEY:
            raise CommandError("Jobs API Key must be set")

        max_records = options.get("max", None)

        unscraped_listings = Listing.objects.filter(scraped=False).order_by(
            "-last_seen"
        )[:max_records]

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
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if api_response.status_code != 200:
                msg = f"API call failed for listing, status code {api_response.status_code}"
                rollbar.report_message(
                    msg,
                    "error",
                    extra_data={
                        "dol_id": listing.dol_id,
                    },
                )
                self.stdout.write(self.style.ERROR(msg))
                continue

            try:
                scraped_data = api_response.json()["value"][0]
            except ValueError:
                msg = f"Invalid JSON"
                self.stdout.write(self.style.ERROR(msg))
                rollbar.report_message(
                    msg,
                    "error",
                    extra_data={"dol_id": listing.dol_id, "response": api_response},
                )
                continue

            if scraped_data["case_number"] != listing.dol_id:
                msg = f"Case number mismatch between scraped data for DOL ID {listing.dol_id}. Scraped URL {settings.JOBS_API_URL}"
                self.stdout.write(self.style.ERROR(msg))
            else:
                listing.scraped = True
                listing.scraped_data = scraped_data
                listing.clean()
                listing.save()
                scraped_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{scraped_count} - Saved data for listing ID {listing.dol_id}"
                    )
                )

            if listing.pdf:
                continue

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
            }
            pdf_url = f"{settings.JOB_ORDER_BASE_URL}{listing.dol_id}"
            job_order_pdf = requests.get(
                pdf_url,
                headers=headers,
                timeout=30,
            )

            if (
                job_order_pdf.status_code in (200, 301)
                and job_order_pdf.url != "https://seasonaljobs.dol.gov/system/404"
            ):
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
                # We want to track in rollbar if there's a spike in this error because maybe then
                # PDF scraping is broken entirely, but don't need to track every single occurance,
                # so throttling to only log 1/10 of the occurences.
                if random.randint(0, 10) == 0:
                    rollbar.report_message(
                        "Failed job order PDF request for listing ID",
                        "warning",
                        extra_data={
                            "dol_id": listing.dol_id,
                            "pdf_request": job_order_pdf,
                            "pdf_url": pdf_url,
                        },
                    )
                self.stdout.write(
                    self.style.WARNING(
                        f"{scraped_count} - Failed job order PDF request for listing ID {listing.dol_id}, url {pdf_url}"
                    )
                )
