#!/bin/bash

OLD_PWD=$PWD

rm function.zip
cd $(pipenv --venv)/lib/python3.11/site-packages/ || exit
zip -q -r9 "$OLD_PWD"/function.zip . -x psycopg2/\* -x psycopg2-2.9.9.dist-info/\* || exit
cd "$OLD_PWD"/aws_psycopg2 || exit
zip -q -r9 "$OLD_PWD"/function.zip . -i psycopg2/\* -i psycopg2_binary-2.9.9.dist-info/\* -i psycopg2_binary.libs/\* || exit
cd "$OLD_PWD"
zip -q -r -g function.zip . -i lambda_function.py -i jobscraper/\* -i listings/\* || exit
aws lambda update-function-code --function-name seasonalJobsScrape --zip-file fileb://function.zip --profile cdm
