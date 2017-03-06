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
    DropboxOAuth2Flow,
    DropboxTeam,
    session,
)
from dropbox.exceptions import (
    ApiError,
    AuthError,
    BadInputError,
)
from dropbox.files import (
    ListFolderError,
)

def _token_from_env_or_die(env_name='DROPBOX_TOKEN'):
    oauth2_token = os.environ.get(env_name)
    if oauth2_token is None:
        print('Set {} environment variable to a valid token.'.format(env_name),
              file=sys.stderr)
        sys.exit(1)
    return oauth2_token

def dbx_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        oauth2_token = _token_from_env_or_die()
        args += (Dropbox(oauth2_token),)
        return f(self, *args, **kwargs)
    return wrapped

def dbx_team_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        team_oauth2_token = _token_from_env_or_die('DROPBOX_TEAM_TOKEN')
        args += (DropboxTeam(team_oauth2_token),)
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
            flow_obj._get_authorize_url('http://localhost/redirect', 'state'),
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

    @dbx_team_from_env
    def test_team(self, dbxt):
        dbxt.team_groups_list()
        r = dbxt.team_members_list()
        if r.members:
            # Only test assuming a member if there is a member
            team_member_id = r.members[0].profile.team_member_id
            dbxt.as_user(team_member_id).files_list_folder('')

if __name__ == '__main__':
    unittest.main()
