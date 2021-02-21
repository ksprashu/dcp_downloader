"""Adjust stored data in case of schema changes.
"""

from typing import Sequence

from absl import app
from absl import logging

import download_helper


def add_str_to_links():

    run_data = download_helper.get_run_data()
    links = run_data.get('links')
    assert type(links) == list, 'Nothing to do, links is not a list'

    logging.info('Adjusting the list of links from %s', type(links))
    new_links = {}
    for link in links:
        new_links[link] = None
    logging.info('Links are adjusted to %s', type(new_links))

    run_data['links'] = new_links
    download_helper.save_run_data(run_data)


def main(argv: Sequence[str]) -> None:
    del argv

    add_str_to_links()


if __name__ == '__main__':
    app.run(main)
