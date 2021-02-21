"""This module will download the solutions for new links.

We will first read the list of links from the provided file
and will then fetch the solutions for the files that are not processed
and save them as individual files.

This should process only the newer links.
"""

from typing import Sequence
from typing import Dict

from absl import app
from absl import flags
from absl import logging

import download_helper
import html_service

import os


_BATCH_SIZE = flags.DEFINE_integer(
    'batch_size', 0,
    'Maximum items to process in a given run'
)


def main(argv: Sequence[str]) -> None:
    del argv

    logging.info('Running program...')
    run_data = download_helper.get_run_data()
    links = run_data.get('links', {})
    problems = run_data.get('problems', {})

    new_links = {link:None for link,val in links.items() if not val}

    batch_size = link_count = len(new_links)

    if _BATCH_SIZE.value:
        batch_size = _BATCH_SIZE.value

    logging.info('Processing %d / %d links',
        batch_size, link_count)    

    new_links = download_content_from_links(problems, new_links, batch_size)
    if new_links:
        links = collect_all_links(new_links, links)
        run_data['links'] = links
        download_helper.save_run_data(run_data)
    
    logging.info('Completed!')


def download_content_from_links(
    problems: Dict[int, str], 
    links: Dict[str,str], 
    batch_size: int) -> Dict[str,str]:
    """Fetch content from links and download it to a file.
    
    Args:
        problems: Dictionary of problem id and difficulty
        links: Dictionary of link and path where file is stored
        batch_size: Number of links to process at a given time
    
    Returns:
        Dictionary of links that were fetched
    """

    logging.info('Downloading content from links')
    html_svc = html_service.Html_Service()

    new_links = {}
    for ix, link in enumerate(links.keys()):
        if ix >= batch_size:
            break
        
        problem_id = html_svc.get_problem_number(link)
        if not problem_id in problems:
            logging.error('Error! Problem ID %d has not been collected!', problem_id)
            break
        else:
            logging.info('Fetching solution for %d', problem_id)
        
        api_link = html_svc.get_api_link_from_href(link)
        content = html_svc.get_api_content_as_md(api_link)
        
        file_path = save_content_to_file(problem_id, problems[problem_id], content)
        new_links[link] = file_path
    
    return new_links


def save_content_to_file(
    problem_id: int, 
    difficulty: str, 
    content: str) -> str:
    """Saves the content into a local file.

    Args: 
        problem_id: The problem number
        difficulty: The difficulty of the problem
        content: The markdown content to be stored

    Returns:
        Path where the file was saved.
    """

    logging.info('Saving problem %d to file', problem_id)
    solution_dir = os.path.join('solutions', difficulty)
    file_path = os.path.join(solution_dir, f'problem_{problem_id:03d}.md')
    
    if not os.path.exists(solution_dir):
        logging.info('Creating folder %s', solution_dir)
        os.mkdir(solution_dir)
    
    with open(file_path, 'w') as file:
        file.write(content)
    logging.info('File written! %s', file_path)

    return file_path


def collect_all_links(
    new_links: Dict[str,str],
    links: Dict[str,str]) -> Dict[str,str]:
    """Collects all the processed links into the full list.

    Args:
        new_links: Dictionary of updated links with solution path
        links: Dictionary of all the links

    Returns:
        Merged Dictionary updated with the solution paths
    """

    logging.info('Collecting all links')
    for link, filepath in new_links.items():
        links[link] = filepath

    return links


if __name__ == "__main__":
    app.run(main)