# This module reads DCP emails on GMail and then downloads 
# all problem solution pairs into HTML / PDF files.

from typing import Sequence
from typing import Tuple
from typing import Generator

import pickle
import os.path

from googleapiclient import discovery
from google_auth_oauthlib import flow
from google.auth.transport import requests
from google.oauth2 import credentials

from absl import app
from absl import flags
from absl import logging


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
_TOKEN_FILE = flags.DEFINE_string(
    'token_file',
    'config/token.pickle', 
    'The path the token file is saved')
_CRED_FILE = flags.DEFINE_string(
    'credential_file',
    'config/credentials.json',
    'The path to the credential file')


def get_credentials() -> credentials.Credentials:
    """Gets the credentials for connecting to GMail API.

    If credential exists as pickled file, then it is retrieved,
    else the credential is fetched from the authentication API
    and saved to a file.

    Returns:
        The credentials to authenticate with the service
    """
    
    creds = None

    # load pickled credentials if it exists
    if os.path.exists(_TOKEN_FILE.value):
        logging.info('Loading existing token from file')
        with open(_TOKEN_FILE.value, 'rb') as token:
            creds = pickle.load(token)

    # if no valid creds then get new ones
    if not creds or not creds.valid:
        logging.warn('Token not available or not valid')
        if creds and creds.expired and creds.refresh_token:
            logging.info('Refreshing the token')
            creds.refresh(requests.Request())
        else:
            logging.info('Starting new OAuth flow')
            app_flow = flow.InstalledAppFlow.from_client_secrets_file(
                _CRED_FILE.value, SCOPES)
            creds = app_flow.run_local_server(port=0)

            # save this for later use
            logging.info('Saving the token into file')
            with open(_TOKEN_FILE.value, 'wb') as token:
                pickle.dump(creds, token)

    return creds
            

def get_gmail_service(creds: credentials.Credentials) -> discovery.Resource:
    """ Returns the GMail resource.

    Args:
        creds: The credentials for the service

    Returns:
        The resource representing the service
    """

    logging.info('Fetching gmail v1 resource')
    service = discovery.build(
        'gmail', 'v1',
        credentials=creds,
        cache_discovery=False)
    return service


def get_labels(service: discovery.Resource) -> Sequence[str]:
    """ Returns the list of labels from GMail.

    Args:
        service: The resource representng the service

    Returns:
        The labels associated with the gmail account
    """

    logging.info('Fetching the list of labels for _self')
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        logging.warn('No labels found!')

    return labels


def display_labels(labels) -> None:
    """ Prints the list of resources.

    Args:
        labels: A list of label strings
    """

    print('Labels:')
    for label in labels:
        print(label['name'])


def _get_emails(service: discovery.Resource, query: str, page_token=None) -> Tuple[Sequence, str]:
    """ Fetches the emails corresponding to the specified query.
    
    Args: 
        service: The service representing the gmail resource
        query: The string for the search query
        page_token: The token to fetch the next page of results

    Returns:
        Tuple containing a list of threads and the next page token if available
    """

    logging.info('Searching emails for query: "%s"', query)
    logging.info('Using pagination: %s', page_token != None)

    results = service.users().threads().list(userId='me', q=query, pageToken = page_token).execute()
    if not page_token:
        logging.info('Retrieved (approx) %d threads', results['resultSizeEstimate'])

    threads = results.get('threads', [])
    next_page_token = results.get('nextPageToken', None)

    logging.info('Retrieved %s %d thread(s)', 
        'first' if not page_token else 'next',
        len(threads))

    return (threads, next_page_token)
    

def get_emails(service: discovery.Resource, query: str) -> Generator[str, None, None]:
    """Returns a iterator to go through all filtered emails

    Args: 
        service: The service representing the gmail resource
        query: The string for the search query

    Returns:
        An iterator of emails ids matching the given query
    """

    threads, next_page_token = _get_emails(service, query)
    if not threads:
        logging.warn('No threads matching the filter "%s"', query)
        return

    collected_threads = []
    collected_threads.extend(threads)

    i = 0
    thread_count = len(collected_threads)

    for thread in collected_threads:
        yield thread['id']
        i += 1

        if i == thread_count and next_page_token:
            threads, next_page_token = _get_emails(service, query, next_page_token)
            collected_threads.extend(threads)

    else:
        logging.info('Reached end of search results')


def load_email_content(service: discovery.Resource, id: str) -> str:
    """Fetches the email content for the provided ID.

    Args:
        service: The GMail resource object
        id: The unique identifier of the email

    Returns:
        The body of the email as a string
    """
    service.users().threads().get(userId='me', id=id)

def main(argv: Sequence[str]) -> None:
    del argv

    try:
        creds = get_credentials()
        service = get_gmail_service(creds)
        # get_labels(service)
        emails = get_emails(service, 'subject:(Daily Coding Problem)')
        for id in emails:
            load_email_content(id: str) -> str(id):
            """Fetches the email content for the provided ID.

            Args:
                id: The unique identifier of the email

            Returns:
                The body of the email as a string
            """


    except:
        logging.exception('Uncaught exception occurred')


if __name__ == '__main__':
    app.run(main)