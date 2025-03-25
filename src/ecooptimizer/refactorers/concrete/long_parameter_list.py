import libcst as cst
import libcst.matchers as m
from libcst.metadata import PositionProvider, MetadataWrapper, ParentNodeProvider
from pathlib import Path
from typing import Optional
from collections.abc import Mapping

from ..multi_file_refactorer import MultiFileRefactorer
from ...data_types.smell import LPLSmell


class FunctionCallVisitor(cst.CSTVisitor):
    def __init__(self, function_name: str, class_name: str, is_constructor: bool):
        self.function_name = function_name
        self.is_constructor = is_constructor  # whether or not given function call is a constructor
        self.class_name = (
            class_name  # name of class being instantiated if function is a constructor
        )
        self.found = False

    def visit_Call(self, node: cst.Call):
        """Check if the function/class constructor is called."""
        # handle class constructor call
        if self.is_constructor and m.matches(node.func, m.Name(self.class_name)):  # type: ignore
            self.found = True

        # handle standalone function calls
        elif m.matches(node.func, m.Name(self.function_name)):
            self.found = True

        # handle method calss
        elif m.matches(node.func, m.Attribute(attr=m.Name(self.function_name))):
            self.found = True


class ParameterAnalyzer:
    @staticmethod
    def get_used_parameters(function_node: cst.FunctionDef, params: list[str]) -> list[str]:
        """
        Identifies parameters that actually are used within the function/method body using CST analysis
        """

        # visitor class to collect variable names used in the function body
        class UsedParamVisitor(cst.CSTVisitor):
            def __init__(self):
                self.used_names = set()

            def visit_Name(self, node: cst.Name) -> None:
                self.used_names.add(node.value)

        # traverse the function body to collect used variable names
        visitor = UsedParamVisitor()
        function_node.body.visit(visitor)

        return [name for name in params if name in visitor.used_names]

    @staticmethod
    def get_parameters_with_default_value(params: list[cst.Param]) -> dict[str, cst.Arg]:
        """
        Given a list of function parameters and their default values, maps parameter names to their default values
        """
        param_defaults = {}

        for param in params:
            if param.default is not None:  # check if the parameter has a default value
                param_defaults[param.name.value] = param.default

        return param_defaults

    @staticmethod
    def classify_parameters(params: list[str]) -> dict[str, list[str]]:
        """
        Classifies parameters into 'data' and 'config' groups based on naming conventions
        """
        data_params, config_params = [], []
        data_keywords = {"data", "input", "output", "result", "record", "item"}
        config_keywords = {"config", "setting", "option", "env", "parameter", "path"}

        for param in params:
            param_lower = param.lower()
            if any(keyword in param_lower for keyword in data_keywords):
                data_params.append(param)
            elif any(keyword in param_lower for keyword in config_keywords):
                config_params.append(param)
            else:
                data_params.append(param)
        return {"data_params": data_params, "config_params": config_params}


class ParameterEncapsulator:
    @staticmethod
    def encapsulate_parameters(
        classified_params: dict[str, list[str]],
        default_value_params: dict[str, cst.Arg],
        classified_param_names: tuple[str, str],
    ) -> list[cst.ClassDef]:
        """
        Generates CST class definitions for encapsulating parameter objects.
        """
        data_params, config_params = (
            classified_params["data_params"],
            classified_params["config_params"],
        )
        class_nodes = []

        data_class_name, config_class_name = classified_param_names

        if data_params:
            data_param_class = ParameterEncapsulator.create_parameter_object_class(
                data_params, default_value_params, data_class_name
            )
            class_nodes.append(data_param_class)

        if config_params:
            config_param_class = ParameterEncapsulator.create_parameter_object_class(
                config_params, default_value_params, config_class_name
            )
            class_nodes.append(config_param_class)

        return class_nodes

    @staticmethod
    def create_parameter_object_class(
        param_names: list[str],
        default_value_params: dict[str, cst.Arg],
        class_name: str = "ParamsObject",
    ) -> cst.ClassDef:
        """
        Creates a CST class definition for encapsulating related parameters.
        """
        # create constructor parameters
        constructor_params = [cst.Param(name=cst.Name("self"))]
        assignments = []

        for param in param_names:
            default_value = default_value_params.get(param, None)

            param_cst = cst.Param(
                name=cst.Name(param),
                default=default_value,  # set default value if available # type: ignore
            )
            constructor_params.append(param_cst)

            assignment = cst.SimpleStatementLine(
                [
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                cst.Attribute(value=cst.Name("self"), attr=cst.Name(param))
                            )
                        ],
                        value=cst.Name(param),
                    )
                ]
            )
            assignments.append(assignment)

        constructor = cst.FunctionDef(
            name=cst.Name("__init__"),
            params=cst.Parameters(params=constructor_params),
            body=cst.IndentedBlock(body=assignments),
        )

        # create class definition
        return cst.ClassDef(
            name=cst.Name(class_name),
            body=cst.IndentedBlock(body=[constructor]),
        )


class FunctionCallUpdater:
    @staticmethod
    def get_method_type(func_node: cst.FunctionDef) -> str:
        """
        Determines whether a function is an instance method, class method, or static method
        """
        # check for @staticmethod or @classmethod decorators
        for decorator in func_node.decorators:
            if isinstance(decorator.decorator, cst.Name):
                if decorator.decorator.value == "staticmethod":
                    return "static method"
                if decorator.decorator.value == "classmethod":
                    return "class method"

        # check the first parameter name
        if func_node.params.params:
            first_param = func_node.params.params[0].name.value
            if first_param == "self":
                return "instance method"
            if first_param == "cls":
                return "class method"

        return "unknown method type"

    @staticmethod
    def remove_unused_params(
        function_node: cst.FunctionDef,
        used_params: list[str],
        default_value_params: dict[str, cst.Arg],
    ) -> cst.FunctionDef:
        """
        Removes unused parameters from the function signature while preserving self/cls if applicable.
        Ensures there is no trailing comma when removing the last parameter.
        """
        method_type = FunctionCallUpdater.get_method_type(function_node)

        updated_params = []
        updated_defaults = []

        # preserve self/cls if it's an instance or class method
        if function_node.params.params and method_type in {"instance method", "class method"}:
            updated_params.append(function_node.params.params[0])

        # remove unused parameters, keeping only those that are used
        for param in function_node.params.params:
            if param.name.value in used_params:
                updated_params.append(param)
                if param.name.value in default_value_params:
                    updated_defaults.append(default_value_params[param.name.value])

        # ensure that the last parameter does not leave a trailing comma
        updated_params = [p.with_changes(comma=cst.MaybeSentinel.DEFAULT) for p in updated_params]

        return function_node.with_changes(
            params=function_node.params.with_changes(params=updated_params)
        )

    @staticmethod
    def update_function_signature(
        function_node: cst.FunctionDef, classified_params: dict[str, list[str]]
    ) -> cst.FunctionDef:
        """
        Updates the function signature to use encapsulated parameter objects
        """
        data_params, config_params = (
            classified_params["data_params"],
            classified_params["config_params"],
        )

        method_type = FunctionCallUpdater.get_method_type(function_node)
        new_params = []

        # preserve self/cls if it's a method
        if function_node.params.params and method_type in {"instance method", "class method"}:
            new_params.append(function_node.params.params[0])

        # add encapsulated objects as new parameters
        if data_params:
            new_params.append(cst.Param(name=cst.Name("data_params")))
        if config_params:
            new_params.append(cst.Param(name=cst.Name("config_params")))

        return function_node.with_changes(
            params=function_node.params.with_changes(params=new_params)
        )

    @staticmethod
    def update_parameter_usages(
        function_node: cst.FunctionDef, classified_params: dict[str, list[str]]
    ):
        """
        Updates the function body to use encapsulated parameter objects.
        This method transforms parameter references in the function body to use new data_params
        and config_params objects.

        Args:
            function_node: CST node of the function to transform
            classified_params: Dictionary mapping parameter groups ('data_params' or 'config_params')
                            to lists of parameter names in each group

        Returns:
            The transformed function node with updated parameter usages
        """
        # Create a module with just the function to get metadata
        module = cst.Module(body=[function_node])
        wrapper = MetadataWrapper(module)

        class ParameterUsageTransformer(cst.CSTTransformer):
            """
            A CST transformer that updates parameter references to use the new parameter objects.
            """

            METADATA_DEPENDENCIES = (ParentNodeProvider,)

            def __init__(
                self, classified_params: dict[str, list[str]], metadata_wrapper: MetadataWrapper
            ):
                super().__init__()
                # map each parameter to its group (data_params or config_params)
                self.param_to_group = {}
                self.parent_provider = metadata_wrapper.resolve(ParentNodeProvider)
                # flatten classified_params to map each param to its group (dataParams or configParams)
                for group, params in classified_params.items():
                    for param in params:
                        self.param_to_group[param] = group

            def is_in_assignment_target(self, node: cst.CSTNode) -> bool:
                """
                Check if a node is part of an assignment target (left side of =).

                Args:
                    node: The CST node to check

                Returns:
                    True if the node is part of an assignment target that should not be transformed,
                    False otherwise
                """
                current = node
                while current:
                    parent = self.parent_provider.get(current)

                    # if we're at an AssignTarget, check if it's a simple Name assignment
                    if isinstance(parent, cst.AssignTarget):
                        if isinstance(current, cst.Name):
                            # allow transformation for simple parameter assignments
                            return False
                        return True

                    if isinstance(parent, cst.Assign):
                        # if we reach an Assign node, check if we came from the targets
                        for target in parent.targets:
                            if target.target.deep_equals(current):
                                if isinstance(current, cst.Name):
                                    # allow transformation for simple parameter assignments
                                    return False
                                return True
                        return False

                    if isinstance(parent, cst.Module):
                        return False

                    current = parent
                return False

            def leave_Name(
                self, original_node: cst.Name, updated_node: cst.Name
            ) -> cst.BaseExpression:
                """
                Transform standalone parameter references.

                Skip transformation if:
                1. The name is part of an attribute access (eg: self.param)
                2. The name is part of a complex assignment target (eg: self.x = y)

                Transform if:
                1. The name is a simple parameter being assigned (eg: param1 = value)
                2. The name is used as a value (eg: x = param1)

                Args:
                    original_node: The original Name node
                    updated_node: The current state of the Name node

                Returns:
                    The transformed node or the original if no transformation is needed
                """
                # dont't transform if this is part of a complex assignment target
                if self.is_in_assignment_target(original_node):
                    return updated_node

                # dont't transform if this is part of an attribute access (e.g., self.param)
                parent = self.parent_provider.get(original_node)
                if isinstance(parent, cst.Attribute) and original_node is parent.attr:
                    return updated_node

                name_value = updated_node.value
                if name_value in self.param_to_group:
                    # transform the name into an attribute access on the appropriate parameter object
                    return cst.Attribute(
                        value=cst.Name(self.param_to_group[name_value]), attr=cst.Name(name_value)
                    )
                return updated_node

            def leave_Attribute(
                self, original_node: cst.Attribute, updated_node: cst.Attribute
            ) -> cst.BaseExpression:
                """
                Handle method calls and attribute access on parameters.
                This method handles several cases:

                1. Assignment targets (eg: self.x = y)
                2. Simple attribute access (eg: self.x or report.x)
                3. Nested attribute access (eg: data_params.user_id)
                4. Subscript access (eg: self.settings["timezone"])
                5. Parameter attribute access (eg: username.strip())

                Args:
                    original_node: The original Attribute node
                    updated_node: The current state of the Attribute node

                Returns:
                    The transformed node or the original if no transformation is needed
                """
                # don't transform if this is part of an assignment target
                if self.is_in_assignment_target(original_node):
                    # if this is a simple attribute access (eg: self.x or report.x), don't transform it
                    if isinstance(updated_node.value, cst.Name) and updated_node.value.value in {
                        "self",
                        "report",
                    }:
                        return original_node
                    return updated_node

                # if this is a nested attribute access (eg: data_params.user_id), don't transform it further
                if (
                    isinstance(updated_node.value, cst.Attribute)
                    and isinstance(updated_node.value.value, cst.Name)
                    and updated_node.value.value.value in {"data_params", "config_params"}
                ):
                    return updated_node

                # if this is a simple attribute access (eg: self.x or report.x), don't transform it
                if isinstance(updated_node.value, cst.Name) and updated_node.value.value in {
                    "self",
                    "report",
                }:
                    # check if this is part of a subscript target (eg: self.settings["timezone"])
                    parent = self.parent_provider.get(original_node)
                    if isinstance(parent, cst.Subscript):
                        return original_node
                    # check if this is part of a subscript value
                    if isinstance(parent, cst.SubscriptElement):
                        return original_node
                    return original_node

                # if the attribute's value is a parameter name, update it to use the encapsulated parameter object
                if (
                    isinstance(updated_node.value, cst.Name)
                    and updated_node.value.value in self.param_to_group
                ):
                    param_name = updated_node.value.value
                    return cst.Attribute(
                        value=cst.Name(self.param_to_group[param_name]), attr=updated_node.attr
                    )

                return updated_node

        # create transformer with metadata wrapper
        transformer = ParameterUsageTransformer(classified_params, wrapper)
        # transform the function body
        updated_module = module.visit(transformer)
        # return the transformed function
        return updated_module.body[0]

    @staticmethod
    def get_enclosing_class_name(
        init_node: cst.FunctionDef,
        parent_metadata: Mapping[cst.CSTNode, cst.CSTNode],
    ) -> Optional[str]:
        """
        Finds the class name enclosing the given __init__ function node.
        """
        current_node = init_node
        while current_node in parent_metadata:
            parent = parent_metadata[current_node]
            if isinstance(parent, cst.ClassDef):
                return parent.name.value
            current_node = parent
        return None

    @staticmethod
    def update_function_calls(
        tree: cst.Module,
        function_node: cst.FunctionDef,
        used_params: list[str],
        classified_params: dict[str, list[str]],
        classified_param_names: tuple[str, str],
        enclosing_class_name: str,
    ) -> cst.Module:
        param_to_group = {}
        for group_name, params in zip(classified_param_names, classified_params.values()):
            for param in params:
                param_to_group[param] = group_name

        function_name = function_node.name.value
        if function_name == "__init__":
            function_name = enclosing_class_name

        # Get all parameter names from the function definition
        all_param_names = [p.name.value for p in function_node.params.params]
        # Find where variadic args start (if any)
        variadic_start = len(all_param_names)
        for i, param in enumerate(function_node.params.params):
            if param.star == "*" or param.star == "**":
                variadic_start = i
                break

        class FunctionCallTransformer(cst.CSTTransformer):
            def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:  # noqa: ARG002
                """Transforms function calls to use grouped parameters."""
                # Handle both standalone function calls and instance method calls
                if not isinstance(updated_node.func, (cst.Name, cst.Attribute)):
                    return updated_node  # Ignore other calls that are not functions/methods

                # Extract the function/method name
                func_name = (
                    updated_node.func.attr.value
                    if isinstance(updated_node.func, cst.Attribute)
                    else updated_node.func.value
                )

                # If the function/method being called is not the one we're refactoring, skip it
                if func_name != function_name:
                    return updated_node

                positional_args = []
                keyword_args = {}
                variadic_args = []
                variadic_kwargs = {}

                # Separate positional, keyword, and variadic arguments
                for i, arg in enumerate(updated_node.args):
                    if isinstance(arg, cst.Arg):  # type: ignore
                        if arg.keyword is None:
                            # If this is a positional argument beyond the number of parameters,
                            # it's a variadic arg
                            if i >= variadic_start:
                                variadic_args.append(arg.value)
                            elif i < len(used_params):
                                positional_args.append(arg.value)
                        else:
                            # If this is a keyword argument for a used parameter, keep it
                            if arg.keyword.value in param_to_group:
                                keyword_args[arg.keyword.value] = arg.value
                            # If this is a keyword argument not in the original parameters,
                            # it's a variadic kwarg
                            elif arg.keyword.value not in all_param_names:
                                variadic_kwargs[arg.keyword.value] = arg.value

                # Group arguments based on classified_params
                grouped_args = {group: [] for group in classified_param_names}

                # Process positional arguments
                param_index = 0
                for param in used_params:
                    if param_index < len(positional_args):
                        grouped_args[param_to_group[param]].append(
                            cst.Arg(value=positional_args[param_index])
                        )
                        param_index += 1

                # Process keyword arguments
                for kw, value in keyword_args.items():
                    if kw in param_to_group:
                        grouped_args[param_to_group[kw]].append(
                            cst.Arg(value=value, keyword=cst.Name(kw))
                        )

                # Construct new grouped arguments
                new_args = [
                    cst.Arg(
                        value=cst.Call(func=cst.Name(group_name), args=grouped_args[group_name])
                    )
                    for group_name in classified_param_names
                    if grouped_args[group_name]  # Skip empty groups
                ]

                # Add variadic positional arguments
                new_args.extend([cst.Arg(value=arg) for arg in variadic_args])

                # Add variadic keyword arguments
                new_args.extend(
                    [
                        cst.Arg(keyword=cst.Name(key), value=value)
                        for key, value in variadic_kwargs.items()
                    ]
                )

                return updated_node.with_changes(args=new_args)

        transformer = FunctionCallTransformer()
        return tree.visit(transformer)

    @staticmethod
    def update_function_calls_unclassified(
        tree: cst.Module,
        function_node: cst.FunctionDef,
        used_params: list[str],
        enclosing_class_name: str,
    ) -> cst.Module:
        """
        Updates all calls to a given function to only include used parameters.
        This is used when parameters are removed without being classified into objects.

        Args:
            tree: CST tree of the code
            function_node: CST node of the function to update calls for
            used_params: List of parameter names that are actually used in the function
            enclosing_class_name: Name of the enclosing class if this is a method

        Returns:
            Updated CST tree with modified function calls
        """
        function_name = function_node.name.value
        if function_name == "__init__":
            function_name = enclosing_class_name

        class FunctionCallTransformer(cst.CSTTransformer):
            def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:  # noqa: ARG002
                """Transforms function calls to only include used parameters."""
                # handle both standalone function calls and instance method calls
                if not isinstance(updated_node.func, (cst.Name, cst.Attribute)):
                    return updated_node

                # extract the function/method name
                func_name = (
                    updated_node.func.attr.value
                    if isinstance(updated_node.func, cst.Attribute)
                    else updated_node.func.value
                )

                # if not the target function, leave unchanged
                if func_name != function_name:
                    return updated_node

                # map original parameters to their positions
                param_positions = {
                    param.name.value: i for i, param in enumerate(function_node.params.params)
                }

                # keep track of which positions in the argument list correspond to used parameters
                used_positions = {i for param, i in param_positions.items() if param in used_params}

                new_args = []
                pos_arg_count = 0

                # process all arguments
                for arg in updated_node.args:
                    if arg.keyword is None:
                        # handle positional arguments
                        if pos_arg_count in used_positions:
                            new_args.append(arg)
                        pos_arg_count += 1
                    else:
                        # handle keyword arguments
                        if arg.keyword.value in used_params:
                            # keep keyword arguments for used parameters
                            new_args.append(arg)

                # ensure the last argument does not have a trailing comma
                if new_args:
                    final_args = new_args[:-1]
                    final_args.append(new_args[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT))
                    new_args = final_args

                return updated_node.with_changes(args=new_args)

        transformer = FunctionCallTransformer()
        return tree.visit(transformer)


class ClassInserter(cst.CSTTransformer):
    def __init__(self, class_nodes: list[cst.ClassDef]):
        self.class_nodes = class_nodes
        self.insert_index = None

    def visit_Module(self, node: cst.Module) -> None:
        """
        Identify the first function definition in the module.
        """
        for i, statement in enumerate(node.body):
            if isinstance(statement, cst.FunctionDef):
                self.insert_index = i
                break

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:  # noqa: ARG002
        """
        Insert the generated class definitions before the first function definition.
        """
        if self.insert_index is None:
            # if no function is found, append the class nodes at the beginning
            new_body = list(self.class_nodes) + list(updated_node.body)
        else:
            # insert class nodes before the first function
            new_body = (
                list(updated_node.body[: self.insert_index])
                + list(self.class_nodes)
                + list(updated_node.body[self.insert_index :])
            )

        return updated_node.with_changes(body=new_body)


class FunctionFinder(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, position_metadata, target_line):  # noqa: ANN001
        self.position_metadata = position_metadata
        self.target_line = target_line
        self.function_node = None

    def visit_FunctionDef(self, node: cst.FunctionDef):
        """Check if the function's starting line matches the target."""
        pos = self.position_metadata.get(node)
        if pos and pos.start.line == self.target_line:
            self.function_node = node  # Store the function node


class LongParameterListRefactorer(MultiFileRefactorer[LPLSmell]):
    def __init__(self):
        super().__init__()
        self.parameter_analyzer = ParameterAnalyzer()
        self.parameter_encapsulator = ParameterEncapsulator()
        self.function_updater = FunctionCallUpdater()
        self.function_node: Optional[cst.FunctionDef] = (
            None  # AST node of definition of function that needs to be refactored
        )
        self.used_params: None  # list of unclassified used params
        self.classified_params = None
        self.classified_param_names = None
        self.classified_param_nodes = []
        self.enclosing_class_name: Optional[str] = None
        self.is_constructor = False

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: LPLSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactors function/method with more than 6 parameters by encapsulating those with related names and removing those that are unused
        """
        # maximum limit on number of parameters beyond which the code smell is configured to be detected(see analyzers_config.py)
        max_param_limit = 6
        self.target_file = target_file

        with target_file.open() as f:
            source_code = f.read()

        tree = cst.parse_module(source_code)
        wrapper = MetadataWrapper(tree)
        position_metadata = wrapper.resolve(PositionProvider)
        parent_metadata = wrapper.resolve(ParentNodeProvider)
        target_line = smell.occurences[0].line

        visitor = FunctionFinder(position_metadata, target_line)
        wrapper.visit(visitor)  # Traverses the CST tree

        if visitor.function_node:
            self.function_node = visitor.function_node

            self.is_constructor = self.function_node.name.value == "__init__"
            if self.is_constructor:
                self.enclosing_class_name = FunctionCallUpdater.get_enclosing_class_name(
                    self.function_node, parent_metadata
                )
            param_names = [
                param.name.value
                for param in self.function_node.params.params
                if param.name.value != "self"
            ]
            param_nodes = [
                param for param in self.function_node.params.params if param.name.value != "self"
            ]
            # params that have default value assigned in function definition, stored as a dict of param name to default value
            default_value_params = self.parameter_analyzer.get_parameters_with_default_value(
                param_nodes
            )

            if len(param_nodes) > max_param_limit:
                # need to identify used parameters so unused ones can be removed
                self.used_params = self.parameter_analyzer.get_used_parameters(
                    self.function_node, param_names
                )

                if len(self.used_params) > max_param_limit:  # type: ignore
                    # classify used params into data and config types and store the results in a dictionary, if number of used params is beyond the configured limit
                    self.classified_params = self.parameter_analyzer.classify_parameters(
                        self.used_params  # type: ignore
                    )
                    self.classified_param_names = self._generate_unique_param_class_names(
                        target_line
                    )
                    # add class defitions for data and config encapsulations to the tree
                    self.classified_param_nodes = (
                        self.parameter_encapsulator.encapsulate_parameters(
                            self.classified_params,
                            default_value_params,
                            self.classified_param_names,
                        )
                    )

                    # insert class definitions and update function calls
                    tree = tree.visit(ClassInserter(self.classified_param_nodes))
                    # update calls to the function
                    tree = self.function_updater.update_function_calls(
                        tree,
                        self.function_node,
                        self.used_params,  # type: ignore
                        self.classified_params,
                        self.classified_param_names,
                        self.enclosing_class_name,  # type: ignore
                    )
                    # next updaate function signature and parameter usages within function body
                    updated_function_node = self.function_updater.update_function_signature(
                        self.function_node, self.classified_params
                    )
                    updated_function_node = self.function_updater.update_parameter_usages(
                        updated_function_node, self.classified_params
                    )

                else:
                    # just remove the unused params if the used parameters are within the max param list
                    updated_function_node = self.function_updater.remove_unused_params(
                        self.function_node,
                        self.used_params,  # type: ignore
                        default_value_params,  # type: ignore
                    )

                    # update all calls to match the new signature
                    tree = self.function_updater.update_function_calls_unclassified(
                        tree,
                        self.function_node,
                        self.used_params,  # type: ignore
                        self.enclosing_class_name,  # type: ignore
                    )

                class FunctionReplacer(cst.CSTTransformer):
                    def __init__(
                        self, original_function: cst.FunctionDef, updated_function: cst.FunctionDef
                    ):
                        self.original_function = original_function
                        self.updated_function = updated_function

                    def leave_FunctionDef(
                        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
                    ) -> cst.FunctionDef:
                        """Replace the original function definition with the updated one."""
                        if original_node.deep_equals(self.original_function):
                            return self.updated_function  # replace with the modified function
                        return updated_node  # leave other functions unchanged

                tree = tree.visit(FunctionReplacer(self.function_node, updated_function_node))  # type: ignore

        # Write the modified source
        modified_source = tree.code

        with output_file.open("w") as temp_file:
            temp_file.write(modified_source)

        if overwrite:
            with target_file.open("w") as f:
                f.write(modified_source)

        self.traverse_and_process(source_dir)

    def _generate_unique_param_class_names(self, target_line: int) -> tuple[str, str]:
        """
        Generate unique class names for data params and config params based on function name and line number.
        :return: A tuple containing (DataParams class name, ConfigParams class name).
        """
        unique_suffix = f"{self.function_node.name.value}_{target_line}"  # type: ignore
        data_class_name = f"DataParams_{unique_suffix}"
        config_class_name = f"ConfigParams_{unique_suffix}"
        return data_class_name, config_class_name

    def _process_file(self, file: Path):
        if file.samefile(self.target_file):
            return False

        tree = cst.parse_module(file.read_text())

        visitor = FunctionCallVisitor(
            self.function_node.name.value,  # type: ignore
            self.enclosing_class_name,  # type: ignore
            self.is_constructor,  # type: ignore
        )
        tree.visit(visitor)

        if not visitor.found:
            return False

        # insert class definitions before modifying function calls
        tree = tree.visit(ClassInserter(self.classified_param_nodes))

        # update function calls/class instantiations
        tree = self.function_updater.update_function_calls(
            tree,
            self.function_node,  # type: ignore
            self.used_params,  # type: ignore
            self.classified_params,  # type: ignore
            self.classified_param_names,  # type: ignore
            self.enclosing_class_name,  # type: ignore
        )

        modified_source = tree.code
        with file.open("w") as f:
            f.write(modified_source)

        return True
