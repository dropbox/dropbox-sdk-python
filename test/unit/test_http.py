import pytest

from dropbox._http import format_byte_range, build_range_headers


@pytest.mark.parametrize(
    "byte_range, expected",
    [
        (None, None),
        ((0, 99), "bytes=0-99"),
        ((100, None), "bytes=100-"),
        ((None, 500), "bytes=-500"),
    ],
)
def test_format_byte_range(byte_range, expected):
    assert format_byte_range(byte_range) == expected


@pytest.mark.parametrize(
    "byte_range",
    [
        (None, None),
        (-1, 10),
        (10, -1),
        (10, 5),
        "0-10",
        (0,),
    ],
)
def test_format_byte_range_rejects_invalid_values(byte_range):
    with pytest.raises((TypeError, ValueError)):
        format_byte_range(byte_range)


def test_format_byte_range_rejects_bool():
    with pytest.raises(TypeError):
        format_byte_range((True, 10))


@pytest.mark.parametrize(
    "byte_range, expected",
    [
        (None, None),
        ((0, 99), {"Range": "bytes=0-99"}),
        ((100, None), {"Range": "bytes=100-"}),
        ((None, 500), {"Range": "bytes=-500"}),
    ],
)
def test_build_range_headers(byte_range, expected):
    assert build_range_headers(byte_range) == expected
