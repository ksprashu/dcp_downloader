"""This will help check if all the problem ids are collected.
"""

from typing import Sequence

from absl import app
from absl import logging

import download_helper

def main(argv: Sequence[str]) -> None:
    del argv

    run_data = download_helper.get_run_data()

    logging.info('collecting all problems')
    problems = run_data.get('problems')
    print(problems)

    sorted_problems = sorted(list(problems.keys()))
    min_p = sorted_problems[0]
    max_p = sorted_problems[-1]

    print(f'We have problems from {min_p} to {max_p}')
    print(f'Total problems should be {max_p - min_p + 1}, and we have {len(sorted_problems)}')

    logging.info('Finding missing problems')
    for i in range(min_p, max_p+1):
        if not i in sorted_problems:
            print(f'probem {i} not found')    


if __name__ == "__main__":
    app.run(main)