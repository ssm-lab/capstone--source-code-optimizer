import libcst as cst
from pathlib import Path
from libcst.metadata import PositionProvider

from ..base_refactorer import BaseRefactorer
from ...data_types.smell import UGESmell


class ListCompInAnyAllTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, target_line: int, start_col: int, end_col: int):
        super().__init__()
        self.target_line = target_line
        self.start_col = start_col
        self.end_col = end_col
        self.found = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        """
        Detects `any([...])` or `all([...])` calls and converts their list comprehension argument
        to a generator expression.
        """
        if self.found:
            return updated_node  # Avoid modifying multiple nodes in one pass

        # Check if the function is `any` or `all`
        if isinstance(original_node.func, cst.Name) and original_node.func.value in {"any", "all"}:
            # Ensure it has exactly one argument
            if len(original_node.args) == 1:
                arg = original_node.args[0].value  # Extract the argument expression

                # Ensure the argument is a list comprehension
                if isinstance(arg, cst.ListComp):
                    metadata = self.get_metadata(PositionProvider, original_node, None)
                    if (
                        metadata and metadata.start.line == self.target_line
                        # and self.start_col <= metadata.start.column < self.end_col
                    ):
                        self.found = True
                        return updated_node.with_changes(
                            args=[
                                updated_node.args[0].with_changes(
                                    value=cst.GeneratorExp(
                                        elt=arg.elt, for_in=arg.for_in, lpar=[], rpar=[]
                                    )
                                )
                            ]
                        )

        return updated_node


class UseAGeneratorRefactorer(BaseRefactorer[UGESmell]):
    def __init__(self):
        super().__init__()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: UGESmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactors an unnecessary list comprehension inside `any()` or `all()` calls
        by converting it to a generator expression.
        """
        line_number = smell.occurences[0].line
        start_column = smell.occurences[0].column
        end_column = smell.occurences[0].endColumn

        # Read the source file
        source_code = target_file.read_text()

        # Parse with LibCST
        wrapper = cst.MetadataWrapper(cst.parse_module(source_code))

        # Apply transformation
        transformer = ListCompInAnyAllTransformer(line_number, start_column, end_column)  # type: ignore
        modified_tree = wrapper.visit(transformer)

        if transformer.found:
            if overwrite:
                target_file.write_text(modified_tree.code)
            else:
                output_file.write_text(modified_tree.code)
