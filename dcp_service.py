"""This module has the helper methods required to get the right email content

This will fetch the Daily Coding Problem emails and get the relevant HTML content from it
"""

from typing import Sequence
from typing import Tuple 

from absl import logging

from googleapiclient import discovery

import base64
import bs4
import re

import gmail_service

class Error(Exception):
    """Base class for Errors while fetching emails
    """

class InvalidMessageError(Error):
    """Message ID is not found.
    """

class TooManyHtmlParts(Error):
    """The message has more than 1 html part    
    """

class DCP_Service():
    """Helper for fetching the right emails relevant for DCP.

    This uses a gmail resource object and fetches all the relevant information
    pertaining to the problem and solution for download

    Attributes:
        _gmail_service: The authenticated resources used to fetch the message from gmail
    """

    _DCP_QUERY = 'subject:(Daily Coding Problem)'
    _MAX_RESULTS = 250
    _SOLUTION_LINK_PATTERN = 'dailycodingproblem.com/solution'

    def __init__(self, gmail_service: gmail_service.GmailService):
        self._gmail_service = gmail_service

    def get_dcp_messages(
        self, 
        next_page_token: str,
        timestamp: int) -> Tuple[Sequence[str], str]:
        """Fetches all DCP messages based on a query string.

        Returns a list of matching message ids and a token to
        fetch the next page of results.

        Args:
            next_page_token: A string used by the gmail service for pagination
            timestamp: The starting timestamp from when to fetch the emails
        """
        
        logging.info('Getting %s %d messages',
            'first' if not next_page_token else 'next',
            DCP_Service._MAX_RESULTS)

        query = DCP_Service._DCP_QUERY
        if timestamp:
            query += f' after: {timestamp}'

        messages, next_page_token = self._gmail_service.search_messages(
            query, 
            next_page_token, 
            DCP_Service._MAX_RESULTS)
        
        return messages, next_page_token


    def get_html_message(self, message_id: str) -> str:
        """Parse the content of the message and return 
        only the HTML content that we are interested in.

        Args:
            message_id: Unique identifier of the message

        Returns:
            A single html message if present

        Raises:
            InvalidMessageError: If the message id is not found
            TooManyHtmlParts: If the message has more than one html content
        """

        MIME_TYPE = 'text/html'
        message = self._gmail_service.get_message_content(message_id)
        parts = message.get('parts', [])
        html_parts = filter(lambda p: p.get('mimeType', None) == MIME_TYPE, parts)

        data_parts = []
        for part in html_parts:
            text_data = base64.urlsafe_b64decode(part.get('body').get('data'))
            data_parts.append(text_data)

        if len(data_parts) > 1:
            raise TooManyHtmlParts

        if data_parts:
            return data_parts[0]
        else:
            return None


    def get_solution_links_from_html(self, message: str) -> Sequence[str]:
        """Returns a list of solution links from the HTML content.

        Args:
            message: The html content as a string
        
        Returns:
            A list of link urls
        """

        soup = bs4.BeautifulSoup(message, 'html.parser')
        link_tags = soup.find_all('a')
        
        links = []
        for tag in link_tags:
            href = tag.get('href')
            if re.search(self._SOLUTION_LINK_PATTERN, href):
                links.append(href)

        logging.info('Got %d solution link(s)', len(links))
        return links

