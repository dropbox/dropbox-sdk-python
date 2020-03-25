#!/usr/bin/env python

import mock

import pytest

# Tests OAuth Flow
from dropbox import DropboxOAuth2Flow, session, Dropbox, create_session
from dropbox.oauth import OAuth2FlowNoRedirectResult
from datetime import datetime, timedelta

APP_KEY = 'dummy_app_key'
APP_SECRET = 'dummy_app_secret'
ACCESS_TOKEN = 'dummy_access_token'
REFRESH_TOKEN = 'dummy_refresh_token'
EXPIRES_IN = 14400
ACCOUNT_ID = 'dummy_account_id'
USER_ID = 'dummy_user_id'
EXPIRATION = datetime.utcnow() + timedelta(seconds=EXPIRES_IN)

EXPIRATION_BUFFER = timedelta(seconds=20)

class TestOAuth:

    def test_authorization_url_legacy_default(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET,
                                     'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')

        legacy_default_authorization_url = flow_obj._get_authorize_url(None, None, 'legacy')
        assert legacy_default_authorization_url == \
               'https://{}/oauth2/authorize?response_type=code&client_id={}'.format(session.WEB_HOST, APP_KEY)

    def test_authorization_url_invalid_token_type_raises_assertion_error(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET,
                                     'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')
        with pytest.raises(AssertionError):
            flow_obj._get_authorize_url(None, None, 'invalid')


    def test_authorization_url_online_token_type(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET,
                                     'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')
        online_authorization_url = flow_obj._get_authorize_url(None, None, 'online')
        assert online_authorization_url == \
               'https://{}/oauth2/authorize?token_access_type=online&response_type=code&client_id={}'.format(
                   session.WEB_HOST, APP_KEY)
    def test_authorization_url_offline_token_type(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET,
                                     'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')

        offline_authorization_url = flow_obj._get_authorize_url(None, None, 'offline')
        assert offline_authorization_url == \
               'https://{}/oauth2/authorize?token_access_type=offline&response_type=code&client_id={}'.format(session.WEB_HOST, APP_KEY)

    def test_OAuth2FlowNoRedirectResult_legacy(self):
        # Test legacy result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, None, None, ACCOUNT_ID, USER_ID)
        assert result_obj.access_token == ACCESS_TOKEN
        assert not result_obj.refresh_token
        assert not result_obj.expires_at

    def test_OAuth2FlowNoRedirectResult_offline(self):
        # Test offline result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_IN, ACCOUNT_ID, USER_ID)
        assert result_obj.access_token == ACCESS_TOKEN
        assert result_obj.refresh_token == REFRESH_TOKEN
        assert abs(result_obj.expires_at - EXPIRATION) < EXPIRATION_BUFFER
        assert result_obj.account_id == ACCOUNT_ID
        assert result_obj.user_id == USER_ID

    def test_OAuth2FlowNoRedirectResult_online(self):
        # Test online result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, None, EXPIRES_IN, ACCOUNT_ID, USER_ID)
        assert result_obj.access_token == ACCESS_TOKEN
        assert not result_obj.refresh_token
        assert abs(result_obj.expires_at - EXPIRATION) < EXPIRATION_BUFFER

    def test_OAuth2FlowNoRedirectResult_copy(self):
        # Test constructor for copying object
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, REFRESH_TOKEN, EXPIRATION, ACCOUNT_ID, USER_ID)
        assert result_obj.expires_at == EXPIRATION

class TestClient:

    @pytest.fixture(scope='function')
    def session_instance(self, mocker):
        session_obj = create_session()
        post_response = mock.MagicMock()
        post_response.json.return_value = {"access_token": ACCESS_TOKEN, "expires_in": EXPIRES_IN}
        mocker.patch.object(session_obj, 'post', return_value=post_response)
        return session_obj

    def test_default_Dropbox_raises_assertion_error(self):
        with pytest.raises(AssertionError):
            # Requires either access token or refresh token
            Dropbox()

    def test_Dropbox_with_refresh_only_raises_assertion_error(self):
        with pytest.raises(AssertionError):
            # Refresh tokens also require app key and secret
            Dropbox(oauth2_refresh_token=REFRESH_TOKEN)

    def test_Dropbox_with_legacy_token(self, session_instance):
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN, session=session_instance)
        session_instance.post.assert_not_called()

    def test_Dropbox_with_valid_online_token(self, session_instance):
        # Test Online Case w/ valid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN, oauth2_access_token_expiration=EXPIRATION, session=session_instance)
        session_instance.post.assert_not_called()

    def test_Dropbox_with_expired_online_token(self, session_instance):
        # Test Online Case w/ invalid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                      session=session_instance)
        session_instance.post.assert_not_called()

    def test_Dropbox_with_valid_offline_token(self, session_instance):
        # Test Offline Case w/ valid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_refresh_token=REFRESH_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        session_instance.post.assert_not_called()

    def test_Dropbox_with_expired_offline_token(self, session_instance):
        # Test Offline Case w/ invalid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_refresh_token=REFRESH_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        session_instance.post.assert_called_once()

    def test_Dropbox_with_only_refresh(self, session_instance):
        # Test Offline Case w/ only refresh
        dbx = Dropbox(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        session_instance.post.assert_called_once()