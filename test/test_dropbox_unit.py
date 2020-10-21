#!/usr/bin/env python

import mock

import pytest

# Tests OAuth Flow
from dropbox import DropboxOAuth2Flow, session, Dropbox, create_session
from dropbox.dropbox import BadInputException, DropboxTeam
from dropbox.exceptions import AuthError
from dropbox.oauth import OAuth2FlowNoRedirectResult, DropboxOAuth2FlowNoRedirect
from datetime import datetime, timedelta

APP_KEY = 'dummy_app_key'
APP_SECRET = 'dummy_app_secret'
ACCESS_TOKEN = 'dummy_access_token'
REFRESH_TOKEN = 'dummy_refresh_token'
EXPIRES_IN = 14400
ACCOUNT_ID = 'dummy_account_id'
USER_ID = 'dummy_user_id'
ADMIN_ID = 'dummy_admin_id'
TEAM_MEMBER_ID = 'dummy_team_member_id'
SCOPE_LIST = ['files.metadata.read', 'files.metadata.write']
EXPIRATION = datetime.utcnow() + timedelta(seconds=EXPIRES_IN)

EXPIRATION_BUFFER = timedelta(minutes=5)

class TestOAuth:

    def test_authorization_url(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')
        for redirect_uri in [None, 'localhost']:
            for state in [None, 'state']:
                for token_access_type in [None, 'legacy', 'offline', 'online']:
                    for scope in [None, SCOPE_LIST]:
                        for include_granted_scopes in [None, 'user', 'team']:
                            for code_challenge in [None, 'mychallenge']:
                                authorization_url = \
                                    flow_obj._get_authorize_url(redirect_uri, state,
                                                                token_access_type, scope,
                                                                include_granted_scopes,
                                                                code_challenge)
                                assert authorization_url\
                                    .startswith('https://{}/oauth2/authorize?'
                                                .format(session.WEB_HOST))
                                assert 'client_id={}'.format(APP_KEY) in authorization_url
                                assert 'response_type=code' in authorization_url

                                if redirect_uri:
                                    assert 'redirect_uri={}'.format(redirect_uri) \
                                        in authorization_url
                                else:
                                    assert 'redirect_uri' not in authorization_url

                                if state:
                                    assert 'state={}'.format(state) in authorization_url
                                else:
                                    assert 'state' not in authorization_url

                                if token_access_type:
                                    assert 'token_access_type={}'.format(token_access_type) \
                                        in authorization_url
                                else:
                                    assert 'token_access_type' not in authorization_url

                                if scope:
                                    assert 'scope={}'.format("+".join(scope)) \
                                           in authorization_url
                                else:
                                    assert 'scope' not in authorization_url

                                if include_granted_scopes and scope:
                                    assert 'include_granted_scopes={}'\
                                        .format(include_granted_scopes)\
                                        in authorization_url
                                else:
                                    assert 'include_granted_scopes' not in authorization_url

                                if code_challenge:
                                    assert 'code_challenge_method=S256' in authorization_url
                                    assert 'code_challenge={}'.format(code_challenge)\
                                        in authorization_url
                                else:
                                    assert 'code_challenge_method' not in authorization_url
                                    assert 'code_challenge' not in authorization_url

    def test_authorization_url_legacy_default(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')

        legacy_default_authorization_url = flow_obj._get_authorize_url(None, None, 'legacy')
        assert legacy_default_authorization_url.startswith('https://{}/oauth2/authorize?'
                                                           .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in legacy_default_authorization_url
        assert 'response_type=code' in legacy_default_authorization_url

    def test_authorization_url_invalid_token_type_raises_assertion_error(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')
        with pytest.raises(AssertionError):
            flow_obj._get_authorize_url(None, None, 'invalid')

    def test_authorization_url_online_token_type(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')
        online_authorization_url = flow_obj._get_authorize_url(None, None, 'online')
        assert online_authorization_url.startswith('https://{}/oauth2/authorize?'
                                                   .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in online_authorization_url
        assert 'response_type=code' in online_authorization_url
        assert 'token_access_type=online' in online_authorization_url

    def test_authorization_url_offline_token_type(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')

        offline_authorization_url = flow_obj._get_authorize_url(None, None, 'offline')
        assert offline_authorization_url.startswith('https://{}/oauth2/authorize?'
                                                    .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in offline_authorization_url
        assert 'response_type=code' in offline_authorization_url
        assert 'token_access_type=offline' in offline_authorization_url

    def test_authorization_url_with_scopes_and_granted(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')

        scopes = ['account_info.read', 'files.metadata.read']
        scope_authorization_url = flow_obj._get_authorize_url(None, None, 'offline', scopes, 'user')
        assert scope_authorization_url.startswith('https://{}/oauth2/authorize?'
                .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in scope_authorization_url
        assert 'response_type=code' in scope_authorization_url
        assert 'token_access_type=offline' in scope_authorization_url
        assert 'scope=account_info.read+files.metadata.read' in scope_authorization_url
        assert 'include_granted_scopes=user' in scope_authorization_url

    def test_authorization_url_with_scopes(self):
        flow_obj = DropboxOAuth2Flow(APP_KEY, APP_SECRET, 'http://localhost/dummy',
                                     'dummy_session', 'dbx-auth-csrf-token')

        scopes = ['account_info.read', 'files.metadata.read']
        scope_authorization_url = flow_obj._get_authorize_url(None, None, 'offline', scopes)
        assert scope_authorization_url.startswith('https://{}/oauth2/authorize?'
                                                  .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in scope_authorization_url
        assert 'response_type=code' in scope_authorization_url
        assert 'token_access_type=offline' in scope_authorization_url
        assert 'scope=account_info.read+files.metadata.read' in scope_authorization_url
        assert 'include_granted_scopes' not in scope_authorization_url

    def test_OAuth2FlowNoRedirectResult_legacy(self):
        # Test legacy result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, ACCOUNT_ID, USER_ID, None, None,
                                                SCOPE_LIST)
        assert result_obj.access_token == ACCESS_TOKEN
        assert not result_obj.refresh_token
        assert not result_obj.expires_at

    def test_OAuth2FlowNoRedirectResult_offline(self):
        # Test offline result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, ACCOUNT_ID, USER_ID,
                                                REFRESH_TOKEN, EXPIRES_IN, SCOPE_LIST)
        assert result_obj.access_token == ACCESS_TOKEN
        assert result_obj.refresh_token == REFRESH_TOKEN
        assert abs(result_obj.expires_at - EXPIRATION) < EXPIRATION_BUFFER
        assert result_obj.account_id == ACCOUNT_ID
        assert result_obj.user_id == USER_ID
        assert result_obj.scope == SCOPE_LIST

    def test_OAuth2FlowNoRedirectResult_online(self):
        # Test online result
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, ACCOUNT_ID, USER_ID, None, EXPIRES_IN,
                                                SCOPE_LIST)
        assert result_obj.access_token == ACCESS_TOKEN
        assert not result_obj.refresh_token
        assert abs(result_obj.expires_at - EXPIRATION) < EXPIRATION_BUFFER

    def test_OAuth2FlowNoRedirectResult_copy(self):
        # Test constructor for copying object
        result_obj = OAuth2FlowNoRedirectResult(ACCESS_TOKEN, ACCOUNT_ID, USER_ID,
                                                REFRESH_TOKEN, EXPIRATION, SCOPE_LIST)
        assert result_obj.expires_at == EXPIRATION

    @pytest.fixture(scope='function')
    def auth_flow_offline_with_scopes(self, mocker):
        auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type='offline',
                                                scope=SCOPE_LIST)
        session = mock.MagicMock()
        post_response = mock.MagicMock(status_code=200)
        post_response.json.return_value = {"access_token": ACCESS_TOKEN, "refresh_token":
            REFRESH_TOKEN, "expires_in": EXPIRES_IN, "uid": USER_ID, "account_id": ACCOUNT_ID,
                                           "scope": " ".join(SCOPE_LIST)}
        mocker.patch.object(session, 'post', return_value=post_response)
        auth_flow.requests_session = session
        return auth_flow

    def test_NoRedirect_whole_flow(self, auth_flow_offline_with_scopes):
        authorization_url = auth_flow_offline_with_scopes.start()

        assert authorization_url.startswith('https://{}/oauth2/authorize?'
                                            .format(session.WEB_HOST))
        assert 'client_id={}'.format(APP_KEY) in authorization_url
        assert 'response_type=code' in authorization_url
        mycode = 'test oauth code'
        auth_result = auth_flow_offline_with_scopes.finish(mycode)
        assert auth_result.access_token == ACCESS_TOKEN
        assert auth_result.refresh_token == REFRESH_TOKEN
        assert abs(auth_result.expires_at - EXPIRATION) < EXPIRATION_BUFFER
        assert auth_result.user_id == USER_ID
        assert auth_result.account_id == ACCOUNT_ID
        assert auth_result.scope == " ".join(SCOPE_LIST)

        auth_flow_offline_with_scopes.requests_session.post.assert_called_once()
        token_call_args = auth_flow_offline_with_scopes.requests_session.post.call_args_list
        assert len(token_call_args) == 1
        first_call_args = token_call_args[0]
        assert first_call_args[0][0] == 'https://{}/oauth2/token'.format(session.API_HOST)
        call_data = first_call_args[1]['data']
        assert call_data['client_id'] == APP_KEY
        assert call_data['grant_type'] == 'authorization_code'
        assert call_data['client_secret'] == APP_SECRET
        assert call_data['code'] == mycode

class TestClient:

    @pytest.fixture(scope='function')
    def session_instance(self, mocker):
        session_obj = create_session()
        post_response = mock.MagicMock(status_code=200)
        post_response.json.return_value = {"access_token": ACCESS_TOKEN, "expires_in": EXPIRES_IN}
        mocker.patch.object(session_obj, 'post', return_value=post_response)
        return session_obj

    @pytest.fixture(scope='function')
    def invalid_grant_session_instance(self, mocker):
        session_obj = create_session()
        post_response = mock.MagicMock(status_code=400)
        post_response.json.return_value = {"error": "invalid_grant"}
        mocker.patch.object(session_obj, 'post', return_value=post_response)
        return session_obj

    def test_default_Dropbox_raises_assertion_error(self):
        with pytest.raises(BadInputException):
            # Requires either access token or refresh token
            Dropbox()

    def test_Dropbox_with_refresh_only_raises_assertion_error(self):
        with pytest.raises(BadInputException):
            # Refresh tokens also require app key and secret
            Dropbox(oauth2_refresh_token=REFRESH_TOKEN)

    def test_Dropbox_with_legacy_token(self, session_instance):
        Dropbox(oauth2_access_token=ACCESS_TOKEN, session=session_instance)

    def test_Dropbox_with_valid_online_token(self, session_instance):
        # Test Online Case w/ valid access
        Dropbox(oauth2_access_token=ACCESS_TOKEN, oauth2_access_token_expiration=EXPIRATION,
                session=session_instance)

    def test_Dropbox_with_expired_online_token(self, session_instance):
        # Test Online Case w/ invalid access
        Dropbox(oauth2_access_token=ACCESS_TOKEN,
                oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                session=session_instance)

    def test_Dropbox_with_valid_offline_token(self, session_instance):
        # Test Offline Case w/ valid access
        Dropbox(oauth2_access_token=ACCESS_TOKEN,
                oauth2_refresh_token=REFRESH_TOKEN,
                oauth2_access_token_expiration=EXPIRATION,
                app_key=APP_KEY,
                app_secret=APP_SECRET,
                session=session_instance)

    def test_Dropbox_with_expired_offline_token(self, session_instance):
        # Test Offline Case w/ invalid access
        Dropbox(oauth2_access_token=ACCESS_TOKEN,
                oauth2_refresh_token=REFRESH_TOKEN,
                oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                app_key=APP_KEY,
                app_secret=APP_SECRET,
                session=session_instance)

    def test_Dropbox_with_only_refresh(self, session_instance):
        # Test Offline Case w/ only refresh
        Dropbox(oauth2_refresh_token=REFRESH_TOKEN,
                app_key=APP_KEY,
                app_secret=APP_SECRET,
                session=session_instance)

    def test_check_refresh_with_legacy_token(self, session_instance):
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN, session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_not_called()

    def test_check_refresh_with_valid_online_token(self, session_instance):
        # Test Online Case w/ valid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN, oauth2_access_token_expiration=EXPIRATION,
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_not_called()

    def test_check_refresh_with_expired_online_token(self, session_instance):
        # Test Online Case w/ invalid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_not_called()

    def test_check_refresh_with_valid_offline_token(self, session_instance):
        # Test Offline Case w/ valid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_refresh_token=REFRESH_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_not_called()

    def test_check_refresh_with_expired_offline_token(self, session_instance):
        # Test Offline Case w/ invalid access
        dbx = Dropbox(oauth2_access_token=ACCESS_TOKEN,
                      oauth2_refresh_token=REFRESH_TOKEN,
                      oauth2_access_token_expiration=EXPIRATION - timedelta(weeks=1),
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_called_once()

    def test_check_refresh_with_only_refresh(self, session_instance):
        # Test Offline Case w/ only refresh
        dbx = Dropbox(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_called_once()

    def test_check_refresh_with_invalid_grant(self, invalid_grant_session_instance):
        dbx = Dropbox(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=invalid_grant_session_instance)
        with pytest.raises(AuthError) as e:
            dbx.check_and_refresh_access_token()
            invalid_grant_session_instance.post.assert_called_once()
            assert e.error.is_invalid_access_token()

    def test_team_client_refresh(self, session_instance):
        dbx = DropboxTeam(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.check_and_refresh_access_token()
        session_instance.post.assert_called_once()

    def test_team_client_as_admin(self, session_instance):
        dbx = DropboxTeam(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.as_admin(ADMIN_ID)

    def test_team_client_as_user(self, session_instance):
        dbx = DropboxTeam(oauth2_refresh_token=REFRESH_TOKEN,
                      app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      session=session_instance)
        dbx.as_user(TEAM_MEMBER_ID)
