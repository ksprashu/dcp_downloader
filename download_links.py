"""This module will read in a list of emails IDs from a file
and parse the contained solution links and save it in a file.
"""

from typing import Sequence
from absl import app
from absl import flags
from absl import logging

import dcp_service
import download_helper
import gmail_service


# Number of records to process in every run
_BATCH_SIZE = 100


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')

    gmail_svc = download_helper.init_and_get_gmail_service()
    assert gmail_svc

    run_data = download_helper.get_run_data()
    email_ids = run_data.get('email_ids', [])
    email_count = len(email_ids)

    logging.info('Processing %d / %d emails',
        _BATCH_SIZE if _BATCH_SIZE < email_count else email_count,
        len(email_ids))

    dcp_svc = dcp_service.DCP_Service(gmail_svc)

    # # slice the list only if there are more emails than batch size
    # if email_count > _BATCH_SIZE:
    #     skipped_email_ids = email_ids[_BATCH_SIZE:]
    #     email_ids = email_ids[:_BATCH_SIZE]
    # else:
    #     skipped_email_ids = []

    # process all emails
    links = []
    skipped_email_ids = []
    for email_id in email_ids:
        message = []
        try:
            message = dcp_svc.get_text_message(email_id)
        except dcp_service.InvalidMessageError:
            logging.error('Skipping message %s; identifier not found', email_id)
        except dcp_service.TooManyTextParts:
            logging.error('Skipping message %s; unsupported message format', email_id)     
        except gmail_service.ReadTimeoutError:
            logging.warning('Timeout error, will process the message %s again', email_id)
            skipped_email_ids.append(email_id)

        if message:
            new_links = dcp_svc.get_solution_links_from_text(message)
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

        download_helper.save_run_data(run_data)

    logging.info('Completed!')


if __name__ == '__main__':
    app.run(main)