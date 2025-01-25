import logging
from pathlib import Path
import astor
import ast
from ast import NodeTransformer

from .base_refactorer import BaseRefactorer
from ..data_types.smell import MIMSmell


class CallTransformer(NodeTransformer):
    def __init__(self, mim_method: str, mim_class: str):
        super().__init__()
        self.mim_method = mim_method
        self.mim_class = mim_class
        self.transformed = False

    def reset(self):
        self.transformed = False

    def visit_Call(self, node: ast.Call):
        logging.debug("visiting Call")

        if isinstance(node.func, ast.Attribute) and node.func.attr == self.mim_method:
            if isinstance(node.func.value, ast.Name):
                logging.debug("Modifying Call")
                attr = ast.Attribute(
                    value=ast.Name(id=self.mim_class, ctx=ast.Load()),
                    attr=node.func.attr,
                    ctx=ast.Load(),
                )
                self.transformed = True
                return ast.Call(func=attr, args=node.args, keywords=node.keywords)
        return node


class MakeStaticRefactorer(NodeTransformer, BaseRefactorer):
    """
    Refactorer that targets methods that don't use any class attributes and makes them static to improve performance
    """

    def __init__(self):
        super().__init__()
        self.target_line = None
        self.mim_method_class = ""
        self.mim_method = ""

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: MIMSmell,
        output_file: Path,  # noqa: ARG002
        overwrite: bool = True,  # noqa: ARG002
    ):
        """
        Perform refactoring

        :param target_file: absolute path to source code
        :param smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_line = smell.occurences[0].line
        logging.info(
            f"Applying 'Make Method Static' refactor on '{target_file.name}' at line {self.target_line} for identified code smell."
        )
        # Parse the code into an AST
        source_code = target_file.read_text()
        logging.debug(source_code)
        tree = ast.parse(source_code, target_file)

        # Apply the transformation
        modified_tree = self.visit(tree)

        target_file.write_text(astor.to_source(modified_tree))

        transformer = CallTransformer(self.mim_method, self.mim_method_class)

        self._refactor_files(source_dir, transformer)

        # temp_file_path = output_file

        # temp_file_path.write_text(modified_code)
        # if overwrite:
        #     target_file.write_text(modified_code)

        logging.info(
            f"Refactoring completed for the following files: {[target_file, *self.modified_files]}"
        )

    def _refactor_files(self, directory: Path, transformer: CallTransformer):
        for item in directory.iterdir():
            logging.debug(f"Refactoring {item!s}")
            if item.is_dir():
                self._refactor_files(item, transformer)
            elif item.is_file():
                if item.suffix == ".py":
                    modified_file = transformer.visit(ast.parse(item.read_text()))
                    if transformer.transformed:
                        self.modified_files.append(item)

                        item.write_text(astor.to_source(modified_file))
                        transformer.reset()

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
