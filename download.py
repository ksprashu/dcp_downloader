# This module reads DCP emails on GMail and then downloads 
# all problem solution pairs into HTML / PDF files.

from typing import Sequence

import pickle
import os.path

from googleapiclient import discovery
from google_auth_oauthlib import flow
from google.auth.transport import requests
from google.oauth2 import credentials

from absl import app
from absl import flags

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
        with open(_TOKEN_FILE.value, 'rb') as token:
            creds = pickle.load(token)

    # if no valid creds then get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(requests.Request())
        else:
            app_flow = flow.InstalledAppFlow.from_client_secrets_file(
                _CRED_FILE.value, SCOPES)
            creds = app_flow.run_local_server(port=0)

            # save this for later use
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

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found!')

    return labels


def display_labels(labels) -> None:
    """ Prints the list of resources.

    Args:
        labels: A list of label strings
    """

    print('Labels:')
    for label in labels:
        print(label['name'])


def main(argv: Sequence[str]) -> None:
    del argv

    creds = get_credentials()
    service = get_gmail_service(creds)
    labels = get_labels(service)
    if labels:
        display_labels(labels) 


if __name__ == '__main__':
    app.run(main)