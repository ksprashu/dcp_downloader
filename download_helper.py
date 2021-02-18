"""This module is a helper module to initialize the token,
and the gmail service resource.
"""

from typing import Sequence

from absl import app
from absl import flags
from absl import logging

import credential_service
import dcp_service
import gmail_service

import math
import os
import pickle
import datetime

_SCOPES = flags.DEFINE_list(
    'scopes',
    ['https://www.googleapis.com/auth/gmail.readonly'],
    'The scopes to be requested while fetching the token')
_TOKEN_FILE = flags.DEFINE_string(
    'token_file',
    'config/token.pickle', 
    'The path where the token file is saved')
_CRED_FILE = flags.DEFINE_string(
    'credential_file',
    'config/credentials.json',
    'The path to the credential file')

def init_and_get_gmail_service() -> gmail_service.GmailService:
    """Returns an authenticated gmail service object.
    """

    # start by getting the credential
    # initialize an oauth flow in case the token is not present
    # or is invalid
    try:
        cred = credential_service.Credential(
            cred_file=_CRED_FILE.value,
            token_file=_TOKEN_FILE.value,
            scopes=_SCOPES.value)
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

    return gmail_svc