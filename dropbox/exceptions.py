class DropboxException(Exception):
    """All errors related to making an API request extend this."""
    pass


class ApiError(DropboxException):
    """Errors produced by the Dropbox API."""

    def __init__(self, reason):
        super(ApiError, self).__init__(reason)
        self.reason = reason

    def __repr__(self):
        return 'ApiError({})'.format(self.reason)


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

    def __init__(self, reason):
        super(AuthError, self).__init__(401, None)
        self.reason = reason

    def __repr__(self):
        return 'AuthError({!r})'.format(self.reason)


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
