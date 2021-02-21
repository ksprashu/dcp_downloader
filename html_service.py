"""This module help retrieve and parse HTML content.

Since the solution page uses dynamic async javascript,
we will have to use a headless browser to render the page
and then parse it.
"""

from absl import logging

import collections
import re
from urllib import parse
from urllib import request

class LinkWithoutTokenError(Exception):
    """Provided solution link doesn't contain a token.
    """


class Html_Service():
    """Helps fetch and parse dynamic HTML data
    """

    API_BASE_PATH = 'www.dailycodingproblem.com/api/solution'

    def __init__(self):
        pass

    def fetch_page_from_link(self):
        pass

    def parse_html(self):
        pass


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

        api_url = parse.ParseResult(scheme='https',netloc=None, path=Html_Service.API_BASE_PATH, params=None, query=query, fragment=None)
        return api_url.geturl()
        



