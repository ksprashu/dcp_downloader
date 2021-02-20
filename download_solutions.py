"""This module will download the solutions for new links.

We will first read the list of links from the provided file
and will then fetch the solutions for the files that are not processed
and save them as individual files.

This should process only the newer links.
"""

from typing import Sequence
from absl import app
from absl import flags
from absl import logging

from bs4 import BeautifulSoup

import os
import pickle

import dcp_service
import download_helper
import gmail_service
import requests

# Number of records to process in every run
_BATCH_SIZE = 50


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')
    run_data = download_helper.get_run_data()

    links = run_data.get('links', [])
    for link in links:
        result = requests.get(link)
        print(result.text)
        break

    logging.info('Completed!')


if __name__ == "__main__":
    app.run(main)