import json
import subprocess
import sys
import textwrap
from unittest import mock

import pytest

from dropbox import base, base_team
from dropbox._lazy_namespace import LazyNamespace


def _run(code):
    """Run code in a fresh interpreter so sys.modules starts empty."""
    out = subprocess.check_output([sys.executable, "-c", textwrap.dedent(code)])
    return json.loads(out.decode("utf-8").strip().splitlines()[-1])


class TestLazyNamespace:
    def test_importing_dropbox_does_not_load_team_namespaces(self):
        loaded = _run(
            """
            import json, sys
            import dropbox
            print(json.dumps(sorted(m for m in sys.modules if m.startswith("dropbox."))))
            """
        )
        assert "dropbox.team_log" not in loaded
        assert "dropbox.team" not in loaded
        assert "dropbox.files" in loaded

    def test_namespace_is_loaded_on_first_route_call(self):
        result = _run(
            """
            import json, sys
            from unittest import mock
            import dropbox

            dbx = dropbox.DropboxTeam("token")
            before = "dropbox.team_log" in sys.modules
            with mock.patch.object(dbx, "request", return_value="ok") as request:
                dbx.team_log_get_events(limit=5)
            route, namespace, arg, binary = request.call_args[0]
            from dropbox import team_log
            print(json.dumps({
                "before": before,
                "after": "dropbox.team_log" in sys.modules,
                "same_route": route is team_log.get_events,
                "namespace": namespace,
                "arg_type": type(arg).__name__,
                "limit": arg.limit,
            }))
            """
        )
        assert result == {
            "before": False,
            "after": True,
            "same_route": True,
            "namespace": "team_log",
            "arg_type": "GetTeamEventsArg",
            "limit": 5,
        }

    def test_concurrent_first_access_sees_one_module(self):
        result = _run(
            """
            import json, threading
            from dropbox._lazy_namespace import LazyNamespace

            ns = LazyNamespace("dropbox.team_log")
            barrier = threading.Barrier(16)
            seen = []

            def worker():
                barrier.wait()
                seen.append(ns.get_events)

            threads = [threading.Thread(target=worker) for _ in range(16)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            print(json.dumps({"count": len(seen), "distinct": len({id(r) for r in seen})}))
            """
        )
        assert result == {"count": 16, "distinct": 1}

    def test_proxy_behaves_like_the_module(self):
        from dropbox import files

        ns = LazyNamespace("dropbox.files")
        assert "not loaded" in repr(ns)
        assert ns.DownloadArg is files.DownloadArg
        assert "loaded" in repr(ns) and "not loaded" not in repr(ns)
        assert "DownloadArg" in dir(ns)
        with pytest.raises(AttributeError):
            ns.does_not_exist

    def test_missing_module_raises_import_error_on_use(self):
        ns = LazyNamespace("dropbox.no_such_namespace")
        with pytest.raises(ImportError):
            ns.anything

    def test_base_clients_use_lazy_namespaces(self):
        assert isinstance(base.team_log, LazyNamespace)
        assert isinstance(base_team.team_log, LazyNamespace)

    def test_user_route_still_builds_real_types(self):
        from dropbox import Dropbox, files

        dbx = Dropbox("token")
        with mock.patch.object(dbx, "request", return_value="ok") as request:
            dbx.files_get_metadata("/a")
        route, namespace, arg, binary = request.call_args[0]
        assert route is files.get_metadata
        assert isinstance(arg, files.GetMetadataArg)
        assert arg.path == "/a"
