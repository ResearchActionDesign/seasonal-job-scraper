import csv
import json
from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.dropbox import DropBoxStorage


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

    if settings.DROPBOX_OAUTH2_TOKEN and len(settings.DROPBOX_OAUTH2_TOKEN):
        dropbox = DropBoxStorage()
        with default_storage.open(f"exports/{filename}", "rb") as input_file:
            dropbox.save(f"Seasonal Job Exports/{filename}", input_file)


def export_listings_json(filename, listings):
    if settings.DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
        import os

        basepath = os.path.join(settings.MEDIA_ROOT, "exports")
        if not os.path.exists(basepath):
            os.makedirs(basepath)

    with default_storage.open(f"exports/{filename}", "w") as f:
        f.write("[")
        for listing in listings:
            json.dump(listing, f, default=str)
            f.write(",")
        f.write("]")

    if settings.DROPBOX_OAUTH2_TOKEN and len(settings.DROPBOX_OAUTH2_TOKEN):
        dropbox = DropBoxStorage()
        with default_storage.open(f"exports/{filename}", "rb") as input_file:
            dropbox.save(f"Seasonal Job Exports/{filename}", input_file)
