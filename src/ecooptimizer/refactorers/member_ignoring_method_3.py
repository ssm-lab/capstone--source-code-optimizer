import logging
import libcst as cst

# import libcst.matchers as m
from libcst.metadata import (
    PositionProvider,
    MetadataWrapper,
    ScopeProvider,
    # Scope,
)
from pathlib import Path

from .base_refactorer import BaseRefactorer
from ..data_types.smell import MIMSmell


class CallTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (ScopeProvider,)

    def __init__(self, mim_method: str, mim_class: str, subclasses: set[str]):
        super().__init__()
        self.mim_method = mim_method
        self.mim_class = mim_class
        self.subclasses = subclasses | {mim_class}  # Include the base class itself
        self.transformed = False

    # def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
    #     class ScopeVisitor(cst.CSTVisitor):
    #         def __init__(self, instance_name: str, mim_class: str):
    #             self.instance_name = instance_name
    #             self.mim_class = mim_class
    #             self.isClassType = False

    #         def visit_Param(self, node: cst.Param) -> None:
    #             if (
    #                 node.name.value == self.instance_name
    #                 and node.annotation
    #                 and isinstance(node.annotation.annotation, cst.Name)
    #                 and node.annotation.annotation.value == self.mim_class
    #             ):
    #                 self.isClassType = True

    #         def visit_Assign(self, node: cst.Assign) -> None:
    #             for target in node.targets:
    #                 if (
    #                     isinstance(target.target, cst.Name)
    #                     and target.target.value == self.instance_name
    #                 ):
    #                     if isinstance(node.value, cst.Call) and isinstance(
    #                         node.value.func, cst.Name
    #                     ):
    #                         class_name = node.value.func.value
    #                         if class_name == self.mim_class:
    #                             self.isClassType = True

    #     if m.matches(original_node.func, m.Attribute(value=m.Name(), attr=m.Name(self.mim_method))):
    #         if isinstance(original_node.func, cst.Attribute) and isinstance(
    #             original_node.func.value, cst.Name
    #         ):
    #             instance_name = original_node.func.value.value  # type: ignore # The variable name of the instance
    #             scope = self.get_metadata(ScopeProvider, original_node)

    #             if not scope or not isinstance(scope, Scope):
    #                 return updated_node

    #             for binding in scope.accesses:
    #                 logging.debug(f"name: {binding.node}")
    #                 for referant in binding.referents:
    #                     logging.debug(f"referant: {referant.name}\n")

    #             # Check the declared type of the instance within the current scope
    #             logging.debug("Checking instance type")
    #             instance_type = None

    #             if instance_type:
    #                 logging.debug(f"Modifying Call for instance of {instance_type}")
    #                 new_func = cst.Attribute(
    #                     value=cst.Name(self.mim_class),
    #                     attr=original_node.func.attr,  # type: ignore
    #                 )
    #                 self.transformed = True
    #                 return updated_node.with_changes(func=new_func)
    #             # else:
    #             #     # If type is unknown, add a comment instead of modifying
    #             #     return updated_node.with_changes(
    #             #         leading_lines=[cst.EmptyLine(comment=cst.Comment("# Cannot determine instance type, skipping transformation")), *list(updated_node.leading_lines)]
    #             #     )
    #     return updated_node


class MakeStaticRefactorer(BaseRefactorer[MIMSmell], cst.CSTTransformer):
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
    )

    def __init__(self):
        super().__init__()
        self.target_line = None
        self.mim_method_class = ""
        self.mim_method = ""
        self.subclasses = set()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: MIMSmell,
        output_file: Path,
        overwrite: bool = True,  # noqa: ARG002
    ):
        self.target_line = smell.occurences[0].line
        self.target_file = target_file

        if not smell.obj:
            raise TypeError("No method object found")

        self.mim_method_class, self.mim_method = smell.obj.split(".")

        logging.info(
            f"Applying 'Make Method Static' refactor on '{target_file.name}' at line {self.target_line}."
        )

        source_code = target_file.read_text()
        tree = MetadataWrapper(cst.parse_module(source_code))

        # Find all subclasses of the target class
        self._find_subclasses(tree)

        modified_tree = tree.visit(self)
        target_file.write_text(modified_tree.code)

        transformer = CallTransformer(self.mim_method, self.mim_method_class, self.subclasses)
        self._refactor_files(source_dir, transformer)
        output_file.write_text(target_file.read_text())

        logging.info(
            f"Refactoring completed for the following files: {[target_file, *self.modified_files]}"
        )

    def _find_subclasses(self, tree: MetadataWrapper):
        """Find all subclasses of the target class within the file."""

        class SubclassCollector(cst.CSTVisitor):
            def __init__(self, base_class: str):
                self.base_class = base_class
                self.subclasses = set()

            def visit_ClassDef(self, node: cst.ClassDef):
                if any(
                    base.value.value == self.base_class
                    for base in node.bases
                    if isinstance(base.value, cst.Name)
                ):
                    logging.debug(f"Found subclass <{node.name.value}>")
                    self.subclasses.add(node.name.value)

        collector = SubclassCollector(self.mim_method_class)
        logging.debug("Getting subclasses")
        tree.visit(collector)
        self.subclasses = collector.subclasses

    def _refactor_files(self, directory: Path, transformer: CallTransformer):
        for item in directory.iterdir():
            logging.debug(f"Refactoring {item!s}")
            if item.is_dir():
                self._refactor_files(item, transformer)
            elif item.is_file() and item.suffix == ".py":
                tree = MetadataWrapper(cst.parse_module(item.read_text()))
                modified_tree = tree.visit(transformer)
                if transformer.transformed:
                    item.write_text(modified_tree.code)
                    if not item.samefile(self.target_file):
                        self.modified_files.append(item.resolve())
                    transformer.transformed = False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        func_name = original_node.name.value
        if func_name and updated_node.deep_equals(original_node):
            position = self.get_metadata(PositionProvider, original_node).start  # type: ignore
            if position.line == self.target_line and func_name == self.mim_method:
                logging.debug("Modifying FunctionDef")
                decorators = [
                    *list(original_node.decorators),
                    cst.Decorator(cst.Name("staticmethod")),
                ]
                params = original_node.params
                if params.params and params.params[0].name.value == "self":
                    params = params.with_changes(params=params.params[1:])
                return updated_node.with_changes(decorators=decorators, params=params)
        return updated_node
