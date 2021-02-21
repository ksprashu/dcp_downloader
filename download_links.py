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
    
    batch_size = email_count = len(emails)
    problem_count = len(problems)

    if _BATCH_SIZE.value:
        batch_size = _BATCH_SIZE.value

    logging.info('Processing %d / %d emails',
        batch_size, email_count)

    new_emails, links = get_subject_and_links(emails, batch_size)
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
        run_data['emails'] = emails
        download_helper.save_run_data(run_data)

    logging.info('Completed!')


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

        print(emails[email_id])
        diff_match = re.search(r'\[.+\]', emails[email_id])
        prob_match = re.search(r'#\d+', emails[email_id])

        if diff_match and prob_match:
            difficulty = diff_match.group()
            problem_id = prob_match.group()

            if problem_id not in problems:
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

    logging.info('Fetching and Processing all emails')

    gmail_svc = download_helper.init_and_get_gmail_service()
    dcp_svc = dcp_service.DCP_Service(gmail_svc)

    links = []

    for ix, id in enumerate(emails.keys()):
        if emails[id]:
            pass

        if ix >= batch_size:
            break

        try:
            subject, message = dcp_svc.get_text_message(id)
        except dcp_service.InvalidMessageError:
            logging.error('Skipping message %s; identifier not found', id)
        except dcp_service.TooManyTextParts:
            logging.error('Skipping message %s; unsupported message format', id)
        except gmail_service.ReadTimeoutError:
            logging.warning('Timeout error, will process the message %s again', id)

        emails[id] = subject
        new_links = dcp_svc.get_solution_links_from_text(message)
        links.extend(new_links)

    links = set(links)
    logging.info('Fetched %d links', len(links))

    return emails, links


if __name__ == '__main__':
    app.run(main)