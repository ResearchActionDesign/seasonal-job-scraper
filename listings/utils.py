import csv
from django.conf import settings
from django.core.files.storage import default_storage


def export_listings_csv(filename, fieldnames, listings):
    if settings.DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
        import os

        basepath = os.path.join(settings.MEDIA_ROOT, "exports")
        if not os.path.exists(basepath):
            os.makedirs(basepath)

    with default_storage.open(f"exports/{filename}", "w") as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(listings)
