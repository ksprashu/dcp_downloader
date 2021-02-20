"""This module will help check all the downloaded link for any mmissing solutions.
"""

from typing import Sequence

from absl import app
from absl import logging

import download_helper


def main(argv: Sequence[str]) -> None:
    del argv

    run_data = download_helper.get_run_data()

    logging.info('collecting all links')
    links = run_data.get('links')
    questions = []
    for link in links:
        url_part, _ = link.split('?')
        q_num = url_part.split('/')[-1]

        if q_num:
            questions.append(int(q_num))
    
    sorted_questions = sorted(questions)
    min_q = sorted_questions[0]
    max_q = sorted_questions[-1]
    print(f'We have questions from {min_q} to {max_q}')
    print(f'Total questions should be {max_q - min_q + 1}, and we have {len(sorted_questions)}')

    logging.info('Finding missing questions')
    for i in range(min_q, max_q+1):
        if not i in sorted_questions:
            print(f'probem {i} not found')

    logging.info('Finding duplicates')
    last_q = 0
    for q in sorted_questions:
        if q == last_q:
            print('Duplicate Question - %d' % q)
        
        last_q  = q

        
if __name__ == "__main__":
    app.run(main)