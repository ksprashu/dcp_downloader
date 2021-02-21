"""This module will read in a list of emails IDs from a file
and parse the contained solution links and save it in a file.
"""

from typing import Sequence
from typing import Dict

from absl import app
from absl import flags
from absl import logging

import dcp_service
import download_helper

_BATCH_SIZE = flags.DEFINE_integer(
    'batch_size', 0,
    'Maximum items to process in a given run'
)


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')

    run_data = download_helper.get_run_data()
    emails = run_data.get('emails', [])
    problems = run_data.get('problems', {})

    assert emails, "Please download emails before proceeding!"

    new_emails = {email_id:None for email_id,sub in emails.items() if not sub}
    
    batch_size = email_count = len(new_emails)
    problem_count = len(problems)

    if _BATCH_SIZE.value:
        batch_size = _BATCH_SIZE.value

    logging.info('Processing %d / %d emails',
        batch_size, email_count)    

    gmail_svc = download_helper.init_and_get_gmail_service()
    dcp_svc = dcp_service.DCP_Service(gmail_svc)
    new_emails, links = dcp_svc.get_subject_and_links(new_emails, batch_size)
    problems = dcp_svc.collect_problem_difficulty(new_emails, problems)

    # update data file only if emails were processed
    has_changes = False
    if links:
        has_changes = True
        prev_links = run_data.get('links', [])
        links.update(prev_links)
        run_data['links'] = list(links)

    if len(problems) != problem_count:
        has_changes = True        
        run_data['problems'] = problems

    if has_changes:
        emails = collect_all_emails(new_emails, emails)
        run_data['emails'] = emails
        download_helper.save_run_data(run_data)

    logging.info('Completed!')


def collect_all_emails(
    new_emails: Dict[str, str],
    emails: Dict[str, str]) -> Dict[str, str]:
    """Collects updates from new emails into old emails.

    Args:
        new_emails: The new emails that were updated
        emails: The list of emails from run state data

    Returns:
        A dictionary of emails id and subjects
    """

    logging.info('Collecting all email subjects')

    for email_id, subject in new_emails.items():
        emails[email_id] = subject

    return emails


if __name__ == '__main__':
    app.run(main)