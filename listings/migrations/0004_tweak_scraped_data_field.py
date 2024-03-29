# Generated by Django 3.1a1 on 2020-06-09 09:03

from django.db import migrations


def unwrap_data(apps, schema_editor):
    Listing = apps.get_model("listings", "Listing")
    listings_to_unwrap = Listing.objects.filter(scraped=True)

    for l in listings_to_unwrap:
        if not isinstance(l.scraped_data, dict) and len(l.scraped_data) == 1:
            l.scraped_data = l.scraped_data[0]
            l.save()


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0003_auto_20200609_0804"),
    ]

    operations = [migrations.RunPython(unwrap_data)]
