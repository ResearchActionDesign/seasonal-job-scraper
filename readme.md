# Seasonal Jobs.gov data scraper for CDM

## Local set-up

1. Run `pipenv install`
2. Configure environment variables in `.env` file. You'll need, at a minimum:
    * JOBS_API_KEY = API key for requests to seasonaljobs.dol.gov's Microsoft Search back-end. Can be found by inspecting network requests on an individual job listing in web browser.
 3. Run `pre-commit install` to install pre-commit hooks for Black python formatter.
 4. Run `python manage.py migrate --run-syncdb` to create a local database.
 
 ## Scraper commands
 All of the scraper functionality can be run via Django's `python manage.py ___` command.
 
 * `scrape_rss` - Download the most recent RSS feed of job listings and create/update listing records for each item in the feed.
 * `scrape_listings` - Query API for the data of a single listing, save it to the database, and download PDF of full job listing application and save to wherever local file uploads are stored.
 
 ## Production deployment
 
 The scraper is designed to run as an AWS Lambda function, saving listings to an RDS database and saving PDFs to an S3 bucket.
 The file `lambda_function.py` contains a lambda function handler which essentially passes through commands to the Django management command parser. If no command or an invalid command is set, the lambda handler just returns some basic stats.
 
 In order to run on AWS, the following environment variables need to be set:
 * `AWS_PGPASS` - password for postgres user on RDS instance
 * `AWS_PGHOST` - domain name for RDS instance
 * `USE_AWS` - flag to use AWS, should be set to anything other than `False`
 * `AWS_STORAGE_BUCKET_NAME` - S3 bucket to store job order PDFs in
 
 Additionally, the Lambda function must be in the same VPC as the RDS instance and have a role which has write access to the relevant S3 bucket. Lastly, the VPC needs to have a NAT Gateway in order for the scraper to successfully make outgoing requests. See [this article](https://medium.com/@philippholly/aws-lambda-enable-outgoing-internet-access-within-vpc-8dd250e11e12#.bhx40hq3e) for a full how-to.
 
 ### To deploy to AWS
 * Run `./deploy-lambda.sh` from the console. This command will create a zip file with all project dependencies (from `.venv/../site-packages`), a special AWS Lambda-friendly version of psycopg2 (from `aws_psycopg2` directory) and the project code, and then upload it to AWS as a lambda function.
 
 ### Scheduling on AWS
 Schedule the scraper using Amazon Event Bridge. Event input should be fixed JSON, e.g.:
 ```
{"command": "scrape_rss"}
```
 