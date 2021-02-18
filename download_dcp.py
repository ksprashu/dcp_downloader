# This module reads DCP emails on GMail and then downloads 
# all problem solution pairs into HTML / PDF files.

from typing import Sequence
from typing import Tuple
from typing import Generator

import base64
import functools
import operator
import os.path
import pickle
import re

from bs4 import BeautifulSoup

from googleapiclient import discovery
from google_auth_oauthlib import flow
from google.auth.transport import requests
from google.oauth2 import credentials

from absl import app
from absl import flags
from absl import logging

import credential_service
import gmail_service
import dcp_service
import html_service

_SCOPES = flags.DEFINE_list(
    'scopes',
    ['https://www.googleapis.com/auth/gmail.readonly'],
    'The scopes to be requested while fetching the token')
_TOKEN_FILE = flags.DEFINE_string(
    'token_file',
    'config/token.pickle', 
    'The path the token file is saved')
_CRED_FILE = flags.DEFINE_string(
    'credential_file',
    'config/credentials.json',
    'The path to the credential file')
_LINK_FILE = flags.DEFINE_string(
    'link_file',
    'data/links.txt',
    'The file where the links will be stored')


class Error(Exception):
    """Base class for all exceptions in this module.
    """


class BadMessageIdError(Error):
    """The provided email message id is invalid.
    """


class TooManyHtmlStrings(Error):
    """The HTML body has more than expected strings.
    """


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
        logging.warning('Token not available or not valid')
        if creds and creds.expired and creds.refresh_token:
            logging.info('Refreshing the token')
            creds.refresh(requests.Request())
        else:
            logging.info('Starting new OAuth flow')
            app_flow = flow.InstalledAppFlow.from_client_secrets_file(
                _CRED_FILE.value, _SCOPES)
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
        logging.warning('No labels found!')

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
        Tuple containing a list of messages and the next page token if available
    """

    logging.info('Searching emails for query: "%s"', query)
    logging.info('Using pagination: %s', page_token != None)

    results = service.users().messages().list(userId='me', q=query, pageToken = page_token, maxResults = 10).execute()
    if not page_token:
        logging.info('Retrieved (approx) %d messages', results['resultSizeEstimate'])

    messages = results.get('messages', [])
    next_page_token = results.get('nextPageToken', None)

    logging.info('Retrieved %s %d message(s)', 
        'first' if not page_token else 'next',
        len(messages))

    return (messages, next_page_token)
    

def get_emails(service: discovery.Resource, query: str) -> Generator[str, None, None]:
    """Returns a iterator to go through all filtered emails

    Args: 
        service: The service representing the gmail resource
        query: The string for the search query

    Returns:
        An iterator of emails ids matching the given query
    """

    messages, next_page_token = _get_emails(service, query)
    if not messages:
        logging.warning('No messages matching the filter "%s"', query)
        return

    collected_messages = []
    collected_messages.extend(messages)

    i = 0
    message_count = len(collected_messages)

    for message in collected_messages:
        yield message['id']
        i += 1

        if i == message_count and next_page_token:
            messages, next_page_token = _get_emails(service, query, next_page_token)
            collected_messages.extend(messages)
            message_count += len(messages)

    else:
        logging.info('Reached end of search results')


def get_email_content(service: discovery.Resource, id: str) -> str:
    """Fetches the email content for the provided ID.

    Args:
        service: The GMail resource object
        id: The unique identifier of the email

    Returns:
        The body of the email as a string

    Raises:
        BadMessageIdError: The provided ID is invalid
    """

    logging.info('Fetching content of email: %s', id)
    message = service.users().messages().get(userId='me', id=id).execute()

    if not message:
        raise BadMessageIdError('Cannot find an email with the provided id', id)

    payload = message.get('payload', None)
    return payload


def filter_html_part(part) -> bool:
    """Filter function: Returns true if the header has content-type = text/html.

    Args:
        part: The MessagePart object of the email
    """

    headers = part.get('headers', [])
    content_type_headers = filter(lambda h: h.get('name', None) == 'Content-Type', headers)
    content_types = map(lambda t: t.get('value', None), content_type_headers)

    return True if 'text/html' in content_types else False


def get_html_from_payload(payload) -> Sequence[str]:
    """Parses the contents of the email and gets the link to the solution.

    Args:
        email: The email content string

    Returns:
        List of html strings

    Raises:
        TooManyHtmlStrings: In case there is more than one html string
    """

    logging.info('Fetching html from payload')
    parts = payload.get('parts', [])
    html_parts = filter(filter_html_part, parts)
    html_bodies = map(lambda p: p.get('body', None), html_parts)
    html_data = map(lambda b: b.get('data', None), html_bodies)
    html_strings = map(lambda d: base64.urlsafe_b64decode(d), html_data)


    # There should be only one html string in the content
    # So return the last one and raise exception if there are more
    count = 0
    for s in html_strings:
        count += 1

    if count > 1:
        raise TooManyHtmlStrings('Found %d html strings in the email' % count)
    
    if not count:
        logging.warning('No html content in payload')
        return None

    return s


def get_links_from_html(html: Sequence[str]) -> str:
    """Returns the link to the solution contained in the html.

    Uses beautiful soup and converts the html into an object.
    Then looks for the link to the solution and returns in.

    Args:
        html: The content as a list of html

    Returns:
        A list of extracted links
    """

    logging.info('Extracting the links from the html')
    soup = BeautifulSoup(html, 'html.parser')
    link_tags = soup.find_all('a')
    links = map(lambda l: l.get('href'), link_tags)

    # getting only links where it is linked to a solution
    links = filter(lambda l: re.search('dailycodingproblem.com/solution', l), links)

    return links


def main(argv: Sequence[str]) -> None:
    del argv

    # start by getting the credential
    # initialize an oauth flow in case the token is not present
    # or is invalid
    try:
        cred = credential_service.Credential(
            cred_file=_CRED_FILE,
            token_file=_TOKEN_FILE,
            scopes=_SCOPES)
        token = cred.get_token()
    except:
        logging.exception('Exiting! Unable to load Credentials')
        exit()

    # get the gmail service instance
    try:
        gmail_svc = gmail_service.GmailService(token)
        gmail_svc.load_gmail_resource()
    except:
        logging.exception('Exiting! Unable to load the GMail service')
        exit()

    try:
        dcp_svc = dcp_service.DCP_Service(gmail_svc)
        email_ids, next_page_token = dcp_svc.get_dcp_messages(next_page_token=None)

        email_index = 0
        email_count = len(email_ids)

        # until there is no next page, keep going through the list 
        while email_count and next_page_token:
            try:
                message = dcp_svc.get_html_message(email_ids[email_index])
            except dcp_service.InvalidMessageError:
                logging.warning('Skipping message %s; no message found', email_ids[email_index])
            except dcp_service.TooManyHtmlParts:
                logging.warning('Skipping message %s; unsupported message format', email_ids[email_index])
            finally:
                email_index += 1

            if message:
                links = dcp_svc.get_solution_links(message)
                for link in links:
                    print(link)

                # fetch the next page of results if needed
                if email_index >= email_count and next_page_token:
                    new_email_ids, next_page_token = dcp_svc.get_dcp_messages(
                        next_page_token=next_page_token)

                    email_ids.extend(new_email_ids)


    except:
        logging.exception('Uncaught Error!')
        exit()

    try:
        creds = get_credentials()
        service = get_gmail_service(creds)
        # get_labels(service)
        emails = get_emails(service, 'subject:(Daily Coding Problem)')
        payload = map(lambda c: get_email_content(service, c), emails)
        html_data = map(get_html_from_payload, payload)
        html_data = filter(lambda h: h != None, html_data)
        links = map(get_links_from_html, html_data)
        
        # flatten the list of links
        list_links = functools.reduce(operator.iconcat, links, [])

        with open(_LINK_FILE, 'w') as file:
            for link in list_links:
                file.write(link)

    except:
        logging.exception('Uncaught exception occurred')


if __name__ == '__main__':
    app.run(main)