"""This module help retrieve and parse HTML content.

Since the solution page uses dynamic async javascript,
we will have to use a headless browser to render the page
and then parse it.
"""

from absl import logging

import ratelimiter
import re
import requests


from urllib import parse

class LinkWithoutTokenError(Exception):
    """Provided solution link doesn't contain a token.
    """


class InvalidJsonApiError(Exception):
    """API didn't return a valid JSON response
    """


class Html_Service():
    """Helps fetch and parse dynamic HTML data
    """

    API_PATH = 'api/solution'
    API_HOST = 'www.dailycodingproblem.com'

    def get_api_link_from_href(self, href: str) -> str:
        """Parses the link to the solution HTML page and return the API link.

        Args:
            href: The link to the HTML page of the solution

        Returns:
            A link to the API that contains the solution markdown
        """

        logging.info('Getting API link for %s', href)

        result = parse.urlparse(href)
        query = result.query

        if not re.search('token', query):
            raise LinkWithoutTokenError('There was no token in the link %s', href)

        api_url = parse.ParseResult(
            scheme='https', 
            netloc=Html_Service.API_HOST, 
            path=Html_Service.API_PATH, 
            params=None, 
            query=query, 
            fragment=None)

        return api_url.geturl()
        

    @ratelimiter.RateLimiter(max_calls=1, period=1)
    def get_api_content_as_md(self, href: str) -> str:
        """Calls the API link and returns the response as Markdown.

        Args:
            href: The link to the API
        
        Returns:
            The response as a markdown document

        Raises:
            InvalidJsonApiError: The API didn't return a valid JSON
        """

        logging.info('Getting content from url %s', href)
        r = requests.get(href)

        try:
            res = r.json()
        except ValueError:
            logging.error('Unable to get solution json from link %s', href)
            raise InvalidJsonApiError('API didn\'t return a JSON')

        if res:
            doc = f"## Problem #{res['problemId']}\n{res['problem']}\n## Solution\n{res['solution']}"

        return doc


    def get_problem_number(self, href: str) -> int:
        """Returns the problem number provided in the contained link.

        Args:
            href: Link to the problem solution
        """

        logging.info('Getting problem number from link %s', href)
        result = parse.urlparse(href)
        path = result.path
        problem_id = path.split('/')[-1]

        return int(problem_id)
