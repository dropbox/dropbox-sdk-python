"""Cached credential tests: no Dropbox credentials or real HTTP requests."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Event, Lock
from unittest.mock import patch

import pytest
import requests

from dropbox import AccessTokenSnapshot, Dropbox, DropboxTeam
from dropbox.common import PathRoot
from dropbox.exceptions import AuthError


NOW = datetime(2030, 1, 2, 3, 4, 5)
OLD_EXPIRATION = NOW - timedelta(hours=1)
NEW_EXPIRATION = NOW + timedelta(hours=1)


def response(body, status=200):
    result = requests.Response()
    result.status_code = status
    result.headers["Content-Type"] = "application/json"
    result._content = json.dumps(body).encode("utf-8")
    return result


@pytest.fixture(autouse=True)
def fixed_time():
    with patch("dropbox.dropbox_client.datetime") as clock:
        clock.utcnow.return_value = NOW
        yield


@pytest.fixture
def http():
    # Patch below Session.post so unexpected requests through any HTTP method fail.
    with patch.object(
        requests.Session, "request", side_effect=AssertionError("Unexpected HTTP")
    ) as req:
        yield req


@pytest.fixture(params=[Dropbox, DropboxTeam])
def client_type(request):
    return request.param


def make_client(client_type, token="old-token", expiration=OLD_EXPIRATION):
    return client_type(
        oauth2_access_token=token,
        oauth2_access_token_expiration=expiration,
        oauth2_refresh_token="refresh-secret",
        app_key="app-key",
    )


@pytest.mark.parametrize("token", [None, ""])
def test_no_cached_token(client_type, http, token):
    client = make_client(client_type, token)
    assert client.get_access_token_snapshot() is None
    http.assert_not_called()


@pytest.mark.parametrize("expiration", [None, OLD_EXPIRATION, NEW_EXPIRATION])
def test_cached_snapshot_never_refreshes(client_type, http, expiration):
    client = make_client(client_type, expiration=expiration)
    with (
        patch.object(client, "check_and_refresh_access_token") as check,
        patch.object(client, "refresh_access_token") as refresh,
    ):
        snapshot = client.get_access_token_snapshot()
    assert isinstance(snapshot, AccessTokenSnapshot)
    assert snapshot.access_token == "old-token"
    assert snapshot.expires_at == expiration
    assert snapshot._fields == ("access_token", "expires_at")
    assert not hasattr(snapshot, "refresh_token")
    assert "old-token" not in repr(snapshot)
    assert "refresh-secret" not in repr(snapshot)
    check.assert_not_called()
    refresh.assert_not_called()
    http.assert_not_called()


@pytest.mark.parametrize("render", [repr, str], ids=["repr", "str"])
def test_snapshot_text_redacts_access_token(client_type, http, render):
    snapshot = make_client(client_type, token="sensitive-access-token").get_access_token_snapshot()
    text = render(snapshot)
    assert "sensitive-access-token" not in text
    assert "<redacted>" in text
    assert snapshot.access_token == "sensitive-access-token"
    assert tuple(snapshot) == ("sensitive-access-token", OLD_EXPIRATION)
    http.assert_not_called()


@pytest.mark.parametrize("placeholder", ["%s", "%r"])
def test_snapshot_logging_redacts_access_token(client_type, http, caplog, placeholder):
    snapshot = make_client(client_type, token="sensitive-access-token").get_access_token_snapshot()
    logger = logging.getLogger(__name__)
    with caplog.at_level(logging.WARNING, logger=__name__):
        logger.warning("Cached credentials: " + placeholder, snapshot)
    assert len(caplog.records) == 1
    assert "sensitive-access-token" not in caplog.text
    assert "<redacted>" in caplog.records[0].getMessage()
    assert snapshot.access_token == "sensitive-access-token"
    http.assert_not_called()


def test_app_credentials_without_token(client_type, http):
    assert client_type(app_key="key", app_secret="secret").get_access_token_snapshot() is None
    http.assert_not_called()


def test_snapshot_is_immutable(client_type, http):
    snapshot = make_client(client_type).get_access_token_snapshot()
    for name in ("access_token", "expires_at", "extra"):
        with pytest.raises(AttributeError):
            setattr(snapshot, name, "replacement")
    with pytest.raises(TypeError):
        snapshot[0] = "replacement"
    http.assert_not_called()


def test_explicit_refresh_keeps_old_snapshot(client_type, http):
    client = make_client(client_type)
    before = client.get_access_token_snapshot()
    http.side_effect = None
    http.return_value = response({"access_token": "new-token", "expires_in": 3600})
    assert client.refresh_access_token() is None  # Preserve the existing return value.
    assert client.get_access_token_snapshot() == AccessTokenSnapshot("new-token", NEW_EXPIRATION)
    assert before == AccessTokenSnapshot("old-token", OLD_EXPIRATION)
    assert http.call_count == 1


@pytest.mark.parametrize("token,expiration", [(None, None), ("old", None), ("old", OLD_EXPIRATION)])
def test_automatic_refresh_and_reuse(client_type, http, token, expiration):
    client = make_client(client_type, token, expiration)

    def handle(method, url, **kwargs):
        assert method == "POST"
        if url.endswith("/oauth2/token"):
            return response({"access_token": "new-token", "expires_in": 3600})
        assert kwargs["headers"]["Authorization"] == "Bearer new-token"
        if url.endswith("/team/members/list"):
            return response({"members": [], "has_more": False, "cursor": "cursor"})
        return response({"result": "ok"})

    def api_request(dbx):
        if isinstance(dbx, DropboxTeam):
            assert dbx.team_members_list().members == []
        else:
            assert dbx.check_user().result == "ok"

    http.side_effect = handle
    # A normal generated API call exercises request() and automatic refresh.
    api_request(client)
    snapshot = client.get_access_token_snapshot()
    assert snapshot == AccessTokenSnapshot("new-token", NEW_EXPIRATION)
    reused = client_type(
        oauth2_access_token=snapshot.access_token,
        oauth2_access_token_expiration=snapshot.expires_at,
        oauth2_refresh_token="refresh-secret",
        app_key="app-key",
    )
    api_request(reused)
    assert reused.get_access_token_snapshot() == snapshot
    assert http.call_count == 3  # One refresh, two API calls.
    assert sum(call.args[1].endswith("/oauth2/token") for call in http.call_args_list) == 1


@pytest.mark.parametrize("failure", ["http", "network", "json", "missing", "expiration"])
def test_failed_refresh_preserves_pair(client_type, http, failure):
    client = make_client(client_type)
    before = client.get_access_token_snapshot()
    http.side_effect = None
    if failure == "http":
        http.return_value = response({"error": "invalid_grant"}, 400)
        error = AuthError
    elif failure == "network":
        http.side_effect = requests.ConnectionError("offline")
        error = requests.ConnectionError
    elif failure == "json":
        http.return_value = response({})
        http.return_value._content = b"invalid json"
        error = ValueError
    elif failure == "missing":
        http.return_value = response({"access_token": "partial-token"})
        error = KeyError
    else:
        http.return_value = response({"access_token": "partial-token", "expires_in": "invalid"})
        error = ValueError
    with pytest.raises(error):
        client.refresh_access_token()
    assert client.get_access_token_snapshot() == before
    assert http.call_count == 1


def test_refresh_without_refresh_credentials_preserves_snapshot(client_type, http):
    client = client_type("cached-token")
    before = client.get_access_token_snapshot()
    assert client.refresh_access_token() is None
    assert client.get_access_token_snapshot() == before
    http.assert_not_called()


@pytest.mark.parametrize("factory", ["clone", "with_path_root", "as_user", "as_admin"])
@pytest.mark.parametrize("token", [None, "old-token"])
def test_clones_copy_credentials_and_refresh_independently(http, factory, token):
    client = make_client(DropboxTeam, token)
    if factory == "clone":
        child = client.clone()
    elif factory == "with_path_root":
        child = client.with_path_root(PathRoot.home)
    else:
        child = getattr(client, factory)("member-id")
    before = client.get_access_token_snapshot()
    assert child.get_access_token_snapshot() == before
    assert type(child) is (Dropbox if factory in ("as_user", "as_admin") else DropboxTeam)
    assert child._session is client._session
    http.assert_not_called()
    http.side_effect = None
    http.return_value = response({"access_token": "child-token", "expires_in": 3600})
    child.refresh_access_token()
    assert client.get_access_token_snapshot() == before
    child_snapshot = child.get_access_token_snapshot()
    assert child_snapshot == AccessTokenSnapshot("child-token", NEW_EXPIRATION)
    http.return_value = response({"access_token": "parent-token", "expires_in": 7200})
    client.refresh_access_token()
    assert child.get_access_token_snapshot() == child_snapshot


def test_clone_overrides_preserve_existing_fallbacks(client_type, http):
    client = make_client(client_type)
    assert client.clone().get_access_token_snapshot() == client.get_access_token_snapshot()
    assert client.with_path_root(PathRoot.home).get_access_token_snapshot() == (
        client.get_access_token_snapshot()
    )
    assert client.clone(oauth2_access_token="override").get_access_token_snapshot() == (
        AccessTokenSnapshot("override", OLD_EXPIRATION)
    )
    assert client.clone(
        oauth2_access_token_expiration=NEW_EXPIRATION
    ).get_access_token_snapshot() == (AccessTokenSnapshot("old-token", NEW_EXPIRATION))
    http.assert_not_called()


def test_concurrent_refreshes_and_reads(client_type, http):
    client = make_client(client_type)
    original = client.get_access_token_snapshot()
    entered = [Event(), Event()]
    release = [Event(), Event()]

    def handle(method, url, **kwargs):
        index = int(kwargs["data"]["scope"])
        entered[index].set()
        assert release[index].wait(10), "Test did not release mocked HTTP request"
        return response(
            {"access_token": "token-{}".format(index), "expires_in": (index + 1) * 3600}
        )

    http.side_effect = handle
    with ThreadPoolExecutor(max_workers=3) as executor:
        first = executor.submit(client.refresh_access_token, scope=["0"])
        second = executor.submit(client.refresh_access_token, scope=["1"])
        try:
            assert all(event.wait(10) for event in entered)
            # Reads must finish while both HTTP requests remain blocked.
            assert executor.submit(client.get_access_token_snapshot).result(10) == original
            release[1].set()
            second.result(10)
            second_snapshot = client.get_access_token_snapshot()
            assert second_snapshot == AccessTokenSnapshot("token-1", NOW + timedelta(hours=2))
            release[0].set()
            first.result(10)
            assert client.get_access_token_snapshot() == AccessTokenSnapshot(
                "token-0", NEW_EXPIRATION
            )
            assert second_snapshot.access_token == "token-1"
            assert original == AccessTokenSnapshot("old-token", OLD_EXPIRATION)
        finally:
            for event in release:
                event.set()
    assert http.call_count == 2


@pytest.mark.parametrize(
    "client_type,reader",
    [
        (Dropbox, "snapshot"),
        (Dropbox, "clone"),
        (Dropbox, "with_path_root"),
        (DropboxTeam, "snapshot"),
        (DropboxTeam, "clone"),
        (DropboxTeam, "with_path_root"),
        (DropboxTeam, "as_user"),
        (DropboxTeam, "as_admin"),
    ],
)
def test_snapshot_waits_for_complete_publication(client_type, http, reader):
    token_written = Event()
    finish_publication = Event()
    reader_entered = Event()

    class ObservedLock:
        def __init__(self):
            self.lock = Lock()

        def __enter__(self):
            if not self.lock.acquire(blocking=False):
                # Signal actual contention, not merely a thread about to acquire.
                # This makes missing publication/read locks fail deterministically.
                reader_entered.set()
                self.lock.acquire()

        def __exit__(self, *args):
            self.lock.release()

    class PausingClient(client_type):
        def __setattr__(self, name, value):
            super().__setattr__(name, value)
            if name == "_oauth2_access_token" and value == "new-token":
                token_written.set()
                assert finish_publication.wait(10), "Test did not release publication"

    client = make_client(PausingClient)
    client._access_token_lock = ObservedLock()
    http.side_effect = None
    http.return_value = response({"access_token": "new-token", "expires_in": 3600})

    def read_credentials():
        if reader == "snapshot":
            return client.get_access_token_snapshot()
        if reader == "clone":
            child = client.clone()
        elif reader == "with_path_root":
            child = client.with_path_root(PathRoot.home)
        else:
            child = getattr(client, reader)("member-id")
        return child.get_access_token_snapshot()

    with ThreadPoolExecutor(max_workers=2) as executor:
        refresh = executor.submit(client.refresh_access_token)
        try:
            # Pause the real refresh between its two field assignments.
            assert token_written.wait(10)
            read = executor.submit(read_credentials)
            assert reader_entered.wait(10)
        finally:
            finish_publication.set()
        refresh.result(10)
        assert read.result(10) == AccessTokenSnapshot("new-token", NEW_EXPIRATION)
