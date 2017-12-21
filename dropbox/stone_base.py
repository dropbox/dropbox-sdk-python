"""
Helpers for representing Stone data types in Python.

This module should be dropped into a project that requires the use of Stone. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

from __future__ import absolute_import, unicode_literals

try:
    from . import stone_validators as bv
except (ImportError, SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import stone_validators as bv  # type: ignore

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression


class Union(object):
    # TODO(kelkabany): Possible optimization is to remove _value if a
    # union is composed of only symbols.
    __slots__ = ['_tag', '_value']
    _tagmap = {}  # type: typing.Dict[typing.Text, bv.Validator]
    _permissioned_tagmaps = set()  # type: typing.Set[typing.Text]

    def __init__(self, tag, value=None):
        validator = None
        tagmap_names = ['_{}_tagmap'.format(map_name) for map_name in self._permissioned_tagmaps]
        for tagmap_name in ['_tagmap'] + tagmap_names:
            if tag in getattr(self, tagmap_name):
                validator = getattr(self, tagmap_name)[tag]
        assert validator is not None, 'Invalid tag %r.' % tag
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value

    def __eq__(self, other):
        # Also need to check if one class is a subclass of another. If one union extends another,
        # the common fields should be able to be compared to each other.
        return (
            isinstance(other, Union) and
            (isinstance(self, other.__class__) or isinstance(other, self.__class__)) and
            self._tag == other._tag and self._value == other._value
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self._tag, self._value))

    @classmethod
    def _is_tag_present(cls, tag, caller_permissions):
        assert tag, 'tag value should not be None'

        if tag in cls._tagmap:
            return True

        for extra_permission in caller_permissions.permissions:
            tagmap_name = '_{}_tagmap'.format(extra_permission)
            if hasattr(cls, tagmap_name) and tag in getattr(cls, tagmap_name):
                return True

        return False

    @classmethod
    def _get_val_data_type(cls, tag, caller_permissions):
        assert tag, 'tag value should not be None'

        for extra_permission in caller_permissions.permissions:
            tagmap_name = '_{}_tagmap'.format(extra_permission)
            if hasattr(cls, tagmap_name) and tag in getattr(cls, tagmap_name):
                return getattr(cls, tagmap_name)[tag]

        return cls._tagmap[tag]

class Route(object):

    def __init__(self, name, deprecated, arg_type, result_type, error_type, attrs):
        self.name = name
        self.deprecated = deprecated
        self.arg_type = arg_type
        self.result_type = result_type
        self.error_type = error_type
        assert isinstance(attrs, dict), 'Expected dict, got %r' % attrs
        self.attrs = attrs

    def __repr__(self):
        return 'Route({!r}, {!r}, {!r}, {!r}, {!r}, {!r})'.format(
            self.name,
            self.deprecated,
            self.arg_type,
            self.result_type,
            self.error_type,
            self.attrs)
