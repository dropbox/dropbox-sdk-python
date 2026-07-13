#!/usr/bin/env python

import hashlib
import io

import pytest

from dropbox.content_hash import (
    DropboxContentHasher,
    StreamHasher,
    content_hash,
)

BLOCK_SIZE = DropboxContentHasher.BLOCK_SIZE

# SHA-256 of empty input; the content hash of empty content.
EMPTY_HASH = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


def _reference_hash(data):
    # Independent reference implementation of the block-based algorithm.
    block_hashes = b''
    for i in range(0, len(data), BLOCK_SIZE):
        block_hashes += hashlib.sha256(data[i:i + BLOCK_SIZE]).digest()
    return hashlib.sha256(block_hashes).hexdigest()


class TestContentHash:

    def test_empty(self):
        assert content_hash(b'') == EMPTY_HASH

    def test_single_block(self):
        data = b'hello world'
        assert content_hash(data) == _reference_hash(data)

    def test_exact_block_boundary(self):
        data = b'a' * BLOCK_SIZE
        assert content_hash(data) == _reference_hash(data)

    def test_multiple_blocks(self):
        data = b'a' * (BLOCK_SIZE + 123)
        assert content_hash(data) == _reference_hash(data)

    def test_update_in_chunks_matches_single_update(self):
        data = b'x' * (BLOCK_SIZE * 2 + 500)
        chunked = DropboxContentHasher()
        for i in range(0, len(data), 1000):
            chunked.update(data[i:i + 1000])
        assert chunked.hexdigest() == content_hash(data)

    def test_digest_and_hexdigest_agree(self):
        data = b'some bytes'
        h1 = DropboxContentHasher()
        h1.update(data)
        h2 = DropboxContentHasher()
        h2.update(data)
        assert h1.digest().hex() == h2.hexdigest()

    def test_update_rejects_non_bytes(self):
        hasher = DropboxContentHasher()
        with pytest.raises(AssertionError):
            hasher.update(u'not bytes')

    def test_cannot_reuse_after_digest(self):
        hasher = DropboxContentHasher()
        hasher.update(b'data')
        hasher.hexdigest()
        with pytest.raises(AssertionError):
            hasher.update(b'more')

    def test_copy_is_independent(self):
        h = DropboxContentHasher()
        h.update(b'prefix')
        c = h.copy()
        assert c.digest_size == h.digest_size
        h.update(b'-original')
        c.update(b'-copy')
        assert h.hexdigest() != c.hexdigest()


class TestStreamHasher:

    def test_read_hashes_passthrough(self):
        data = b'streamed content'
        hasher = DropboxContentHasher()
        wrapped = StreamHasher(io.BytesIO(data), hasher)
        read_back = wrapped.read()
        assert read_back == data
        assert hasher.hexdigest() == content_hash(data)

    def test_write_hashes_passthrough(self):
        data = b'written content'
        hasher = DropboxContentHasher()
        out = io.BytesIO()
        wrapped = StreamHasher(out, hasher)
        wrapped.write(data)
        assert out.getvalue() == data
        assert hasher.hexdigest() == content_hash(data)

    def test_readlines_hashes_and_returns_all_lines(self):
        lines = [b'first\n', b'second\n']
        hasher = DropboxContentHasher()
        wrapped = StreamHasher(io.BytesIO(b''.join(lines)), hasher)
        assert wrapped.readlines() == lines
        assert hasher.hexdigest() == content_hash(b''.join(lines))

    def test_readlines_empty_stream(self):
        hasher = DropboxContentHasher()
        wrapped = StreamHasher(io.BytesIO(), hasher)
        assert wrapped.readlines() == []
        assert hasher.hexdigest() == content_hash(b'')

    def test_python3_iteration_hashes_passthrough(self):
        data = b'first\nsecond\n'
        hasher = DropboxContentHasher()
        wrapped = StreamHasher(io.BytesIO(data), hasher)
        assert list(wrapped) == [b'first\n', b'second\n']
        assert hasher.hexdigest() == content_hash(data)

    def test_next_compatibility_method_hashes_passthrough(self):
        data = b'first\nsecond\n'
        hasher = DropboxContentHasher()
        wrapped = StreamHasher(io.BytesIO(data), hasher)
        assert wrapped.next() == b'first\n'
        assert wrapped.next() == b'second\n'
        with pytest.raises(StopIteration):
            wrapped.next()
        assert hasher.hexdigest() == content_hash(data)
