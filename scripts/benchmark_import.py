"""Measure what `import dropbox` costs on its own.

Each run uses a fresh interpreter. requests and stone are imported first, so the
numbers only cover the SDK's own modules. Times are medians over `runs`
interpreters; traced memory (tracemalloc) is the median of 3 separate runs.

    python scripts/benchmark_import.py [runs]
"""

import json
import statistics
import subprocess
import sys

CODE = r"""
import json, resource, sys, time, tracemalloc
import requests
import stone.backends.python_rsrc.stone_validators

trace = sys.argv[1] == "trace"
rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if trace:
    tracemalloc.start()
start = time.perf_counter()
import dropbox
elapsed = time.perf_counter() - start
traced = tracemalloc.get_traced_memory()[0] if trace else 0
rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
# ru_maxrss is bytes on macOS and kilobytes on Linux
scale = 1 if sys.platform == "darwin" else 1024
print(json.dumps({
    "ms": elapsed * 1000,
    "traced_mb": traced / 1e6,
    "rss_mb": (rss_after - rss_before) * scale / 1e6,
    "modules": sorted(m for m in sys.modules if m.startswith("dropbox.")),
}))
"""


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 15

    def run(mode):
        out = subprocess.check_output([sys.executable, "-c", CODE, mode])
        return json.loads(out)

    # Timing runs don't use tracemalloc, which slows imports down a lot.
    results = [run("time") for _ in range(runs)]
    traced = [run("trace")["traced_mb"] for _ in range(3)]
    summary = {
        "runs": runs,
        "import_ms_median": round(statistics.median(r["ms"] for r in results), 1),
        "traced_mb_median": round(statistics.median(traced), 1),
        "rss_mb_median": round(statistics.median(r["rss_mb"] for r in results), 1),
        "dropbox_modules_loaded": len(results[-1]["modules"]),
        "team_log_loaded": "dropbox.team_log" in results[-1]["modules"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
