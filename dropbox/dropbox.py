__all__ = [
    'Dropbox',
]

# TODO(kelkabany): We need to auto populate this as done in the v1 SDK.
__version__ = '3.34'

import contextlib
import json
import logging
import os
import random
import six
import time

import requests

from . import babel_serializers
from .base import DropboxBase
from .exceptions import (
    ApiError,
    AuthError,
    BadInputError,
    HttpError,
    InternalServerError,
    RateLimitError,
)
from .session import pinned_session

class RouteResult(object):
    """The successful result of a call to a route."""

    def __init__(self, obj_result, http_resp=None):
        """
        :param str obj_result: The result of a route not including the binary
            payload portion, if one exists. Must be serialized JSON.
        :param requests.models.Response http_resp: A raw HTTP response. It will
            be used to stream the binary-body payload of the response.
        """
        assert isinstance(obj_result, six.string_types), \
            'obj_result: expected string, got %r' % type(obj_result)
        if http_resp is not None:
            assert isinstance(http_resp, requests.models.Response), \
                'http_resp: expected requests.models.Response, got %r' % \
                type(http_resp)
        self.obj_result = obj_result
        self.http_resp = http_resp

class RouteErrorResult(object):
    """The error result of a call to a route."""

    def __init__(self, obj_result):
        """
        :param str obj_result: The result of a route not including the binary
            payload portion, if one exists.
        """
        self.obj_result = obj_result

class Dropbox(DropboxBase):
    """
    Use this to make requests to the Dropbox API.
    """

    API_VERSION = '2-beta-2'

    DEFAULT_DOMAIN = 'dropbox.com'

    # host for web routes (used for oauth2)
    HOST_WEB = 'www'

    # Host for RPC-style routes.
    HOST_API = 'api'

    # Host for upload and download-style routes.
    HOST_CONTENT = 'content'

    # Host for longpoll routes.
    HOST_NOTIFY = 'notify'

    # Download style means that the route argument goes in a Dropbox-API-Arg
    # header, and the result comes back in a Dropbox-API-Result header. The
    # HTTP response body contains a binary payload.
    ROUTE_STYLE_DOWNLOAD = 'download'

    # Upload style means that the route argument goes in a Dropbox-API-Arg
    # header. The HTTP request body contains a binary payload. The result
    # comes back in a Dropbox-API-Result header.
    ROUTE_STYLE_UPLOAD = 'upload'

    # RPC style means that the argument and result of a route are contained in
    # the HTTP body.
    ROUTE_STYLE_RPC = 'rpc'

    def __init__(self,
                 oauth2_access_token,
                 max_connections=8,
                 max_retries_on_error=4,
                 user_agent=None,
                 proxies=None):
        """
        :param str oauth2_access_token: OAuth2 access token for making client
            requests.
        :param int max_connections: Maximum connection pool size.
        :param int max_retries_on_error: On 5xx errors, the number of times to
            retry.
        :param str user_agent: The user agent to use when making requests. This
            helps us identify requests coming from your application. We
            recommend you use the format "AppName/Version". If set, we append
            "/OfficialDropboxPythonV2SDK/__version__" to the user_agent,
        :param dict proxies: See the `requests module
            <http://docs.python-requests.org/en/latest/user/advanced/#proxies>`_
            for more details.
        """
        assert len(oauth2_access_token) > 0, \
            'OAuth2 access token cannot be empty.'
        self._oauth2_access_token = oauth2_access_token

        # We only need as many pool_connections as we have unique hostnames.
        self._session = pinned_session(pool_maxsize=max_connections)
        if proxies:
            self._session.proxies = proxies
        self._max_retries_on_error = max_retries_on_error

        base_user_agent = 'OfficialDropboxPythonV2SDK/' + __version__
        if user_agent:
            self._user_agent = '{}/{}'.format(user_agent, base_user_agent)
        else:
            self._user_agent = base_user_agent

        self._logger = logging.getLogger('dropbox')

        self._domain = os.environ.get('DROPBOX_DOMAIN', Dropbox.DEFAULT_DOMAIN)
        self._api_hostname = os.environ.get(
            'DROPBOX_API_HOST', 'api.' + self._domain)
        self._api_content_hostname = os.environ.get(
            'DROPBOX_API_CONTENT_HOST', 'api-content.' + self._domain)
        self._api_notify_hostname = os.environ.get(
            'DROPBOX_API_NOTIFY_HOST', 'api-notify.' + self._domain)
        self._host_map = {self.HOST_API: self._api_hostname,
                          self.HOST_CONTENT: self._api_content_hostname,
                          self.HOST_NOTIFY: self._api_notify_hostname}

    def request(self,
                host,
                route_name,
                route_style,
                arg_data_type,
                result_data_type,
                error_data_type,
                request_arg,
                request_binary):
        """
        Makes a request to the Dropbox API and in the process validates that
        the route argument and result are the expected data types. The
        request_arg is converted to JSON based on the arg_data_type. Likewise,
        the response is deserialized from JSON and converted to an object based
        on the {result,error}_data_type.

        :param host: The Dropbox API host to connect to.
        :param route_name: The name of the route to invoke.
        :param route_style: The style of the route.
        :type arg_data_type: :class:`.datatypes.babel_validators.DataType`
        :type result_data_type: :class:`.datatypes.babel_validators.DataType`
        :type error_data_type: :class:`.datatypes.babel_validators.DataType`
        :param request_arg: Argument for the route that conforms to the
            validator specified by arg_data_type.
        :param request_binary: String or file pointer representing the binary
            payload. Use None if there is no binary payload.
        :return: The route's result.
        """

        serialized_arg = babel_serializers.json_encode(arg_data_type,
                                                       request_arg)
        res = self.request_json_string_with_retry(host,
                                                  route_name,
                                                  route_style,
                                                  serialized_arg,
                                                  request_binary)
        decoded_obj_result = json.loads(res.obj_result)
        if isinstance(res, RouteResult):
            returned_data_type = result_data_type
            obj = decoded_obj_result
        elif isinstance(res, RouteErrorResult):
            returned_data_type = error_data_type
            obj = decoded_obj_result['error']
            user_message = decoded_obj_result.get('user_message')
            user_message_text = user_message and user_message.get('text')
            user_message_locale =  user_message and user_message.get('locale')
        else:
            raise AssertionError('Expected RouteResult or RouteErrorResult, '
                                 'but res is %s' % type(res))


        deserialized_result = babel_serializers.json_compat_obj_decode(
            returned_data_type, obj, strict=False)

        if isinstance(res, RouteErrorResult):
            raise ApiError(deserialized_result,
                           user_message_text,
                           user_message_locale)
        elif route_style == self.ROUTE_STYLE_DOWNLOAD:
            return (deserialized_result, res.http_resp)
        else:
            return deserialized_result

    def request_json_object(self,
                            host,
                            route_name,
                            route_style,
                            request_arg,
                            request_binary):
        """
        Makes a request to the Dropbox API, taking a JSON-serializable Python
        object as an argument, and returning one as a response.

        :param host: The Dropbox API host to connect to.
        :param route_name: The name of the route to invoke.
        :param route_style: The style of the route.
        :param str request_arg: A JSON-serializable Python object representing
            the argument for the route.
        :param request_binary: String or file pointer representing the binary
            payload. Use None if there is no binary payload.
        :return: The route's result as a JSON-serializable Python object.
        """
        serialized_arg = json.dumps(request_arg)
        res = self.request_json_string_with_retry(host,
                                                  route_name,
                                                  route_style,
                                                  serialized_arg,
                                                  request_binary)
        # This can throw a ValueError if the result is not deserializable,
        # but that would be completely unexpected.
        deserialized_result = json.loads(res.obj_result)
        if isinstance(res, RouteResult) and res.http_resp is not None:
            return (deserialized_result, res.http_resp)
        else:
            return deserialized_result

    def request_json_string_with_retry(self,
                                       host,
                                       route_name,
                                       route_style,
                                       request_json_arg,
                                       request_binary):
        """
        See :meth:`request_json_object` for description of parameters.

        :param request_json_arg: A string representing the serialized JSON
            argument to the route.
        """
        attempt = 0
        while True:
            self._logger.info('Request to %s', route_name)
            try:
                return self.request_json_string(host,
                                                route_name,
                                                route_style,
                                                request_json_arg,
                                                request_binary)
            except (InternalServerError, RateLimitError) as e:
                if isinstance(e, InternalServerError):
                    # Do not count a rate limiting error as an attempt
                    attempt += 1
                if attempt <= self._max_retries_on_error:
                    # Use exponential backoff
                    backoff = 2**attempt * random.random()
                    self._logger.info('HttpError status_code=%s: '
                                      'Retrying in %.1f seconds',
                                      e.status_code, backoff)
                    time.sleep(backoff)
                else:
                    raise

    def request_json_string(self,
                            host,
                            func_name,
                            route_style,
                            request_json_arg,
                            request_binary):
        """
        See :meth:`request_json_string_with_retry` for description of
        parameters.
        """
        if host not in self._host_map:
            raise ValueError('Unknown value for host: %r' % host)

        # Fully qualified hostname
        fq_hostname = self._host_map[host]
        url = self._get_route_url(fq_hostname, func_name)

        headers = {'Authorization': 'Bearer %s' % self._oauth2_access_token,
                   'User-Agent': self._user_agent}

        # The contents of the body of the HTTP request
        body = None
        # Whether the response should be streamed incrementally, or buffered
        # entirely. If stream is True, the caller is responsible for closing
        # the HTTP response.
        stream = False

        if route_style == self.ROUTE_STYLE_RPC:
            headers['Content-Type'] = 'application/json'
            body = request_json_arg
        elif route_style == self.ROUTE_STYLE_DOWNLOAD:
            headers['Dropbox-API-Arg'] = request_json_arg
            stream = True
        elif route_style == self.ROUTE_STYLE_UPLOAD:
            headers['Content-Type'] = 'application/octet-stream'
            headers['Dropbox-API-Arg'] = request_json_arg
            body = request_binary
        else:
            raise ValueError('Unknown operation style: %r' % route_style)

        r = self._session.post(url,
                               headers=headers,
                               data=body,
                               stream=stream,
                               verify=True,
                               )

        if r.status_code >= 500:
            raise InternalServerError(r.status_code, r.text)
        elif r.status_code == 400:
            raise BadInputError(r.text)
        elif r.status_code == 401:
            assert r.headers.get('content-type') == 'application/json', (
                'Expected content-type to be application/json, got %r' %
                r.headers.get('content-type'))
            raise AuthError(r.json())
        elif r.status_code == 429:
            # TODO(kelkabany): Use backoff if provided in response.
            raise RateLimitError()
        elif 200 <= r.status_code <= 299:
            if route_style == self.ROUTE_STYLE_DOWNLOAD:
                raw_resp = r.headers['dropbox-api-result']
            else:
                assert r.headers.get('content-type') == 'application/json', (
                    'Expected content-type to be application/json, got %r' %
                    r.headers.get('content-type'))
                raw_resp = r.content.decode('utf-8')
            if route_style == self.ROUTE_STYLE_DOWNLOAD:
                return RouteResult(raw_resp, r)
            else:
                return RouteResult(raw_resp)
        elif r.status_code in (403, 404, 409):
            raw_resp = r.content.decode('utf-8')
            return RouteErrorResult(raw_resp)
        else:
            raise HttpError(r.status_code, r.text)

    def _get_route_url(self, hostname, route_name):
        """Returns the URL of the route.

        :param str hostname: Hostname to make the request to.
        :param str route_name: Name of the route.
        :rtype: str
        """
        return 'https://{hostname}/{version}/{route_name}'.format(
            hostname=hostname,
            version=Dropbox.API_VERSION,
            route_name=route_name,
        )

    def _save_body_to_file(self, download_path, http_resp, chunksize=2**16):
        """
        Saves the body of an HTTP response to a file.

        :param str download_path: Local path to save data to.
        :param http_resp: The HTTP response whose body will be saved.
        :type http_resp: :class:`requests.models.Response`
        :rtype: None
        """
        with open(download_path, 'wb') as f:
            with contextlib.closing(http_resp):
                for c in http_resp.iter_content(chunksize):
                    f.write(c)
