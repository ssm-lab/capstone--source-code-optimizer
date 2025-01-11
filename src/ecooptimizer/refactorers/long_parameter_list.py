import ast
import astor
import logging
from pathlib import Path

from ..data_wrappers.smell import Smell
from .base_refactorer import BaseRefactorer
from ..testing.run_tests import run_tests


class LongParameterListRefactorer(BaseRefactorer):
    def __init__(self):
        super().__init__()
        self.parameter_analyzer = ParameterAnalyzer()
        self.parameter_encapsulator = ParameterEncapsulator()
        self.function_updater = FunctionCallUpdater()

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Refactors function/method with more than 6 parameters by encapsulating those with related names and removing those that are unused
        """
        # maximum limit on number of parameters beyond which the code smell is configured to be detected(see analyzers_config.py)
        max_param_limit = 6

        with file_path.open() as f:
            tree = ast.parse(f.read())

        # find the line number of target function indicated by the code smell object
        target_line = pylint_smell["line"]
        logging.info(
            f"Applying 'Fix Too Many Parameters' refactor on '{file_path.name}' at line {target_line} for identified code smell."
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

                        # update function signature, body and calls corresponding to new params
                        updated_function = self.function_updater.update_function_signature(
                            node, classified_params
                        )
                        updated_function = self.function_updater.update_parameter_usages(
                            node, classified_params
                        )
                        updated_tree = self.function_updater.update_function_calls(
                            tree, node.name, classified_params
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

        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_LPLR_line_{target_line}.py")
        with temp_file_path.open("w") as temp_file:
            temp_file.write(astor.to_source(updated_tree))

            # Measure emissions of the modified code
            final_emission = self.measure_energy(temp_file_path)

            if not final_emission:
                logging.info(
                    f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring."
                )
                return

            if self.check_energy_improvement(initial_emissions, final_emission):
                if run_tests() == 0:
                    logging.info("All tests pass! Refactoring applied.")
                    logging.info(
                        f"Refactored long parameter list into data groups on line {target_line} and saved.\n"
                    )
                    return
                else:
                    logging.info("Tests Fail! Discarded refactored changes")
            else:
                logging.info(
                    "No emission improvement after refactoring. Discarded refactored changes.\n"
                )


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
        if FunctionCallUpdater.get_method_type(function_node) == "instance method":
            updated_node_args = [ast.arg(arg="self", annotation=None)]
        elif FunctionCallUpdater.get_method_type(function_node) == "class method":
            updated_node_args = [ast.arg(arg="cls", annotation=None)]
        else:
            updated_node_args = []

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
        function_node.args.args = [
            ast.arg(arg="self", annotation=None),
            *(ast.arg(arg="data_params", annotation=None) for _ in [1] if data_params),
            *(ast.arg(arg="config_params", annotation=None) for _ in [1] if config_params),
        ]
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
    def update_function_calls(tree: ast.Module, function_name: str, params: dict) -> ast.Module:
        """
        Updates all calls to a given function in the provided AST tree to reflect new encapsulated parameters.

        :param tree: The AST tree of the code.
        :param function_name: The name of the function to update calls for.
        :param params: A dictionary containing 'data' and 'config' parameters.
        :return: The updated AST tree.
        """

        class FunctionCallTransformer(ast.NodeTransformer):
            def __init__(self, function_name: str, params: dict):
                self.function_name = function_name
                self.params = params

            def visit_Call(self, node: ast.Call):
                if isinstance(node.func, ast.Name):
                    node_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    node_name = node.func.attr
                if node_name == self.function_name:
                    return self.transform_call(node)
                return node

            def transform_call(self, node: ast.Call):
                data_params, config_params = self.params["data"], self.params["config"]

                args = node.args
                keywords = {kw.arg: kw.value for kw in node.keywords}

                # extract values for data and config params from positional and keyword arguments
                data_dict = {key: args[i] for i, key in enumerate(data_params) if i < len(args)}
                data_dict.update({key: keywords[key] for key in data_params if key in keywords})
                config_dict = {key: args[i] for i, key in enumerate(config_params) if i < len(args)}
                config_dict.update({key: keywords[key] for key in config_params if key in keywords})

                updated_node_args = []

                # create AST nodes for new arguments
                if data_params:
                    data_node = ast.Call(
                        func=ast.Name(id="DataParams", ctx=ast.Load()),
                        args=[data_dict[key] for key in data_params if key in data_dict],
                        keywords=[],
                    )
                    updated_node_args.append(data_node)

                if config_params:
                    config_node = ast.Call(
                        func=ast.Name(id="ConfigParams", ctx=ast.Load()),
                        args=[config_dict[key] for key in config_params if key in config_dict],
                        keywords=[],
                    )
                    updated_node_args.append(config_node)

                # replace original arguments with new encapsulated arguments
                node.args = updated_node_args
                node.keywords = []
                return node

        # apply the transformer to update all function calls
        transformer = FunctionCallTransformer(function_name, params)
        updated_tree = transformer.visit(tree)

        return updated_tree
