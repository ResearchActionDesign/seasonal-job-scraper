from datetime import timedelta, date

from django.core.management.base import BaseCommand

from listings.models import Listing
from listings.utils import export_listings_csv, export_listings_json


def listing_to_row(listing, fieldnames):
    non_scraped_fields_base = [
        "dol_id",
        "job_title",
        "job_description",
        "last_seen",
        "first_seen",
        "pub_date",
        "is_active",
        "job_order_pdf",
    ]

    non_scraped_data = {
        "dol_id": listing.dol_id,
        "job_title": listing.title,
        "job_description": listing.description,
        "last_seen": listing.last_seen,
        "first_seen": listing.first_seen,
        "pub_date": listing.pub_date,
        "is_active": (listing.last_seen >= date.today() - timedelta(days=1)),
        "job_order_pdf": listing.pdf.url if listing.pdf else "",
    }

    return {
        field: (
            non_scraped_data[field]
            if field in non_scraped_fields_base
            else (listing.scraped_data[field] if listing.scraped_data else "")
        )
        for field in fieldnames
    }


def listings_to_rows(listings, fieldnames):
    for listing in listings:
        yield listing_to_row(listing, fieldnames)
    return


class Command(BaseCommand):
    help = "Export seasonal jobs listings to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--last",
            choices=["year", "month", "week", "day"],
            help="Optional - last seen date range to export (last year, last month, last week, last day). Defaults to all time. Last week and last day are inclusive of today, others are exclusive.",
        )
        parser.add_argument(
            "--drupal",
            action="store_true",
            help="Export specifically to the jobscraper_listings.csv file in CSV format for Drupal import",
        )
        parser.add_argument("--json", action="store_true", help="Export to JSON format")

    def handle(self, *args, **options):
        listings_query = Listing.objects.all()

        last_string = ""  # to be added into filename
        today = date.today()
        file_extension = "csv"

        if options["drupal"]:
            listings_query = listings_query.filter(
                last_seen__gte=today - timedelta(days=1), scraped=True
            )

        if options["json"]:
            file_extension = "json"

        if options["last"]:
            if options["last"] == "day":
                listings_query = listings_query.filter(
                    last_seen__gte=today - timedelta(days=1)
                )
                last_string = "--last-day"
            if options["last"] == "week":
                listings_query = listings_query.filter(
                    last_seen__gte=today - timedelta(days=7)
                )
                last_string = "--last-week"
            elif options["last"] == "month":
                if today.month == 1:
                    listings_query = listings_query.filter(
                        last_seen__year=today.year - 1, last_seen__month=12
                    )
                else:
                    listings_query = listings_query.filter(
                        last_seen__year=today.year, last_seen__month=today.month - 1
                    )
                last_string = "--last-month"
            elif options["last"] == "year":
                listings_query = listings_query.filter(last_seen__year=today.year - 1)
                last_string = "--last-year"

        fieldnames = [
            "dol_id",
            "job_title",
            "pub_date",
            "first_seen",
            "last_seen",
            "is_active",
            "job_order_pdf",
            "job_description",
            "crop",
            "job_duties",
            "work_hour_num_basic",
            "total_positions",
            "basic_rate_to",
            "basic_rate_from",
            "overtime_rate_to",
            "overtime_rate_from",
            "full_time",
            "hourly_work_schedule_am",
            "hourly_work_schedule_pm",
            "begin_date",
            "end_date",
            "emp_experience_reqd",
            "emp_exp_num_months",
            "special_req",
            "training_req",
            "num_months_training",
            "education_level",
            "name_reqd_training",
            "pay_range_desc",
            "employer_business_name",
            "employer_trade_name",
            "employer_city",
            "employer_state",
            "employer_zip",
            "employer_phone",
            "employer_phone_ext",
            "employer_email",
            "naic_id",
            "naic_description",
            "visa_class",
            "worksite_locations",
            "worksite_address",
            "add_wage_info",
            "worksite_address_alt",
            "worksite_city",
            "worksite_state",
            "worksite_zip",
            "accepted_date",
            "affirmed_date",
            "soc_code_id",
            "soc_title",
            "soc_description",
            "coord",
            "job_order_exists",
            "apply_email",
            "apply_phone",
            "apply_url",
            "oflc_cms",
            "case_id",
            "case_status",
            "active",
            "document_available",
            "case_number",
            "job_order_id",
        ]

        filename = f"job-listings{last_string}--{date.today()}.{file_extension}"
        if options["drupal"]:
            filename = f"jobscraper_listings.{file_extension}"

        if options["json"]:
            export_listings_json(filename, listings_to_rows(listings_query, fieldnames))

        else:
            export_listings_csv(
                filename, fieldnames, listings_to_rows(listings_query, fieldnames)
            )
