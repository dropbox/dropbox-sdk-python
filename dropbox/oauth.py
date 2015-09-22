__all__ = [
    'BadRequestException',
    'BadStateException',
    'CsrfException',
    'DropboxOAuth2Flow',
    'DropboxOAuth2FlowNoRedirect',
    'NotApprovedException',
    'ProviderException',
]

import base64
import os
import six
import sys
import urllib

from .dropbox import Dropbox
from .session import pinned_session

OAUTH_ROUTE_VERSION = '1'

class DropboxOAuth2FlowBase(object):

    def __init__(self, consumer_key, consumer_secret, locale=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.locale = locale
        self.requests_session = pinned_session()

        self._domain = os.environ.get('DROPBOX_DOMAIN', Dropbox.DEFAULT_DOMAIN)

    def _get_authorize_url(self, redirect_uri, state):
        params = dict(response_type='code',
                      client_id=self.consumer_key)
        if redirect_uri is not None:
            params['redirect_uri'] = redirect_uri
        if state is not None:
            params['state'] = state

        return self.build_url(Dropbox.HOST_WEB, '/oauth2/authorize', params)

    def _finish(self, code, redirect_uri):
        url = self.build_url(Dropbox.HOST_API, '/oauth2/token')
        params = {'grant_type': 'authorization_code',
                  'code': code,
                  'client_id': self.consumer_key,
                  'client_secret': self.consumer_secret,
                  }
        if self.locale is not None:
            params['locale'] = self.locale
        if redirect_uri is not None:
            params['redirect_uri'] = redirect_uri

        resp = self.requests_session.post(url, data=params)
        resp.raise_for_status()

        d = resp.json()

        access_token = d["access_token"]
        user_id = d["uid"]

        return access_token, user_id

    def build_path(self, target, params=None):
        """Build the path component for an API URL.

        This method urlencodes the parameters, adds them
        to the end of the target url, and puts a marker for the API
        version in front.

        :param str target: A target url (e.g. '/files') to build upon.
        :param dict params: Optional dictionary of parameters (name to value).
        :return: The path and parameters components of an API URL.
        :rtype: str
        """
        if sys.version_info < (3,) and type(target) == six.text_type:
            target = target.encode("utf8")

        target_path = urllib.quote(target)

        params = params or {}
        params = params.copy()

        if self.locale:
            params['locale'] = self.locale

        if params:
            query_string = _params_to_urlencoded(params)
            return "/%s%s?%s" % (OAUTH_ROUTE_VERSION, target_path, query_string)
        else:
            return "/%s%s" % (OAUTH_ROUTE_VERSION, target_path)

    def build_url(self, host, target, params=None):
        """Build an API URL.

        This method adds scheme and hostname to the path
        returned from build_path.

        :param str target: A target url (e.g. '/files') to build upon.
        :param dict params: Optional dictionary of parameters (name to value).
        :return: The full API URL.
        :rtype: str
        """
        return "https://%s.%s%s" % (host, self._domain, self.build_path(target, params))


class DropboxOAuth2FlowNoRedirect(DropboxOAuth2FlowBase):
    """
    OAuth 2 authorization helper for apps that can't provide a redirect URI
    (such as the command-line example apps).

    Example::

        from dropbox import DropboxOAuth2FlowNoRedirect

        auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

        authorize_url = auth_flow.start()
        print "1. Go to: " + authorize_url
        print "2. Click \\"Allow\\" (you might have to log in first)."
        print "3. Copy the authorization code."
        auth_code = raw_input("Enter the authorization code here: ").strip()

        try:
            access_token, user_id = auth_flow.finish(auth_code)
        except Exception, e:
            print('Error: %s' % (e,))
            return

        dbx = Dropbox(access_token)
    """

    def __init__(self, consumer_key, consumer_secret, locale=None):
        """
        Construct an instance.

        Parameters
        :param str consumer_key: Your API app's "app key".
        :param str consumer_secret: Your API app's "app secret".
        :param str locale: The locale of the user of your application.  For
            example "en" or "en_US". Some API calls return localized data and
            error messages; this setting tells the server which locale to use.
            By default, the server uses "en_US".
        """
        super(DropboxOAuth2FlowNoRedirect, self).__init__(consumer_key,
                                                          consumer_secret,
                                                          locale)

    def start(self):
        """
        Starts the OAuth 2 authorization process.

        :return: The URL for a page on Dropbox's website.  This page will let
            the user "approve" your app, which gives your app permission to
            access the user's Dropbox account. Tell the user to visit this URL
            and approve your app.
        """
        return self._get_authorize_url(None, None)

    def finish(self, code):
        """
        If the user approves your app, they will be presented with an
        "authorization code".  Have the user copy/paste that authorization code
        into your app and then call this method to get an access token.

        :param str code: The authorization code shown to the user when they
            approved your app.
        :return: A pair of ``(access_token, user_id)``.  ``access_token`` is a
            string that can be passed to Dropbox.  ``user_id`` is the
            Dropbox user ID (string) of the user that just approved your app.
        :raises: The same exceptions as :meth:`DropboxOAuth2Flow.finish()`.
        """
        return self._finish(code, None)


class DropboxOAuth2Flow(DropboxOAuth2FlowBase):
    """
    OAuth 2 authorization helper.  Use this for web apps.

    OAuth 2 has a two-step authorization process.  The first step is having the
    user authorize your app.  The second involves getting an OAuth 2 access
    token from Dropbox.

    Example::

        from dropbox import DropboxOAuth2Flow

        def get_dropbox_auth_flow(web_app_session):
            redirect_uri = "https://my-web-server.org/dropbox-auth-finish"
            return DropboxOAuth2Flow(
                APP_KEY, APP_SECRET, redirect_uri, web_app_session,
                "dropbox-auth-csrf-token")

        # URL handler for /dropbox-auth-start
        def dropbox_auth_start(web_app_session, request):
            authorize_url = get_dropbox_auth_flow(web_app_session).start()
            redirect_to(authorize_url)

        # URL handler for /dropbox-auth-finish
        def dropbox_auth_finish(web_app_session, request):
            try:
                access_token, user_id, url_state = \\
                        get_dropbox_auth_flow(web_app_session).finish(
                            request.query_params)
            except BadRequestException, e:
                http_status(400)
            except BadStateException, e:
                # Start the auth flow again.
                redirect_to("/dropbox-auth-start")
            except CsrfException, e:
                http_status(403)
            except NotApprovedException, e:
                flash('Not approved?  Why not?')
                return redirect_to("/home")
            except ProviderException, e:
                logger.log("Auth error: %s" % (e,))
                http_status(403)

    """

    def __init__(self, consumer_key, consumer_secret, redirect_uri, session,
                 csrf_token_session_key, locale=None):
        """
        Construct an instance.

        :param str consumer_key: Your API app's "app key".
        :param str consumer_secret: Your API app's "app secret".
        :param str redirect_uri: The URI that the Dropbox server will redirect
            the user to after the user finishes authorizing your app.  This URI
            must be HTTPS-based and pre-registered with the Dropbox servers,
            though localhost URIs are allowed without pre-registration and can
            be either HTTP or HTTPS.
        :param dict session: A dict-like object that represents the current
            user's web session (will be used to save the CSRF token).
        :param str csrf_token_session_key: The key to use when storing the CSRF
            token in the session (for example: "dropbox-auth-csrf-token").
        :param str locale: The locale of the user of your application.  For
            example "en" or "en_US". Some API calls return localized data and
            error messages; this setting tells the server which locale to use.
            By default, the server uses "en_US".
        """
        super(DropboxOAuth2Flow, self).__init__(consumer_key, consumer_secret, locale)
        self.redirect_uri = redirect_uri
        self.session = session
        self.csrf_token_session_key = csrf_token_session_key

    def start(self, url_state=None):
        """
        Starts the OAuth 2 authorization process.

        This function builds an "authorization URL".  You should redirect your
        user's browser to this URL, which will give them an opportunity to
        grant your app access to their Dropbox account.  When the user
        completes this process, they will be automatically redirected to the
        ``redirect_uri`` you passed in to the constructor.

        This function will also save a CSRF token to
        ``session[csrf_token_session_key]`` (as provided to the constructor).
        This CSRF token will be checked on :meth:`finish()` to prevent request
        forgery.

        :param str url_state: Any data that you would like to keep in the URL
            through the authorization process.  This exact value will be
            returned to you by :meth:`finish()`.
        :return: The URL for a page on Dropbox's website.  This page will let
            the user "approve" your app, which gives your app permission to
            access the user's Dropbox account. Tell the user to visit this URL
            and approve your app.
        """
        csrf_token = base64.urlsafe_b64encode(os.urandom(16))
        state = csrf_token
        if url_state is not None:
            state += "|" + url_state
        self.session[self.csrf_token_session_key] = csrf_token

        return self._get_authorize_url(self.redirect_uri, state)

    def finish(self, query_params):
        """
        Call this after the user has visited the authorize URL (see
        :meth:`start()`), approved your app and was redirected to your redirect
        URI.

        :param dict query_params: The query parameters on the GET request to
            your redirect URI.
        :return: A tuple of ``(access_token, user_id, url_state)``.
            ``access_token`` can be used to construct a
            :class:`dropbox.dropbox.Dropbox`. ``user_id`` is the Dropbox user
            ID (string) of the user that just approved your app. ``url_state``
            is the value you originally passed in to :meth:`start()`.
        :raises: :class:`BadRequestException` If the redirect URL was missing
            parameters or if the given parameters were not valid.
        :raises: :class:`BadStateException` If there's no CSRF token in the
            session.
        :raises: :class:`CsrfException` If the ``state`` query parameter
            doesn't contain the CSRF token from the user's session.
        :raises: :class:`NotApprovedException` If the user chose not to
            approve your app.
        :raises: :class:`ProviderException` If Dropbox redirected to your
            redirect URI with some unexpected error identifier and error message.
        """
        # Check well-formedness of request.

        state = query_params.get('state')
        if state is None:
            raise BadRequestException("Missing query parameter 'state'.")

        error = query_params.get('error')
        error_description = query_params.get('error_description')
        code = query_params.get('code')

        if error is not None and code is not None:
            raise BadRequestException(
                "Query parameters 'code' and 'error' are both set; "
                "only one must be set.")
        if error is None and code is None:
            raise BadRequestException(
                "Neither query parameter 'code' or 'error' is set.")

        # Check CSRF token

        if self.csrf_token_session_key not in self.session:
            raise BadStateException('Missing CSRF token in session.')
        csrf_token_from_session = self.session[self.csrf_token_session_key]
        if len(csrf_token_from_session) <= 20:
            raise AssertionError('CSRF token unexpectedly short: %r' %
                                 csrf_token_from_session)

        split_pos = state.find('|')
        if split_pos < 0:
            given_csrf_token = state
            url_state = None
        else:
            given_csrf_token = state[0:split_pos]
            url_state = state[split_pos+1:]

        if not _safe_equals(csrf_token_from_session, given_csrf_token):
            raise CsrfException('expected %r, got %r' %
                                (csrf_token_from_session, given_csrf_token))

        del self.session[self.csrf_token_session_key]

        # Check for error identifier

        if error is not None:
            if error == 'access_denied':
                # The user clicked "Deny"
                if error_description is None:
                    raise NotApprovedException(
                        'No additional description from Dropbox')
                else:
                    raise NotApprovedException(
                        'Additional description from Dropbox: %s' %
                        error_description)
            else:
                # All other errors
                full_message = error
                if error_description is not None:
                    full_message += ": " + error_description
                raise ProviderException(full_message)

        # If everything went ok, make the network call to get an access token.

        access_token, user_id = self._finish(code, self.redirect_uri)
        return access_token, user_id, url_state


class BadRequestException(Exception):
    """
    Thrown if the redirect URL was missing parameters or if the
    given parameters were not valid.

    The recommended action is to show an HTTP 400 error page.
    """
    pass


class BadStateException(Exception):
    """
    Thrown if all the parameters are correct, but there's no CSRF token in the
    session. This probably means that the session expired.

    The recommended action is to redirect the user's browser to try the
    approval process again.
    """
    pass


class CsrfException(Exception):
    """
    Thrown if the given 'state' parameter doesn't contain the CSRF token from
    the user's session. This is blocked to prevent CSRF attacks.

    The recommended action is to respond with an HTTP 403 error page.
    """
    pass


class NotApprovedException(Exception):
    """
    The user chose not to approve your app.
    """
    pass


class ProviderException(Exception):
    """
    Dropbox redirected to your redirect URI with some unexpected error
    identifier and error message.

    The recommended action is to log the error, tell the user something went
    wrong, and let them try again.
    """
    pass


def _safe_equals(a, b):
    if len(a) != len(b): return False
    res = 0
    for ca, cb in zip(a, b):
        res |= ord(ca) ^ ord(cb)
    return res == 0


def _params_to_urlencoded(params):
    """
    Returns a application/x-www-form-urlencoded ``str`` representing the
    key/value pairs in ``params``.

    Keys are values are ``str()``'d before calling ``urllib.urlencode``, with
    the exception of unicode objects which are utf8-encoded.
    """
    def encode(o):
        if isinstance(o, six.text_type):
            return o.encode('utf8')
        else:
            return str(o)
    utf8_params = {encode(k): encode(v) for k, v in six.iteritems(params)}
    return urllib.urlencode(utf8_params)
