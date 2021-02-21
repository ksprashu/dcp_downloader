"""This module will read in a list of emails IDs from a file
and parse the contained solution links and save it in a file.
"""

from typing import Sequence
from typing import Tuple
from typing import Dict
from typing import Set

from absl import app
from absl import flags
from absl import logging

import dcp_service
import download_helper
import gmail_service

import re

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

    new_emails, links = get_subject_and_links(new_emails, batch_size)
    problems = collect_problem_difficulty(new_emails, problems)

    # update data file only if emails were processed
    change = False
    if links:
        change = True
        prev_links = run_data.get('links', [])
        links.update(prev_links)
        run_data['links'] = list(links)

    if len(problems) != problem_count:
        change = True        
        run_data['problems'] = problems

    if change:
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


def collect_problem_difficulty(emails: Dict[str, str], problems: Dict[int, str]) \
    -> Dict[int, str]:
    """Returns the difficulty for each problem from the emails.

    The subject of each email contains the problem number
    and difficulty of the problem. This is parsed and returned.

    Args:
        emails: The email dictionary with email id and subject
        problems: The problem dictionary with problem id and difficulty 
        
    Return:
        A dictionary of problem ids and difficulties
    """

    logging.info('Fetching problem difficulty from subjects')

    for email_id in emails:
        if not emails[email_id]:
            continue

        diff_match = re.search(r'\[.+\]', emails[email_id])
        prob_match = re.search(r'#\d+', emails[email_id])

        if not prob_match:
            continue
        else:
            problem_id = int(re.sub('#', '', prob_match.group()))
        
        if diff_match:
            difficulty = re.sub(r'[\[\]]', '', diff_match.group())
        else:
            difficulty = 'Easy'

        if problem_id not in problems:
            logging.info('Adding problem id %d with difficulty %s',
                problem_id, difficulty)
            problems[problem_id] = difficulty

    return problems


def get_subject_and_links(emails: Dict[str, str], batch_size: int) \
    -> Tuple[Dict[str, str], Set[str]]:
    """Fetches content of all emails.

    Args:
        emails: dictionary of email ids and fetch status
        batch_size: number of emails to process

    Returns:
        Tuple of emails with subjects and solution links from the email content
    """

    logging.info('Fetching and Processing emails')

    gmail_svc = download_helper.init_and_get_gmail_service()
    dcp_svc = dcp_service.DCP_Service(gmail_svc)

    links = []
    new_emails = {}

    for ix, email_id in enumerate(emails.keys()):
        if ix >= batch_size:
            break

        try:
            subject, message = dcp_svc.get_text_message(email_id)
            ix = ix + 1

            new_emails[email_id] = subject
            
            if message:
                new_links = dcp_svc.get_solution_links_from_text(message)
                links.extend(new_links)

        except dcp_service.InvalidMessageError:
            logging.error('Skipping message %s; identifier not found', email_id)
        except dcp_service.TooManyTextParts:
            logging.error('Skipping message %s; unsupported message format', email_id)
        except gmail_service.ReadTimeoutError:
            logging.warning('Timeout error, will process the message %s again', email_id)

    links = set(links)
    logging.info('Processed %d emails', len(new_emails))
    logging.info('Fetched %d links', len(links))

    return new_emails, links


if __name__ == '__main__':
    app.run(main)