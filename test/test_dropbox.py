#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import functools
import os
import posixpath
import random
import string
import sys
import threading
import unittest

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

from dropbox import (
    Dropbox,
    DropboxTeam,
    client,
)
from dropbox.exceptions import (
    ApiError,
    AuthError,
    BadInputError,
)
from dropbox.files import (
    ListFolderError,
)
from dropbox.rest import ErrorResponse


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


PY3 = sys.version_info[0] == 3

def dbx_v1_client_from_env(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        oauth2_token = _token_from_env_or_die()
        args += (client.DropboxClient(oauth2_token),)
        return f(self, *args, **kwargs)
    return wrapped

def dbx_v1_client_from_env_with_test_dir(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        oauth2_token = _token_from_env_or_die()
        dbx_client = client.DropboxClient(oauth2_token)
        test_dir = "/Test/%s" % str(datetime.datetime.utcnow())
        args += (dbx_client, test_dir,)
        try:
            return f(self, *args, **kwargs)
        finally:
            try:
                dbx_client.file_delete(test_dir)
            except ErrorResponse as exc:
                if 'not found' not in exc.body['error']:
                    raise
    return wrapped


class BaseClientTests(unittest.TestCase):

    _LOCAL_TEST_DIR = os.path.dirname(__file__)
    FOO_TXT = os.path.join(_LOCAL_TEST_DIR, 'foo.txt')
    FROG_JPG = os.path.join(_LOCAL_TEST_DIR, 'Costa Rican Frog.jpg')
    SONG_MP3 = os.path.join(_LOCAL_TEST_DIR, 'dropbox_song.mp3')

    def upload_file(self, dbx_client, src, target, **kwargs):
        with open(src, 'rb') as f:
            return dbx_client.put_file(target, f, **kwargs)

    def dict_has(self, dictionary, *args, **kwargs):
        for key in args:
            self.assertTrue(key in dictionary)
        for (key, value) in kwargs.items():
            self.assertEqual(value, dictionary[key])

    def assert_file(self, dictionary, filename, *args, **kwargs):
        defaults = dict(
            bytes=os.path.getsize(filename),
            is_dir=False
        )
        combined = dict(list(defaults.items()) + list(kwargs.items()))
        self.dict_has(dictionary, *args, **combined)

    @dbx_v1_client_from_env
    def test_account_info(self, dbx_client):
        """Tests if the account_info returns the expected fields."""
        account_info = dbx_client.account_info()
        self.dict_has(
            account_info,
            "country",
            "display_name",
            "referral_link",
            "quota_info",
            "uid",
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_put_file(self, dbx_client, test_dir):
        """Tests if put_file returns the expected metadata"""
        def test_put(file, path):  # pylint: disable=redefined-builtin
            file_path = posixpath.join(test_dir, path)
            f = open(file, "rb")
            metadata = dbx_client.put_file(file_path, f)
            self.assert_file(metadata, file, path=file_path)
        test_put(self.FOO_TXT, "put_foo.txt")
        test_put(self.SONG_MP3, "put_song.mp3")
        test_put(self.FROG_JPG, "put_frog.jpg")

    @dbx_v1_client_from_env_with_test_dir
    def test_put_file_overwrite(self, dbx_client, test_dir):
        """Tests if put_file with overwrite=true returns the expected metadata"""
        path = posixpath.join(test_dir, "foo_overwrite.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        f = BytesIO(b"This Overwrites")
        metadata = dbx_client.put_file(path, f, overwrite=True)
        self.dict_has(
            metadata,
            size="15 bytes",
            bytes=15,
            is_dir=False,
            path=path,
            mime_type="text/plain",
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_get_file(self, dbx_client, test_dir):
        """Tests if storing and retrieving a file returns the same file"""
        def test_get(file, path):  # pylint: disable=redefined-builtin
            file_path = posixpath.join(test_dir, path)
            self.upload_file(dbx_client, file, file_path)
            downloaded = dbx_client.get_file(file_path).read()
            local = open(file, "rb").read()
            self.assertEqual(len(downloaded), len(local))
            self.assertEqual(downloaded, local)
        test_get(self.FOO_TXT, "get_foo.txt")
        test_get(self.FROG_JPG, "get_frog.txt")
        test_get(self.SONG_MP3, "get_song.txt")

    @dbx_v1_client_from_env_with_test_dir
    def test_get_partial_file(self, dbx_client, test_dir):
        """Tests if storing a file and retrieving part of it returns the correct part"""
        def test_get(file, path, start_frac, download_frac):  # noqa: E501; pylint: disable=redefined-builtin
            file_path = posixpath.join(test_dir, path)
            self.upload_file(dbx_client, file, file_path)
            local = open(file, "rb").read()
            local_len = len(local)

            download_start = int(start_frac * local_len) if start_frac is not None else None
            download_length = int(download_frac * local_len) if download_frac is not None else None
            downloaded = dbx_client.get_file(file_path, start=download_start,
                length=download_length).read()

            local_file = open(file, "rb")
            if download_start:
                local_file.seek(download_start)
                if download_length is None:
                    local_partial = local_file.read()
                else:
                    local_partial = local_file.read(download_length)
            elif download_length:
                local_file.seek(-1 * download_length, 2)
                local_partial = local_file.read(download_length)

            self.assertEqual(len(downloaded), len(local_partial))
            self.assertEqual(downloaded, local_partial)
        test_get(self.FOO_TXT, "get_foo.txt", 0.25, 0.5)
        test_get(self.FROG_JPG, "get_frog.txt", None, 0.5)
        test_get(self.SONG_MP3, "get_song.txt", 0.25, None)

    @dbx_v1_client_from_env_with_test_dir
    def test_metadata(self, dbx_client, test_dir):
        """Tests if metadata returns the expected values for a files uploaded earlier"""
        path = posixpath.join(test_dir, "foo_upload.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        metadata = dbx_client.metadata(path)
        self.assert_file(metadata, self.FOO_TXT, path=path)

        # Test root metadata
        dbx_client.metadata('/')
        dbx_client.metadata('')

    @dbx_v1_client_from_env_with_test_dir
    def test_metadata_bad(self, dbx_client, test_dir):
        """Tests if metadata returns an error for nonexistent file"""
        self.assertRaises(
            ErrorResponse,
            lambda: dbx_client.metadata(posixpath.join(test_dir, "foo_does_not_exist.txt"))
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_create_folder(self, dbx_client, test_dir):
        """Tests if creating a folder works"""
        path = posixpath.join(test_dir, u"new_fold\xe9r")
        metadata = dbx_client.file_create_folder(path)
        self.dict_has(metadata,
                      size="0 bytes",
                      bytes=0,
                      is_dir=True,
                      path=path)

    @dbx_v1_client_from_env_with_test_dir
    def test_create_folder_dupe(self, dbx_client, test_dir):
        """Tests if creating a folder fails correctly if one already exists"""
        path = posixpath.join(test_dir, u"new_fold\xe9r_dupe")
        dbx_client.file_create_folder(path)
        self.assertRaises(
            ErrorResponse,
            lambda: dbx_client.file_create_folder(path)
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_delete(self, dbx_client, test_dir):
        """Tests if deleting a file really makes it disappear"""
        path = posixpath.join(test_dir, u"d\xe9lfoo.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        metadata = dbx_client.metadata(path)
        self.assert_file(metadata, self.FOO_TXT, path=path)
        dbx_client.file_delete(path)

        metadata = dbx_client.metadata(path)
        self.assert_file(
            metadata,
            self.FOO_TXT,
            path=path,
            bytes=0,
            size="0 bytes",
            is_deleted=True,
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_copy(self, dbx_client, test_dir):
        """Tests copying a file, to ensure that two copies exist after the operation"""
        path = posixpath.join(test_dir, "copyfoo.txt")
        path2 = posixpath.join(test_dir, "copyfoo2.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        dbx_client.file_copy(path, path2)
        metadata = dbx_client.metadata(path)
        metadata2 = dbx_client.metadata(path2)
        self.assert_file(metadata, self.FOO_TXT, path=path)
        self.assert_file(metadata2, self.FOO_TXT, path=path2)

    @dbx_v1_client_from_env_with_test_dir
    def test_move(self, dbx_client, test_dir):
        """Tests moving a file, to ensure the new copy exists and the old copy is removed"""
        path = posixpath.join(test_dir, "movefoo.txt")
        path2 = posixpath.join(test_dir, "movefoo2.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        dbx_client.file_move(path, path2)

        metadata = dbx_client.metadata(path)
        self.assert_file(metadata, self.FOO_TXT, path=path,
            is_deleted=True, size="0 bytes", bytes=0)

        metadata = dbx_client.metadata(path2)
        self.assert_file(metadata, self.FOO_TXT, path=path2)

    @dbx_v1_client_from_env_with_test_dir
    def test_thumbnail(self, dbx_client, test_dir):
        path = posixpath.join(test_dir, "frog.jpeg")
        orig_md = self.upload_file(dbx_client, self.FROG_JPG, path)
        path = orig_md['path']

        for fmt in ('JPEG', 'PNG'):
            prev_len = 0
            for ident in ('xs', 's', 'm', 'l', 'xl'):
                with dbx_client.thumbnail(path, ident, fmt) as r:
                    data1 = r.read()
                r, _ = dbx_client.thumbnail_and_metadata(path, ident, fmt)
                with r:
                    data2 = r.read()
                self.assertEqual(data1, data2)
                # Make sure the amount of data returned increases as we increase the size.
                self.assertTrue(len(data1) > prev_len)
                prev_len = len(data1)

        # Make sure the default is 'm'
        with dbx_client.thumbnail(path, 'm') as r:
            data_m = r.read()
        with dbx_client.thumbnail(path) as r:
            data1 = r.read()
        r, _ = dbx_client.thumbnail_and_metadata(path)
        with r:
            data2 = r.read()
        self.assertEqual(data_m, data1)
        self.assertEqual(data_m, data2)

    @dbx_v1_client_from_env_with_test_dir
    def test_stream(self, dbx_client, test_dir):
        """Tests file streaming using the /media endpoint"""
        path = posixpath.join(test_dir, "stream_song.mp3")
        self.upload_file(dbx_client, self.SONG_MP3, path)
        link = dbx_client.media(path)
        self.dict_has(
            link,
            "url",
            "expires",
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_share(self, dbx_client, test_dir):
        """Tests file streaming using the /media endpoint"""
        path = posixpath.join(test_dir, "stream_song.mp3")
        self.upload_file(dbx_client, self.SONG_MP3, path)
        link = dbx_client.share(path)
        self.dict_has(
            link,
            "url",
            "expires",
        )

    @dbx_v1_client_from_env_with_test_dir
    def test_search(self, dbx_client, test_dir):
        """Tests searching for a file in a folder"""
        path = posixpath.join(test_dir, "search/")

        j = posixpath.join
        self.upload_file(dbx_client, self.FOO_TXT, j(path, "text.txt"))
        self.upload_file(dbx_client, self.FOO_TXT, j(path, u"t\xe9xt.txt"))
        self.upload_file(dbx_client, self.FOO_TXT, j(path, "subFolder/text.txt"))
        self.upload_file(dbx_client, self.FOO_TXT, j(path, "subFolder/cow.txt"))
        self.upload_file(dbx_client, self.FROG_JPG, j(path, "frog.jpg"))
        self.upload_file(dbx_client, self.FROG_JPG, j(path, "frog2.jpg"))
        self.upload_file(dbx_client, self.FROG_JPG, j(path, "subFolder/frog2.jpg"))

        results = dbx_client.search(path, "sasdfasdf")
        self.assertEqual(results, [])

        results = dbx_client.search(path, "jpg")
        self.assertEqual(len(results), 3)
        for metadata in results:
            self.assert_file(metadata, self.FROG_JPG)

        results = dbx_client.search(j(path, "subFolder"), "jpg")
        self.assertEqual(len(results), 1)
        self.assert_file(results[0], self.FROG_JPG)

        all_tex_files = {j(path, n) for n in ["text.txt", u"t\xe9xt.txt", "subFolder/text.txt"]}

        results = dbx_client.search(path, "tex")
        self.assertEqual({r["path"] for r in results}, all_tex_files)

        results = dbx_client.search(path, u"t\xe9x")
        self.assertEqual({r["path"] for r in results}, all_tex_files)

    @dbx_v1_client_from_env_with_test_dir
    def test_revisions_restore(self, dbx_client, test_dir):
        """Tests getting the old revisions of a file"""
        path = posixpath.join(test_dir, "foo_revs.txt")
        self.upload_file(dbx_client, self.FOO_TXT, path)
        self.upload_file(dbx_client, self.FROG_JPG, path, overwrite=True)
        self.upload_file(dbx_client, self.SONG_MP3, path, overwrite=True)
        revs = dbx_client.revisions(path)
        metadata = dbx_client.metadata(path)
        self.assert_file(metadata, self.SONG_MP3, path=path, mime_type="text/plain")

        self.assertEqual(len(revs), 3)
        self.assert_file(revs[0], self.SONG_MP3, path=path, mime_type="text/plain")
        self.assert_file(revs[1], self.FROG_JPG, path=path, mime_type="text/plain")
        self.assert_file(revs[2], self.FOO_TXT, path=path, mime_type="text/plain")

        metadata = dbx_client.restore(path, revs[2]["rev"])
        self.assert_file(metadata, self.FOO_TXT, path=path, mime_type="text/plain")
        metadata = dbx_client.metadata(path)
        self.assert_file(metadata, self.FOO_TXT, path=path, mime_type="text/plain")

    @dbx_v1_client_from_env_with_test_dir
    def test_copy_ref(self, dbx_client, test_dir):
        """Tests using the /copy_ref endpoint to move data within a single dropbox"""
        path = posixpath.join(test_dir, "foo_copy_ref.txt")
        path2 = posixpath.join(test_dir, "foo_copy_ref_target.txt")

        self.upload_file(dbx_client, self.FOO_TXT, path)
        copy_ref = dbx_client.create_copy_ref(path)
        self.dict_has(
            copy_ref,
            "expires",
            "copy_ref"
        )

        dbx_client.add_copy_ref(copy_ref["copy_ref"], path2)
        metadata = dbx_client.metadata(path2)
        self.assert_file(metadata, self.FOO_TXT, path=path2)
        copied_foo = dbx_client.get_file(path2).read()
        local_foo = open(self.FOO_TXT, "rb").read()
        self.assertEqual(len(copied_foo), len(local_foo))
        self.assertEqual(copied_foo, local_foo)

    @dbx_v1_client_from_env_with_test_dir
    def test_chunked_upload2(self, dbx_client, test_dir):
        target_path = posixpath.join(test_dir, 'chunked_upload_file.txt')
        chunk_size = 4 * 1024
        _, random_data1 = make_random_data(chunk_size)
        _, random_data2 = make_random_data(chunk_size)

        new_offset, upload_id = dbx_client.upload_chunk(BytesIO(random_data1), 0)
        self.assertEqual(new_offset, chunk_size)
        self.assertIsNotNone(upload_id)

        new_offset, upload_id2 = dbx_client.upload_chunk(
            BytesIO(random_data2),
            0,
            new_offset,
            upload_id,
        )
        self.assertEqual(new_offset, chunk_size * 2)
        self.assertEqual(upload_id2, upload_id)

        metadata = dbx_client.commit_chunked_upload(
            '/auto' + target_path,
            upload_id,
            overwrite=True,
        )
        self.dict_has(metadata, bytes=chunk_size * 2, path=target_path)

        downloaded = dbx_client.get_file(target_path).read()
        self.assertEqual(chunk_size * 2, len(downloaded))
        self.assertEqual(random_data1, downloaded[:chunk_size])
        self.assertEqual(random_data2, downloaded[chunk_size:])

    @dbx_v1_client_from_env_with_test_dir
    def test_chunked_uploader(self, dbx_client, test_dir):
        path = posixpath.join(test_dir, "chunked_uploader_file.txt")
        size = 10 * 1024 * 1024
        chunk_size = 4 * 1024 * 1102
        _, random_data = make_random_data(size)
        uploader = dbx_client.get_chunked_uploader(BytesIO(random_data), len(random_data))
        error_count = 0
        while uploader.offset < size and error_count < 5:
            try:
                uploader.upload_chunked(chunk_size=chunk_size)
            except ErrorResponse:
                error_count += 1
        uploader.finish(path)
        downloaded = dbx_client.get_file(path).read()
        self.assertEqual(size, len(downloaded))
        self.assertEqual(random_data, downloaded)

    @dbx_v1_client_from_env_with_test_dir
    def test_delta(self, dbx_client, test_dir):
        prefix = posixpath.join(test_dir, "delta")

        a = posixpath.join(prefix, "a.txt")
        self.upload_file(dbx_client, self.FOO_TXT, a)
        b = posixpath.join(prefix, "b.txt")
        self.upload_file(dbx_client, self.FOO_TXT, b)
        c = posixpath.join(prefix, "c")
        c_1 = posixpath.join(prefix, "c/1.txt")
        self.upload_file(dbx_client, self.FOO_TXT, c_1)
        c_2 = posixpath.join(prefix, "c/2.txt")
        self.upload_file(dbx_client, self.FOO_TXT, c_2)

        prefix_lc = prefix.lower()
        c_lc = c.lower()

        # /delta on everything
        expected = {p.lower() for p in (prefix, a, b, c, c_1, c_2)}
        entries = set()
        cursor = None
        while True:
            r = dbx_client.delta(cursor)
            if r['reset']:
                entries = set()
            for path_lc, md in r['entries']:
                if path_lc.startswith(prefix_lc + '/') or path_lc == prefix_lc:
                    assert md is not None, "we should never get deletes under 'prefix'"
                    entries.add(path_lc)
            if not r['has_more']:
                break
            cursor = r['cursor']

        self.assertEqual(expected, entries)

        # /delta where path_prefix=c
        expected = {p.lower() for p in (c, c_1, c_2)}
        entries = set()
        cursor = None
        while True:
            r = dbx_client.delta(cursor, path_prefix=c)
            if r['reset']:
                entries = set()
            for path_lc, md in r['entries']:
                assert path_lc.startswith(c_lc + '/') or path_lc == c_lc
                assert md is not None, "we should never get deletes"
                entries.add(path_lc)
            if not r['has_more']:
                break
            cursor = r['cursor']

        self.assertEqual(expected, entries)

    @dbx_v1_client_from_env_with_test_dir
    def test_longpoll_delta(self, dbx_client, test_dir):
        cursor = dbx_client.delta()['cursor']

        def assert_longpoll():
            r = dbx_client.longpoll_delta(cursor)
            assert (r['changes'])

        t = threading.Thread(target=assert_longpoll)
        t.start()

        self.upload_file(dbx_client, self.FOO_TXT, posixpath.join(test_dir, "foo.txt"))
        t.join()


def make_random_data(size):
    random_data = os.urandom(size)
    if PY3:
        random_string = random_data.decode('latin1')
    else:
        random_string = random_data
    return random_string, random_data


if __name__ == '__main__':
    unittest.main()
