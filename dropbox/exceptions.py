class DropboxException(Exception):
    """All errors related to making an API request extend this."""
    pass


class ApiError(DropboxException):
    """Errors produced by the Dropbox API."""

    def __init__(self, error, user_message_text, user_message_locale):
        """
        :param error: An instance of the error data type for the route.
        :param (str) user_message_text: A human-readable message that can be
            displayed to the end user. Is None, if unavailable.
        :param (str) user_message_locale: The locale of ``user_message_text``,
            if present.
        """
        super(ApiError, self).__init__(error)
        self.error = error
        self.user_message_text = user_message_text
        self.user_message_locale = user_message_locale

    def __repr__(self):
        return 'ApiError({})'.format(self.error)


class HttpError(DropboxException):
    """Errors produced at the HTTP layer."""

    def __init__(self, status_code, body):
        super(HttpError, self).__init__(status_code, body)
        self.status_code = status_code
        self.body = body

    def __repr__(self):
        return 'HttpError({}, {!r})'.format(self.status_code, self.body)


class BadInputError(HttpError):
    """Errors due to bad input parameters to an API Operation."""

    def __init__(self, message):
        super(BadInputError, self).__init__(400, message)
        self.message = message

    def __repr__(self):
        return 'BadInputError({!r})'.format(self.message)


class AuthError(HttpError):
    """Errors due to invalid authentication credentials."""

    def __init__(self, error):
        super(AuthError, self).__init__(401, None)
        self.error = error

    def __repr__(self):
        return 'AuthError({!r})'.format(self.error)


class RateLimitError(HttpError):
    """Error caused by rate limiting."""

    def __init__(self, backoff=None):
        super(RateLimitError, self).__init__(429, None)
        self.backoff = backoff

    def __repr__(self):
        return 'RateLimitError({!r})'.format(self.backoff)


class InternalServerError(HttpError):
    """Errors due to a problem on Dropbox."""

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __repr__(self):
        return 'InternalServerError({}, {!r})'.format(self.status_code, self.message)
