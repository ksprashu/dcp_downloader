"""This module will authenticate with gmail and download the
requested emails.

The module will instantiate an authenticate instance of the gmail 
service using the provided token and retain this single instance.

The module will be able to search for emails, and fetch the content
of a provided email (message id)

Methods:
__init__ : Construct the authenticated gmail service object
search_message: Search for a specified query term
get_message_content: Returns the contents of the message

"""
from typing import Sequence
from typing import Tuple

from absl import logging

from googleapiclient import discovery

class Error(Exception):
    """Generic error class for this module.
    """

class BadMessageIdError(Error):
    """Invalid Message Id used to fetch email
    """


class GmailService():
    """Fetches the resource object after authenticating with
    the Gmail service. Also provides member functions to 
    search for and retrieve email messages.

    Attributes:
        _token: The authentication token
        _gmail_service: The authenticated gmail resource 
    """
    
    def __init__(self, token) -> None:
        self._token = token
        self._gmail_service = None


    def load_gmail_resource(self) -> None:
        """Loads and returns the authenticated gmail resource.
        """
        
        logging.info('Getting an authenticated gmail resource')
        res = None

        if self._gmail_service:
            res = self._gmail_service
        else:            
            try:
                res = discovery.build(
                    'gmail', 'v1',
                    credentials=self._token,
                    cache_discovery=False)

                self._gmail_service = res
            except:
                logging.exception('Uncaught exception while getting gmail resource')
                raise



    def search_messsages(
        self, 
        query: str, 
        next_page_token: str = None, 
        max_results: int = None) -> Tuple[Sequence[str], str]:
        """Returns results for the specified query term.

        Searches for the specified query terms and returns the
        matching message ids in case there are results, else will
        return []. 

        The method also supports search pagination and limiting the number
        of results returned.

        Args:
            query: A search term string
            next_page_token: The pagination token as returned from a previous search result
            max_results: The number of search results to be returned in a single page

        Returns:
            A tuple containing a list of message ids, and a pagination token
        """

        logging.info('Searching emails for query: "%s"', query)
        logging.info('Using pagination: %s', next_page_token != None)

        results = self._gmail_service.users().messages().list( # pylint: disable=no-member
            userId='me', 
            q=query, 
            pageToken = next_page_token, 
            maxResults = max_results).execute()

        messages = results.get('messages', [])
        next_page_token = results.get('nextPageToken', None)

        logging.info('Retrieved %d / %d (approx) messages', 
            len(messages),
            results['resultSizeEstimate'])

        message_ids = []
        for message in messages:
            message_ids.append(message['id'])

        return (message_ids, next_page_token)        


    def get_messsage_content(self, message_id: str) -> object:
        """Returns the content object give a message id.

        This returns the entire content of the message including
        headers, mime type, and multipart message body

        Args:
            message_id: The unique id of a given message

        Returns:
            An object with the payload of the email message

        Raises:
            BadMessageIdError: If a message cannot be retrieved using the provided id
        """

        logging.info('Fetching content of email: %s', message_id)

        try:
            message = self._gmail_service.users().messages().get(userId='me', id=message_id).execute() #pylint: disable=no-member
        except:
            logging.exception('Uncaught exception while fetching email')
            raise

        if not message:
            raise BadMessageIdError('Cannot find an email with the provided id', id)

        payload = message.get('payload', None)
        return payload




