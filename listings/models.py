from django.db import models
from django.utils import timezone
from django.conf import settings

from dirtyfields import DirtyFieldsMixin


class CreatedModifiedMixin(DirtyFieldsMixin, models.Model):
    class Meta:
        abstract = True

    ENABLE_M2M_CHECK = True
    # Created timestamp
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.created and self.is_dirty():
            delta = timezone.now() - self.created
            # Only save modified flag if more than 10 seconds have passed, in production. Disable in DEBUG for automated testing.
            if settings.DEBUG or delta.days > 0 or delta.seconds > 10:
                self.modified = timezone.now()

        return super().save(*args, **kwargs)


class Listing(CreatedModifiedMixin, models.Model):
    # RSS listing fields
    title = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    description = models.TextField()
    dol_id = models.CharField(max_length=255, unique=True)
    pub_date = models.DateField()
    last_seen = models.DateTimeField(auto_now_add=True)

    # Has this listing been scraped?
    scraped = models.BooleanField(default=False)

    # Full job listing as scraped from SeasonalJobs API
    scraped_data = models.JSONField(null=True)

    # Associated PDF
    pdf = models.FileField(upload_to="job_pdfs/", null=True)


class StaticValue(models.Model):
    """
    Static value storage in the DB for between runs.
    """

    key = models.CharField(max_length=255, primary_key=True)
    value = models.CharField(max_length=255, blank=True)
