# Auto-generated by Stone, do not modify.
# @generated
# flake8: noqa
# pylint: skip-file
"""
This namespace contains common data types used within the users namespace.
"""

from stone.backends.python_rsrc import stone_base as bb
from stone.backends.python_rsrc import stone_validators as bv

class AccountType(bb.Union):
    """
    What type of account this user has.

    This class acts as a tagged union. Only one of the ``is_*`` methods will
    return true. To get the associated value of a tag (if one exists), use the
    corresponding ``get_*`` method.

    :ivar users_common.AccountType.basic: The basic account type.
    :ivar users_common.AccountType.pro: The Dropbox Pro account type.
    :ivar users_common.AccountType.business: The Dropbox Business account type.
    """

    _catch_all = None
    # Attribute is overwritten below the class definition
    basic = None
    # Attribute is overwritten below the class definition
    pro = None
    # Attribute is overwritten below the class definition
    business = None

    def is_basic(self):
        """
        Check if the union tag is ``basic``.

        :rtype: bool
        """
        return self._tag == 'basic'

    def is_pro(self):
        """
        Check if the union tag is ``pro``.

        :rtype: bool
        """
        return self._tag == 'pro'

    def is_business(self):
        """
        Check if the union tag is ``business``.

        :rtype: bool
        """
        return self._tag == 'business'

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super()._process_custom_annotations(annotation_type, field_path, processor)

AccountType_validator = bv.Union(AccountType)

AccountId_validator = bv.String(min_length=40, max_length=40)
AccountType._basic_validator = bv.Void()
AccountType._pro_validator = bv.Void()
AccountType._business_validator = bv.Void()
AccountType._tagmap = {
    'basic': AccountType._basic_validator,
    'pro': AccountType._pro_validator,
    'business': AccountType._business_validator,
}

AccountType.basic = AccountType('basic')
AccountType.pro = AccountType('pro')
AccountType.business = AccountType('business')

ROUTES = {
}

