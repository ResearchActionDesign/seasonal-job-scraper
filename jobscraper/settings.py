"""
Django settings for jobscraper project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def base_dir_join(*args):
    return os.path.join(BASE_DIR, *args)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "fdiqs@2l8@v0l8e-jl96%t)5a^ht0rv8r6vd#rnk6nmwx2s$*("

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = ["listings"]
MIDDLEWARE = []
WSGI_APPLICATION = "jobscraper.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Upload handling
MEDIA_ROOT = base_dir_join("files")

USE_AWS = os.getenv("USE_AWS", os.getenv("AWS_ACCESS_KEY_ID", False))

if USE_AWS and USE_AWS != "False":
    DEBUG = False
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": os.getenv("AWS_PGPASS", ""),
            "HOST": os.getenv("AWS_PGHOST", ""),
            "PORT": "5432",
        }
    }

DROPBOX_OAUTH2_TOKEN = os.getenv("DROPBOX_OAUTH2_TOKEN", "")

# Seasonal jobs specific URLS
JOBS_RSS_FEED_URL = "https://seasonaljobs.dol.gov/job_rss.xml"
JOBS_API_URL = "https://foreign-labor.search.windows.net/indexes/foreign-labor/docs/search?api-version=2017-11-11"
JOB_ORDER_BASE_URL = "https://seasonaljobs.dol.gov/job-order/"
JOBS_API_KEY = os.getenv("JOBS_API_KEY", False)

# Rollbar
ROLLBAR = {
    "access_token": os.getenv("ROLLBAR_ACCESS_TOKEN", ""),
    "environment": "development" if DEBUG else "production",
    "root": BASE_DIR,
}
import rollbar

rollbar.init(**ROLLBAR)
