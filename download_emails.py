"""This module will download all the relevant email identifiers.

Based on the search term, the emails are searched for and the
resulting emails ids are saved in a file.

When run again, it should be able to retrieve only the newer files
"""

from typing import Sequence
from typing import Dict

from absl import app
from absl import logging

import dcp_service
import download_helper

import math
import datetime


def get_all_emails(last_run_at: int) -> Sequence[str]:
    """Returns all the emails ids for the provided search terms.

    Args:
        last_run_at: Last email fetch timestamp
    """

    logging.info('fetching the list of all email ids from %s', datetime.datetime.fromtimestamp(last_run_at))

    gmail_svc = download_helper.init_and_get_gmail_service()
    dcp_svc = dcp_service.DCP_Service(gmail_svc)

    email_ids, next_page_token = dcp_svc.get_dcp_messages(
        next_page_token=None,
        timestamp=last_run_at)

    # until there is no next page, keep fetching the messages
    while next_page_token:
        new_email_ids, next_page_token = \
            dcp_svc.get_dcp_messages(
                next_page_token=next_page_token,
                timestamp=last_run_at)

        if new_email_ids:
            email_ids.extend(new_email_ids)

    return email_ids


def collect_all_email_ids(
    new_email_ids: Sequence[str], 
    old_emails: Dict[str, bool]) -> Dict[str, bool]:
    """Returns emails as a dictionary.

    Collects the list of old and new emails and returns
    a single dictionary of email ids

    Args:
        new_emails: A list of email ids
        old_emails: A Dictionary of email ids with a boolean status

    Returns:
        A dictionary of email ids with a boolean status
    """
    logging.info('Collecting new and old email ids into a single dictionary')
    
    old_ids = old_emails.keys()
    new_email_ids = set(new_email_ids) - set(old_ids)
    new_emails = {email_id: False for email_id in new_email_ids}
    new_emails.update(old_emails)
    
    return new_emails


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')
    current_timestamp = datetime.datetime.now().timestamp()

    run_data = download_helper.get_run_data()
    last_run_at = run_data.get('last_email_fetch_at', 0)
    email_ids = get_all_emails(last_run_at)
    email_ids = set(email_ids)
    logging.info('Fetched %d emails', len(email_ids))

    run_data['last_email_fetch_at'] = math.floor(current_timestamp)

    if email_ids:
        old_emails = run_data.get('emails', {})
        all_emails = collect_all_email_ids(new_email_ids=email_ids, old_emails=old_emails)
        all_emails.update(old_emails)
        run_data['emails'] = all_emails

    download_helper.save_run_data(run_data)
    logging.info('Completed!')


if __name__ == '__main__':
    app.run(main)
