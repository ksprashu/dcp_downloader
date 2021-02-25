"""This module fetches the credentials for use with the gmail service.

The module fetches any previously saved credentials, or 
authenticates and fetches new one if needed.

The module will fetch and store the credential as an instance attribute
and return the same upon request.

Methods:
    __init__ : to create the object with specified files and scopes
    get_token : to load the token from file or from oauth flow
"""

import os
import pickle
from typing import Sequence

from absl import logging

from google_auth_oauthlib import flow
from google.auth.transport import requests
from google.oauth2 import credentials


class Error(Exception):
    """The base exception class for this module.
    """


class BadFileError(Error):
    """Unable to read the token from the file.
    """


class Credential():
    """Fetches the authentication token for the service API.

    Attributes:
        _cred_file: The credential file with the client id and secret
        _token_file: The physical file where the token will be saved
        _scopes: A list of scopes that are associated with this token
        _cred: The token that is used to authenticate with the service
    """

    def __init__(
        self,
        cred_file: str, 
        token_file: str,
        scopes: Sequence[str]) -> None:

        self._cred_file = cred_file
        self._token_file = token_file
        self._scopes = scopes
        self._cred = None
        

    def _get_token_from_file(self) -> credentials.Credentials:
        """Loads the file from the filesystem.

        Raises:
            BadFileError: The file does not contain a readable token
        """

        logging.info('Looking for token in file - %s', self._token_file)
        cred = None

        if os.path.exists(self._token_file):
            logging.info('Loading existing token from file')
            try:
                with open(self._token_file, 'rb') as token:
                    cred = pickle.load(token)
            except OSError:
                logging.error('Unable to read the token file')
                raise BadFileError('The contents of the file cannot be read')
        else:
            logging.warning('Specified file does not exist')

        return cred


    def _save_token_to_file(self, cred = credentials.Credentials) -> None:
        """Saves the provided token to filesystem.
        """   

        try:   
            logging.info('Saving the token into file')
            with open(self._token_file, 'wb') as token:
                pickle.dump(cred, token)
        except OSError:
            logging.warning('Unable to save to file')


    def _get_new_token(self) -> credentials.Credentials:
        """Gets the new token using OAuth.
        """

        cred = None
        try:
            logging.info('Starting new OAuth flow')
            app_flow = flow.InstalledAppFlow.from_client_secrets_file(
                self._cred_file, self._scopes)
            cred = app_flow.run_local_server(port=0) # will open up the consent page
        except:
            logging.error('Unknown exception while getting token from oauth')
            raise

        return cred


    def _refresh_token(self, cred: credentials.Credentials) -> credentials.Credentials:
        """Refreshes the existing token if expired.
        """

        try:
            logging.info('Refreshing the token')
            cred.refresh(requests.Request())
        except:
            logging.warn('Error trying to refresh the token!')
            cred = self._get_new_token()

        return cred
        

    def get_token(self) -> credentials.Credentials:
        """Gets the Token for connecting to GMail API.

        If credential exists as pickled file, then it is retrieved,
        else the credential is fetched from the authentication API
        and saved to a file.

        Returns:
            The credentials to authenticate with the service
        """

        logging.info('Getting a token')
        cred = None

        # try to get from instance attribute otherwise load from file
        if self._cred:
            cred = self._cred
        else:
            cred = self._get_token_from_file()

        # if no valid cred then get new ones
        if not cred or not cred.valid:
            logging.warning('Token not available or not valid')
            if cred and cred.expired and cred.refresh_token:
                cred = self._refresh_token(cred)
            else:
                cred = self._get_new_token()
                
            self._save_token_to_file(cred) # save for later use
            self._cred = cred

        return cred