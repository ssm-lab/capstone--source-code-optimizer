import ast
import astor
from .base_refactorer import BaseRefactorer


def get_used_parameters(function_node, params):
    """
    Identify parameters that are used within the function body using AST analysis
    """
    used_params = set()
    source_code = astor.to_source(function_node)

    # Parse the function's source code into an AST tree
    tree = ast.parse(source_code)

    # Define a visitor to track parameter usage
    class ParamUsageVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load) and node.id in params:
                used_params.add(node.id)

    # Traverse the AST to collect used parameters
    ParamUsageVisitor().visit(tree)

    return used_params


def create_parameter_object_class(param_names):
    """
    Create a class definition for encapsulating parameters as attributes.
    """
    class_name = "ParamsObject"
    class_def = f"class {class_name}:\n"
    init_method = "    def __init__(self, {}):\n".format(", ".join(param_names))
    init_body = "".join([f"        self.{param} = {param}\n" for param in param_names])
    return class_def + init_method + init_body


class LongParameterListRefactorer(BaseRefactorer):
    """
    Refactorer that targets methods that take too many arguments
    """

    def __init__(self, logger):
        super().__init__(logger)

    def refactor(self, file_path, pylint_smell, initial_emission):
        self.logger.log(f"Refactoring functions with long parameter lists in {file_path}")

        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())

        modified = False

        # Use ast.walk() to find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]

                # Only consider functions with an initial long parameter list
                if len(params) > 4:
                    # Identify parameters that are actually used in function body
                    used_params = get_used_parameters(node, params)

                    # Remove unused parameters
                    new_args = [arg for arg in node.args.args if arg.arg in used_params]
                    if len(new_args) != len(node.args.args):  # Check if any parameters were removed
                        node.args.args[:] = new_args  # Update in place
                        modified = True

                    # Encapsulate remaining parameters if 4 or more are still used
                    if len(used_params) >= 4:

                        modified = True
                        param_names = list(used_params)
                        param_object_code = create_parameter_object_class(param_names)
                        param_object_ast = ast.parse(param_object_code).body[0]

                        # Insert parameter object class at the beginning of the file
                        tree.body.insert(0, param_object_ast)

                        # Modify function to use a single parameter for the parameter object
                        node.args.args = [ast.arg(arg="params", annotation=None)]

                        # Update all parameter usages within the function to access attributes of the parameter object
                        class ParamAttributeUpdater(ast.NodeTransformer):
                            def visit_Name(self, node):
                                if node.id in param_names and isinstance(node.ctx, ast.Load):
                                    return ast.Attribute(value=ast.Name(id="params", ctx=ast.Load()), attr=node.id,
                                                         ctx=node.ctx)
                                return node

                        node.body = [ParamAttributeUpdater().visit(stmt) for stmt in node.body]

        if modified:
            # Write back modified code to file
            # Using temporary file to retain test contents. To see energy reduction remove temp suffix
            temp_file_path = f"{file_path}"
            with open(temp_file_path, "w") as temp_file:
                temp_file.write(astor.to_source(tree))

