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
        maxParamLimit = 6

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
                params = [arg.arg for arg in node.args.args]

                if (
                    len(params) > maxParamLimit
                ):  # max limit beyond which the code smell is configured to be detected
                    # need to identify used parameters so unused ones can be removed
                    used_params = self.parameter_analyzer.get_used_parameters(node, params)
                    if len(used_params) > maxParamLimit:
                        # classify used params into data and config types and store the results in a dictionary, if number of used params is beyond the configured limit
                        classifiedParams = self.parameter_analyzer.classify_parameters(used_params)

                        class_nodes = self.parameter_encapsulator.encapsulate_parameters(
                            classifiedParams
                        )
                        for class_node in class_nodes:
                            tree.body.insert(0, class_node)

                        updated_function = self.function_updater.update_function_signature(
                            node, classifiedParams
                        )
                        updated_function = self.function_updater.update_parameter_usages(
                            updated_function, classifiedParams
                        )
                        updated_tree = self.function_updater.update_function_calls(
                            tree, node.name, classifiedParams
                        )
                    else:
                        # just remove the unused params if used parameters are within the maxParamLimit
                        updated_function = self.function_updater.remove_unused_params(
                            node, used_params
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
        param_names: list[str], class_name: str = "ParamsObject"
    ) -> str:
        """
        Creates a class definition for encapsulating related parameters
        """
        class_def = f"class {class_name}:\n"
        init_method = "    def __init__(self, {}):\n".format(", ".join(param_names))
        init_body = "".join([f"        self.{param} = {param}\n" for param in param_names])
        return class_def + init_method + init_body

    def encapsulate_parameters(self, params: dict) -> list[ast.ClassDef]:
        """
        Injects parameter object classes into the AST tree
        """
        data_params, config_params = params["data"], params["config"]
        class_nodes = []

        if data_params:
            data_param_object_code = self.create_parameter_object_class(
                data_params, class_name="DataParams"
            )
            class_nodes.append(ast.parse(data_param_object_code).body[0])

        if config_params:
            config_param_object_code = self.create_parameter_object_class(
                config_params, class_name="ConfigParams"
            )
            class_nodes.append(ast.parse(config_param_object_code).body[0])

        return class_nodes


class FunctionCallUpdater:
    @staticmethod
    def remove_unused_params(
        function_node: ast.FunctionDef, used_params: set[str]
    ) -> ast.FunctionDef:
        """
        Removes unused parameters from the function signature.
        """
        function_node.args.args = [arg for arg in function_node.args.args if arg.arg in used_params]
        return function_node

    @staticmethod
    def update_function_signature(function_node: ast.FunctionDef, params: dict) -> ast.FunctionDef:
        """
        Updates the function signature to use encapsulated parameter objects.
        """
        data_params, config_params = params["data"], params["config"]

        # function_node.args.args = [ast.arg(arg="self", annotation=None)]
        # if data_params:
        #     function_node.args.args.append(ast.arg(arg="data_params", annotation=None))
        # if config_params:
        #     function_node.args.args.append(ast.arg(arg="config_params", annotation=None))

        function_node.args.args = [
            ast.arg(arg="self", annotation=None),
            *(ast.arg(arg="data_params", annotation=None) for _ in [1] if data_params),
            *(ast.arg(arg="config_params", annotation=None) for _ in [1] if config_params),
        ]

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

                # create AST nodes for new arguments
                data_node = ast.Call(
                    func=ast.Name(id="DataParams", ctx=ast.Load()),
                    args=[data_dict[key] for key in data_params if key in data_dict],
                    keywords=[],
                )

                config_node = ast.Call(
                    func=ast.Name(id="ConfigParams", ctx=ast.Load()),
                    args=[config_dict[key] for key in config_params if key in config_dict],
                    keywords=[],
                )

                # replace original arguments with new encapsulated arguments
                node.args = [data_node, config_node]
                node.keywords = []
                return node

        # apply the transformer to update all function calls
        transformer = FunctionCallTransformer(function_name, params)
        updated_tree = transformer.visit(tree)

        return updated_tree
