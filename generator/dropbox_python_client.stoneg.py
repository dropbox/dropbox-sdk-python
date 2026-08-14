from stone.backends import python_client
from stone.backends.helpers import fmt_underscores
from stone.backends.python_helpers import fmt_func
from stone.ir import (
    is_nullable_type,
    is_struct_type,
    is_union_type,
    is_user_defined_type,
    is_void_type,
)


class DropboxPythonClientBackend(python_client.PythonClientBackend):
    """Generate Dropbox-specific Python client methods."""

    def generate(self, api):
        """Generates a module called "base"."""

        with self.output_to_relative_path("%s.py" % self.args.module_name):
            self.emit_raw(python_client.base)
            found_deprecated = False
            for namespace in api.namespaces.values():
                for route in namespace.routes:
                    if route.deprecated:
                        self.emit("import warnings")
                        found_deprecated = True
                        break
                if found_deprecated:
                    break
            self.emit()
            self._generate_imports(api.namespaces.values())
            self.emit()
            self.emit()
            self.emit("class %s(object):" % self.args.class_name)
            with self.indent():
                self.emit("__metaclass__ = ABCMeta")
                self.emit()
                self.emit("@abstractmethod")
                self.emit(
                    "def request(self, route, namespace, request_arg, "
                    "request_binary, timeout=None, extra_headers=None):"
                )
                with self.indent():
                    self.emit("pass")
                self.emit()
                self._generate_route_methods(api.namespaces.values())

    @staticmethod
    def _supports_extra_headers(namespace, route):
        return namespace.name == "files" and route.name == "download"

    def _generate_route_method_decl(
        self,
        namespace,
        route,
        arg_data_type,
        request_binary_body,
        method_name_suffix="",
        extra_args=None,
    ):
        if not self._supports_extra_headers(namespace, route):
            return super()._generate_route_method_decl(
                namespace,
                route,
                arg_data_type,
                request_binary_body,
                method_name_suffix=method_name_suffix,
                extra_args=extra_args,
            )

        args = ["self"]

        if extra_args:
            args += extra_args

        if request_binary_body:
            args.append("f")

        if is_struct_type(arg_data_type):
            for field in arg_data_type.all_fields:
                if is_nullable_type(field.data_type):
                    args.append("{}=None".format(field.name))
                elif field.has_default:
                    if is_user_defined_type(field.data_type):
                        ns = field.data_type.namespace
                    else:
                        ns = None

                    args.append(
                        "{}={}".format(
                            field.name,
                            self._generate_python_value(ns, field.default),
                        )
                    )
                else:
                    args.append(field.name)
        elif is_union_type(arg_data_type):
            args.append("arg")
        elif not is_void_type(arg_data_type):
            raise AssertionError("Unhandled request type: %r" % arg_data_type)

        args.append("extra_headers=None")

        method_name = fmt_func(
            route.name + method_name_suffix,
            version=route.version,
        )
        namespace_name = fmt_underscores(namespace.name)

        self.generate_multiline_list(
            args,
            "def {}_{}".format(namespace_name, method_name),
            ":",
        )

    def _generate_route_helper(self, namespace, route, download_to_file=False):
        if not self._supports_extra_headers(namespace, route):
            return super()._generate_route_helper(
                namespace,
                route,
                download_to_file=download_to_file,
            )

        arg_data_type = route.arg_data_type
        result_data_type = route.result_data_type
        response_binary_body = route.attrs.get("style") == "download"

        if download_to_file:
            assert response_binary_body
            self._generate_route_method_decl(
                namespace,
                route,
                arg_data_type,
                False,
                method_name_suffix="_to_file",
                extra_args=["download_path"],
            )
        else:
            self._generate_route_method_decl(
                namespace,
                route,
                arg_data_type,
                False,
            )

        with self.indent():
            extra_request_args = []
            if download_to_file:
                extra_request_args.append(
                    (
                        "download_path",
                        "str",
                        "Path on local machine to save file.",
                    )
                )

            extra_request_args.append(
                (
                    "extra_headers",
                    "object",
                    "Additional HTTP headers for this request.",
                )
            )

            if route.doc:
                func_docstring = self.process_doc(route.doc, self._docf)
            else:
                func_docstring = None

            self._generate_docstring_for_func(
                namespace,
                arg_data_type,
                result_data_type,
                route.error_data_type,
                overview=func_docstring,
                extra_request_args=extra_request_args,
                extra_return_arg=(
                    None if download_to_file else ":class:`requests.models.Response`"
                ),
                footer=(None if download_to_file else python_client.DOCSTRING_CLOSE_RESPONSE),
                attrs=route.attrs,
            )

            self._maybe_generate_deprecation_warning(route)
            self.generate_multiline_list(
                [field.name for field in arg_data_type.all_fields],
                before="arg = {}.{}".format(
                    python_client.fmt_namespace(arg_data_type.namespace.name),
                    python_client.fmt_class(arg_data_type.name),
                ),
            )

            args = [
                "{}.{}".format(
                    python_client.fmt_namespace(namespace.name),
                    python_client.fmt_func(
                        route.name,
                        version=route.version,
                    ),
                ),
                "'{}'".format(namespace.name),
                "arg",
                "None",
            ]

            self.emit("if extra_headers is None:")
            with self.indent():
                self.generate_multiline_list(
                    args,
                    "r = self.request",
                    compact=False,
                )
            self.emit("else:")
            with self.indent():
                self.generate_multiline_list(
                    args + ["extra_headers=extra_headers"],
                    "r = self.request",
                    compact=False,
                )

            if download_to_file:
                self.emit("self._save_body_to_file(download_path, r[1])")
                self.emit("return r[0]")
            else:
                self.emit("return r")

        self.emit()
