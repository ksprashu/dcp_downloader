#!/usr/bin/env bash

source env/bin/activate
python3 download_emails.py
python3 download_links.py
python3 download_solutions.py

