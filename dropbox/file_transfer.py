"""
Reliable upload and download helpers for Dropbox files.

The generated ``files_*`` methods remain the low-level API. This module adds a
small transfer layer modeled after the Go SDK's ``filetransfer`` package:
download targets, upload sources, retries, progress callbacks, content
validation, and optional parallel ranged transfers.
"""

from __future__ import absolute_import

import contextlib
import io
import os
import random
import tempfile
import threading
import time
from dataclasses import dataclass
from urllib import request as urllib_request

import requests

from dropbox import files
from dropbox.content_hash import DropboxContentHasher, content_hash
from dropbox.exceptions import ApiError, HttpError, InternalServerError, RateLimitError


DOWNLOAD_CHUNK_SIZE = 32 * 1024
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024
DEFAULT_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 0.2
RETRY_MAX_DELAY = 5.0


@dataclass(frozen=True)
class DownloadInfo:
    size: int
    content_hash: str = None


@dataclass(frozen=True)
class DownloadOptions:
    max_attempts: int = 0
    parallel_downloads: int = 0
    progress: object = None


@dataclass(frozen=True)
class DownloadProgress:
    bytes_committed: int
    total_bytes: int


@dataclass(frozen=True)
class DownloadResult:
    metadata: files.FileMetadata


@dataclass(frozen=True)
class UploadOptions:
    max_attempts: int = 0
    parallel_uploads: int = 0
    progress: object = None


@dataclass(frozen=True)
class UploadProgress:
    bytes_committed: int
    total_bytes: int


@dataclass(frozen=True)
class UploadResult:
    metadata: files.FileMetadata


class TransferError(Exception):
    """Raised when transfer setup or validation fails."""


class BytesTarget(object):
    """In-memory download target."""

    def __init__(self):
        self._lock = threading.RLock()
        self._info = None
        self._data = None
        self._committed = False

    def prepare(self, info):
        if info.size < 0:
            raise TransferError("download size must not be negative")
        with self._lock:
            if self._data is not None:
                raise TransferError("download target is already prepared")
            self._info = info
            self._data = bytearray(info.size)
            self._committed = False

    def write_at(self, data, offset):
        with self._lock:
            if self._data is None:
                raise TransferError("download target is not prepared")
            if offset < 0 or offset > len(self._data):
                raise TransferError("invalid write offset: {}".format(offset))
            end = offset + len(data)
            if end > len(self._data):
                raise IOError("short write")
            self._data[offset:end] = data
            return len(data)

    def commit(self):
        with self._lock:
            if self._data is None or self._info is None:
                raise TransferError("download target is not prepared")
            if self._info.content_hash:
                actual = content_hash(bytes(self._data))
                if actual != self._info.content_hash:
                    raise TransferError(
                        'download content hash mismatch: got "{}", expected "{}"'.format(
                            actual, self._info.content_hash
                        )
                    )
            self._committed = True
            self._info = None

    def abort(self, cause=None):
        with self._lock:
            self._info = None
            self._data = None
            self._committed = False

    def bytes(self):
        with self._lock:
            if not self._committed:
                return None
            return bytes(self._data)


class FileTarget(object):
    """File download target that commits by atomically renaming a temp file."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._info = None
        self._file = None
        self._temp_path = None

    def prepare(self, info):
        if info.size < 0:
            raise TransferError("download size must not be negative")
        with self._lock:
            if self._file is not None:
                raise TransferError("download target is already prepared")
            directory = os.path.dirname(os.path.abspath(self.path)) or "."
            prefix = "." + os.path.basename(self.path) + "."
            fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".part", dir=directory)
            f = os.fdopen(fd, "r+b")
            try:
                f.truncate(info.size)
            except Exception:
                f.close()
                with contextlib.suppress(OSError):
                    os.remove(temp_path)
                raise
            self._info = info
            self._file = f
            self._temp_path = temp_path

    def write_at(self, data, offset):
        with self._lock:
            if self._file is None:
                raise TransferError("download target is not prepared")
            self._file.seek(offset)
            written = self._file.write(data)
            if written != len(data):
                raise IOError("short write")
            return written

    def commit(self):
        with self._lock:
            if self._file is None or self._temp_path is None or self._info is None:
                raise TransferError("download target is not prepared")
            self._file.flush()
            stat_size = os.fstat(self._file.fileno()).st_size
            if stat_size != self._info.size:
                raise TransferError(
                    "download size mismatch: got {} bytes, expected {}".format(
                        stat_size, self._info.size
                    )
                )
            if self._info.content_hash:
                self._file.seek(0)
                hasher = DropboxContentHasher()
                while True:
                    chunk = self._file.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                actual = hasher.hexdigest()
                if actual != self._info.content_hash:
                    raise TransferError(
                        'download content hash mismatch: got "{}", expected "{}"'.format(
                            actual, self._info.content_hash
                        )
                    )
            self._file.close()
            self._file = None
            os.replace(self._temp_path, self.path)
            self._temp_path = None
            self._info = None

    def abort(self, cause=None):
        with self._lock:
            if self._file is not None:
                with contextlib.suppress(Exception):
                    self._file.close()
                self._file = None
            if self._temp_path:
                with contextlib.suppress(OSError):
                    os.remove(self._temp_path)
                self._temp_path = None
            self._info = None


def Bytes():
    return BytesTarget()


def File(path):
    return FileTarget(path)


class FileSource(object):
    def __init__(self, path):
        self.path = path
        stat = os.stat(path)
        if not os.path.isfile(path):
            raise TransferError("upload source is not a regular file: {}".format(path))
        self._size = stat.st_size

    def size(self):
        return self._size

    def open(self):
        return self.open_range(0, self._size)

    def open_range(self, offset, length):
        _validate_range(self._size, offset, length)
        return _SectionReader(open(self.path, "rb"), offset, length)


class BytesSource(object):
    def __init__(self, data):
        self._data = bytes(data)

    def size(self):
        return len(self._data)

    def open(self):
        return self.open_range(0, len(self._data))

    def open_range(self, offset, length):
        _validate_range(len(self._data), offset, length)
        return io.BytesIO(self._data[offset : offset + length])


class ReaderSource(object):
    def __init__(self, reader, size=None):
        if reader is None:
            raise TransferError("upload reader is required")
        if size is not None and size < 0:
            raise TransferError("upload size must not be negative")
        self._reader = reader
        self._size = size
        self._opened = False
        self._lock = threading.Lock()

    def size(self):
        if self._size is None:
            return -1
        return self._size

    def open(self):
        with self._lock:
            if self._opened:
                raise TransferError("upload source has already been opened")
            self._opened = True
            return _ReaderCloser(self._reader)


def FileUpload(path):
    return FileSource(path)


def BytesUpload(data):
    return BytesSource(data)


def ReaderUpload(reader):
    return ReaderSource(reader)


def SizedReaderUpload(reader, size):
    return ReaderSource(reader, size=size)


def HTTPUpload(url, timeout=None):
    response = urllib_request.urlopen(url, timeout=timeout)
    size_header = response.headers.get("Content-Length")
    size = int(size_header) if size_header else None
    return ReaderSource(response, size=size)


class Downloader(object):
    def __init__(self, client):
        self.client = client

    def download(self, remote_path, target, options=None):
        if self.client is None:
            raise TransferError("download client is required")
        if not remote_path:
            raise TransferError("download path is required")
        if target is None:
            raise TransferError("download target is required")
        options = options or DownloadOptions()
        max_attempts = options.max_attempts if options.max_attempts > 0 else DEFAULT_MAX_ATTEMPTS
        if options.parallel_downloads > 1:
            return self._download_with_parallel_fallback(
                remote_path, target, max_attempts, options.parallel_downloads, options.progress
            )
        return self._download_sequential(remote_path, target, max_attempts, options.progress)

    def download_file(self, dropbox_path, local_path, rev=None, progress=None):
        if rev is not None:
            dropbox_path = "rev:{}".format(rev)
        return self.download(dropbox_path, File(local_path), DownloadOptions(progress=progress))

    def _download_with_parallel_fallback(
        self, remote_path, target, max_attempts, parallel_downloads, progress
    ):
        try:
            metadata, info, first_written = self._prepare_parallel_download(
                remote_path, target, max_attempts
            )
        except ApiError as err:
            if _is_unsatisfiable_initial_range(err):
                return self._download_sequential(remote_path, target, max_attempts, progress)
            raise
        return self._download_prepared_parallel(
            remote_path,
            target,
            metadata,
            info,
            first_written,
            max_attempts,
            parallel_downloads,
            progress,
        )

    def _download_sequential(self, remote_path, target, max_attempts, progress):
        metadata = None
        info = None
        prepared = False
        committed = 0
        tracker = None
        last_err = None
        try:
            for attempt in range(max_attempts):
                try:
                    metadata_response, body = self._download_range_retryable(
                        remote_path, committed, None
                    )
                except Exception as err:
                    if not _is_retryable_transfer_error(err):
                        raise
                    last_err = err
                    _wait_for_retry(attempt, max_attempts)
                    continue
                if body is None:
                    last_err = TransferError("download response body is nil")
                    _wait_for_retry(attempt, max_attempts)
                    continue
                try:
                    if not prepared:
                        metadata, info = _download_metadata(metadata_response)
                        target.prepare(info)
                        tracker = _ProgressTracker(info.size, progress, DownloadProgress)
                        prepared = True
                    else:
                        _validate_download_metadata(metadata, metadata_response)
                    remaining = info.size - committed
                    if remaining < 0:
                        raise TransferError(
                            "download exceeded expected size: got at least {} bytes, expected {}".format(
                                committed, info.size
                            )
                        )
                    written, copy_err, retryable = _copy_download_range(
                        body, target, committed, remaining, tracker
                    )
                    committed += written
                    if copy_err is None and committed == info.size:
                        target.commit()
                        return DownloadResult(metadata)
                    if copy_err is None:
                        copy_err = TransferError(
                            "incomplete download: got {} bytes, expected {}".format(
                                committed, info.size
                            )
                        )
                        retryable = True
                    last_err = copy_err
                    if not retryable:
                        raise copy_err
                    _wait_for_retry(attempt, max_attempts)
                finally:
                    with contextlib.suppress(Exception):
                        body.close()
            raise last_err or TransferError("download failed")
        except Exception as err:
            if prepared:
                target.abort(err)
            raise

    def _prepare_parallel_download(self, remote_path, target, max_attempts):
        last_err = None
        for attempt in range(max_attempts):
            try:
                metadata, body = self._download_range_retryable(remote_path, 0, 1)
            except Exception as err:
                if not _is_retryable_transfer_error(err):
                    raise
                last_err = err
                _wait_for_retry(attempt, max_attempts)
                continue
            if body is None:
                last_err = TransferError("download response body is nil")
                _wait_for_retry(attempt, max_attempts)
                continue
            try:
                stable_metadata, info = _download_metadata(metadata)
                target.prepare(info)
                expected = 1 if info.size > 0 else 0
                tracker = _ProgressTracker(info.size, None, DownloadProgress)
                written, copy_err, retryable = _copy_download_range(
                    body, target, 0, expected, tracker
                )
                if copy_err is None and written == expected:
                    return stable_metadata, info, written
                target.abort(copy_err)
                if copy_err is None:
                    copy_err = TransferError(
                        "incomplete initial range: got {} bytes, expected {}".format(
                            written, expected
                        )
                    )
                if not retryable:
                    raise copy_err
                last_err = copy_err
                _wait_for_retry(attempt, max_attempts)
            finally:
                with contextlib.suppress(Exception):
                    body.close()
        raise last_err or TransferError("download failed")

    def _download_prepared_parallel(
        self,
        remote_path,
        target,
        metadata,
        info,
        first_written,
        max_attempts,
        parallel_downloads,
        progress,
    ):
        tracker = _ProgressTracker(info.size, progress, DownloadProgress)
        tracker.add(first_written)
        try:
            ranges = _split_ranges(first_written, info.size - first_written, parallel_downloads)
            errors = []
            lock = threading.Lock()

            def worker(byte_range):
                try:
                    self._download_byte_range(
                        remote_path, target, byte_range, metadata, max_attempts, tracker
                    )
                except Exception as err:
                    with lock:
                        errors.append(err)

            threads = [threading.Thread(target=worker, args=(r,)) for r in ranges]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            if errors:
                raise errors[0]
            if tracker.committed_bytes() != info.size:
                raise TransferError(
                    "incomplete download: committed {} of {} bytes".format(
                        tracker.committed_bytes(), info.size
                    )
                )
            target.commit()
            return DownloadResult(metadata)
        except Exception as err:
            target.abort(err)
            raise

    def _download_byte_range(
        self, remote_path, target, byte_range, metadata, max_attempts, tracker
    ):
        committed = 0
        last_err = None
        for attempt in range(max_attempts):
            remaining = byte_range.length - committed
            if remaining == 0:
                return
            try:
                response_metadata, body = self._download_range_retryable(
                    remote_path, byte_range.offset + committed, remaining
                )
            except Exception as err:
                if not _is_retryable_transfer_error(err):
                    raise
                last_err = err
                _wait_for_retry(attempt, max_attempts)
                continue
            if body is None:
                last_err = TransferError("download response body is nil")
                _wait_for_retry(attempt, max_attempts)
                continue
            try:
                _validate_download_metadata(metadata, response_metadata)
                written, copy_err, retryable = _copy_download_range(
                    body, target, byte_range.offset + committed, remaining, tracker
                )
                committed += written
                if copy_err is None and committed == byte_range.length:
                    return
                if copy_err is None:
                    copy_err = TransferError(
                        "incomplete range at offset {}: got {} bytes, expected {}".format(
                            byte_range.offset, committed, byte_range.length
                        )
                    )
                    retryable = True
                if not retryable:
                    raise copy_err
                last_err = copy_err
                _wait_for_retry(attempt, max_attempts)
            finally:
                with contextlib.suppress(Exception):
                    body.close()
        raise last_err or TransferError("download range failed")

    def _download_range_retryable(self, remote_path, offset, length):
        if offset or length is not None:
            return _files_download_range(self.client, remote_path, offset, length)
        metadata, body = self.client.files_download(remote_path)
        return metadata, _readable_response(body)


class Uploader(object):
    def __init__(self, client):
        self.client = client

    def upload(self, source, commit_info, options=None):
        if self.client is None:
            raise TransferError("upload client is required")
        if source is None:
            raise TransferError("upload source is required")
        if commit_info is None:
            raise TransferError("upload commit info is required")
        if not isinstance(commit_info, files.CommitInfo):
            commit_info = files.CommitInfo(commit_info)
        if not commit_info.path:
            raise TransferError("upload destination path is required")
        options = options or UploadOptions()
        max_attempts = options.max_attempts if options.max_attempts > 0 else DEFAULT_MAX_ATTEMPTS
        if options.parallel_uploads > 1:
            if not hasattr(source, "open_range") or not hasattr(source, "size"):
                raise TransferError("parallel uploads require a ranged upload source")
            if source.size() == 0:
                return self._upload_sequential(source, commit_info, max_attempts, options.progress)
            return self._upload_parallel(
                source, commit_info, max_attempts, options.parallel_uploads, options.progress
            )
        return self._upload_sequential(source, commit_info, max_attempts, options.progress)

    def upload_file(self, local_path, commit_info, progress=None):
        return self.upload(FileUpload(local_path), commit_info, UploadOptions(progress=progress))

    def _upload_sequential(self, source, commit_info, max_attempts, progress):
        total = source.size() if hasattr(source, "size") else -1
        if total < -1:
            raise TransferError("upload size must not be negative")
        tracker = _ProgressTracker(total, progress, UploadProgress)
        reader = source.open()
        try:
            start = self._start_upload_session(max_attempts)
            offset = 0
            while True:
                chunk, eof = _read_upload_chunk(reader, UPLOAD_CHUNK_SIZE)
                if total >= 0 and offset + len(chunk) > total:
                    raise TransferError(
                        "read upload content: got more than declared size {}".format(total)
                    )
                if eof:
                    if total >= 0 and offset + len(chunk) != total:
                        raise TransferError(
                            "read upload content: got {} bytes, expected {}".format(
                                offset + len(chunk), total
                            )
                        )
                    metadata = self._finish_upload(
                        start.session_id, offset, commit_info, chunk, max_attempts
                    )
                    if metadata is None:
                        raise TransferError("upload metadata is nil")
                    tracker.add(len(chunk))
                    return UploadResult(metadata)
                if len(chunk) == 0:
                    raise TransferError("read upload content: no progress")
                self._append_upload(start.session_id, offset, chunk, False, max_attempts)
                offset += len(chunk)
                tracker.add(len(chunk))
        finally:
            with contextlib.suppress(Exception):
                reader.close()

    def _upload_parallel(self, source, commit_info, max_attempts, parallel_uploads, progress):
        size = source.size()
        if size < 0:
            raise TransferError("upload size must not be negative")
        start = self._start_upload_session(max_attempts, concurrent=True)
        tracker = _ProgressTracker(size, progress, UploadProgress)
        ranges = _split_upload_ranges(size)
        errors = []
        lock = threading.Lock()
        jobs = ranges[:-1]
        final_range = ranges[-1] if ranges else None

        def worker(byte_range):
            try:
                self._upload_byte_range(source, start.session_id, byte_range, max_attempts, tracker)
            except Exception as err:
                with lock:
                    errors.append(err)

        workers = min(parallel_uploads, len(jobs))
        active = []
        for byte_range in jobs:
            thread = threading.Thread(target=worker, args=(byte_range,))
            active.append(thread)
            thread.start()
            if len(active) >= workers:
                active[0].join()
                active = active[1:]
            if errors:
                break
        for thread in active:
            thread.join()
        if errors:
            raise errors[0]
        if final_range is not None:
            self._upload_byte_range(source, start.session_id, final_range, max_attempts, tracker)
        if tracker.committed_bytes() != size:
            raise TransferError(
                "incomplete upload: committed {} of {} bytes".format(
                    tracker.committed_bytes(), size
                )
            )
        metadata = self._finish_upload(start.session_id, size, commit_info, b"", max_attempts)
        if metadata is None:
            raise TransferError("upload metadata is nil")
        return UploadResult(metadata)

    def _upload_byte_range(self, source, session_id, byte_range, max_attempts, tracker):
        reader = source.open_range(byte_range.offset, byte_range.length)
        try:
            data = reader.read()
        finally:
            with contextlib.suppress(Exception):
                reader.close()
        if len(data) != byte_range.length:
            raise TransferError(
                "read upload range: got {} bytes, expected {}".format(len(data), byte_range.length)
            )
        self._append_upload(session_id, byte_range.offset, data, byte_range.close, max_attempts)
        tracker.add(byte_range.length)

    def _start_upload_session(self, max_attempts, concurrent=False):
        last_err = None
        for attempt in range(max_attempts):
            try:
                session_type = files.UploadSessionType.concurrent if concurrent else None
                start = self.client.files_upload_session_start(b"", session_type=session_type)
                if start is None or not start.session_id:
                    raise TransferError("upload session id is empty")
                return start
            except Exception as err:
                if not _is_retryable_transfer_error(err):
                    raise
                last_err = err
                _wait_for_retry(attempt, max_attempts)
        raise last_err or TransferError("upload session start failed")

    def _append_upload(self, session_id, offset, data, close, max_attempts):
        last_err = None
        for attempt in range(max_attempts):
            try:
                cursor = files.UploadSessionCursor(session_id, offset)
                self.client.files_upload_session_append_v2(
                    data, cursor, close=close, content_hash=content_hash(data)
                )
                return
            except Exception as err:
                correct_offset = _upload_append_correct_offset(err)
                if correct_offset is not None:
                    expected_offset = offset + len(data)
                    if correct_offset == expected_offset:
                        return
                    if correct_offset == offset:
                        last_err = err
                        _wait_for_retry(attempt, max_attempts)
                        continue
                    raise TransferError(
                        "upload session offset mismatch: got {}, expected {} or {}".format(
                            correct_offset, offset, expected_offset
                        )
                    )
                if not _is_retryable_transfer_error(err):
                    raise
                last_err = err
                _wait_for_retry(attempt, max_attempts)
        raise last_err or TransferError("upload append failed")

    def _finish_upload(self, session_id, offset, commit_info, data, max_attempts):
        last_err = None
        for attempt in range(max_attempts):
            try:
                cursor = files.UploadSessionCursor(session_id, offset)
                return self.client.files_upload_session_finish(
                    data, cursor, commit_info, content_hash=content_hash(data)
                )
            except Exception as err:
                correct_offset = _upload_finish_correct_offset(err)
                if correct_offset is not None:
                    expected_offset = offset + len(data)
                    if correct_offset == expected_offset:
                        offset = correct_offset
                        data = b""
                    elif correct_offset != offset:
                        raise TransferError(
                            "upload session offset mismatch: got {}, expected {} or {}".format(
                                correct_offset, offset, expected_offset
                            )
                        )
                    last_err = err
                    _wait_for_retry(attempt, max_attempts)
                    continue
                if not _is_retryable_transfer_error(err):
                    raise
                last_err = err
                _wait_for_retry(attempt, max_attempts)
        raise last_err or TransferError("upload finish failed")


def download_file(dbx, dropbox_path, local_path, **kwargs):
    return Downloader(dbx).download_file(dropbox_path, local_path, **kwargs)


def upload_file(dbx, local_path, commit_info, **kwargs):
    return Uploader(dbx).upload_file(local_path, commit_info, **kwargs)


class _ProgressTracker(object):
    def __init__(self, total, callback, progress_type):
        self.total = total
        self.callback = callback
        self.progress_type = progress_type
        self.committed = 0
        self.lock = threading.Lock()

    def add(self, count):
        if count <= 0:
            return
        with self.lock:
            self.committed += count
            if self.callback:
                self.callback(self.progress_type(self.committed, self.total))

    def committed_bytes(self):
        with self.lock:
            return self.committed


@dataclass(frozen=True)
class _ByteRange:
    offset: int
    length: int
    close: bool = False


class _SectionReader(object):
    def __init__(self, f, offset, length):
        self._file = f
        self._remaining = length
        self._file.seek(offset)

    def read(self, size=-1):
        if self._remaining <= 0:
            return b""
        if size is None or size < 0 or size > self._remaining:
            size = self._remaining
        data = self._file.read(size)
        self._remaining -= len(data)
        return data

    def close(self):
        return self._file.close()


class _ReaderCloser(object):
    def __init__(self, reader):
        self._reader = reader

    def read(self, size=-1):
        return self._reader.read(size)

    def close(self):
        close = getattr(self._reader, "close", None)
        if close:
            return close()


class _ResponseReader(object):
    def __init__(self, response):
        self._response = response
        self._iterator = response.iter_content(DOWNLOAD_CHUNK_SIZE)
        self._buffer = bytearray()

    def read(self, size=-1):
        if size is None or size < 0:
            chunks = [bytes(self._buffer)]
            self._buffer.clear()
            chunks.extend(chunk for chunk in self._iterator if chunk)
            return b"".join(chunks)
        while len(self._buffer) < size:
            try:
                chunk = next(self._iterator)
            except StopIteration:
                break
            if chunk:
                self._buffer.extend(chunk)
        data = bytes(self._buffer[:size])
        del self._buffer[:size]
        return data

    def close(self):
        return self._response.close()


def _download_metadata(metadata):
    if metadata is None:
        raise TransferError("download metadata is nil")
    return metadata, DownloadInfo(int(metadata.size), getattr(metadata, "content_hash", None))


def _validate_download_metadata(expected, actual):
    if actual is None:
        raise TransferError("download metadata is nil")
    if expected is None:
        return
    expected_rev = getattr(expected, "rev", None)
    actual_rev = getattr(actual, "rev", None)
    if expected_rev and actual_rev and actual_rev != expected_rev:
        raise TransferError(
            'remote file changed during download: got rev "{}", expected "{}"'.format(
                actual_rev, expected_rev
            )
        )
    if int(actual.size) != int(expected.size):
        raise TransferError(
            "remote file size changed during download: got {}, expected {}".format(
                actual.size, expected.size
            )
        )
    expected_hash = getattr(expected, "content_hash", None)
    actual_hash = getattr(actual, "content_hash", None)
    if expected_hash and actual_hash and actual_hash != expected_hash:
        raise TransferError(
            'remote file content hash changed during download: got "{}", expected "{}"'.format(
                actual_hash, expected_hash
            )
        )


def _copy_download_range(reader, target, offset, length, progress):
    if length < 0:
        return 0, TransferError("download range length must not be negative"), False
    written = 0
    while written < length:
        remaining = length - written
        try:
            chunk = reader.read(min(DOWNLOAD_CHUNK_SIZE, remaining))
        except Exception as err:
            return written, err, True
        if not chunk:
            return written, EOFError("unexpected EOF"), True
        chunk_written = 0
        while chunk_written < len(chunk):
            try:
                count = target.write_at(chunk[chunk_written:], offset + written)
            except Exception as err:
                return written, err, False
            if count <= 0:
                return written, IOError("no progress"), False
            if count > len(chunk) - chunk_written:
                return written, TransferError("download target wrote too many bytes"), False
            chunk_written += count
            written += count
            progress.add(count)
    try:
        extra = reader.read(1)
    except Exception:
        extra = b""
    if extra:
        return written, TransferError("download response exceeded requested range"), False
    return written, None, False


def _split_ranges(offset, length, parts):
    if length <= 0:
        return []
    if parts <= 1:
        return [_ByteRange(offset, length)]
    parts = min(parts, length)
    part_size = length // parts
    remainder = length % parts
    ranges = []
    for index in range(parts):
        size = part_size + (1 if index < remainder else 0)
        ranges.append(_ByteRange(offset, size))
        offset += size
    return ranges


def _split_upload_ranges(size):
    if size == 0:
        return []
    ranges = []
    offset = 0
    while offset < size:
        length = min(UPLOAD_CHUNK_SIZE, size - offset)
        ranges.append(_ByteRange(offset, length))
        offset += length
    ranges[-1] = _ByteRange(ranges[-1].offset, ranges[-1].length, True)
    return ranges


def _read_upload_chunk(reader, limit):
    if limit <= 0:
        raise TransferError("upload chunk size must be positive")
    chunks = []
    total = 0
    while total < limit:
        data = reader.read(limit - total)
        if data is None:
            data = b""
        if not data:
            return b"".join(chunks), True
        chunks.append(data)
        total += len(data)
    return b"".join(chunks), False


def _validate_range(size, offset, length):
    if size < 0:
        raise TransferError("source size must not be negative")
    if offset < 0:
        raise TransferError("range offset must not be negative")
    if length < 0:
        raise TransferError("range length must not be negative")
    if offset > size or length > size - offset:
        raise TransferError(
            "range [{},{}) exceeds source size {}".format(offset, offset + length, size)
        )


def _wait_for_retry(attempt, max_attempts):
    if attempt + 1 >= max_attempts:
        return
    delay = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (2**attempt))
    delay = delay / 2 + random.random() * (delay / 2)
    time.sleep(delay)


def _is_retryable_transfer_error(err):
    if isinstance(err, (InternalServerError, RateLimitError, TimeoutError, EOFError)):
        return True
    if isinstance(
        err,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ),
    ):
        return True
    if isinstance(err, HttpError):
        return err.status_code == 408 or err.status_code == 429 or 500 <= err.status_code <= 599
    return isinstance(err, (ConnectionError,))


def _upload_append_correct_offset(err):
    endpoint = _api_endpoint_error(err)
    if endpoint is not None and getattr(endpoint, "is_incorrect_offset", lambda: False)():
        return endpoint.get_incorrect_offset().correct_offset
    return None


def _upload_finish_correct_offset(err):
    endpoint = _api_endpoint_error(err)
    if endpoint is not None and getattr(endpoint, "is_lookup_failed", lambda: False)():
        lookup = endpoint.get_lookup_failed()
        if getattr(lookup, "is_incorrect_offset", lambda: False)():
            return lookup.get_incorrect_offset().correct_offset
    return None


def _api_endpoint_error(err):
    if isinstance(err, ApiError):
        return err.error
    return getattr(err, "error", None) or getattr(err, "endpoint_error", None)


def _is_unsatisfiable_initial_range(err):
    return isinstance(err, ApiError) and "range/not_satisfiable" in repr(err.error)


def _files_download_range(dbx, dropbox_path, offset, length=None):
    range_header = "bytes={}-".format(offset)
    if length is not None:
        range_header = "bytes={}-{}".format(offset, offset + length - 1)
    metadata, body = dbx.files_download(
        dropbox_path,
        extra_headers={"Range": range_header},
    )
    return metadata, _readable_response(body)


def _readable_response(body):
    if hasattr(body, "read"):
        return body
    if hasattr(body, "iter_content"):
        return _ResponseReader(body)
    return body
