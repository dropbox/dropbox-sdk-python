# Auto-generated by Stone, do not modify.
# @generated
# flake8: noqa
# pylint: skip-file
from stone.backends.python_rsrc import stone_base as bb
from stone.backends.python_rsrc import stone_validators as bv

class EchoArg(bb.Struct):
    """
    Contains the arguments to be sent to the Dropbox servers.

    :ivar check.EchoArg.query: The string that you'd like to be echoed back to
        you.
    """

    __slots__ = [
        '_query_value',
    ]

    _has_required_fields = False

    def __init__(self,
                 query=None):
        self._query_value = bb.NOT_SET
        if query is not None:
            self.query = query

    # Instance attribute type: str (validator is set below)
    query = bb.Attribute("query")

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super()._process_custom_annotations(annotation_type, field_path, processor)

EchoArg_validator = bv.Struct(EchoArg)

class EchoResult(bb.Struct):
    """
    EchoResult contains the result returned from the Dropbox servers.

    :ivar check.EchoResult.result: If everything worked correctly, this would be
        the same as query.
    """

    __slots__ = [
        '_result_value',
    ]

    _has_required_fields = False

    def __init__(self,
                 result=None):
        self._result_value = bb.NOT_SET
        if result is not None:
            self.result = result

    # Instance attribute type: str (validator is set below)
    result = bb.Attribute("result")

    def _process_custom_annotations(self, annotation_type, field_path, processor):
        super()._process_custom_annotations(annotation_type, field_path, processor)

EchoResult_validator = bv.Struct(EchoResult)

EchoArg.query.validator = bv.String(max_length=500)
EchoArg._all_field_names_ = {'query'}
EchoArg._all_fields_ = [('query', EchoArg.query.validator)]

EchoResult.result.validator = bv.String()
EchoResult._all_field_names_ = {'result'}
EchoResult._all_fields_ = [('result', EchoResult.result.validator)]

EchoArg.query.default = ''
EchoResult.result.default = ''
app = bb.Route(
    'app',
    1,
    False,
    EchoArg_validator,
    EchoResult_validator,
    bv.Void(),
    {'auth': 'app',
     'host': 'api',
     'style': 'rpc'},
)
user = bb.Route(
    'user',
    1,
    False,
    EchoArg_validator,
    EchoResult_validator,
    bv.Void(),
    {'auth': 'user',
     'host': 'api',
     'style': 'rpc'},
)

ROUTES = {
    'app': app,
    'user': user,
}

