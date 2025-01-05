import ast
import logging
from pathlib import Path

import astor

from ..data_wrappers.smell import Smell
from .base_refactorer import BaseRefactorer
from ..testing.run_tests import run_tests


def get_used_parameters(function_node: ast.FunctionDef, params: list[str]):
    """
    Identifies parameters that are used within the function body using AST analysis
    """
    used_params: set[str] = set()
    source_code = astor.to_source(function_node)

    # Parse the function's source code into an AST tree
    tree = ast.parse(source_code)

    # Define a visitor to track parameter usage
    class ParamUsageVisitor(ast.NodeVisitor):
        def visit_Name(self, node):  # noqa: ANN001
            if isinstance(node.ctx, ast.Load) and node.id in params:
                used_params.add(node.id)

    # Traverse the AST to collect used parameters
    ParamUsageVisitor().visit(tree)

    return used_params


def classify_parameters(params: list[str]):
    """
    Classifies parameters into 'data' and 'config' groups based on naming conventions
    """
    data_params: list[str] = []
    config_params: list[str] = []

    for param in params:
        if param.startswith(("config", "flag", "option", "setting")):
            config_params.append(param)
        else:
            data_params.append(param)

    return data_params, config_params


def create_parameter_object_class(param_names: list[str], class_name: str = "ParamsObject"):
    """
    Creates a class definition for encapsulating parameters as attributes
    """
    class_def = f"class {class_name}:\n"
    init_method = "    def __init__(self, {}):\n".format(", ".join(param_names))
    init_body = "".join([f"        self.{param} = {param}\n" for param in param_names])
    return class_def + init_method + init_body


class LongParameterListRefactorer(BaseRefactorer):
    """
    Refactorer that targets methods in source code that take too many parameters
    """

    def __init__(self):
        super().__init__()

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Identifies methods with too many parameters, encapsulating related ones & removing unused ones
        """
        target_line = pylint_smell["line"]
        logging.info(
            f"Applying 'Fix Too Many Parameters' refactor on '{file_path.name}' at line {target_line} for identified code smell."
        )
        with file_path.open() as f:
            tree = ast.parse(f.read())

        # Flag indicating if a refactoring has been made
        modified = False

        # Find function definitions at the specific line number
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.lineno == target_line:
                params = [arg.arg for arg in node.args.args]

                # Only consider functions with an initial long parameter list
                if len(params) > 6:
                    # Identify parameters that are actually used in function body
                    used_params = get_used_parameters(node, params)

                    # Remove unused parameters
                    new_params = [arg for arg in node.args.args if arg.arg in used_params]
                    if len(new_params) != len(
                        node.args.args
                    ):  # Check if any parameters were removed
                        node.args.args[:] = new_params  # Update in place
                        modified = True

                    # Encapsulate remaining parameters if 4 or more are still used
                    if len(used_params) >= 6:
                        modified = True
                        param_names = list(used_params)

                        # Classify parameters into data and configuration groups
                        data_params, config_params = classify_parameters(param_names)
                        data_params.remove("self")

                        # Create parameter object classes for each group
                        if data_params:
                            data_param_object_code = create_parameter_object_class(
                                data_params, class_name="DataParams"
                            )
                            data_param_object_ast = ast.parse(data_param_object_code).body[0]
                            tree.body.insert(0, data_param_object_ast)

                        if config_params:
                            config_param_object_code = create_parameter_object_class(
                                config_params, class_name="ConfigParams"
                            )
                            config_param_object_ast = ast.parse(config_param_object_code).body[0]
                            tree.body.insert(0, config_param_object_ast)

                        # Modify function to use two parameters for the parameter objects
                        node.args.args = [
                            ast.arg(arg="self", annotation=None),
                            ast.arg(arg="data_params", annotation=None),
                            ast.arg(arg="config_params", annotation=None),
                        ]

                        # Update all parameter usages within the function to access attributes of the parameter objects
                        class ParamAttributeUpdater(ast.NodeTransformer):
                            def visit_Attribute(self, node):  # noqa: ANN001
                                if node.attr in data_params and isinstance(node.ctx, ast.Load):  # noqa: B023
                                    return ast.Attribute(
                                        value=ast.Name(id="self", ctx=ast.Load()),
                                        attr="data_params",
                                        ctx=node.ctx,
                                    )
                                elif node.attr in config_params and isinstance(node.ctx, ast.Load):  # noqa: B023
                                    return ast.Attribute(
                                        value=ast.Name(id="self", ctx=ast.Load()),
                                        attr="config_params",
                                        ctx=node.ctx,
                                    )
                                return node

                            def visit_Name(self, node):  # noqa: ANN001
                                if node.id in data_params and isinstance(node.ctx, ast.Load):  # noqa: B023
                                    return ast.Attribute(
                                        value=ast.Name(id="data_params", ctx=ast.Load()),
                                        attr=node.id,
                                        ctx=ast.Load(),
                                    )
                                elif node.id in config_params and isinstance(node.ctx, ast.Load):  # noqa: B023
                                    return ast.Attribute(
                                        value=ast.Name(id="config_params", ctx=ast.Load()),
                                        attr=node.id,
                                        ctx=ast.Load(),
                                    )

                        node.body = [ParamAttributeUpdater().visit(stmt) for stmt in node.body]

        if modified:
            # Write back modified code to temporary file
            temp_file_path = self.temp_dir / Path(f"{file_path.stem}_LPLR_line_{target_line}.py")
            with temp_file_path.open("w") as temp_file:
                temp_file.write(astor.to_source(tree))

            # Measure emissions of the modified code
            final_emission = self.measure_energy(temp_file_path)

            if not final_emission:
                # os.remove(temp_file_path)
                logging.info(
                    f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring."
                )
                return

            if self.check_energy_improvement(initial_emissions, final_emission):
                # If improved, replace the original file with the modified content
                if run_tests() == 0:
                    logging.info("All test pass! Functionality maintained.")
                    # shutil.move(temp_file_path, file_path)
                    logging.info(
                        f"Refactored long parameter list into data groups on line {target_line} and saved.\n"
                    )
                    return

                logging.info("Tests Fail! Discarded refactored changes")

            else:
                logging.info(
                    "No emission improvement after refactoring. Discarded refactored changes.\n"
                )

            # Remove the temporary file if no energy improvement or failing tests
            # os.remove(temp_file_path)
