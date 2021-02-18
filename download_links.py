"""This module will read in a list of emails IDs from a file
and parse the contained solution links and save it in a file.
"""

from typing import Sequence
from absl import app
from absl import flags
from absl import logging


_LAST_RUN_FILE = flags.DEFINE_string(
    'last_run_file',
    'data/last_run.pickle', 
    'The path where the last run data is saved')

def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')


if __name__ == '__main__':
    app.run(main)