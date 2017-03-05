"""
Serializers that marshal Babel data types into wire formats.

Currently, only JSON is supported. If possible, serializers should be kept
separate from the RPC format.

This module should be dropped into a project that requires the use of Babel. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.

EDITING THIS FILE? Please modify the version in the babelapi repo,
"""

from __future__ import absolute_import

import base64
import collections
import datetime
import functools
import json
import six

try:
    from . import babel_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import babel_validators as bv


# --------------------------------------------------------------
# JSON Encoder

def json_encode(data_type, obj, alias_validators=None, old_style=False):
    """Encodes an object into JSON based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.
        alias_validators (Optional[Mapping[bv.Validator, Callable[[], None]]]):
            Custom validation functions. These must raise bv.ValidationError on
            failure.

    Returns:
        str: JSON-encoded object.

    This function will also do additional validation that wasn't done by the
    objects themselves:

    1. The passed in obj may not have been validated with data_type yet.
    2. If an object that should be a Struct was assigned to a field, its
       type has been validated, but the presence of all required fields
       hasn't been.
    3. If an object that should be a Union was assigned to a field, whether
       or not a tag has been set has not been validated.
    4. A list may have passed validation initially, but been mutated since.

    Example of serializing a struct to JSON:

    struct FileRef
       path String
       rev String

    > fr = FileRef()
    > fr.path = 'a/b/c'
    > fr.rev = '1234'
    > JsonEncoder.encode(fr)
    "{'path': 'a/b/c', 'rev': '1234'}"

    Example of serializing a union to JSON:

    union UploadMode
        add
        overwrite
        update FileRef

    > um = UploadMode()
    > um.set_add()
    > JsonEncoder.encode(um)
    '"add"'
    > um.update = fr
    > JsonEncoder.encode(um)
    "{'update': {'path': 'a/b/c', 'rev': '1234'}}"
    """
    return json.dumps(
        json_compat_obj_encode(
            data_type, obj, alias_validators, old_style))


def json_compat_obj_encode(
        data_type, obj, alias_validators=None, old_style=False,
        for_msgpack=False):
    """Encodes an object into a JSON-compatible dict based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.

    Returns:
        An object that when passed to json.dumps() will produce a string
        giving the JSON-encoded object.

    See json_encode() for additional information about validation.
    """
    if isinstance(data_type, (bv.Struct, bv.Union)):
        # Only validate the type because fields are validated on assignment.
        data_type.validate_type_only(obj)
    else:
        data_type.validate(obj)
    return _json_compat_obj_encode_helper(
        data_type, obj, alias_validators, old_style, for_msgpack)


def _json_compat_obj_encode_helper(
        data_type, obj, alias_validators, old_style, for_msgpack):
    """
    See json_encode() for argument descriptions.
    """
    if isinstance(data_type, bv.List):
        return _encode_list(
            data_type, obj, alias_validators, old_style=old_style,
            for_msgpack=for_msgpack)
    elif isinstance(data_type, bv.Nullable):
        return _encode_nullable(
            data_type, obj, alias_validators, old_style=old_style,
            for_msgpack=for_msgpack)
    elif isinstance(data_type, bv.Primitive):
        return _make_json_friendly(
            data_type, obj, alias_validators, for_msgpack=for_msgpack)
    elif isinstance(data_type, bv.StructTree):
        return _encode_struct_tree(
            data_type, obj, alias_validators, old_style=old_style,
            for_msgpack=for_msgpack)
    elif isinstance(data_type, bv.Struct):
        return _encode_struct(
            data_type, obj, alias_validators, old_style=old_style,
            for_msgpack=for_msgpack)
    elif isinstance(data_type, bv.Union):
        if old_style:
            return _encode_union_old(
                data_type, obj, alias_validators, for_msgpack=for_msgpack)
        else:
            return _encode_union(
                data_type, obj, alias_validators, for_msgpack=for_msgpack)
    else:
        raise AssertionError('Unsupported data type %r' %
                             type(data_type).__name__)


def _encode_list(data_type, obj, alias_validators, old_style, for_msgpack):
    """
    The data_type argument must be a List.
    See json_encode() for argument descriptions.
    """
    # Because Lists are mutable, we always validate them during serialization.
    obj = data_type.validate(obj)
    return [
        _json_compat_obj_encode_helper(
            data_type.item_validator, item, alias_validators, old_style, for_msgpack)
        for item in obj
    ]


def _encode_nullable(data_type, obj, alias_validators, old_style, for_msgpack):
    """
    The data_type argument must be a Nullable.
    See json_encode() for argument descriptions.
    """
    if obj is not None:
        return _json_compat_obj_encode_helper(
            data_type.validator, obj, alias_validators, old_style, for_msgpack)
    else:
        return None


def _encode_struct(data_type, obj, alias_validators, old_style, for_msgpack):
    """
    The data_type argument must be a Struct or StructTree.
    See json_encode() for argument descriptions.
    """
    # We skip validation of fields with primitive data types in structs and
    # unions because they've already been validated on assignment.
    d = collections.OrderedDict()
    for field_name, field_data_type in data_type.definition._all_fields_:
        try:
            val = getattr(obj, field_name)
        except AttributeError as e:
            raise bv.ValidationError(e.args[0])
        presence_key = '_%s_present' % field_name
        if val is not None and getattr(obj, presence_key):
            # This check makes sure that we don't serialize absent struct
            # fields as null, even if there is a default.
            try:
                d[field_name] = _json_compat_obj_encode_helper(
                    field_data_type, val, alias_validators, old_style,
                    for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(field_name)
                raise
    return d


def _encode_union(data_type, obj, alias_validators, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_encode() for argument descriptions.
    """
    if obj._tag is None:
        raise bv.ValidationError('no tag set')
    field_data_type = data_type.definition._tagmap[obj._tag]

    if (isinstance(field_data_type, bv.Void) or
            (isinstance(field_data_type, bv.Nullable) and obj._value is None)):
        return {'.tag': obj._tag}
    else:
        try:
            encoded_val = _json_compat_obj_encode_helper(
                field_data_type, obj._value, alias_validators, False,
                for_msgpack)
        except bv.ValidationError as e:
            e.add_parent(obj._tag)
            raise
        else:
            if isinstance(field_data_type, bv.Nullable):
                # We've already checked for the null case above, so now we're
                # only interested in what the wrapped validator is.
                field_data_type = field_data_type.validator
            if (isinstance(field_data_type, bv.Struct) and
                    not isinstance(field_data_type, bv.StructTree)):
                d = collections.OrderedDict()
                d['.tag'] = obj._tag
                d.update(encoded_val)
                return d
            else:
                return collections.OrderedDict([
                    ('.tag', obj._tag),
                    (obj._tag, encoded_val)])


def _encode_union_old(data_type, obj, alias_validators, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_encode() for argument descriptions.
    """
    if obj._tag is None:
        raise bv.ValidationError('no tag set')
    field_data_type = data_type.definition._tagmap[obj._tag]
    if field_data_type is None:
        return obj._tag
    else:
        if (isinstance(field_data_type, bv.Void) or
                (isinstance(field_data_type, bv.Nullable) and
                 obj._value is None)):
            return obj._tag
        else:
            try:
                encoded_val = _json_compat_obj_encode_helper(
                    field_data_type, obj._value, alias_validators, True,
                    for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(obj._tag)
                raise
            else:
                return {obj._tag: encoded_val}


def _encode_struct_tree(
        data_type, obj, alias_validators, old_style, for_msgpack):
    """
    Args:
        data_type (StructTree)
        as_root (bool): If a struct with enumerated subtypes is designated as a
            root, then its fields including those that are inherited are
            encoded in the outermost JSON object together.

    See json_encode() for other argument descriptions.
    """
    assert type(obj) in data_type.definition._pytype_to_tag_and_subtype_, (
        '%r is not a serializable subtype of %r.' %
        (type(obj), data_type.definition))
    tags, subtype = data_type.definition._pytype_to_tag_and_subtype_[type(obj)]
    assert len(tags) == 1, tags
    assert not isinstance(subtype, bv.StructTree), (
        'Cannot serialize type %r because it enumerates subtypes.' %
        subtype.definition)
    if old_style:
        return {
            tags[0]:
                _encode_struct(
                    subtype, obj, alias_validators, old_style, for_msgpack)
        }
    d = collections.OrderedDict()
    d['.tag'] = tags[0]
    d.update(
        _encode_struct(subtype, obj, alias_validators, old_style, for_msgpack))
    return d


def _make_json_friendly(data_type, val, alias_validators, for_msgpack):
    """
    Convert a primitive type to a Python type that can be serialized by the
    json package.
    """
    if alias_validators is not None and data_type in alias_validators:
        alias_validators[data_type](val)
    if isinstance(data_type, bv.Void):
        return None
    elif isinstance(data_type, bv.Timestamp):
        return val.strftime(data_type.format)
    elif isinstance(data_type, bv.Bytes):
        if for_msgpack:
            return val
        else:
            return base64.b64encode(val).decode('ascii')
    elif isinstance(data_type, bv.Integer) and isinstance(val, bool):
        # A bool is a subclass of an int so it passes Integer validation. But,
        # we want the bool to be encoded as an Integer (1/0) rather than T/F.
        return int(val)
    else:
        return val


# --------------------------------------------------------------
# JSON Decoder

def json_decode(
        data_type, serialized_obj, alias_validators=None, strict=True,
        old_style=False):
    """Performs the reverse operation of json_encode.

    Args:
        data_type (Validator): Validator for serialized_obj.
        serialized_obj (str): The JSON string to deserialize.
        alias_validators (Optional[Mapping[bv.Validator, Callable[[], None]]]):
            Custom validation functions. These must raise bv.ValidationError on
            failure.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. strict should only be used by a
            recipient of serialized JSON if it's guaranteed that its Babel
            specs are at least as recent as the senders it receives messages
            from.

    Returns:
        The returned object depends on the input data_type.
            - Boolean -> bool
            - Bytes -> bytes
            - Float -> float
            - Integer -> long
            - List -> list
            - Nullable -> None or its wrapped type.
            - String -> unicode (PY2) or str (PY3)
            - Struct -> An instance of its definition attribute.
            - Timestamp -> datetime.datetime
            - Union -> An instance of its definition attribute.
    """
    try:
        deserialized_obj = json.loads(serialized_obj)
    except ValueError:
        raise bv.ValidationError('could not decode input as JSON')
    else:
        return json_compat_obj_decode(
            data_type, deserialized_obj, alias_validators, strict, old_style)


def json_compat_obj_decode(
        data_type, obj, alias_validators=None, strict=True, old_style=False,
        for_msgpack=False):
    """
    Decodes a JSON-compatible object based on its data type into a
    representative Python object.

    Args:
        data_type (Validator): Validator for serialized_obj.
        obj: The JSON-compatible object to decode based on data_type.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. See json_decode() for more.

    Returns:
        See json_decode().
    """
    if isinstance(data_type, bv.Primitive):
        return _make_babel_friendly(
            data_type, obj, alias_validators, strict, True, for_msgpack)
    else:
        return _json_compat_obj_decode_helper(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)


def _json_compat_obj_decode_helper(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    See json_compat_obj_decode() for argument descriptions.
    """
    if isinstance(data_type, bv.StructTree):
        return _decode_struct_tree(
            data_type, obj, alias_validators, strict, for_msgpack)
    elif isinstance(data_type, bv.Struct):
        return _decode_struct(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Union):
        if old_style:
            return _decode_union_old(
                data_type, obj, alias_validators, strict, for_msgpack)
        else:
            return _decode_union(
                data_type, obj, alias_validators, strict, for_msgpack)
    elif isinstance(data_type, bv.List):
        return _decode_list(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Nullable):
        return _decode_nullable(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Primitive):
        # Set validate to false because validation will be done by the
        # containing struct or union when the field is assigned.
        return _make_babel_friendly(
            data_type, obj, alias_validators, strict, False, for_msgpack)
    else:
        raise AssertionError('Cannot handle type %r.' % data_type)


def _decode_struct(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a Struct.
    See json_compat_obj_decode() for argument descriptions.
    """
    if obj is None and data_type.has_default():
        return data_type.get_default()
    elif not isinstance(obj, dict):
        raise bv.ValidationError('expected object, got %s' %
                                 bv.generic_type_name(obj))
    if strict:
        for key in obj:
            if (key not in data_type.definition._all_field_names_ and
                    not key.startswith('.tag')):
                raise bv.ValidationError("unknown field '%s'" % key)
    ins = data_type.definition()
    _decode_struct_fields(
        ins, data_type.definition._all_fields_, obj, alias_validators, strict,
        old_style, for_msgpack)
    # Check that all required fields have been set.
    data_type.validate_fields_only(ins)
    return ins


def _decode_struct_fields(
        ins, fields, obj, alias_validators, strict, old_style, for_msgpack):
    """
    Args:
        ins: An instance of the class representing the data type being decoded.
            The object will have its fields set.
        fields: A tuple of (field_name: str, field_validator: Validator)
        obj (dict): JSON-compatible dict that is being decoded.
        strict (bool): See :func:`json_compat_obj_decode`.

    Returns:
        None: `ins` has its fields set based on the contents of `obj`.
    """
    for name, field_data_type in fields:
        if name in obj:
            try:
                v = _json_compat_obj_decode_helper(
                    field_data_type, obj[name], alias_validators, strict,
                    old_style, for_msgpack)
                setattr(ins, name, v)
            except bv.ValidationError as e:
                e.add_parent(name)
                raise
        elif field_data_type.has_default():
            setattr(ins, name, field_data_type.get_default())


def _decode_union(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_compat_obj_decode() for argument descriptions.
    """
    val = None
    if isinstance(obj, six.string_types):
        # Handles the shorthand format where the union is serialized as only
        # the string of the tag.
        tag = obj
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if not isinstance(val_data_type, (bv.Void, bv.Nullable)):
                raise bv.ValidationError(
                    "expected object for '%s', got symbol" % tag)
            if tag == data_type.definition._catch_all:
                raise bv.ValidationError(
                    "unexpected use of the catch-all tag '%s'" % tag)
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    elif isinstance(obj, dict):
        tag, val = _decode_union_dict(
            data_type, obj, alias_validators, strict, for_msgpack)
    else:
        raise bv.ValidationError("expected string or object, got %s" %
                                 bv.generic_type_name(obj))
    return data_type.definition(tag, val)


def _decode_union_dict(data_type, obj, alias_validators, strict, for_msgpack):
    if '.tag' not in obj:
        raise bv.ValidationError("missing '.tag' key")
    tag = obj['.tag']
    if not isinstance(tag, six.string_types):
        raise bv.ValidationError(
            'tag must be string, got %s' % bv.generic_type_name(tag))

    if tag not in data_type.definition._tagmap:
        if not strict and data_type.definition._catch_all:
            return data_type.definition._catch_all, None
        else:
            raise bv.ValidationError("unknown tag '%s'" % tag)
    if tag == data_type.definition._catch_all:
        raise bv.ValidationError(
            "unexpected use of the catch-all tag '%s'" % tag)

    val_data_type = data_type.definition._tagmap[tag]
    if isinstance(val_data_type, bv.Nullable):
        val_data_type = val_data_type.validator
        nullable = True
    else:
        nullable = False

    if isinstance(val_data_type, bv.Void):
        if tag in obj:
            if obj[tag] is not None:
                raise bv.ValidationError('expected null, got %s' %
                                         bv.generic_type_name(obj[tag]))
        for key in obj:
            if key != tag and key != '.tag':
                raise bv.ValidationError("unexpected key '%s'" % key)
        val = None
    elif isinstance(val_data_type,
                    (bv.Primitive, bv.List, bv.StructTree, bv.Union)):
        if tag in obj:
            raw_val = obj[tag]
            try:
                val = _json_compat_obj_decode_helper(
                    val_data_type, raw_val, alias_validators, strict, False, for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(tag)
                raise
        else:
            # Check no other keys
            if nullable:
                val = None
            else:
                raise bv.ValidationError("missing '%s' key" % tag)
        for key in obj:
            if key != tag and key != '.tag':
                raise bv.ValidationError("unexpected key '%s'" % key)
    elif isinstance(val_data_type, bv.Struct):
        if nullable and len(obj) == 1:  # only has a .tag key
            val = None
        else:
            # assume it's not null
            raw_val = obj
            try:
                val = _json_compat_obj_decode_helper(
                    val_data_type, raw_val, alias_validators, strict, False,
                    for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(tag)
                raise
    else:
        assert False, type(val_data_type)
    return tag, val


def _decode_union_old(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_compat_obj_decode() for argument descriptions.
    """
    val = None
    if isinstance(obj, six.string_types):
        # Union member has no associated value
        tag = obj
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if not isinstance(val_data_type, (bv.Void, bv.Nullable)):
                raise bv.ValidationError(
                    "expected object for '%s', got symbol" % tag)
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    elif isinstance(obj, dict):
        # Union member has value
        if len(obj) != 1:
            raise bv.ValidationError('expected 1 key, got %s' % len(obj))
        tag = list(obj)[0]
        raw_val = obj[tag]
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if isinstance(val_data_type, bv.Nullable) and raw_val is None:
                val = None
            elif isinstance(val_data_type, bv.Void):
                if raw_val is None or not strict:
                    # If raw_val is None, then this is the more verbose
                    # representation of a void union member. If raw_val isn't
                    # None, then maybe the spec has changed, so check if we're
                    # in strict mode.
                    val = None
                else:
                    raise bv.ValidationError('expected null, got %s' %
                                             bv.generic_type_name(raw_val))
            else:
                try:
                    val = _json_compat_obj_decode_helper(
                        val_data_type, raw_val, alias_validators, strict, True,
                        for_msgpack)
                except bv.ValidationError as e:
                    e.add_parent(tag)
                    raise
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    else:
        raise bv.ValidationError("expected string or object, got %s" %
                                 bv.generic_type_name(obj))
    return data_type.definition(tag, val)


def _decode_struct_tree(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a StructTree.
    See json_compat_obj_decode() for argument descriptions.
    """
    subtype = _determine_struct_tree_subtype(data_type, obj, strict)
    return _decode_struct(
        subtype, obj, alias_validators, strict, False, for_msgpack)


def _determine_struct_tree_subtype(data_type, obj, strict):
    """
    Searches through the JSON-object-compatible dict using the data type
    definition to determine which of the enumerated subtypes `obj` is.
    """
    if '.tag' not in obj:
        raise bv.ValidationError("missing '.tag' key")
    if not isinstance(obj['.tag'], six.string_types):
        raise bv.ValidationError('expected string, got %s' %
                                 bv.generic_type_name(obj['.tag']),
                                 parent='.tag')

    # Find the subtype the tags refer to
    full_tags_tuple = (obj['.tag'],)
    if full_tags_tuple in data_type.definition._tag_to_subtype_:
        subtype = data_type.definition._tag_to_subtype_[full_tags_tuple]
        if isinstance(subtype, bv.StructTree):
            raise bv.ValidationError("tag '%s' refers to non-leaf subtype" %
                                     ('.'.join(full_tags_tuple)))
        return subtype
    else:
        if strict:
            # In strict mode, the entirety of the tag hierarchy should
            # point to a known subtype.
            raise bv.ValidationError("unknown subtype '%s'" %
                                     '.'.join(full_tags_tuple))
        else:
            # If subtype was not found, use the base.
            if data_type.definition._is_catch_all_:
                return data_type
            else:
                raise bv.ValidationError(
                    "unknown subtype '%s' and '%s' is not a catch-all" %
                    ('.'.join(full_tags_tuple), data_type.definition.__name__))


def _decode_list(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a List.
    See json_compat_obj_decode() for argument descriptions.
    """
    if not isinstance(obj, list):
        raise bv.ValidationError(
            'expected list, got %s' % bv.generic_type_name(obj))
    return [
        _json_compat_obj_decode_helper(
            data_type.item_validator, item, alias_validators, strict,
            old_style, for_msgpack)
        for item in obj]


def _decode_nullable(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a Nullable.
    See json_compat_obj_decode() for argument descriptions.
    """
    if obj is not None:
        return _json_compat_obj_decode_helper(
            data_type.validator, obj, alias_validators, strict, old_style,
            for_msgpack)
    else:
        return None


def _make_babel_friendly(
        data_type, val, alias_validators, strict, validate, for_msgpack):
    """
    Convert a Python object to a type that will pass validation by its
    validator.

    Validation by ``alias_validators`` is performed even if ``validate`` is
    false.
    """
    if isinstance(data_type, bv.Timestamp):
        try:
            ret = datetime.datetime.strptime(val, data_type.format)
        except ValueError as e:
            raise bv.ValidationError(e.args[0])
    elif isinstance(data_type, bv.Bytes):
        if for_msgpack:
            if isinstance(val, six.text_type):
                ret = val.encode('utf-8')
            else:
                ret = val
        else:
            try:
                ret = base64.b64decode(val)
            except TypeError:
                raise bv.ValidationError('invalid base64-encoded bytes')
    elif isinstance(data_type, bv.Void):
        if strict and val is not None:
            raise bv.ValidationError("expected null, got value")
        return None
    else:
        if validate:
            data_type.validate(val)
        ret = val
    if alias_validators is not None and data_type in alias_validators:
        alias_validators[data_type](ret)
    return ret

try:
    import msgpack
except ImportError:
    pass
else:
    msgpack_compat_obj_encode = functools.partial(json_compat_obj_encode,
                                                  for_msgpack=True)

    def msgpack_encode(data_type, obj):
        return msgpack.dumps(
            msgpack_compat_obj_encode(data_type, obj), encoding='utf-8')

    msgpack_compat_obj_decode = functools.partial(json_compat_obj_decode,
                                                  for_msgpack=True)

    def msgpack_decode(
            data_type, serialized_obj, alias_validators=None, strict=True):
        # We decode everything as utf-8 because we want all object keys to be
        # unicode. Otherwise, we need to do a lot more refactoring to make
        # json/msgpack share the same code. We expect byte arrays to fail
        # decoding, but when they don't, we have to convert them to bytes.
        deserialized_obj = msgpack.loads(
            serialized_obj, encoding='utf-8', unicode_errors='ignore')
        return msgpack_compat_obj_decode(
            data_type, deserialized_obj, alias_validators, strict)
