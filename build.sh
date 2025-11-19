#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python3.11 manage.py collectstatic --noinput

python3.11 manage.py migrate
