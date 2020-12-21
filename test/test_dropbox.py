#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import functools
import os
import random
import re
import six
import string
import sys
import unittest

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

from dropbox import (
    Dropbox,
    DropboxAppAuth,
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
)
from dropbox.common import (
    PathRoot,
    PathRoot_validator,
)

def _value_from_env_or_die(env_name='DROPBOX_TOKEN'):
    oauth2_token = os.environ.get(env_name)
    if oauth2_token is None:
        print('Set {} environment variable to a valid token.'.format(env_name),
              file=sys.stderr)
        sys.exit(1)
    return oauth2_token

def dbx_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        oauth2_token = _value_from_env_or_die()
        args += (Dropbox(oauth2_token),)
        return f(self, *args, **kwargs)
    return wrapped

def refresh_dbx_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        refresh_token = _value_from_env_or_die("DROPBOX_REFRESH_TOKEN")
        app_key = _value_from_env_or_die("DROPBOX_APP_KEY")
        app_secret = _value_from_env_or_die("DROPBOX_APP_SECRET")
        args += (Dropbox(oauth2_refresh_token=refresh_token,
                         app_key=app_key, app_secret=app_secret),)
        return f(self, *args, **kwargs)
    return wrapped

def dbx_team_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        team_oauth2_token = _value_from_env_or_die('DROPBOX_TEAM_TOKEN')
        args += (DropboxTeam(team_oauth2_token),)
        return f(self, *args, **kwargs)
    return wrapped


def dbx_app_auth_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        app_key = _value_from_env_or_die("DROPBOX_APP_KEY")
        app_secret = _value_from_env_or_die("DROPBOX_APP_SECRET")
        args += (DropboxAppAuth(app_key=app_key, app_secret=app_secret),)
        return f(self, *args, **kwargs)
    return wrapped


MALFORMED_TOKEN = 'asdf'
INVALID_TOKEN = 'z' * 62

# Need bytes type for Python3
DUMMY_PAYLOAD = string.ascii_letters.encode('ascii')

class TestDropbox(unittest.TestCase):

    def test_default_oauth2_urls(self):
        flow_obj = DropboxOAuth2Flow('dummy_app_key', 'dummy_app_secret',
            'http://localhost/dummy', 'dummy_session', 'dbx-auth-csrf-token')

        six.assertRegex(
            self,
            flow_obj._get_authorize_url('http://localhost/redirect', 'state', 'legacy'),
            r'^https://{}/oauth2/authorize\?'.format(re.escape(session.WEB_HOST)),
        )

        self.assertEqual(
            flow_obj.build_url('/oauth2/authorize'),
            'https://{}/oauth2/authorize'.format(session.API_HOST),
        )

        self.assertEqual(
            flow_obj.build_url('/oauth2/authorize', host=session.WEB_HOST),
            'https://{}/oauth2/authorize'.format(session.WEB_HOST),
        )

    def test_bad_auth(self):
        # Test malformed token
        malformed_token_dbx = Dropbox(MALFORMED_TOKEN)
        with self.assertRaises(BadInputError) as cm:
            malformed_token_dbx.files_list_folder('')
        self.assertIn('token is malformed', cm.exception.message)

        # Test reasonable-looking invalid token
        invalid_token_dbx = Dropbox(INVALID_TOKEN)
        with self.assertRaises(AuthError) as cm:
            invalid_token_dbx.files_list_folder('')
        self.assertTrue(cm.exception.error.is_invalid_access_token())

    @refresh_dbx_from_env
    def test_refresh(self, dbx):
        dbx.users_get_current_account()

    @dbx_app_auth_from_env
    def test_app_auth(self, dbx_app_auth):
        dbx_app_auth.check_app(query="hello world")

    @refresh_dbx_from_env
    def test_downscope(self, dbx):
        dbx.users_get_current_account()
        dbx.refresh_access_token(scope=['files.metadata.read'])
        with self.assertRaises(AuthError):
            # Should fail because downscoped to not include needed scope
            dbx.users_get_current_account()

    @dbx_from_env
    def test_rpc(self, dbx):
        dbx.files_list_folder('')

        # Test API error
        random_folder_path = '/' + \
                             ''.join(random.sample(string.ascii_letters, 15))
        with self.assertRaises(ApiError) as cm:
            dbx.files_list_folder(random_folder_path)
        self.assertIsInstance(cm.exception.error, ListFolderError)

    @dbx_from_env
    def test_upload_download(self, dbx):
        # Upload file
        timestamp = str(datetime.datetime.utcnow())
        random_filename = ''.join(random.sample(string.ascii_letters, 15))
        random_path = '/Test/%s/%s' % (timestamp, random_filename)
        test_contents = DUMMY_PAYLOAD
        dbx.files_upload(test_contents, random_path)

        # Download file
        _, resp = dbx.files_download(random_path)
        self.assertEqual(DUMMY_PAYLOAD, resp.content)

        # Cleanup folder
        dbx.files_delete('/Test/%s' % timestamp)

    @dbx_from_env
    def test_bad_upload_types(self, dbx):
        with self.assertRaises(TypeError):
            dbx.files_upload(BytesIO(b'test'), '/Test')

    @dbx_from_env
    def test_clone_when_user_linked(self, dbx):
        new_dbx = dbx.clone()
        self.assertIsNot(dbx, new_dbx)
        self.assertIsInstance(new_dbx, dbx.__class__)

    @dbx_from_env
    def test_with_path_root_constructor(self, dbx):
        # Verify valid mode types
        for path_root in (
            PathRoot.home,
            PathRoot.root("123"),
            PathRoot.namespace_id("123"),
        ):
            dbx_new = dbx.with_path_root(path_root)
            self.assertIsNot(dbx_new, dbx)

            expected = stone_serializers.json_encode(PathRoot_validator, path_root)
            self.assertEqual(dbx_new._headers.get(PATH_ROOT_HEADER), expected)

        # verify invalid mode raises ValueError
        with self.assertRaises(ValueError):
            dbx.with_path_root(None)

    @dbx_from_env
    def test_path_root(self, dbx):
        root_info = dbx.users_get_current_account().root_info
        root_ns = root_info.root_namespace_id
        home_ns = root_info.home_namespace_id

        # verify home mode
        dbxpr = dbx.with_path_root(PathRoot.home)
        dbxpr.files_list_folder('')

        # verify root mode
        dbxpr = dbx.with_path_root(PathRoot.root(root_ns))
        dbxpr.files_list_folder('')

        # verify namespace_id mode
        dbxpr = dbx.with_path_root(PathRoot.namespace_id(home_ns))
        dbxpr.files_list_folder('')

    @dbx_from_env
    def test_path_root_err(self, dbx):
        # verify invalid namespace return is_no_permission error
        dbxpr = dbx.with_path_root(PathRoot.namespace_id("1234567890"))
        with self.assertRaises(PathRootError) as cm:
            dbxpr.files_list_folder('')
        self.assertTrue(cm.exception.error.is_no_permission())

        dbxpr = dbx.with_path_root(PathRoot.root("1234567890"))
        with self.assertRaises(PathRootError) as cm:
            dbxpr.files_list_folder('')
        self.assertTrue(cm.exception.error.is_invalid_root())

    @dbx_from_env
    def test_versioned_route(self, dbx):
        # Upload a test file
        path = '/test.txt'
        dbx.files_upload(DUMMY_PAYLOAD, path)

        # Delete the file with v2 route
        resp = dbx.files_delete_v2(path)
        # Verify response type is of v2 route
        self.assertIsInstance(resp, DeleteResult)

class TestDropboxTeam(unittest.TestCase):
    @dbx_team_from_env
    def test_team(self, dbxt):
        dbxt.team_groups_list()
        r = dbxt.team_members_list()
        if r.members:
            # Only test assuming a member if there is a member
            team_member_id = r.members[0].profile.team_member_id
            dbxt.as_user(team_member_id).files_list_folder('')

    @dbx_team_from_env
    def test_as_user(self, dbxt):
        dbx_as_user = dbxt.as_user('1')
        path_root = PathRoot.root("123")

        dbx_new = dbx_as_user.with_path_root(path_root)

        self.assertIsInstance(dbx_new, Dropbox)
        self.assertEqual(dbx_new._headers.get(SELECT_USER_HEADER), '1')

        expected = stone_serializers.json_encode(PathRoot_validator, path_root)
        self.assertEqual(dbx_new._headers.get(PATH_ROOT_HEADER), expected)

    @dbx_team_from_env
    def test_as_admin(self, dbxt):
        dbx_as_admin = dbxt.as_admin('1')
        self.assertIsInstance(dbx_as_admin, Dropbox)

    @dbx_team_from_env
    def test_clone_when_team_linked(self, dbxt):
        new_dbxt = dbxt.clone()
        self.assertIsNot(dbxt, new_dbxt)
        self.assertIsInstance(new_dbxt, dbxt.__class__)

if __name__ == '__main__':
    unittest.main()
