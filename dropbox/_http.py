def format_byte_range(byte_range):
    """Format a byte range as an HTTP Range header value."""

    if byte_range is None:
        return None

    if not isinstance(byte_range, tuple) or len(byte_range) != 2:
        raise ValueError("byte_range must be a (start, end) tuple")

    start, end = byte_range

    if start is None and end is None:
        raise ValueError("byte_range must specify start or end")

    for value in (start, end):
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("byte_range values must be non-negative integers")
        if value < 0:
            raise ValueError("byte_range values must be non-negative")

    if start is not None and end is not None and end < start:
        raise ValueError("byte_range end must be greater than or equal to start")

    if start is None:
        return "bytes=-{}".format(end)

    if end is None:
        return "bytes={}-".format(start)

    return "bytes={}-{}".format(start, end)


def build_range_headers(byte_range):
    """Build HTTP Range headers for a download request."""

    range_header = format_byte_range(byte_range)

    if range_header is None:
        return None

    return {"Range": range_header}
