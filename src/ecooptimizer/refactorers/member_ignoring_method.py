import logging
from pathlib import Path
import astor
import ast
from ast import NodeTransformer

from .base_refactorer import BaseRefactorer
from ..data_wrappers.smell import Smell


class MakeStaticRefactorer(NodeTransformer, BaseRefactorer):
    """
    Refactorer that targets methods that don't use any class attributes and makes them static to improve performance
    """

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.target_line = None
        self.mim_method_class = ""
        self.mim_method = ""

    def refactor(self, file_path: Path, pylint_smell: Smell):
        """
        Perform refactoring

        :param file_path: absolute path to source code
        :param pylint_smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_line = pylint_smell["line"]
        logging.info(
            f"Applying 'Make Method Static' refactor on '{file_path.name}' at line {self.target_line} for identified code smell."
        )
        # Parse the code into an AST
        source_code = file_path.read_text()
        logging.debug(source_code)
        tree = ast.parse(source_code, file_path)

        # Apply the transformation
        modified_tree = self.visit(tree)

        # Convert the modified AST back to source code
        modified_code = astor.to_source(modified_tree)

        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_MIMR_line_{self.target_line}.py")

        temp_file_path.write_text(modified_code)
        file_path.write_text(modified_code)

        logging.info(f"Refactoring completed and saved to: {temp_file_path}")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        logging.debug(f"visiting FunctionDef {node.name} line {node.lineno}")
        if node.lineno == self.target_line:
            logging.debug("Modifying FunctionDef")
            self.mim_method = node.name
            # Step 1: Add the decorator
            decorator = ast.Name(id="staticmethod", ctx=ast.Load())
            decorator_list = node.decorator_list
            decorator_list.append(decorator)

            new_args = node.args.args
            # Step 2: Remove 'self' from the arguments if it exists
            if new_args and new_args[0].arg == "self":
                new_args.pop(0)

            arguments = ast.arguments(
                posonlyargs=node.args.posonlyargs,
                args=new_args,
                vararg=node.args.vararg,
                kwonlyargs=node.args.kwonlyargs,
                kw_defaults=node.args.kw_defaults,
                kwarg=node.args.kwarg,
                defaults=node.args.defaults,
            )
            return ast.FunctionDef(
                name=node.name,
                args=arguments,
                body=node.body,
                returns=node.returns,
                decorator_list=decorator_list,
            )
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        logging.debug(f"start line: {node.lineno}, end line: {node.end_lineno}")
        if node.lineno < self.target_line and node.end_lineno > self.target_line:  # type: ignore
            logging.debug("Getting class name")
            self.mim_method_class = node.name
            self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call):
        logging.debug("visiting Call")
        if isinstance(node.func, ast.Attribute) and node.func.attr == self.mim_method:
            if isinstance(node.func.value, ast.Name):
                logging.debug("Modifying Call")
                attr = ast.Attribute(
                    value=ast.Name(id=self.mim_method_class, ctx=ast.Load()),
                    attr=node.func.attr,
                    ctx=ast.Load(),
                )
                return ast.Call(func=attr, args=node.args, keywords=node.keywords)
        return node
