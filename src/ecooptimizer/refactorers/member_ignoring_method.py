import astroid
from astroid import nodes, util
import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper

from pathlib import Path

from .. import OUTPUT_MANAGER

from .multi_file_refactorer import MultiFileRefactorer
from ..data_types.smell import MIMSmell

logger = OUTPUT_MANAGER.loggers["refactor_smell"]


class CallTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, method_calls: list[tuple[str, int, str]], class_name: str):
        self.method_calls = {(caller, lineno, method) for caller, lineno, method in method_calls}
        self.class_name = class_name  # Class name to replace instance calls
        self.transformed = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Transform instance calls to static calls if they match."""
        if isinstance(original_node.func, cst.Attribute):
            caller = original_node.func.value
            method = original_node.func.attr.value
            position = self.get_metadata(PositionProvider, original_node, None)

            if not position:
                raise TypeError("What do you mean you can't find the position?")

            # Check if this call matches one from astroid (by caller, method name, and line number)
            for call_caller, line, call_method in self.method_calls:
                logger.debug(f"cst caller: {call_caller} at line {position.start.line}")
                if (
                    method == call_method
                    and position.start.line - 1 == line
                    and caller.deep_equals(cst.parse_expression(call_caller))
                ):
                    logger.debug("transforming")
                    # Transform `obj.method(args)` -> `ClassName.method(args)`
                    new_func = cst.Attribute(
                        value=cst.Name(self.class_name),  # Replace `obj` with class name
                        attr=original_node.func.attr,
                    )
                    self.transformed = True
                    return updated_node.with_changes(func=new_func)

        return updated_node  # Return unchanged if no match


def find_valid_method_calls(
    tree: nodes.Module, mim_method: str, valid_classes: set[str]
) -> list[tuple[str, int, str]]:
    """
    Finds method calls where the instance is of a valid class.

    Returns:
        A list of (caller_name, line_number, method_name).
    """
    valid_calls = []

    logger.info("Finding valid method calls")

    for node in tree.body:
        for descendant in node.nodes_of_class(nodes.Call):
            if isinstance(descendant.func, nodes.Attribute):
                logger.debug(f"caller: {descendant.func.expr.as_string()}")
                caller = descendant.func.expr  # The object calling the method
                method_name = descendant.func.attrname

                if method_name != mim_method:
                    continue

                inferred_types = []
                inferrences = caller.infer()

                for inferred in inferrences:
                    logger.debug(f"inferred: {inferred.repr_name()}")
                    if isinstance(inferred.repr_name(), util.UninferableBase):
                        hint = check_for_annotations(caller, descendant.scope())
                        if hint:
                            inferred_types.append(hint.as_string())
                        else:
                            continue
                    else:
                        inferred_types.append(inferred.repr_name())

                logger.debug(f"Inferred types: {inferred_types}")

                # Check if any inferred type matches a valid class
                if any(cls in valid_classes for cls in inferred_types):
                    logger.debug(
                        f"Foud valid call: {caller.as_string()} at line {descendant.lineno}"
                    )
                    valid_calls.append((caller.as_string(), descendant.lineno, method_name))

    return valid_calls


def check_for_annotations(caller: nodes.NodeNG, scope: nodes.NodeNG):
    if not isinstance(scope, nodes.FunctionDef):
        return None

    hint = None
    logger.debug(f"annotations: {scope.args}")

    args = scope.args.args
    anns = scope.args.annotations
    if args and anns:
        for i in range(len(args)):
            if args[i].name == caller.as_string():
                hint = scope.args.annotations[i]
                break

    return hint


class MakeStaticRefactorer(MultiFileRefactorer[MIMSmell], cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        super().__init__()
        self.target_line = None
        self.mim_method_class = ""
        self.mim_method = ""
        self.valid_classes: set[str] = set()

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
        self.valid_classes.add(self.mim_method_class)

        source_code = target_file.read_text()
        tree = MetadataWrapper(cst.parse_module(source_code))

        # Find all subclasses of the target class
        self._find_subclasses(tree)

        modified_tree = tree.visit(self)
        target_file.write_text(modified_tree.code)

        astroid_tree = astroid.parse(source_code)
        valid_calls = find_valid_method_calls(astroid_tree, self.mim_method, self.valid_classes)

        self.transformer = CallTransformer(valid_calls, self.mim_method_class)

        self.traverse_and_process(source_dir)
        output_file.write_text(target_file.read_text())

    def _find_subclasses(self, tree: MetadataWrapper):
        """Find all subclasses of the target class within the file."""

        class SubclassCollector(cst.CSTVisitor):
            def __init__(self, base_class: str):
                self.base_class = base_class
                self.subclasses: set[str] = set()

            def visit_ClassDef(self, node: cst.ClassDef):
                if any(
                    base.value.value == self.base_class
                    for base in node.bases
                    if isinstance(base.value, cst.Name)
                ):
                    self.subclasses.add(node.name.value)

        logger.debug("find all subclasses")
        collector = SubclassCollector(self.mim_method_class)
        tree.visit(collector)
        self.valid_classes = self.valid_classes.union(collector.subclasses)
        logger.debug(f"valid classes: {self.valid_classes}")

    def _process_file(self, file: Path):
        tree = MetadataWrapper(cst.parse_module(file.read_text()))

        modified_tree = tree.visit(self.transformer)

        if self.transformer.transformed:
            file.write_text(modified_tree.code)
            if not file.samefile(self.target_file):
                self.modified_files.append(file.resolve())
            self.transformer.transformed = False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        func_name = original_node.name.value
        if func_name and updated_node.deep_equals(original_node):
            position = self.get_metadata(PositionProvider, original_node).start  # type: ignore
            if position.line == self.target_line and func_name == self.mim_method:
                logger.debug("Modifying MIM method")
                decorators = [
                    *list(original_node.decorators),
                    cst.Decorator(cst.Name("staticmethod")),
                ]
                params = original_node.params
                if params.params and params.params[0].name.value == "self":
                    params = params.with_changes(params=params.params[1:])
                return updated_node.with_changes(decorators=decorators, params=params)
        return updated_node
