# -*- coding: utf-8 -*-
# Auto-generated by Stone, do not modify.
# @generated
# flake8: noqa
# pylint: skip-file
from __future__ import unicode_literals
from stone.backends.python_rsrc import stone_base as bb
from stone.backends.python_rsrc import stone_validators as bv

class PathRoot(bb.Union):
    """
    This class acts as a tagged union. Only one of the ``is_*`` methods will
    return true. To get the associated value of a tag (if one exists), use the
    corresponding ``get_*`` method.

    :ivar common.PathRoot.home: Paths are relative to the authenticating user's
        home namespace, whether or not that user belongs to a team.
    :ivar str common.PathRoot.root: Paths are relative to the authenticating
        user's root namespace (This results in
        :field:`PathRootError.invalid_root` if the user's root namespace has
        changed.).
    :ivar str common.PathRoot.namespace_id: Paths are relative to given
        namespace id (This results in :field:`PathRootError.no_permission` if
        you don't have access to this namespace.).
    """

    _catch_all = 'other'
    # Attribute is overwritten below the class definition
    home = None
    # Attribute is overwritten below the class definition
    other = None

    @classmethod
    def root(cls, val):
        """
        Create an instance of this class set to the ``root`` tag with value
        ``val``.

        :param str val:
        :rtype: PathRoot
        """
        return cls('root', val)

    @classmethod
    def namespace_id(cls, val):
        """
        Create an instance of this class set to the ``namespace_id`` tag with
        value ``val``.

        :param str val:
        :rtype: PathRoot
        """
        return cls('namespace_id', val)

    def is_home(self):
        """
        Check if the union tag is ``home``.

        :rtype: bool
        """
        return self._tag == 'home'

    def is_root(self):
        """
        Check if the union tag is ``root``.

        :rtype: bool
        """
        return self._tag == 'root'

    def is_namespace_id(self):
        """
        Check if the union tag is ``namespace_id``.

        :rtype: bool
        """
        return self._tag == 'namespace_id'

    def is_other(self):
        """
        Check if the union tag is ``other``.

        :rtype: bool
        """
        return self._tag == 'other'

    def get_root(self):
        """
        Paths are relative to the authenticating user's root namespace (This
        results in ``PathRootError.invalid_root`` if the user's root namespace
        has changed.).

        Only call this if :meth:`is_root` is true.

        :rtype: str
        """
        if not self.is_root():
            raise AttributeError("tag 'root' not set")
        return self._value

    def get_namespace_id(self):
        """
        Paths are relative to given namespace id (This results in
        ``PathRootError.no_permission`` if you don't have access to this
        namespace.).

        Only call this if :meth:`is_namespace_id` is true.

        :rtype: str
        """
        if not self.is_namespace_id():
            raise AttributeError("tag 'namespace_id' not set")
        return self._value

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super(PathRoot, self)._process_custom_annotations(annotation_type, field_path, processor)

PathRoot_validator = bv.Union(PathRoot)

class PathRootError(bb.Union):
    """
    This class acts as a tagged union. Only one of the ``is_*`` methods will
    return true. To get the associated value of a tag (if one exists), use the
    corresponding ``get_*`` method.

    :ivar RootInfo PathRootError.invalid_root: The root namespace id in
        Dropbox-API-Path-Root header is not valid. The value of this error is
        the user's latest root info.
    :ivar common.PathRootError.no_permission: You don't have permission to
        access the namespace id in Dropbox-API-Path-Root  header.
    """

    _catch_all = 'other'
    # Attribute is overwritten below the class definition
    no_permission = None
    # Attribute is overwritten below the class definition
    other = None

    @classmethod
    def invalid_root(cls, val):
        """
        Create an instance of this class set to the ``invalid_root`` tag with
        value ``val``.

        :param RootInfo val:
        :rtype: PathRootError
        """
        return cls('invalid_root', val)

    def is_invalid_root(self):
        """
        Check if the union tag is ``invalid_root``.

        :rtype: bool
        """
        return self._tag == 'invalid_root'

    def is_no_permission(self):
        """
        Check if the union tag is ``no_permission``.

        :rtype: bool
        """
        return self._tag == 'no_permission'

    def is_other(self):
        """
        Check if the union tag is ``other``.

        :rtype: bool
        """
        return self._tag == 'other'

    def get_invalid_root(self):
        """
        The root namespace id in Dropbox-API-Path-Root header is not valid. The
        value of this error is the user's latest root info.

        Only call this if :meth:`is_invalid_root` is true.

        :rtype: RootInfo
        """
        if not self.is_invalid_root():
            raise AttributeError("tag 'invalid_root' not set")
        return self._value

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super(PathRootError, self)._process_custom_annotations(annotation_type, field_path, processor)

PathRootError_validator = bv.Union(PathRootError)

class RootInfo(bb.Struct):
    """
    Information about current user's root.

    :ivar common.RootInfo.root_namespace_id: The namespace ID for user's root
        namespace. It will be the namespace ID of the shared team root if the
        user is member of a team with a separate team root. Otherwise it will be
        same as ``RootInfo.home_namespace_id``.
    :ivar common.RootInfo.home_namespace_id: The namespace ID for user's home
        namespace.
    """

    __slots__ = [
        '_root_namespace_id_value',
        '_home_namespace_id_value',
    ]

    _has_required_fields = True

    def __init__(self,
                 root_namespace_id=None,
                 home_namespace_id=None):
        self._root_namespace_id_value = bb.NOT_SET
        self._home_namespace_id_value = bb.NOT_SET
        if root_namespace_id is not None:
            self.root_namespace_id = root_namespace_id
        if home_namespace_id is not None:
            self.home_namespace_id = home_namespace_id

    # Instance attribute type: str (validator is set below)
    root_namespace_id = bb.Attribute("root_namespace_id")

    # Instance attribute type: str (validator is set below)
    home_namespace_id = bb.Attribute("home_namespace_id")

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super(RootInfo, self)._process_custom_annotations(annotation_type, field_path, processor)

RootInfo_validator = bv.StructTree(RootInfo)

class TeamRootInfo(RootInfo):
    """
    Root info when user is member of a team with a separate root namespace ID.

    :ivar common.TeamRootInfo.home_path: The path for user's home directory
        under the shared team root.
    """

    __slots__ = [
        '_home_path_value',
    ]

    _has_required_fields = True

    def __init__(self,
                 root_namespace_id=None,
                 home_namespace_id=None,
                 home_path=None):
        super(TeamRootInfo, self).__init__(root_namespace_id,
                                           home_namespace_id)
        self._home_path_value = bb.NOT_SET
        if home_path is not None:
            self.home_path = home_path

    # Instance attribute type: str (validator is set below)
    home_path = bb.Attribute("home_path")

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super(TeamRootInfo, self)._process_custom_annotations(annotation_type, field_path, processor)

TeamRootInfo_validator = bv.Struct(TeamRootInfo)

class UserRootInfo(RootInfo):
    """
    Root info when user is not member of a team or the user is a member of a
    team and the team does not have a separate root namespace.
    """

    __slots__ = [
    ]

    _has_required_fields = True

    def __init__(self,
                 root_namespace_id=None,
                 home_namespace_id=None):
        super(UserRootInfo, self).__init__(root_namespace_id,
                                           home_namespace_id)

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super(UserRootInfo, self)._process_custom_annotations(annotation_type, field_path, processor)

UserRootInfo_validator = bv.Struct(UserRootInfo)

Date_validator = bv.Timestamp(u'%Y-%m-%d')
DisplayName_validator = bv.String(pattern=u'[^/:?*<>"|]*')
DisplayNameLegacy_validator = bv.String()
DropboxTimestamp_validator = bv.Timestamp(u'%Y-%m-%dT%H:%M:%SZ')
EmailAddress_validator = bv.String(max_length=255, pattern=u"^['#&A-Za-z0-9._%+-]+@[A-Za-z0-9-][A-Za-z0-9.-]*\\.[A-Za-z]{2,15}$")
# A ISO639-1 code.
LanguageCode_validator = bv.String(min_length=2)
NamePart_validator = bv.String(min_length=1, max_length=100, pattern=u'[^/:?*<>"|]*')
NamespaceId_validator = bv.String(pattern=u'[-_0-9a-zA-Z:]+')
OptionalNamePart_validator = bv.String(max_length=100, pattern=u'[^/:?*<>"|]*')
SessionId_validator = bv.String()
SharedFolderId_validator = NamespaceId_validator
PathRoot._home_validator = bv.Void()
PathRoot._root_validator = NamespaceId_validator
PathRoot._namespace_id_validator = NamespaceId_validator
PathRoot._other_validator = bv.Void()
PathRoot._tagmap = {
    'home': PathRoot._home_validator,
    'root': PathRoot._root_validator,
    'namespace_id': PathRoot._namespace_id_validator,
    'other': PathRoot._other_validator,
}

PathRoot.home = PathRoot('home')
PathRoot.other = PathRoot('other')

PathRootError._invalid_root_validator = RootInfo_validator
PathRootError._no_permission_validator = bv.Void()
PathRootError._other_validator = bv.Void()
PathRootError._tagmap = {
    'invalid_root': PathRootError._invalid_root_validator,
    'no_permission': PathRootError._no_permission_validator,
    'other': PathRootError._other_validator,
}

PathRootError.no_permission = PathRootError('no_permission')
PathRootError.other = PathRootError('other')

RootInfo.root_namespace_id.validator = NamespaceId_validator
RootInfo.home_namespace_id.validator = NamespaceId_validator
RootInfo._field_names_ = set([
    'root_namespace_id',
    'home_namespace_id',
])
RootInfo._all_field_names_ = RootInfo._field_names_
RootInfo._fields_ = [
    ('root_namespace_id', RootInfo.root_namespace_id.validator),
    ('home_namespace_id', RootInfo.home_namespace_id.validator),
]
RootInfo._all_fields_ = RootInfo._fields_

RootInfo._tag_to_subtype_ = {
    (u'team',): TeamRootInfo_validator,
    (u'user',): UserRootInfo_validator,
}
RootInfo._pytype_to_tag_and_subtype_ = {
    TeamRootInfo: ((u'team',), TeamRootInfo_validator),
    UserRootInfo: ((u'user',), UserRootInfo_validator),
}
RootInfo._is_catch_all_ = True

TeamRootInfo.home_path.validator = bv.String()
TeamRootInfo._field_names_ = set(['home_path'])
TeamRootInfo._all_field_names_ = RootInfo._all_field_names_.union(TeamRootInfo._field_names_)
TeamRootInfo._fields_ = [('home_path', TeamRootInfo.home_path.validator)]
TeamRootInfo._all_fields_ = RootInfo._all_fields_ + TeamRootInfo._fields_

UserRootInfo._field_names_ = set([])
UserRootInfo._all_field_names_ = RootInfo._all_field_names_.union(UserRootInfo._field_names_)
UserRootInfo._fields_ = []
UserRootInfo._all_fields_ = RootInfo._all_fields_ + UserRootInfo._fields_

ROUTES = {
}

