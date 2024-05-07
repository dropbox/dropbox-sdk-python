import os
import ssl

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

API_DOMAIN = os.environ.get('DROPBOX_API_DOMAIN',
    os.environ.get('DROPBOX_DOMAIN', '.dropboxapi.com'))

WEB_DOMAIN = os.environ.get('DROPBOX_WEB_DOMAIN',
    os.environ.get('DROPBOX_DOMAIN', '.dropbox.com'))

# Default short hostname for RPC-style routes.
HOST_API = 'api'

# Default short hostname for upload and download-style routes.
HOST_CONTENT = 'content'

# Default short hostname for longpoll routes.
HOST_NOTIFY = 'notify'

# Default short hostname for the Drobox website.
HOST_WWW = 'www'

API_HOST = os.environ.get('DROPBOX_API_HOST', HOST_API + API_DOMAIN)
API_CONTENT_HOST = os.environ.get('DROPBOX_API_CONTENT_HOST', HOST_CONTENT + API_DOMAIN)
API_NOTIFICATION_HOST = os.environ.get('DROPBOX_API_NOTIFY_HOST', HOST_NOTIFY + API_DOMAIN)
WEB_HOST = os.environ.get('DROPBOX_WEB_HOST', HOST_WWW + WEB_DOMAIN)

# This is the default longest time we'll block on receiving data from the server
DEFAULT_TIMEOUT = 100


# TODO(kelkabany): We probably only want to instantiate this once so that even
# if multiple Dropbox objects are instantiated, they all share the same pool.
class _SSLAdapter(HTTPAdapter):
    _ca_certs = None

    def __init__(self, *args, **kwargs):
        self._ca_certs = kwargs.pop("ca_certs", None)
        super(_SSLAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **_):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=self._ca_certs,
        )

def pinned_session(pool_maxsize=8, ca_certs=None):
    _session = requests.session()

    # always verify, use cert bundle if provided
    if ca_certs is not None:
        _session.verify = ca_certs
    else:
        _session.verify = True

    http_adapter = _SSLAdapter(pool_connections=4, pool_maxsize=pool_maxsize, ca_certs=ca_certs)
    _session.mount('https://', http_adapter)
    return _session

SSLError = requests.exceptions.SSLError  # raised on verification errors
