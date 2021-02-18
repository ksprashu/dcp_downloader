"""This module will read in a list of emails IDs from a file
and parse the contained solution links and save it in a file.
"""

from typing import Sequence
from absl import app
from absl import flags
from absl import logging

import os
import pickle

import dcp_service
import download_helper
import gmail_service


_DATA_FILE = flags.DEFINE_string(
    'data_file',
    'data/run_data.pickle', 
    'The path where the run data is saved')
    
# Number of records to process in every run
_BATCH_SIZE = 50


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')

    gmail_svc = download_helper.init_and_get_gmail_service()
    assert gmail_svc

    # Loading the data file
    logging.info('Loading data file')
    run_data = {}
    if os.path.exists(_DATA_FILE.value):
        try:
            with open(_DATA_FILE.value, 'rb') as file:
                run_data = pickle.load(file)
        except OSError:
            logging.exception('Exiting! Unable to load data file.')
            exit()
    else:
        logging.error('No run data file found; Download emails first!')


    email_ids = run_data.get('email_ids', [])
    email_count = len(email_ids)
    logging.info('Processing %d / %d emails',
        _BATCH_SIZE if _BATCH_SIZE < email_count else email_count,
        len(email_ids))

    dcp_svc = dcp_service.DCP_Service(gmail_svc)

    # slice the list only if there are more emails than batch size
    if email_count > _BATCH_SIZE:
        skipped_email_ids = email_ids[_BATCH_SIZE:]
        email_ids = email_ids[:_BATCH_SIZE]
    else:
        skipped_email_ids = []

    # process all emails
    links = []
    for email_id in email_ids:
        message = []
        try:
            message = dcp_svc.get_html_message(email_id)
        except dcp_service.InvalidMessageError:
            logging.warning('Skipping message %s; identifier not found', email_id)
        except dcp_service.TooManyHtmlParts:
            logging.warning('Skipping message %s; unsupported message format', email_id)     
        except gmail_service.ReadTimeoutError:
            logging.error('Timeout error, will process the message %s again', email_id)
            skipped_email_ids.append(email_id)

        if message:
            new_links = dcp_svc.get_solution_links(message)
            links.extend(new_links)

    links = set(links)
    logging.info('Fetched %d links', len(links))

    # update data file only if emails were processed
    if email_ids:
        prev_links = run_data.get('links', [])
        links.update(prev_links)

        # add newly fetched links, and clear processed emails
        run_data['links'] = list(links)
        run_data['email_ids'] = skipped_email_ids

        try:
            logging.info('Writing to data file: %s', _DATA_FILE.value)
            with open(_DATA_FILE.value, 'wb') as file:
                pickle.dump(run_data, file)
        except OSError:
            logging.exception('Error while writing to data file!')
            exit()

    logging.info('Completed!')


if __name__ == '__main__':
    app.run(main)