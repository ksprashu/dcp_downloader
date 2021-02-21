"""Allow to manually add the missing links into the list of solutions.
"""

from typing import Sequence

from absl import app
from absl import logging

import download_helper

MISSING_LINKS = []

def main(argv: Sequence[str]) -> None:
    del argv

    run_data = download_helper.get_run_data()
    links = run_data.get('links', {})

    if links:
        logging.info('Adding %d links', len(MISSING_LINKS))
        for link in MISSING_LINKS:
            links[link] = None
        run_data['links'] = links
        logging.info('Writing %d links', len(links))
        download_helper.save_run_data(run_data)


if __name__ == "__main__":
    app.run(main)

