import os
import django


def get_stats():
    django.setup()

    from listings.models import Listing

    listing_count = Listing.objects.count()
    listing_unscraped = Listing.objects.filter(scraped=False).count()

    return {
        "listings": listing_count,
        "unscraped": listing_unscraped,
    }


def lambda_handler(event, context):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobscraper.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if "command" in event and event["command"] in [
        "scrape_rss",
        "scrape_listings",
        "export_listings",
    ]:
        extra_args = event.get("args", [])
        execute_from_command_line(["", event["command"]] + extra_args)

    return get_stats()
