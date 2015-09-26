from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os
import random
import string
import sys
import unittest

from dropbox import Dropbox
from dropbox.exceptions import (
    ApiError,
    AuthError,
    BadInputError,
)
from dropbox.files import (
    ListFolderError,
)

# Get token from environment variable.
oauth2_token = os.environ.get('DROPBOX_TOKEN')
if oauth2_token is None:
    print('Set DROPBOX_TOKEN environment variable to a valid token.',
          file=sys.stderr)
    sys.exit(1)

MALFORMED_TOKEN = 'asdf'
INVALID_TOKEN = 'z' * 62


class TestDropbox(unittest.TestCase):

    def setUp(self):
        self.dbx = Dropbox(oauth2_token)

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
        self.assertEqual(cm.exception.error['error']['.tag'],
                         'invalid_access_token')

    def test_rpc(self):
        self.dbx.files_list_folder('')

        # Test API error
        random_folder_path = '/' + \
                             ''.join(random.sample(string.ascii_letters, 15))
        with self.assertRaises(ApiError) as cm:
            self.dbx.files_list_folder(random_folder_path)
        self.assertIsInstance(cm.exception.error, ListFolderError)

    def test_upload_download(self):
        # Upload file
        timestamp = str(datetime.datetime.utcnow())
        random_filename = ''.join(random.sample(string.ascii_letters, 15))
        random_path = '/Test/%s/%s' % (timestamp, random_filename)
        test_contents = string.ascii_letters
        self.dbx.files_upload(test_contents, random_path)

        # Download file
        metadata, resp = self.dbx.files_download(random_path)
        self.assertEqual(string.ascii_letters, resp.text)

        # Cleanup folder
        self.dbx.files_delete('/Test/%s' % timestamp)


from dropbox import client

class TestV1DropboxClient(unittest.TestCase):

    def setUp(self):
        pass

    def test_upload(self):
        print("Hello!")


import json
import os
import posixpath
import six
import sys
import threading
from uuid import UUID

from dropbox import session, client
from dropbox.rest import ErrorResponse

if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

try:
    import json
except ImportError:
    import simplejson as json

PY3 = sys.version_info[0] == 3

class BaseClientTests(unittest.TestCase):

    def setUp(self):
        """Creates the API client and decides on a test directory."""
        self.client = client.DropboxClient(oauth2_token)

        self.test_dir = "/Test/%s" % str(datetime.datetime.utcnow())

        local_test_dir = os.path.dirname(__file__)
        self.foo = os.path.join(local_test_dir, 'foo.txt')
        self.frog = os.path.join(local_test_dir, 'Costa Rican Frog.jpg')
        self.song = os.path.join(local_test_dir, 'dropbox_song.mp3')

    def tearDown(self):
        try:
            self.client.file_delete(self.test_dir)
        except ErrorResponse as e:
            if 'not found' not in e.body['error']:
                raise

    def upload_file(self, src, target, **kwargs):
        with open(src, 'rb') as f:
            return self.client.put_file(target, f, **kwargs)

    def dict_has(self, dictionary, *args, **kwargs):
        for key in args:
            self.assertTrue(key in dictionary)
        for (key, value) in kwargs.items():
            self.assertEqual(value, dictionary[key])

    def assert_file(self, dictionary, filename, *args, **kwargs):
        import os
        defaults = dict(
            bytes = os.path.getsize(filename),
            is_dir = False
        )
        combined = dict(list(defaults.items()) + list(kwargs.items()))
        self.dict_has(dictionary, *args,
            **combined
        )

    def test_account_info(self):
        """Tests if the account_info returns the expected fields."""
        account_info = self.client.account_info()
        self.dict_has(account_info,
            "country",
            "display_name",
            "referral_link",
            "quota_info",
            "uid"
        )

    def test_put_file(self):
        """Tests if put_file returns the expected metadata"""
        def test_put(file, path):
            file_path = posixpath.join(self.test_dir, path)
            f = open(file, "rb")
            metadata = self.client.put_file(file_path, f)
            self.assert_file(metadata, file, path = file_path)
        test_put(self.foo, "put_foo.txt")
        test_put(self.song, "put_song.mp3")
        test_put(self.frog, "put_frog.jpg")

    def test_put_file_overwrite(self):
        """Tests if put_file with overwrite=true returns the expected metadata"""
        path = posixpath.join(self.test_dir, "foo_overwrite.txt")
        self.upload_file(self.foo, path)
        f = StringIO("This Overwrites")
        metadata = self.client.put_file(path, f, overwrite=True)
        self.dict_has(metadata,
            size = "15 bytes",
            bytes = 15,
            is_dir = False,
            path = path,
            mime_type = "text/plain"
        )

    def test_get_file(self):
        """Tests if storing and retrieving a file returns the same file"""
        def test_get(file, path):
            file_path = posixpath.join(self.test_dir, path)
            self.upload_file(file, file_path)
            downloaded = self.client.get_file(file_path).read()
            local = open(file, "rb").read()
            self.assertEqual(len(downloaded), len(local))
            self.assertEqual(downloaded, local)
        test_get(self.foo, "get_foo.txt")
        test_get(self.frog, "get_frog.txt")
        test_get(self.song, "get_song.txt")

    def test_get_partial_file(self):
        """Tests if storing a file and retrieving part of it returns the correct part"""
        def test_get(file, path, start_frac, download_frac):
            file_path = posixpath.join(self.test_dir, path)
            self.upload_file(file, file_path)
            local = open(file, "rb").read()
            local_len = len(local)

            download_start = int(start_frac * local_len) if start_frac is not None else None
            download_length = int(download_frac * local_len) if download_frac is not None else None
            downloaded = self.client.get_file(file_path, start=download_start,
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
        test_get(self.foo, "get_foo.txt", 0.25, 0.5)
        test_get(self.frog, "get_frog.txt", None, 0.5)
        test_get(self.song, "get_song.txt", 0.25, None)

    def test_metadata(self):
        """Tests if metadata returns the expected values for a files uploaded earlier"""
        path = posixpath.join(self.test_dir, "foo_upload.txt")
        self.upload_file(self.foo, path)
        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.foo, path = path)

        # Test root metadata
        self.client.metadata('/')
        self.client.metadata('')

    def test_metadata_bad(self):
        """Tests if metadata returns an error for nonexistent file"""
        self.assertRaises(
            ErrorResponse,
            lambda: self.client.metadata(posixpath.join(self.test_dir, "foo_does_not_exist.txt"))
        )

    def test_create_folder(self):
        """Tests if creating a folder works"""
        path = posixpath.join(self.test_dir, u"new_fold\xe9r")
        metadata = self.client.file_create_folder(path)
        self.dict_has(metadata,
                      size="0 bytes",
                      bytes=0,
                      is_dir=True,
                      path=path)

    def test_create_folder_dupe(self):
        """Tests if creating a folder fails correctly if one already exists"""
        path = posixpath.join(self.test_dir,  u"new_fold\xe9r_dupe")
        self.client.file_create_folder(path)
        self.assertRaises(
            ErrorResponse,
            lambda: self.client.file_create_folder(path)
        )

    def test_delete(self):
        """Tests if deleting a file really makes it disappear"""
        path = posixpath.join(self.test_dir, u"d\xe9lfoo.txt")
        self.upload_file(self.foo, path)
        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.foo, path = path)
        self.client.file_delete(path)

        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.foo,
            path = path,
            bytes = 0,
            size = "0 bytes",
            is_deleted = True
        )

    def test_copy(self):
        """Tests copying a file, to ensure that two copies exist after the operation"""
        path = posixpath.join(self.test_dir, "copyfoo.txt")
        path2 = posixpath.join(self.test_dir, "copyfoo2.txt")
        self.upload_file(self.foo, path)
        self.client.file_copy(path, path2)
        metadata = self.client.metadata(path)
        metadata2 = self.client.metadata(path2)
        self.assert_file(metadata, self.foo, path = path)
        self.assert_file(metadata2, self.foo, path = path2)

    def test_move(self):
        """Tests moving a file, to ensure the new copy exists and the old copy is removed"""
        path = posixpath.join(self.test_dir, "movefoo.txt")
        path2 = posixpath.join(self.test_dir, "movefoo2.txt")
        self.upload_file(self.foo, path)
        self.client.file_move(path, path2)

        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.foo, path = path, is_deleted = True, size = "0 bytes", bytes = 0)

        metadata = self.client.metadata(path2)
        self.assert_file(metadata, self.foo, path = path2)

    def test_thumbnail(self):
        path = posixpath.join(self.test_dir, "frog.jpeg")
        orig_md = self.upload_file(self.frog, path)
        path = orig_md['path']

        for fmt in ('JPEG', 'PNG'):
            prev_len = 0
            for ident in ('xs', 's', 'm', 'l', 'xl'):
                with self.client.thumbnail(path, ident, fmt) as r:
                    data1 = r.read()
                r, md = self.client.thumbnail_and_metadata(path, ident, fmt)
                with r:
                    data2 = r.read()
                self.assertEquals(data1, data2)
                # Make sure the amount of data returned increases as we increase the size.
                self.assertTrue(len(data1) > prev_len)
                prev_len = len(data1)

        # Make sure the default is 'm'
        with self.client.thumbnail(path, 'm') as r:
            data_m = r.read()
        with self.client.thumbnail(path) as r:
            data1 = r.read()
        r, md = self.client.thumbnail_and_metadata(path)
        with r:
            data2 = r.read()
        self.assertEqual(data_m, data1)
        self.assertEqual(data_m, data2)

    def test_stream(self):
        """Tests file streaming using the /media endpoint"""
        path = posixpath.join(self.test_dir, "stream_song.mp3")
        self.upload_file(self.song, path)
        link = self.client.media(path)
        self.dict_has(link,
            "url",
            "expires",
        )

    def test_share(self):
        """Tests file streaming using the /media endpoint"""
        path = posixpath.join(self.test_dir, "stream_song.mp3")
        self.upload_file(self.song, path)
        link = self.client.share(path)
        self.dict_has(link,
            "url",
            "expires",
        )

    def test_search(self):
        """Tests searching for a file in a folder"""
        path = posixpath.join(self.test_dir, "search/")

        j = posixpath.join
        self.upload_file(self.foo, j(path, "text.txt"))
        self.upload_file(self.foo, j(path, u"t\xe9xt.txt"))
        self.upload_file(self.foo, j(path, "subFolder/text.txt"))
        self.upload_file(self.foo, j(path, "subFolder/cow.txt"))
        self.upload_file(self.frog, j(path, "frog.jpg"))
        self.upload_file(self.frog, j(path, "frog2.jpg"))
        self.upload_file(self.frog, j(path, "subFolder/frog2.jpg"))

        results = self.client.search(path, "sasdfasdf")
        self.assertEquals(results, [])

        results = self.client.search(path, "jpg")
        self.assertEquals(len(results), 3)
        for metadata in results:
            self.assert_file(metadata, self.frog)

        results = self.client.search(j(path, "subFolder"), "jpg")
        self.assertEquals(len(results), 1)
        self.assert_file(results[0], self.frog)

        all_tex_files = {j(path, n) for n in ["text.txt", u"t\xe9xt.txt", "subFolder/text.txt"]}

        results = self.client.search(path, "tex")
        self.assertEquals({r["path"] for r in results}, all_tex_files)

        results = self.client.search(path, u"t\xe9x")
        self.assertEquals({r["path"] for r in results}, all_tex_files)

    def test_revisions_restore(self):
        """Tests getting the old revisions of a file"""
        path = posixpath.join(self.test_dir, "foo_revs.txt")
        self.upload_file(self.foo, path)
        self.upload_file(self.frog, path, overwrite = True)
        self.upload_file(self.song, path, overwrite = True)
        revs = self.client.revisions(path)
        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.song, path = path, mime_type = "text/plain")

        self.assertEquals(len(revs), 3)
        self.assert_file(revs[0], self.song, path = path, mime_type = "text/plain")
        self.assert_file(revs[1], self.frog, path = path, mime_type = "text/plain")
        self.assert_file(revs[2], self.foo, path = path, mime_type = "text/plain")

        metadata = self.client.restore(path, revs[2]["rev"])
        self.assert_file(metadata, self.foo, path = path, mime_type = "text/plain")
        metadata = self.client.metadata(path)
        self.assert_file(metadata, self.foo, path = path, mime_type = "text/plain")

    def test_copy_ref(self):
        """Tests using the /copy_ref endpoint to move data within a single dropbox"""
        path = posixpath.join(self.test_dir, "foo_copy_ref.txt")
        path2 = posixpath.join(self.test_dir, "foo_copy_ref_target.txt")

        self.upload_file(self.foo, path)
        copy_ref = self.client.create_copy_ref(path)
        self.dict_has(copy_ref,
            "expires",
            "copy_ref"
        )

        self.client.add_copy_ref(copy_ref["copy_ref"], path2)
        metadata = self.client.metadata(path2)
        self.assert_file(metadata, self.foo, path = path2)
        copied_foo = self.client.get_file(path2).read()
        local_foo = open(self.foo, "rb").read()
        self.assertEqual(len(copied_foo), len(local_foo))
        self.assertEqual(copied_foo, local_foo)


    def test_chunked_upload(self):
        target_path = posixpath.join(self.test_dir, 'chunked_upload_file.txt')
        chunk_size = 4 * 1024
        random_string1, random_data1 = make_random_data(chunk_size)
        random_string2, random_data2 = make_random_data(chunk_size)

        new_offset, upload_id = self.client.upload_chunk(StringIO(random_string1), 0)
        self.assertEquals(new_offset, chunk_size)
        self.assertIsNotNone(upload_id)

        new_offset, upload_id2 = self.client.upload_chunk(StringIO(random_string2), 0,
                                                          new_offset, upload_id)
        self.assertEquals(new_offset, chunk_size * 2)
        self.assertEquals(upload_id2, upload_id)

        metadata = self.client.commit_chunked_upload('/auto' + target_path, upload_id,
                                                     overwrite=True)
        self.dict_has(metadata, bytes=chunk_size * 2, path=target_path)

        downloaded = self.client.get_file(target_path).read()
        self.assertEquals(chunk_size * 2, len(downloaded))
        self.assertEquals(random_data1, downloaded[:chunk_size])
        self.assertEquals(random_data2, downloaded[chunk_size:])

    def test_chunked_uploader(self):
        path = posixpath.join(self.test_dir, "chunked_uploader_file.txt")
        size = 10 * 1024 * 1024
        chunk_size = 4 * 1024 * 1102
        random_string, random_data = make_random_data(size)
        uploader = self.client.get_chunked_uploader(StringIO(random_string), len(random_string))
        error_count = 0
        while uploader.offset < size and error_count < 5:
            try:
                upload = uploader.upload_chunked(chunk_size=chunk_size)
            except ErrorResponse as e:
                error_count += 1
        uploader.finish(path)
        downloaded = self.client.get_file(path).read()
        self.assertEquals(size, len(downloaded))
        self.assertEquals(random_data, downloaded)

    def test_delta(self):
        prefix = posixpath.join(self.test_dir, "delta")

        a = posixpath.join(prefix, "a.txt")
        self.upload_file(self.foo, a)
        b = posixpath.join(prefix, "b.txt")
        self.upload_file(self.foo, b)
        c = posixpath.join(prefix, "c")
        c_1 = posixpath.join(prefix, "c/1.txt")
        self.upload_file(self.foo, c_1)
        c_2 = posixpath.join(prefix, "c/2.txt")
        self.upload_file(self.foo, c_2)

        prefix_lc = prefix.lower()
        c_lc = c.lower()

        # /delta on everything
        expected = { p.lower() for p in (prefix, a, b, c, c_1, c_2) }
        entries = set()
        cursor = None
        while True:
            r = self.client.delta(cursor)
            if r['reset']: entries = set()
            for path_lc, md in r['entries']:
                if path_lc.startswith(prefix_lc+'/') or path_lc == prefix_lc:
                    assert md is not None, "we should never get deletes under 'prefix'"
                    entries.add(path_lc)
            if not r['has_more']: break
            cursor = r['cursor']

        self.assertEqual(expected, entries)

        # /delta where path_prefix=c
        expected = { p.lower() for p in (c, c_1, c_2) }
        entries = set()
        cursor = None
        while True:
            r = self.client.delta(cursor, path_prefix=c)
            if r['reset']: entries = set()
            for path_lc, md in r['entries']:
                assert path_lc.startswith(c_lc+'/') or path_lc == c_lc
                assert md is not None, "we should never get deletes"
                entries.add(path_lc)
            if not r['has_more']: break
            cursor = r['cursor']

        self.assertEqual(expected, entries)

    def test_longpoll_delta(self):
        cursor = self.client.delta()['cursor']

        def assert_longpoll():
            r = self.client.longpoll_delta(cursor)
            assert (r['changes'])

        t = threading.Thread(target=assert_longpoll)
        t.start()

        self.upload_file(self.foo, posixpath.join(self.test_dir, "foo.txt"))
        t.join()


def make_random_data(size):
    random_data = os.urandom(size)
    if PY3:
        random_string = random_data.decode('latin1')
    else:
        random_string = random_data
    return random_string, random_data
