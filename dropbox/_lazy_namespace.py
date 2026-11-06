"""Lazy references to generated namespace modules.

The generated base clients (``dropbox.base`` and ``dropbox.base_team``) have a
method for every route in every namespace. Importing every namespace module up
front costs about 30 MB and a noticeable amount of import time, most of it from
``team_log``, even for apps that only ever call a handful of ``files`` routes.

The base clients refer to namespaces through :class:`LazyNamespace` instead, so a
namespace module is only imported the first time one of its routes or types is
used.
"""

import importlib


class LazyNamespace(object):
    """Stands in for a namespace module and imports it on first attribute access.

    Importing goes through :func:`importlib.import_module`, which takes the
    per-module import lock, so concurrent first accesses from several threads
    are safe and all see the same fully initialized module.
    """

    __slots__ = ("_name", "_module")

    def __init__(self, name):
        self._name = name
        self._module = None

    def _load(self):
        module = self._module
        if module is None:
            module = importlib.import_module(self._name)
            self._module = module
        return module

    def __getattr__(self, attr):
        # Only called for attributes not found on the proxy itself.
        return getattr(self._load(), attr)

    def __dir__(self):
        return dir(self._load())

    def __repr__(self):
        state = "loaded" if self._module is not None else "not loaded"
        return "<LazyNamespace {!r} ({})>".format(self._name, state)
