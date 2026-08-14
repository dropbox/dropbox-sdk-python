#!/usr/bin/env python

import os
import threading
from datetime import datetime

import pytest
import requests

import dropbox.file_transfer as file_transfer
from dropbox import files
from dropbox.content_hash import content_hash
from dropbox.file_transfer import (
    Bytes,
    BytesUpload,
    DownloadOptions,
    Downloader,
    FileUpload,
    ReaderUpload,
    SizedReaderUpload,
    TransferError,
    UploadOptions,
    Uploader,
    download_file,
    upload_file,
)


def _metadata(path, data, rev="123456789"):
    return files.FileMetadata(
        name=os.path.basename(path),
        id="id:file",
        client_modified=datetime(2026, 1, 1),
        server_modified=datetime(2026, 1, 1),
        rev=rev,
        size=len(data),
        path_lower=path.lower(),
        path_display=path,
        content_hash=content_hash(data),
    )


class _Response(object):
    def __init__(self, data, fail_after=None):
        self._data = data
        self._fail_after = fail_after
        self._pos = 0
        self.closed = False

    def read(self, size=-1):
        if self._fail_after is not None and self._pos >= self._fail_after:
            raise EOFError("lost response")
        if size is None or size < 0:
            size = len(self._data) - self._pos
        if self._fail_after is not None:
            size = min(size, self._fail_after - self._pos)
        end = min(len(self._data), self._pos + size)
        chunk = self._data[self._pos : end]
        self._pos = end
        return chunk

    def close(self):
        self.closed = True


class _IterContentOnlyResponse(object):
    def __init__(self, data):
        self._data = data
        self.closed = False

    def iter_content(self, chunk_size):
        for index in range(0, len(self._data), chunk_size):
            yield self._data[index : index + chunk_size]

    def close(self):
        self.closed = True


class _FakeDropbox(object):
    def __init__(self, data=b""):
        self.data = data
        self.download_calls = []
        self.next_session_id = "session-1"
        self.concurrent_session = False
        self.chunks = {}
        self.uploaded = {}
        self.append_calls = 0
        self.finish_calls = 0
        self.finish_bodies = []
        self.append_committed_lost_response = False
        self.finish_committed_lost_response = False
        self.lock = threading.Lock()

    def files_download(self, path, rev=None, extra_headers=None):
        start = 0
        end = len(self.data)
        if extra_headers and "Range" in extra_headers:
            start_text, end_text = extra_headers["Range"].removeprefix("bytes=").split("-", 1)
            start = int(start_text)
            end = len(self.data) if not end_text else int(end_text) + 1
        self.download_calls.append((start, end - start if extra_headers else None))
        return _metadata(path, self.data), _Response(self.data[start:end])

    def files_upload_session_start(self, f, close=False, session_type=None, content_hash=None):
        self.concurrent_session = (
            session_type is not None and getattr(session_type, "is_concurrent", lambda: False)()
        )
        return files.UploadSessionStartResult(self.next_session_id)

    def files_upload_session_append_v2(self, f, cursor, close=False, content_hash=None):
        assert content_hash == globals()["content_hash"](f)
        with self.lock:
            self.append_calls += 1
            self.chunks[cursor.offset] = f
            if self.append_committed_lost_response and self.append_calls == 1:
                raise _EndpointError(
                    files.UploadSessionAppendError.incorrect_offset(
                        files.UploadSessionOffsetError(cursor.offset + len(f))
                    )
                )

    def files_upload_session_finish(self, f, cursor, commit, content_hash=None):
        assert content_hash == globals()["content_hash"](f)
        with self.lock:
            self.finish_calls += 1
            self.finish_bodies.append(f)
            if f:
                self.chunks[cursor.offset] = f
            if self.finish_committed_lost_response and self.finish_calls == 1:
                raise _EndpointError(
                    files.UploadSessionFinishError.lookup_failed(
                        files.UploadSessionLookupError.incorrect_offset(
                            files.UploadSessionOffsetError(cursor.offset + len(f))
                        )
                    )
                )
            data = b"".join(self.chunks[offset] for offset in sorted(self.chunks))
            self.uploaded[commit.path] = data
            return _metadata(commit.path, data)


class _EndpointError(Exception):
    def __init__(self, endpoint_error):
        super(_EndpointError, self).__init__("endpoint error")
        self.endpoint_error = endpoint_error


def test_download_bytes_target():
    dbx = _FakeDropbox(b"hello download")
    target = Bytes()
    progress = []

    result = Downloader(dbx).download(
        "/remote.txt",
        target,
        DownloadOptions(progress=progress.append),
    )

    assert result.metadata.size == len(b"hello download")
    assert target.bytes() == b"hello download"
    assert dbx.download_calls == [(0, None)]
    assert [p.bytes_committed for p in progress] == [len(b"hello download")]


def test_download_file_target_commits_temp_file(tmp_path):
    dbx = _FakeDropbox(b"file target")
    local = tmp_path / "download.txt"

    result = download_file(dbx, "/remote.txt", str(local))

    assert result.metadata.path_display == "/remote.txt"
    assert local.read_bytes() == b"file target"
    assert not list(tmp_path.glob("*.part"))


def test_parallel_download_uses_ranged_requests_and_progress():
    data = b"0123456789"
    dbx = _FakeDropbox(data)
    target = Bytes()
    progress = []

    result = Downloader(dbx).download(
        "/parallel.txt",
        target,
        DownloadOptions(parallel_downloads=3, progress=progress.append),
    )

    assert result.metadata.size == len(data)
    assert target.bytes() == data
    assert dbx.download_calls[0] == (0, 1)
    assert sorted(dbx.download_calls[1:]) == [(1, 3), (4, 3), (7, 3)]
    assert progress[-1].bytes_committed == len(data)
    assert progress[-1].total_bytes == len(data)


def test_parallel_download_uses_public_range_headers():
    class HeaderAwareDropbox(_FakeDropbox):
        def files_download(self, path, rev=None, extra_headers=None):
            self.download_calls.append((path, rev, extra_headers))
            byte_range = extra_headers["Range"]
            start, end = byte_range.removeprefix("bytes=").split("-", 1)
            start = int(start)
            end = len(self.data) - 1 if not end else int(end)
            return _metadata(path, self.data), _Response(self.data[start : end + 1])

    dbx = HeaderAwareDropbox(b"0123456789")
    target = Bytes()

    Downloader(dbx).download(
        "/parallel.txt",
        target,
        DownloadOptions(parallel_downloads=3),
    )

    assert target.bytes() == b"0123456789"
    assert dbx.download_calls[0][2] == {"Range": "bytes=0-0"}
    assert sorted(call[2]["Range"] for call in dbx.download_calls[1:]) == [
        "bytes=1-3",
        "bytes=4-6",
        "bytes=7-9",
    ]


def test_download_handles_partial_target_writes():
    class PartialWriteTarget(object):
        def __init__(self):
            self.info = None
            self.data = None
            self.committed = False

        def prepare(self, info):
            self.info = info
            self.data = bytearray(info.size)

        def write_at(self, data, offset):
            count = min(1, len(data))
            self.data[offset : offset + count] = data[:count]
            return count

        def commit(self):
            assert content_hash(bytes(self.data)) == self.info.content_hash
            self.committed = True

        def abort(self, cause=None):
            self.data = None

    target = PartialWriteTarget()

    Downloader(_FakeDropbox(b"abcdef")).download("/remote.txt", target)

    assert target.committed
    assert target.data == b"abcdef"


def test_download_rejects_metadata_change_during_retry():
    class ChangingMetadataDropbox(_FakeDropbox):
        def files_download(self, path, rev=None, extra_headers=None):
            start = 0
            if extra_headers:
                start = int(extra_headers["Range"].removeprefix("bytes=").split("-", 1)[0])
            self.download_calls.append((start, None))
            rev = "123456789" if len(self.download_calls) == 1 else "987654321"
            fail_after = 3 if len(self.download_calls) == 1 else None
            return _metadata(path, self.data, rev=rev), _Response(self.data[start:], fail_after)

    with pytest.raises(TransferError, match="remote file changed"):
        Downloader(ChangingMetadataDropbox(b"abcdef")).download("/remote.txt", Bytes())


def test_download_retries_request_failure(monkeypatch):
    monkeypatch.setattr(file_transfer, "_wait_for_retry", lambda attempt, max_attempts: None)

    class FlakyRequestDropbox(_FakeDropbox):
        def files_download(self, path, rev=None, extra_headers=None):
            start = 0
            if extra_headers:
                start = int(extra_headers["Range"].removeprefix("bytes=").split("-", 1)[0])
            self.download_calls.append((start, None))
            if len(self.download_calls) == 1:
                raise EOFError("request failed")
            return _metadata(path, self.data), _Response(self.data[start:])

    target = Bytes()
    result = Downloader(FlakyRequestDropbox(b"abcdef")).download("/remote.txt", target)

    assert result.metadata.size == 6
    assert target.bytes() == b"abcdef"


@pytest.mark.parametrize(
    "error_type",
    [
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ChunkedEncodingError,
    ],
)
def test_download_retries_requests_transport_failures(monkeypatch, error_type):
    monkeypatch.setattr(file_transfer, "_wait_for_retry", lambda attempt, max_attempts: None)

    class FlakyRequestDropbox(_FakeDropbox):
        def files_download(self, path, rev=None, extra_headers=None):
            if not self.download_calls:
                self.download_calls.append((0, None))
                raise error_type("transport failure")
            return super(FlakyRequestDropbox, self).files_download(path, rev, extra_headers)

    target = Bytes()

    Downloader(FlakyRequestDropbox(b"abcdef")).download("/remote.txt", target)

    assert target.bytes() == b"abcdef"


def test_download_accepts_requests_style_response_body():
    class RequestsStyleDropbox(_FakeDropbox):
        def files_download(self, path, rev=None, extra_headers=None):
            start = 0
            if extra_headers:
                start = int(extra_headers["Range"].removeprefix("bytes=").split("-", 1)[0])
            self.download_calls.append((start, None))
            return _metadata(path, self.data), _IterContentOnlyResponse(self.data[start:])

    target = Bytes()
    Downloader(RequestsStyleDropbox(b"abcdef")).download("/remote.txt", target)

    assert target.bytes() == b"abcdef"


def test_upload_bytes_source_sequential():
    dbx = _FakeDropbox()
    progress = []

    result = Uploader(dbx).upload(
        BytesUpload(b"hello upload"),
        files.CommitInfo("/upload.txt"),
        UploadOptions(progress=progress.append),
    )

    assert result.metadata.size == len(b"hello upload")
    assert dbx.uploaded["/upload.txt"] == b"hello upload"
    assert [p.bytes_committed for p in progress] == [len(b"hello upload")]


def test_upload_file_wrapper(tmp_path):
    local = tmp_path / "upload.txt"
    local.write_bytes(b"file upload")
    dbx = _FakeDropbox()

    result = upload_file(dbx, str(local), files.CommitInfo("/upload.txt"))

    assert result.metadata.path_display == "/upload.txt"
    assert dbx.uploaded["/upload.txt"] == b"file upload"


def test_upload_reader_unknown_size_reports_negative_total():
    dbx = _FakeDropbox()
    progress = []

    Uploader(dbx).upload(
        ReaderUpload(_Response(b"streamed")),
        files.CommitInfo("/streamed.txt"),
        UploadOptions(progress=progress.append),
    )

    assert dbx.uploaded["/streamed.txt"] == b"streamed"
    assert progress[-1].total_bytes == -1


def test_upload_sized_reader_rejects_declared_size_mismatch():
    with pytest.raises(TransferError, match="expected 10"):
        Uploader(_FakeDropbox()).upload(
            SizedReaderUpload(_Response(b"short"), 10),
            files.CommitInfo("/short.txt"),
        )


def test_parallel_upload_uses_concurrent_session():
    dbx = _FakeDropbox()
    progress = []

    result = Uploader(dbx).upload(
        BytesUpload(b"abcdef"),
        files.CommitInfo("/parallel.bin"),
        UploadOptions(parallel_uploads=3, progress=progress.append),
    )

    assert result.metadata.size == 6
    assert dbx.concurrent_session
    assert dbx.uploaded["/parallel.bin"] == b"abcdef"
    assert progress[-1].bytes_committed == 6


def test_parallel_upload_rejects_one_shot_source():
    with pytest.raises(TransferError, match="ranged upload source"):
        Uploader(_FakeDropbox()).upload(
            ReaderUpload(_Response(b"data")),
            files.CommitInfo("/data.txt"),
            UploadOptions(parallel_uploads=2),
        )


def test_append_incorrect_offset_after_committed_chunk_is_success(monkeypatch):
    monkeypatch.setattr(file_transfer, "UPLOAD_CHUNK_SIZE", 3)
    dbx = _FakeDropbox()
    dbx.append_committed_lost_response = True

    Uploader(dbx).upload(BytesUpload(b"abcdef"), files.CommitInfo("/retry.bin"))

    assert dbx.append_calls == 2
    assert dbx.chunks == {0: b"abc", 3: b"def"}
    assert dbx.uploaded["/retry.bin"] == b"abcdef"


def test_finish_incorrect_offset_retries_with_empty_body():
    dbx = _FakeDropbox()
    dbx.finish_committed_lost_response = True

    Uploader(dbx).upload(BytesUpload(b"abcdef"), files.CommitInfo("/retry-finish.bin"))

    assert dbx.finish_calls == 2
    assert dbx.finish_bodies == [b"abcdef", b""]
    assert dbx.uploaded["/retry-finish.bin"] == b"abcdef"


def test_file_upload_source_validates_ranges(tmp_path):
    local = tmp_path / "source.bin"
    local.write_bytes(b"abc")
    source = FileUpload(str(local))

    with pytest.raises(TransferError, match="exceeds source size"):
        source.open_range(2, 2)
