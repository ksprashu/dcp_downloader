"""This module will download all the relevant email identifiers.

Based on the search term, the emails are searched for and the
resulting emails ids are saved in a file.

When run again, it should be able to retrieve only the newer files
"""

from typing import Sequence

from absl import app
from absl import flags
from absl import logging

import credential_service
import dcp_service
import gmail_service

import math
import os
import pickle
import datetime


_SCOPES = flags.DEFINE_list(
    'scopes',
    ['https://www.googleapis.com/auth/gmail.readonly'],
    'The scopes to be requested while fetching the token')
_TOKEN_FILE = flags.DEFINE_string(
    'token_file',
    'config/token.pickle', 
    'The path where the token file is saved')
_CRED_FILE = flags.DEFINE_string(
    'credential_file',
    'config/credentials.json',
    'The path to the credential file')
_LINK_FILE = flags.DEFINE_string(
    'link_file',
    'data/links.txt',
    'The file where the links will be stored')
_EMAIL_FILE = flags.DEFINE_string(
    'email_file',
    'data/emails.pickle',
    'The file where the message ids are stored'
)    
_LAST_RUN_FILE = flags.DEFINE_string(
    'last_run_file',
    'data/last_run.pickle', 
    'The path where the last run data is saved')
    

def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')
    current_timestamp = datetime.datetime.now().timestamp()

    # start by getting the credential
    # initialize an oauth flow in case the token is not present
    # or is invalid
    try:
        cred = credential_service.Credential(
            cred_file=_CRED_FILE.value,
            token_file=_TOKEN_FILE.value,
            scopes=_SCOPES.value)
        token = cred.get_token()
    except:
        logging.exception('Exiting! Unable to load Credentials')
        exit()

    # get the gmail service instance
    try:
        gmail_svc = gmail_service.GmailService(token)
        gmail_svc.load_gmail_resource()
    except:
        logging.exception('Exiting! Unable to load the GMail service')
        exit()

    # check if there were previously retrieved emails
    last_run_state = {}
    logging.info('Looking for last run file')
    if os.path.exists(_LAST_RUN_FILE.value):
        try:
            with open(_LAST_RUN_FILE.value, 'rb') as file:
                last_run_state = pickle.load(file)
        except OSError: 
            logging.exception('Exiting! State file is bad!')
            exit()
    else:
        logging.warning('No last run state file present; fetching all emails')

    last_run_timestamp = last_run_state.get('timestamp', 0)
    
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

    # save email ids to file
    try:
        logging.info('Writing to file: %s', _EMAIL_FILE.value)
        with open(_EMAIL_FILE.value, 'wb') as file:
            pickle.dump(email_ids, file)
    except OSError:
        logging.exception('Error while writing to file')
        exit()

    # save last run state
    try:
        last_run_state['timestamp'] = math.floor(current_timestamp)
        with open(_LAST_RUN_FILE.value, 'wb') as file:
            pickle.dump(last_run_state, file)
    except OSError:
        logging.warn('Error while saving run state')


        # # until there is no next page, keep going through the list 
        # while email_count and next_page_token:
        #     try:
        #         message = dcp_svc.get_html_message(email_ids[email_index])
        #     except dcp_service.InvalidMessageError:
        #         logging.warning('Skipping message %s; no message found', email_ids[email_index])
        #     except dcp_service.TooManyHtmlParts:
        #         logging.warning('Skipping message %s; unsupported message format', email_ids[email_index])
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