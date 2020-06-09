import csv


def export_listings_csv(filepath, fieldnames, listings):
    with open(filepath, "w") as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(listings)
