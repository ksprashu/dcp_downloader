"""Allow manually adding missing problems.
"""

from typing import Sequence

from absl import app
from absl import logging

import download_helper

MISSING_PROBS = []

def main(argv: Sequence[str]) -> None:
    del argv

    run_data = download_helper.get_run_data()
    problems = run_data.get('problems')

    if problems:
        logging.info('Adding %d problems', len(MISSING_PROBS))
        for prob in MISSING_PROBS:
            problems[prob] = 'Easy'
        run_data['problems'] = problems
        logging.info('Saving %d problems', len(problems))
        download_helper.save_run_data(run_data)

    if problems:
        logging.info('remove wrong problem data')
        old_count = len(problems)
        del problems[2989]    
        del problems[2916]    
        del problems[2332]  
        del problems[2130]
        new_count = len(problems)

        if new_count != old_count:
            run_data['problems'] = problems
            logging.info('Saving %d problems', len(problems))
            download_helper.save_run_data(run_data)

if __name__ == "__main__":
    app.run(main)

