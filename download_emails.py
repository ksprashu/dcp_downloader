"""This module will download all the relevant email identifiers.

Based on the search term, the emails are searched for and the
resulting emails ids are saved in a file.

When run again, it should be able to retrieve only the newer files
"""

from typing import Sequence

from absl import app
from absl import flags
from absl import logging

import dcp_service
import download_helper

import math
import os
import pickle
import datetime


_DATA_FILE = flags.DEFINE_string(
    'data_file',
    'data/run_data.pickle', 
    'The path where the run data is saved')
    

def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')
    current_timestamp = datetime.datetime.now().timestamp()

    gmail_svc = download_helper.init_and_get_gmail_service()
    assert gmail_svc

    # check if there were previously retrieved emails
    run_data = {}
    logging.info('Loading data file')
    if os.path.exists(_DATA_FILE.value):
        try:
            with open(_DATA_FILE.value, 'rb') as file:
                run_data = pickle.load(file)
        except OSError: 
            logging.exception('Exiting! Unable to load data file.')
            exit()
    else:
        logging.warning('No run data file found')

    last_run_timestamp = run_data.get('last_run_at', 0)
    
    dcp_svc = dcp_service.DCP_Service(gmail_svc)
    email_ids, next_page_token = dcp_svc.get_dcp_messages(
        next_page_token=None,
        timestamp=last_run_timestamp)

    # email_index = 0
    # email_count = len(email_ids)

    # until there is no next page, keep going through the list 
    while next_page_token:
        new_email_ids, next_page_token = \
            dcp_svc.get_dcp_messages(
                next_page_token=next_page_token,
                timestamp=last_run_timestamp)

        if new_email_ids:
            email_ids.extend(new_email_ids)

    logging.info('Fetched %d emails', len(email_ids))

    # save data to file
    run_data['last_run_at'] = math.floor(current_timestamp)

    saved_email_ids = run_data.get('email_ids', [])
    email_ids.extend(saved_email_ids)
    email_ids = list(set(email_ids))
    run_data['email_ids'] = email_ids    

    try:
        
        logging.info('Writing to file: %s', _DATA_FILE.value)
        with open(_DATA_FILE.value, 'wb') as file:
            pickle.dump(run_data, file)
    except OSError:
        logging.exception('Error while writing to file')
        exit()


        # # until there is no next page, keep going through the list 
        # while email_count and next_page_token:

        #     finally:
        #         email_index += 1

        #     if message:
        #         links = dcp_svc.get_solution_links(message)
        #         for link in links:
        #             print(link)

        #         # fetch the next page of results if needed
        #         if email_index >= email_count and next_page_token:
        #             new_email_ids, next_page_token = dcp_svc.get_dcp_messages(
        #                 next_page_token=next_page_token)

        #             email_ids.extend(new_email_ids)
        #             email_count = len(email_ids)

        #     break


    logging.info('Completed!')


if __name__ == '__main__':
    app.run(main)
