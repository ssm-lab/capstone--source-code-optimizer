import libcst as cst
import libcst.matchers as m
from libcst.metadata import PositionProvider, MetadataWrapper
from pathlib import Path

from .base_refactorer import BaseRefactorer
from ..data_types.smell import MIMSmell


class CallTransformer(cst.CSTTransformer):
    def __init__(self, mim_method: str, mim_class: str):
        super().__init__()
        self.mim_method = mim_method
        self.mim_class = mim_class
        self.transformed = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if m.matches(original_node.func, m.Attribute(value=m.Name(), attr=m.Name(self.mim_method))):

            # Convert `obj.method()` → `Class.method()`
            new_func = cst.Attribute(
                value=cst.Name(self.mim_class),
                attr=original_node.func.attr,  # type: ignore
            )

            self.transformed = True
            return updated_node.with_changes(func=new_func)

        return updated_node


class MakeStaticRefactorer(BaseRefactorer[MIMSmell], cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

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
        output_file: Path,
        overwrite: bool = True,  # noqa: ARG002
    ):
        """
        Perform refactoring

        :param target_file: absolute path to source code
        :param smell: pylint code for smell
        """
        self.target_line = smell.occurences[0].line
        self.target_file = target_file

        if not smell.obj:
            raise TypeError("No method object found")

        self.mim_method_class, self.mim_method = smell.obj.split(".")

        source_code = target_file.read_text()
        tree = MetadataWrapper(cst.parse_module(source_code))

        modified_tree = tree.visit(self)
        target_file.write_text(modified_tree.code)

        transformer = CallTransformer(self.mim_method, self.mim_method_class)
        self._refactor_files(source_dir, transformer)
        output_file.write_text(target_file.read_text())

    def _refactor_files(self, directory: Path, transformer: CallTransformer):
        for item in directory.iterdir():
            if item.is_dir():
                self._refactor_files(item, transformer)
            elif item.is_file():
                if item.suffix == ".py":
                    tree = cst.parse_module(item.read_text())
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

                decorators = [
                    *list(original_node.decorators),
                    cst.Decorator(cst.Name("staticmethod")),
                ]

                params = original_node.params
                if params.params and params.params[0].name.value == "self":
                    params = params.with_changes(params=params.params[1:])

                return updated_node.with_changes(decorators=decorators, params=params)

        return updated_node
