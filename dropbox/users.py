# Auto-generated by BabelAPI, do not modify.
"""
This namespace contains endpoints user management.
"""

try:
    from . import babel_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import babel_validators as bv

class GetAccountArg(object):
    """
    Arguments for get_account.

    :ivar account_id: A user's account identifier.
    """

    __slots__ = [
        '_account_id_value',
        '_account_id_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 account_id=None):
        self._account_id_value = None
        self._account_id_present = False
        if account_id is not None:
            self.account_id = account_id

    @property
    def account_id(self):
        """
        A user's account identifier.

        :rtype: str
        """
        if self._account_id_present:
            return self._account_id_value
        else:
            raise AttributeError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        val = self._account_id_validator.validate(val)
        self._account_id_value = val
        self._account_id_present = True

    @account_id.deleter
    def account_id(self):
        self._account_id_value = None
        self._account_id_present = False

    def __repr__(self):
        return 'GetAccountArg(account_id={!r})'.format(
            self._account_id_value,
        )

class GetAccountError(object):
    """
    Error returned by get_account.

    :ivar no_account: The specified ``GetAccountArg.account_id`` does not exist.
    """

    __slots__ = ['_tag', '_value']

    _catch_all = 'unknown'
    # Attribute is overwritten below the class definition
    no_account = None
    # Attribute is overwritten below the class definition
    unknown = None

    def __init__(self, tag, value=None):
        assert tag in self._tagmap, 'Invalid tag %r.' % tag
        validator = self._tagmap[tag]
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value

    def is_no_account(self):
        return self._tag == 'no_account'

    def is_unknown(self):
        return self._tag == 'unknown'

    def __repr__(self):
        return 'GetAccountError(%r)' % self._tag

class AccountType(object):
    """
    What type of account this user has.

    :ivar basic: The basic account type.
    :ivar pro: The Dropbox Pro account type.
    :ivar business: The Dropbox for Business account type.
    """

    __slots__ = ['_tag', '_value']

    _catch_all = None
    # Attribute is overwritten below the class definition
    basic = None
    # Attribute is overwritten below the class definition
    pro = None
    # Attribute is overwritten below the class definition
    business = None

    def __init__(self, tag, value=None):
        assert tag in self._tagmap, 'Invalid tag %r.' % tag
        validator = self._tagmap[tag]
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value

    def is_basic(self):
        return self._tag == 'basic'

    def is_pro(self):
        return self._tag == 'pro'

    def is_business(self):
        return self._tag == 'business'

    def __repr__(self):
        return 'AccountType(%r)' % self._tag

class Account(object):
    """
    The amount of detail revealed about an account depends on the user being
    queried and the user making the query.

    :ivar account_id: The user's unique Dropbox ID.
    :ivar name: Details of a user's name.
    """

    __slots__ = [
        '_account_id_value',
        '_account_id_present',
        '_name_value',
        '_name_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 account_id=None,
                 name=None):
        self._account_id_value = None
        self._account_id_present = False
        self._name_value = None
        self._name_present = False
        if account_id is not None:
            self.account_id = account_id
        if name is not None:
            self.name = name

    @property
    def account_id(self):
        """
        The user's unique Dropbox ID.

        :rtype: str
        """
        if self._account_id_present:
            return self._account_id_value
        else:
            raise AttributeError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        val = self._account_id_validator.validate(val)
        self._account_id_value = val
        self._account_id_present = True

    @account_id.deleter
    def account_id(self):
        self._account_id_value = None
        self._account_id_present = False

    @property
    def name(self):
        """
        Details of a user's name.

        :rtype: Name
        """
        if self._name_present:
            return self._name_value
        else:
            raise AttributeError("missing required field 'name'")

    @name.setter
    def name(self, val):
        self._name_validator.validate_type_only(val)
        self._name_value = val
        self._name_present = True

    @name.deleter
    def name(self):
        self._name_value = None
        self._name_present = False

    def __repr__(self):
        return 'Account(account_id={!r}, name={!r})'.format(
            self._account_id_value,
            self._name_value,
        )

class BasicAccount(Account):
    """
    Basic information about any account.

    :ivar is_teammate: Whether this user is a teammate of the current user. If
        this account is the current user's account, then this will be ``True``.
    """

    __slots__ = [
        '_is_teammate_value',
        '_is_teammate_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 account_id=None,
                 name=None,
                 is_teammate=None):
        super(BasicAccount, self).__init__(account_id,
                                           name)
        self._is_teammate_value = None
        self._is_teammate_present = False
        if is_teammate is not None:
            self.is_teammate = is_teammate

    @property
    def is_teammate(self):
        """
        Whether this user is a teammate of the current user. If this account is
        the current user's account, then this will be ``True``.

        :rtype: bool
        """
        if self._is_teammate_present:
            return self._is_teammate_value
        else:
            raise AttributeError("missing required field 'is_teammate'")

    @is_teammate.setter
    def is_teammate(self, val):
        val = self._is_teammate_validator.validate(val)
        self._is_teammate_value = val
        self._is_teammate_present = True

    @is_teammate.deleter
    def is_teammate(self):
        self._is_teammate_value = None
        self._is_teammate_present = False

    def __repr__(self):
        return 'BasicAccount(account_id={!r}, name={!r}, is_teammate={!r})'.format(
            self._account_id_value,
            self._name_value,
            self._is_teammate_value,
        )

class FullAccount(Account):
    """
    Detailed information about the current user's account.

    :ivar email: The user's e-mail address.
    :ivar country: The user's two-letter country code, if available. Country
        codes are based on `ISO 3166-1
        <http://en.wikipedia.org/wiki/ISO_3166-1>`_.
    :ivar locale: The language that the user specified. Locale tags will be
        `IETF language tags <http://en.wikipedia.org/wiki/IETF_language_tag>`_.
    :ivar referral_link: The user's `referral link
        <https://www.dropbox.com/referrals>`_.
    :ivar team: If this account is a member of a team, information about that
        team.
    :ivar is_paired: Whether the user has a personal and work account. If the
        current account is personal, then ``team`` will always be None, but
        ``is_paired`` will indicate if a work account is linked.
    :ivar account_type: What type of account this user has.
    """

    __slots__ = [
        '_email_value',
        '_email_present',
        '_country_value',
        '_country_present',
        '_locale_value',
        '_locale_present',
        '_referral_link_value',
        '_referral_link_present',
        '_team_value',
        '_team_present',
        '_is_paired_value',
        '_is_paired_present',
        '_account_type_value',
        '_account_type_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 account_id=None,
                 name=None,
                 email=None,
                 locale=None,
                 referral_link=None,
                 is_paired=None,
                 account_type=None,
                 country=None,
                 team=None):
        super(FullAccount, self).__init__(account_id,
                                          name)
        self._email_value = None
        self._email_present = False
        self._country_value = None
        self._country_present = False
        self._locale_value = None
        self._locale_present = False
        self._referral_link_value = None
        self._referral_link_present = False
        self._team_value = None
        self._team_present = False
        self._is_paired_value = None
        self._is_paired_present = False
        self._account_type_value = None
        self._account_type_present = False
        if email is not None:
            self.email = email
        if country is not None:
            self.country = country
        if locale is not None:
            self.locale = locale
        if referral_link is not None:
            self.referral_link = referral_link
        if team is not None:
            self.team = team
        if is_paired is not None:
            self.is_paired = is_paired
        if account_type is not None:
            self.account_type = account_type

    @property
    def email(self):
        """
        The user's e-mail address.

        :rtype: str
        """
        if self._email_present:
            return self._email_value
        else:
            raise AttributeError("missing required field 'email'")

    @email.setter
    def email(self, val):
        val = self._email_validator.validate(val)
        self._email_value = val
        self._email_present = True

    @email.deleter
    def email(self):
        self._email_value = None
        self._email_present = False

    @property
    def country(self):
        """
        The user's two-letter country code, if available. Country codes are
        based on `ISO 3166-1 <http://en.wikipedia.org/wiki/ISO_3166-1>`_.

        :rtype: str
        """
        if self._country_present:
            return self._country_value
        else:
            return None

    @country.setter
    def country(self, val):
        if val is None:
            del self.country
            return
        val = self._country_validator.validate(val)
        self._country_value = val
        self._country_present = True

    @country.deleter
    def country(self):
        self._country_value = None
        self._country_present = False

    @property
    def locale(self):
        """
        The language that the user specified. Locale tags will be `IETF language
        tags <http://en.wikipedia.org/wiki/IETF_language_tag>`_.

        :rtype: str
        """
        if self._locale_present:
            return self._locale_value
        else:
            raise AttributeError("missing required field 'locale'")

    @locale.setter
    def locale(self, val):
        val = self._locale_validator.validate(val)
        self._locale_value = val
        self._locale_present = True

    @locale.deleter
    def locale(self):
        self._locale_value = None
        self._locale_present = False

    @property
    def referral_link(self):
        """
        The user's `referral link <https://www.dropbox.com/referrals>`_.

        :rtype: str
        """
        if self._referral_link_present:
            return self._referral_link_value
        else:
            raise AttributeError("missing required field 'referral_link'")

    @referral_link.setter
    def referral_link(self, val):
        val = self._referral_link_validator.validate(val)
        self._referral_link_value = val
        self._referral_link_present = True

    @referral_link.deleter
    def referral_link(self):
        self._referral_link_value = None
        self._referral_link_present = False

    @property
    def team(self):
        """
        If this account is a member of a team, information about that team.

        :rtype: Team
        """
        if self._team_present:
            return self._team_value
        else:
            return None

    @team.setter
    def team(self, val):
        if val is None:
            del self.team
            return
        self._team_validator.validate_type_only(val)
        self._team_value = val
        self._team_present = True

    @team.deleter
    def team(self):
        self._team_value = None
        self._team_present = False

    @property
    def is_paired(self):
        """
        Whether the user has a personal and work account. If the current account
        is personal, then ``team`` will always be None, but ``is_paired`` will
        indicate if a work account is linked.

        :rtype: bool
        """
        if self._is_paired_present:
            return self._is_paired_value
        else:
            raise AttributeError("missing required field 'is_paired'")

    @is_paired.setter
    def is_paired(self, val):
        val = self._is_paired_validator.validate(val)
        self._is_paired_value = val
        self._is_paired_present = True

    @is_paired.deleter
    def is_paired(self):
        self._is_paired_value = None
        self._is_paired_present = False

    @property
    def account_type(self):
        """
        What type of account this user has.

        :rtype: AccountType
        """
        if self._account_type_present:
            return self._account_type_value
        else:
            raise AttributeError("missing required field 'account_type'")

    @account_type.setter
    def account_type(self, val):
        self._account_type_validator.validate_type_only(val)
        self._account_type_value = val
        self._account_type_present = True

    @account_type.deleter
    def account_type(self):
        self._account_type_value = None
        self._account_type_present = False

    def __repr__(self):
        return 'FullAccount(account_id={!r}, name={!r}, email={!r}, locale={!r}, referral_link={!r}, is_paired={!r}, account_type={!r}, country={!r}, team={!r})'.format(
            self._account_id_value,
            self._name_value,
            self._email_value,
            self._locale_value,
            self._referral_link_value,
            self._is_paired_value,
            self._account_type_value,
            self._country_value,
            self._team_value,
        )

class Team(object):
    """
    Information about a team.

    :ivar id: The team's unique ID.
    :ivar name: The name of the team.
    """

    __slots__ = [
        '_id_value',
        '_id_present',
        '_name_value',
        '_name_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 id=None,
                 name=None):
        self._id_value = None
        self._id_present = False
        self._name_value = None
        self._name_present = False
        if id is not None:
            self.id = id
        if name is not None:
            self.name = name

    @property
    def id(self):
        """
        The team's unique ID.

        :rtype: str
        """
        if self._id_present:
            return self._id_value
        else:
            raise AttributeError("missing required field 'id'")

    @id.setter
    def id(self, val):
        val = self._id_validator.validate(val)
        self._id_value = val
        self._id_present = True

    @id.deleter
    def id(self):
        self._id_value = None
        self._id_present = False

    @property
    def name(self):
        """
        The name of the team.

        :rtype: str
        """
        if self._name_present:
            return self._name_value
        else:
            raise AttributeError("missing required field 'name'")

    @name.setter
    def name(self, val):
        val = self._name_validator.validate(val)
        self._name_value = val
        self._name_present = True

    @name.deleter
    def name(self):
        self._name_value = None
        self._name_present = False

    def __repr__(self):
        return 'Team(id={!r}, name={!r})'.format(
            self._id_value,
            self._name_value,
        )

class Name(object):
    """
    Representations for a person's name to assist with internationalization.

    :ivar given_name: Also known as a first name.
    :ivar surname: Also known as a last name or family name.
    :ivar familiar_name: Locale-dependent name. In the US, a person's familiar
        name is their ``given_name``, but elsewhere, it could be any combination
        of a person's ``given_name`` and ``surname``.
    :ivar display_name: A name that can be used directly to represent the name
        of a user's Dropbox account.
    """

    __slots__ = [
        '_given_name_value',
        '_given_name_present',
        '_surname_value',
        '_surname_present',
        '_familiar_name_value',
        '_familiar_name_present',
        '_display_name_value',
        '_display_name_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 given_name=None,
                 surname=None,
                 familiar_name=None,
                 display_name=None):
        self._given_name_value = None
        self._given_name_present = False
        self._surname_value = None
        self._surname_present = False
        self._familiar_name_value = None
        self._familiar_name_present = False
        self._display_name_value = None
        self._display_name_present = False
        if given_name is not None:
            self.given_name = given_name
        if surname is not None:
            self.surname = surname
        if familiar_name is not None:
            self.familiar_name = familiar_name
        if display_name is not None:
            self.display_name = display_name

    @property
    def given_name(self):
        """
        Also known as a first name.

        :rtype: str
        """
        if self._given_name_present:
            return self._given_name_value
        else:
            raise AttributeError("missing required field 'given_name'")

    @given_name.setter
    def given_name(self, val):
        val = self._given_name_validator.validate(val)
        self._given_name_value = val
        self._given_name_present = True

    @given_name.deleter
    def given_name(self):
        self._given_name_value = None
        self._given_name_present = False

    @property
    def surname(self):
        """
        Also known as a last name or family name.

        :rtype: str
        """
        if self._surname_present:
            return self._surname_value
        else:
            raise AttributeError("missing required field 'surname'")

    @surname.setter
    def surname(self, val):
        val = self._surname_validator.validate(val)
        self._surname_value = val
        self._surname_present = True

    @surname.deleter
    def surname(self):
        self._surname_value = None
        self._surname_present = False

    @property
    def familiar_name(self):
        """
        Locale-dependent name. In the US, a person's familiar name is their
        ``given_name``, but elsewhere, it could be any combination of a person's
        ``given_name`` and ``surname``.

        :rtype: str
        """
        if self._familiar_name_present:
            return self._familiar_name_value
        else:
            raise AttributeError("missing required field 'familiar_name'")

    @familiar_name.setter
    def familiar_name(self, val):
        val = self._familiar_name_validator.validate(val)
        self._familiar_name_value = val
        self._familiar_name_present = True

    @familiar_name.deleter
    def familiar_name(self):
        self._familiar_name_value = None
        self._familiar_name_present = False

    @property
    def display_name(self):
        """
        A name that can be used directly to represent the name of a user's
        Dropbox account.

        :rtype: str
        """
        if self._display_name_present:
            return self._display_name_value
        else:
            raise AttributeError("missing required field 'display_name'")

    @display_name.setter
    def display_name(self, val):
        val = self._display_name_validator.validate(val)
        self._display_name_value = val
        self._display_name_present = True

    @display_name.deleter
    def display_name(self):
        self._display_name_value = None
        self._display_name_present = False

    def __repr__(self):
        return 'Name(given_name={!r}, surname={!r}, familiar_name={!r}, display_name={!r})'.format(
            self._given_name_value,
            self._surname_value,
            self._familiar_name_value,
            self._display_name_value,
        )

class SpaceUsage(object):
    """
    Information about a user's space usage and quota.

    :ivar used: The user's total space usage (bytes).
    :ivar allocation: The user's space allocation.
    """

    __slots__ = [
        '_used_value',
        '_used_present',
        '_allocation_value',
        '_allocation_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 used=None,
                 allocation=None):
        self._used_value = None
        self._used_present = False
        self._allocation_value = None
        self._allocation_present = False
        if used is not None:
            self.used = used
        if allocation is not None:
            self.allocation = allocation

    @property
    def used(self):
        """
        The user's total space usage (bytes).

        :rtype: long
        """
        if self._used_present:
            return self._used_value
        else:
            raise AttributeError("missing required field 'used'")

    @used.setter
    def used(self, val):
        val = self._used_validator.validate(val)
        self._used_value = val
        self._used_present = True

    @used.deleter
    def used(self):
        self._used_value = None
        self._used_present = False

    @property
    def allocation(self):
        """
        The user's space allocation.

        :rtype: SpaceAllocation
        """
        if self._allocation_present:
            return self._allocation_value
        else:
            raise AttributeError("missing required field 'allocation'")

    @allocation.setter
    def allocation(self, val):
        self._allocation_validator.validate_type_only(val)
        self._allocation_value = val
        self._allocation_present = True

    @allocation.deleter
    def allocation(self):
        self._allocation_value = None
        self._allocation_present = False

    def __repr__(self):
        return 'SpaceUsage(used={!r}, allocation={!r})'.format(
            self._used_value,
            self._allocation_value,
        )

class SpaceAllocation(object):
    """
    Space is allocated differently based on the type of account.

    :ivar IndividualSpaceAllocation individual: The user's space allocation
        applies only to their individual account.
    :ivar TeamSpaceAllocation team: The user shares space with other members of
        their team.
    """

    __slots__ = ['_tag', '_value']

    _catch_all = 'other'
    # Attribute is overwritten below the class definition
    other = None

    def __init__(self, tag, value=None):
        assert tag in self._tagmap, 'Invalid tag %r.' % tag
        validator = self._tagmap[tag]
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value

    @classmethod
    def individual(cls, val):
        return cls('individual', val)

    @classmethod
    def team(cls, val):
        return cls('team', val)

    def is_individual(self):
        return self._tag == 'individual'

    def is_team(self):
        return self._tag == 'team'

    def is_other(self):
        return self._tag == 'other'

    def get_individual(self):
        if not self.is_individual():
            raise AttributeError("tag 'individual' not set")
        return self._value

    def get_team(self):
        if not self.is_team():
            raise AttributeError("tag 'team' not set")
        return self._value

    def __repr__(self):
        return 'SpaceAllocation(%r)' % self._tag

class IndividualSpaceAllocation(object):
    """
    :ivar allocated: The total space allocated to the user's account (bytes).
    """

    __slots__ = [
        '_allocated_value',
        '_allocated_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 allocated=None):
        self._allocated_value = None
        self._allocated_present = False
        if allocated is not None:
            self.allocated = allocated

    @property
    def allocated(self):
        """
        The total space allocated to the user's account (bytes).

        :rtype: long
        """
        if self._allocated_present:
            return self._allocated_value
        else:
            raise AttributeError("missing required field 'allocated'")

    @allocated.setter
    def allocated(self, val):
        val = self._allocated_validator.validate(val)
        self._allocated_value = val
        self._allocated_present = True

    @allocated.deleter
    def allocated(self):
        self._allocated_value = None
        self._allocated_present = False

    def __repr__(self):
        return 'IndividualSpaceAllocation(allocated={!r})'.format(
            self._allocated_value,
        )

class TeamSpaceAllocation(object):
    """
    :ivar used: The total space currently used by the user's team (bytes).
    :ivar allocated: The total space allocated to the user's team (bytes).
    """

    __slots__ = [
        '_used_value',
        '_used_present',
        '_allocated_value',
        '_allocated_present',
    ]

    _has_required_fields = True

    def __init__(self,
                 used=None,
                 allocated=None):
        self._used_value = None
        self._used_present = False
        self._allocated_value = None
        self._allocated_present = False
        if used is not None:
            self.used = used
        if allocated is not None:
            self.allocated = allocated

    @property
    def used(self):
        """
        The total space currently used by the user's team (bytes).

        :rtype: long
        """
        if self._used_present:
            return self._used_value
        else:
            raise AttributeError("missing required field 'used'")

    @used.setter
    def used(self, val):
        val = self._used_validator.validate(val)
        self._used_value = val
        self._used_present = True

    @used.deleter
    def used(self):
        self._used_value = None
        self._used_present = False

    @property
    def allocated(self):
        """
        The total space allocated to the user's team (bytes).

        :rtype: long
        """
        if self._allocated_present:
            return self._allocated_value
        else:
            raise AttributeError("missing required field 'allocated'")

    @allocated.setter
    def allocated(self, val):
        val = self._allocated_validator.validate(val)
        self._allocated_value = val
        self._allocated_present = True

    @allocated.deleter
    def allocated(self):
        self._allocated_value = None
        self._allocated_present = False

    def __repr__(self):
        return 'TeamSpaceAllocation(used={!r}, allocated={!r})'.format(
            self._used_value,
            self._allocated_value,
        )

GetAccountArg._account_id_validator = bv.String(min_length=40, max_length=40)
GetAccountArg._all_field_names_ = set(['account_id'])
GetAccountArg._all_fields_ = [('account_id', GetAccountArg._account_id_validator)]

GetAccountError._no_account_validator = bv.Void()
GetAccountError._unknown_validator = bv.Void()
GetAccountError._tagmap = {
    'no_account': GetAccountError._no_account_validator,
    'unknown': GetAccountError._unknown_validator,
}

GetAccountError.no_account = GetAccountError('no_account')
GetAccountError.unknown = GetAccountError('unknown')

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

Account._account_id_validator = bv.String(min_length=40, max_length=40)
Account._name_validator = bv.Struct(Name)
Account._all_field_names_ = set([
    'account_id',
    'name',
])
Account._all_fields_ = [
    ('account_id', Account._account_id_validator),
    ('name', Account._name_validator),
]

BasicAccount._is_teammate_validator = bv.Boolean()
BasicAccount._all_field_names_ = Account._all_field_names_.union(set(['is_teammate']))
BasicAccount._all_fields_ = Account._all_fields_ + [('is_teammate', BasicAccount._is_teammate_validator)]

FullAccount._email_validator = bv.String()
FullAccount._country_validator = bv.Nullable(bv.String(min_length=2, max_length=2))
FullAccount._locale_validator = bv.String(min_length=2, max_length=5)
FullAccount._referral_link_validator = bv.String()
FullAccount._team_validator = bv.Nullable(bv.Struct(Team))
FullAccount._is_paired_validator = bv.Boolean()
FullAccount._account_type_validator = bv.Union(AccountType)
FullAccount._all_field_names_ = Account._all_field_names_.union(set([
    'email',
    'country',
    'locale',
    'referral_link',
    'team',
    'is_paired',
    'account_type',
]))
FullAccount._all_fields_ = Account._all_fields_ + [
    ('email', FullAccount._email_validator),
    ('country', FullAccount._country_validator),
    ('locale', FullAccount._locale_validator),
    ('referral_link', FullAccount._referral_link_validator),
    ('team', FullAccount._team_validator),
    ('is_paired', FullAccount._is_paired_validator),
    ('account_type', FullAccount._account_type_validator),
]

Team._id_validator = bv.String()
Team._name_validator = bv.String()
Team._all_field_names_ = set([
    'id',
    'name',
])
Team._all_fields_ = [
    ('id', Team._id_validator),
    ('name', Team._name_validator),
]

Name._given_name_validator = bv.String()
Name._surname_validator = bv.String()
Name._familiar_name_validator = bv.String()
Name._display_name_validator = bv.String()
Name._all_field_names_ = set([
    'given_name',
    'surname',
    'familiar_name',
    'display_name',
])
Name._all_fields_ = [
    ('given_name', Name._given_name_validator),
    ('surname', Name._surname_validator),
    ('familiar_name', Name._familiar_name_validator),
    ('display_name', Name._display_name_validator),
]

SpaceUsage._used_validator = bv.UInt64()
SpaceUsage._allocation_validator = bv.Union(SpaceAllocation)
SpaceUsage._all_field_names_ = set([
    'used',
    'allocation',
])
SpaceUsage._all_fields_ = [
    ('used', SpaceUsage._used_validator),
    ('allocation', SpaceUsage._allocation_validator),
]

SpaceAllocation._individual_validator = bv.Struct(IndividualSpaceAllocation)
SpaceAllocation._team_validator = bv.Struct(TeamSpaceAllocation)
SpaceAllocation._other_validator = bv.Void()
SpaceAllocation._tagmap = {
    'individual': SpaceAllocation._individual_validator,
    'team': SpaceAllocation._team_validator,
    'other': SpaceAllocation._other_validator,
}

SpaceAllocation.other = SpaceAllocation('other')

IndividualSpaceAllocation._allocated_validator = bv.UInt64()
IndividualSpaceAllocation._all_field_names_ = set(['allocated'])
IndividualSpaceAllocation._all_fields_ = [('allocated', IndividualSpaceAllocation._allocated_validator)]

TeamSpaceAllocation._used_validator = bv.UInt64()
TeamSpaceAllocation._allocated_validator = bv.UInt64()
TeamSpaceAllocation._all_field_names_ = set([
    'used',
    'allocated',
])
TeamSpaceAllocation._all_fields_ = [
    ('used', TeamSpaceAllocation._used_validator),
    ('allocated', TeamSpaceAllocation._allocated_validator),
]

