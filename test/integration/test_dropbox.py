#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os
import random
import re
import string
import sys
import pytest

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

from dropbox import (
    Dropbox,
    DropboxOAuth2Flow,
    DropboxTeam,
    session,
    stone_serializers,
)
from dropbox.dropbox_client import PATH_ROOT_HEADER, SELECT_USER_HEADER
from dropbox.exceptions import (
    ApiError,
    AuthError,
    BadInputError,
    PathRootError,
)
from dropbox.files import (
    DeleteResult,
    ListFolderError,
    PathOrLink,
    SharedLinkFileInfo,
)
from dropbox.common import (
    PathRoot,
    PathRoot_validator,
)

def _value_from_env_or_die(env_name='DROPBOX_TOKEN'):
    value = os.environ.get(env_name)
    if value is None:
        print('Set {} environment variable to a valid value.'.format(env_name),
              file=sys.stderr)
        sys.exit(1)
    return value


@pytest.fixture()
def dbx_from_env():
    oauth2_token = _value_from_env_or_die()
    return Dropbox(oauth2_token)


@pytest.fixture()
def refresh_dbx_from_env():
    refresh_token = _value_from_env_or_die("DROPBOX_REFRESH_TOKEN")
    app_key = _value_from_env_or_die("DROPBOX_APP_KEY")
    app_secret = _value_from_env_or_die("DROPBOX_APP_SECRET")
    return Dropbox(oauth2_refresh_token=refresh_token,
                   app_key=app_key, app_secret=app_secret)


@pytest.fixture()
def dbx_team_from_env():
    team_oauth2_token = _value_from_env_or_die('DROPBOX_TEAM_TOKEN')
    return DropboxTeam(team_oauth2_token)


@pytest.fixture()
def dbx_app_auth_from_env():
    app_key = _value_from_env_or_die("DROPBOX_APP_KEY")
    app_secret = _value_from_env_or_die("DROPBOX_APP_SECRET")
    return Dropbox(app_key=app_key, app_secret=app_secret)


@pytest.fixture()
def dbx_share_url_from_env():
    return _value_from_env_or_die("DROPBOX_SHARED_LINK")


MALFORMED_TOKEN = 'asdf'
INVALID_TOKEN = 'z' * 62

# Need bytes type for Python3
DUMMY_PAYLOAD = string.ascii_letters.encode('ascii')


@pytest.mark.usefixtures(
    "dbx_from_env", "refresh_dbx_from_env", "dbx_app_auth_from_env", "dbx_share_url_from_env"
)
class TestDropbox:
    def test_default_oauth2_urls(self):
        flow_obj = DropboxOAuth2Flow('dummy_app_key', 'dummy_app_secret',
            'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')

        assert re.match(
            r'^https://{}/oauth2/authorize\?'.format(re.escape(session.WEB_HOST)),
            flow_obj._get_authorize_url('http://localhost/redirect', 'state', 'legacy'),
        )

        assert flow_obj.build_url(
            '/oauth2/authorize'
        ) == 'https://{}/oauth2/authorize'.format(session.API_HOST)

        assert flow_obj.build_url(
            '/oauth2/authorize', host=session.WEB_HOST
        ) == 'https://{}/oauth2/authorize'.format(session.WEB_HOST)

    def test_bad_auth(self):
        # Test malformed token
        malformed_token_dbx = Dropbox(MALFORMED_TOKEN)
        with pytest.raises(BadInputError) as cm:
            malformed_token_dbx.files_list_folder('')
        assert 'token is malformed' in cm.value.message

        # Test reasonable-looking invalid token
        invalid_token_dbx = Dropbox(INVALID_TOKEN)
        with pytest.raises(AuthError) as cm:
            invalid_token_dbx.files_list_folder('')
        assert cm.value.error.is_invalid_access_token()

    def test_multi_auth(self, dbx_from_env, dbx_app_auth_from_env, dbx_share_url_from_env):
        # Test for user (with oauth token)
        preview_result, resp = dbx_from_env.files_get_thumbnail_v2(
            PathOrLink.link(SharedLinkFileInfo(url=dbx_share_url_from_env))
        )
        assert resp.status_code == 200

        # Test for app (with app key and secret)
        preview_result, resp = dbx_from_env.files_get_thumbnail_v2(
            PathOrLink.link(SharedLinkFileInfo(url=dbx_share_url_from_env))
        )
        assert resp.status_code == 200

    def test_refresh(self, refresh_dbx_from_env):
        refresh_dbx_from_env.users_get_current_account()

    def test_app_auth(self, dbx_app_auth_from_env):
        dbx_app_auth_from_env.check_app(query="hello world")

    def test_downscope(self, refresh_dbx_from_env):
        refresh_dbx_from_env.users_get_current_account()
        refresh_dbx_from_env.refresh_access_token(scope=['files.metadata.read'])
        with pytest.raises(AuthError):
            # Should fail because downscoped to not include needed scope
            refresh_dbx_from_env.users_get_current_account()

    def test_rpc(self, dbx_from_env):
        dbx_from_env.files_list_folder('')

        # Test API error
        random_folder_path = '/' + \
                             ''.join(random.sample(string.ascii_letters, 15))
        with pytest.raises(ApiError) as cm:
            dbx_from_env.files_list_folder(random_folder_path)
        assert isinstance(cm.value.error, ListFolderError)

    def test_upload_download(self, dbx_from_env):
        # Upload file
        timestamp = str(datetime.datetime.utcnow())
        random_filename = ''.join(random.sample(string.ascii_letters, 15))
        random_path = '/Test/%s/%s' % (timestamp, random_filename)
        test_contents = DUMMY_PAYLOAD
        dbx_from_env.files_upload(test_contents, random_path)

        # Download file
        _, resp = dbx_from_env.files_download(random_path)
        assert DUMMY_PAYLOAD == resp.content

        # Cleanup folder
        dbx_from_env.files_delete('/Test/%s' % timestamp)

    def test_bad_upload_types(self, dbx_from_env):
        with pytest.raises(TypeError):
            dbx_from_env.files_upload(BytesIO(b'test'), '/Test')

    def test_clone_when_user_linked(self, dbx_from_env):
        new_dbx = dbx_from_env.clone()
        assert dbx_from_env is not new_dbx
        assert isinstance(new_dbx, dbx_from_env.__class__)

    def test_with_path_root_constructor(self, dbx_from_env):
        # Verify valid mode types
        for path_root in (
            PathRoot.home,
            PathRoot.root("123"),
            PathRoot.namespace_id("123"),
        ):
            dbx_new = dbx_from_env.with_path_root(path_root)
            assert dbx_new is not dbx_from_env

            expected = stone_serializers.json_encode(PathRoot_validator, path_root)
            assert dbx_new._headers.get(PATH_ROOT_HEADER) == expected

        # verify invalid mode raises ValueError
        with pytest.raises(ValueError):
            dbx_from_env.with_path_root(None)

    def test_path_root(self, dbx_from_env):
        root_info = dbx_from_env.users_get_current_account().root_info
        root_ns = root_info.root_namespace_id
        home_ns = root_info.home_namespace_id

        # verify home mode
        dbxpr = dbx_from_env.with_path_root(PathRoot.home)
        dbxpr.files_list_folder('')

        # verify root mode
        dbxpr = dbx_from_env.with_path_root(PathRoot.root(root_ns))
        dbxpr.files_list_folder('')

        # verify namespace_id mode
        dbxpr = dbx_from_env.with_path_root(PathRoot.namespace_id(home_ns))
        dbxpr.files_list_folder('')

    def test_path_root_err(self, dbx_from_env):
        # verify invalid namespace return is_no_permission error
        dbxpr = dbx_from_env.with_path_root(PathRoot.namespace_id("1234567890"))
        with pytest.raises(PathRootError) as cm:
            dbxpr.files_list_folder('')
        assert cm.value.error.is_no_permission()

        dbxpr = dbx_from_env.with_path_root(PathRoot.root("1234567890"))
        with pytest.raises(PathRootError) as cm:
            dbxpr.files_list_folder('')
        assert cm.value.error.is_invalid_root()

    def test_versioned_route(self, dbx_from_env):
        # Upload a test file
        path = '/test.txt'
        dbx_from_env.files_upload(DUMMY_PAYLOAD, path)

        # Delete the file with v2 route
        resp = dbx_from_env.files_delete_v2(path)
        # Verify response type is of v2 route
        assert isinstance(resp, DeleteResult)

@pytest.mark.usefixtures("dbx_team_from_env")
class TestDropboxTeam:
    def test_team(self, dbx_team_from_env):
        dbx_team_from_env.team_groups_list()
        r = dbx_team_from_env.team_members_list()
        if r.members:
            # Only test assuming a member if there is a member
            team_member_id = r.members[0].profile.team_member_id
            dbx_team_from_env.as_user(team_member_id).files_list_folder('')

    def test_as_user(self, dbx_team_from_env):
        dbx_as_user = dbx_team_from_env.as_user('1')
        path_root = PathRoot.root("123")

        dbx_new = dbx_as_user.with_path_root(path_root)

        assert isinstance(dbx_new, Dropbox)
        assert dbx_new._headers.get(SELECT_USER_HEADER) == '1'

        expected = stone_serializers.json_encode(PathRoot_validator, path_root)
        assert dbx_new._headers.get(PATH_ROOT_HEADER) == expected

    def test_as_admin(self, dbx_team_from_env):
        dbx_as_admin = dbx_team_from_env.as_admin('1')
        assert isinstance(dbx_as_admin, Dropbox)

    def test_clone_when_team_linked(self, dbx_team_from_env):
        new_dbxt = dbx_team_from_env.clone()
        assert dbx_team_from_env is not new_dbxt
        assert isinstance(new_dbxt, dbx_team_from_env.__class__)
