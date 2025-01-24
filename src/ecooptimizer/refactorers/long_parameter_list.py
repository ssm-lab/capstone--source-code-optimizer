import ast
import astor
import logging
from pathlib import Path

from ..data_wrappers.smell import LPLSmell
from .base_refactorer import BaseRefactorer


class LongParameterListRefactorer(BaseRefactorer):
    def __init__(self):
        super().__init__()
        self.parameter_analyzer = ParameterAnalyzer()
        self.parameter_encapsulator = ParameterEncapsulator()
        self.function_updater = FunctionCallUpdater()

    def refactor(
        self,
        input_file: Path,
        smell: LPLSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactors function/method with more than 6 parameters by encapsulating those with related names and removing those that are unused
        """
        # maximum limit on number of parameters beyond which the code smell is configured to be detected(see analyzers_config.py)
        max_param_limit = 6

        with input_file.open() as f:
            tree = ast.parse(f.read())

        # find the line number of target function indicated by the code smell object
        target_line = smell["occurences"][0]["line"]
        logging.info(
            f"Applying 'Fix Too Many Parameters' refactor on '{input_file.name}' at line {target_line} for identified code smell."
        )
        # use target_line to find function definition at the specific line for given code smell object
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.lineno == target_line:
                params = [arg.arg for arg in node.args.args if arg.arg != "self"]
                default_value_params = self.parameter_analyzer.get_parameters_with_default_value(
                    node.args.defaults, params
                )  # params that have default value assigned in function definition, stored as a dict of param name to default value

                if (
                    len(params) > max_param_limit
                ):  # max limit beyond which the code smell is configured to be detected
                    # need to identify used parameters so unused ones can be removed
                    used_params = self.parameter_analyzer.get_used_parameters(node, params)
                    if len(used_params) > max_param_limit:
                        # classify used params into data and config types and store the results in a dictionary, if number of used params is beyond the configured limit
                        classified_params = self.parameter_analyzer.classify_parameters(used_params)

                        # add class defitions for data and config encapsulations to the tree
                        class_nodes = self.parameter_encapsulator.encapsulate_parameters(
                            classified_params, default_value_params
                        )
                        for class_node in class_nodes:
                            tree.body.insert(0, class_node)

                        # first update calls to this function(this needs to use existing params)
                        updated_tree = self.function_updater.update_function_calls(
                            tree, node, classified_params
                        )
                        # then update function signature and parameter usages with function body)
                        updated_function = self.function_updater.update_function_signature(
                            node, classified_params
                        )
                        updated_function = self.function_updater.update_parameter_usages(
                            node, classified_params
                        )

                    else:
                        # just remove the unused params if used parameters are within the max param list
                        updated_function = self.function_updater.remove_unused_params(
                            node, used_params, default_value_params
                        )

                    # update the tree by replacing the old function with the updated one
                    for i, body_node in enumerate(tree.body):
                        if body_node == node:
                            tree.body[i] = updated_function
                            break
                    updated_tree = tree

        temp_file_path = output_file

        modified_source = astor.to_source(updated_tree)
        with temp_file_path.open("w") as temp_file:
            temp_file.write(modified_source)

        if overwrite:
            with input_file.open("w") as f:
                f.write(modified_source)


class ParameterAnalyzer:
    @staticmethod
    def get_used_parameters(function_node: ast.FunctionDef, params: list[str]) -> set[str]:
        """
        Identifies parameters that actually are used within the function/method body using AST analysis
        """
        source_code = astor.to_source(function_node)
        tree = ast.parse(source_code)

        used_set = set()

        # visitor class that tracks parameter usage
        class ParamUsageVisitor(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name):
                if isinstance(node.ctx, ast.Load) and node.id in params:
                    used_set.add(node.id)

        ParamUsageVisitor().visit(tree)

        # preserve the order of params by filtering used parameters
        used_params = [param for param in params if param in used_set]
        return used_params

    @staticmethod
    def get_parameters_with_default_value(default_values: list[ast.Constant], params: list[str]):
        """
        Given list of default values for params and params, creates a dictionary mapping param names to default values
        """
        default_params_len = len(default_values)
        params_len = len(params)
        # default params are always defined towards the end of param list, so offest is needed to access param names
        offset = params_len - default_params_len

        defaultsDict = dict()
        for i in range(0, default_params_len):
            defaultsDict[params[offset + i]] = default_values[i].value
        return defaultsDict

    @staticmethod
    def classify_parameters(params: list[str]) -> dict:
        """
        Classifies parameters into 'data' and 'config' groups based on naming conventions
        """
        data_params: list[str] = []
        config_params: list[str] = []

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
        return {"data": data_params, "config": config_params}


class ParameterEncapsulator:
    @staticmethod
    def create_parameter_object_class(
        param_names: list[str], default_value_params: dict, class_name: str = "ParamsObject"
    ) -> str:
        """
        Creates a class definition for encapsulating related parameters
        """
        # class_def = f"class {class_name}:\n"
        # init_method = "    def __init__(self, {}):\n".format(", ".join(param_names))
        # init_body = "".join([f"        self.{param} = {param}\n" for param in param_names])
        # return class_def + init_method + init_body
        class_def = f"class {class_name}:\n"
        init_params = []
        init_body = []
        for param in param_names:
            if param in default_value_params:  # Include default value in the constructor
                init_params.append(f"{param}={default_value_params[param]}")
            else:
                init_params.append(param)
            init_body.append(f"        self.{param} = {param}\n")

        init_method = "    def __init__(self, {}):\n".format(", ".join(init_params))
        return class_def + init_method + "".join(init_body)

    def encapsulate_parameters(
        self, classified_params: dict, default_value_params: dict
    ) -> list[ast.ClassDef]:
        """
        Injects parameter object classes into the AST tree
        """
        data_params, config_params = classified_params["data"], classified_params["config"]
        class_nodes = []

        if data_params:
            data_param_object_code = self.create_parameter_object_class(
                data_params, default_value_params, class_name="DataParams"
            )
            class_nodes.append(ast.parse(data_param_object_code).body[0])

        if config_params:
            config_param_object_code = self.create_parameter_object_class(
                config_params, default_value_params, class_name="ConfigParams"
            )
            class_nodes.append(ast.parse(config_param_object_code).body[0])

        return class_nodes


class FunctionCallUpdater:
    @staticmethod
    def get_method_type(func_node: ast.FunctionDef):
        # Check decorators
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
                return "static method"
            if isinstance(decorator, ast.Name) and decorator.id == "classmethod":
                return "class method"

        # Check first argument
        if func_node.args.args:
            first_arg = func_node.args.args[0].arg
            if first_arg == "self":
                return "instance method"
            elif first_arg == "cls":
                return "class method"

        return "unknown method type"

    @staticmethod
    def remove_unused_params(
        function_node: ast.FunctionDef, used_params: set[str], default_value_params: dict
    ) -> ast.FunctionDef:
        """
        Removes unused parameters from the function signature.
        """
        method_type = FunctionCallUpdater.get_method_type(function_node)
        updated_node_args = (
            [ast.arg(arg="self", annotation=None)]
            if method_type == "instance method"
            else [ast.arg(arg="cls", annotation=None)]
            if method_type == "class method"
            else []
        )

        updated_node_defaults = []
        for arg in function_node.args.args:
            if arg.arg in used_params:
                updated_node_args.append(arg)
                if arg.arg in default_value_params.keys():
                    updated_node_defaults.append(default_value_params[arg.arg])

        function_node.args.args = updated_node_args
        function_node.args.defaults = updated_node_defaults
        return function_node

    @staticmethod
    def update_function_signature(function_node: ast.FunctionDef, params: dict) -> ast.FunctionDef:
        """
        Updates the function signature to use encapsulated parameter objects.
        """
        data_params, config_params = params["data"], params["config"]

        method_type = FunctionCallUpdater.get_method_type(function_node)
        updated_node_args = (
            [ast.arg(arg="self", annotation=None)]
            if method_type == "instance method"
            else [ast.arg(arg="cls", annotation=None)]
            if method_type == "class method"
            else []
        )

        updated_node_args += [
            ast.arg(arg="data_params", annotation=None) for _ in [data_params] if data_params
        ] + [
            ast.arg(arg="config_params", annotation=None) for _ in [config_params] if config_params
        ]

        function_node.args.args = updated_node_args
        function_node.args.defaults = []

        return function_node

    @staticmethod
    def update_parameter_usages(function_node: ast.FunctionDef, params: dict) -> ast.FunctionDef:
        """
        Updates all parameter usages within the function body with encapsulated objects.
        """
        data_params, config_params = params["data"], params["config"]

        class ParameterUsageTransformer(ast.NodeTransformer):
            def visit_Name(self, node: ast.Name):
                if node.id in data_params and isinstance(node.ctx, ast.Load):
                    return ast.Attribute(
                        value=ast.Name(id="data_params", ctx=ast.Load()), attr=node.id, ctx=node.ctx
                    )
                if node.id in config_params and isinstance(node.ctx, ast.Load):
                    return ast.Attribute(
                        value=ast.Name(id="config_params", ctx=ast.Load()),
                        attr=node.id,
                        ctx=node.ctx,
                    )
                return node

        function_node.body = [
            ParameterUsageTransformer().visit(stmt) for stmt in function_node.body
        ]
        return function_node

    @staticmethod
    def get_enclosing_class_name(tree: ast.Module, init_node: ast.FunctionDef) -> str | None:
        """
        Finds the class name enclosing the given __init__ function node. This will be the class that is instantiaeted by the init method.

        :param tree: AST tree
        :param init_node: __init__ function node
        :return: name of the enclosing class, or None if not found
        """
        # Stack to track parent nodes
        parent_stack = []

        class ClassNameVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node: ast.ClassDef):
                # Push the class onto the stack
                parent_stack.append(node)
                self.generic_visit(node)
                # Pop the class after visiting its children
                parent_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef):
                # If this is the target __init__ function, get the enclosing class
                if node is init_node:
                    # Find the nearest enclosing class from the stack
                    for parent in reversed(parent_stack):
                        if isinstance(parent, ast.ClassDef):
                            raise StopIteration(parent.name)  # Return the class name
                self.generic_visit(node)

        # Traverse the AST with the visitor
        try:
            ClassNameVisitor().visit(tree)
        except StopIteration as e:
            return e.value

        # If no enclosing class is found
        return None

    @staticmethod
    def update_function_calls(
        tree: ast.Module, function_node: ast.FunctionDef, params: dict
    ) -> ast.Module:
        """
        Updates all calls to a given function in the provided AST tree to reflect new encapsulated parameters.

        :param tree: The AST tree of the code.
        :param function_name: The name of the function to update calls for.
        :param params: A dictionary containing 'data' and 'config' parameters.
        :return: The updated AST tree.
        """

        class FunctionCallTransformer(ast.NodeTransformer):
            def __init__(
                self,
                function_node: ast.FunctionDef,
                params: dict,
                is_constructor: bool = False,
                class_name: str = "",
            ):
                self.function_node = function_node
                self.params = params
                self.is_constructor = is_constructor
                self.class_name = class_name

            def visit_Call(self, node: ast.Call):
                # node.func is a ast.Name if it is a function call, and ast.Attribute if it is a a method class
                if isinstance(node.func, ast.Name):
                    node_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    node_name = node.func.attr

                if self.is_constructor and node_name == self.class_name:
                    return self.transform_call(node)
                elif node_name == self.function_node.name:
                    return self.transform_call(node)
                return node

            def create_ast_call(
                self,
                function_name: str,
                param_list: dict,
                args_map: list[ast.expr],
                keywords_map: list[ast.keyword],
            ):
                """
                Creates a AST for function call
                """

                return (
                    ast.Call(
                        func=ast.Name(id=function_name, ctx=ast.Load()),
                        args=[args_map[key] for key in param_list if key in args_map],
                        keywords=[
                            ast.keyword(arg=key, value=keywords_map[key])
                            for key in param_list
                            if key in keywords_map
                        ],
                    )
                    if param_list
                    else None
                )

            def transform_call(self, node: ast.Call):
                # original and classified params from function node
                params = [arg.arg for arg in self.function_node.args.args if arg.arg != "self"]
                data_params, config_params = self.params["data"], self.params["config"]

                # positional and keyword args passed in function call
                args, keywords = node.args, node.keywords

                data_args = {
                    param: args[i]
                    for i, param in enumerate(params)
                    if i < len(args) and param in data_params
                }
                config_args = {
                    param: args[i]
                    for i, param in enumerate(params)
                    if i < len(args) and param in config_params
                }

                data_keywords = {kw.arg: kw.value for kw in keywords if kw.arg in data_params}
                config_keywords = {kw.arg: kw.value for kw in keywords if kw.arg in config_params}

                updated_node_args = []
                if data_node := self.create_ast_call(
                    "DataParams", data_params, data_args, data_keywords
                ):
                    updated_node_args.append(data_node)
                if config_node := self.create_ast_call(
                    "ConfigParams", config_params, config_args, config_keywords
                ):
                    updated_node_args.append(config_node)

                # update function call node. note that keyword arguments are updated within encapsulated param objects above
                node.args, node.keywords = updated_node_args, []
                return node

        # apply the transformer to update all function calls to given function node
        if function_node.name == "__init__":
            # if function is a class initialization, then we need to fetch class name
            class_name = FunctionCallUpdater.get_enclosing_class_name(tree, function_node)
            transformer = FunctionCallTransformer(function_node, params, True, class_name)
        else:
            transformer = FunctionCallTransformer(function_node, params)
        updated_tree = transformer.visit(tree)

        return updated_tree
