import astroid
from astroid import nodes, util
import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper

from pathlib import Path

from ...config import CONFIG

from ..multi_file_refactorer import MultiFileRefactorer
from ...data_types.smell import MIMSmell

logger = CONFIG["refactorLogger"]


class CallTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, class_name: str):
        self.method_calls: list[tuple[str, int, str, str]] = None  # type: ignore
        self.class_name = class_name  # Class nme to replace instance calls
        self.transformed = False

    def set_calls(self, valid_calls: list[tuple[str, int, str, str]]):
        self.method_calls = valid_calls

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Transform instance calls to static calls if they match."""
        if isinstance(original_node.func, cst.Attribute):
            caller = original_node.func.value
            method = original_node.func.attr.value
            position = self.get_metadata(PositionProvider, original_node, None)

            if not position:
                raise TypeError("What do you mean you can't find the position?")

            # Check if this call matches one from astroid (by caller, method name, and line number)
            for call_caller, line, call_method, cls in self.method_calls:
                logger.debug(f"cst caller: {call_caller} at line {position.start.line}")
                if (
                    method == call_method
                    and position.start.line == line
                    and caller.deep_equals(cst.parse_expression(call_caller))
                ):
                    logger.debug("transforming")
                    # Transform `obj.method(args)` -> `ClassName.method(args)`
                    new_func = cst.Attribute(
                        value=cst.Name(cls),  # Replace `obj` with class name
                        attr=original_node.func.attr,
                    )
                    self.transformed = True
                    return updated_node.with_changes(func=new_func)

        return updated_node  # Return unchanged if no match


def find_valid_method_calls(
    tree: nodes.Module, mim_method: str, valid_classes: set[str]
) -> list[tuple[str, int, str, str]]:
    """
    Finds method calls where the instance is of a valid class.

    Returns:
        A list of (caller_name, line_number, method_name).
    """
    valid_calls = []

    logger.debug("Finding valid method calls")

    for node in tree.body:
        for descendant in node.nodes_of_class(nodes.Call):
            if isinstance(descendant.func, nodes.Attribute):
                logger.debug(f"caller: {descendant.func.expr.as_string()}")
                caller = descendant.func.expr  # The object calling the method
                method_name = descendant.func.attrname

                if method_name != mim_method:
                    continue

                inferred_types: list[str] = []
                try:
                    inferrences = caller.infer()

                    for inferred in inferrences:
                        logger.debug(f"inferred: {inferred.repr_name()}")
                        if isinstance(inferred, util.UninferableBase):
                            hint = check_for_annotations(caller, descendant.scope())
                            inits = check_for_initializations(caller, descendant.scope())
                            if hint:
                                inferred_types.append(hint.as_string())
                            elif inits:
                                inferred_types.extend(inits)
                            else:
                                continue
                        else:
                            inferred_types.append(inferred.repr_name())
                except astroid.InferenceError as e:
                    print(e)
                    continue

                logger.debug(f"Inferred types: {inferred_types}")

                # Check if any inferred type matches a valid class
                for cls in inferred_types:
                    if cls in valid_classes:
                        logger.debug(
                            f"Foud valid call: {caller.as_string()} at line {descendant.lineno}"
                        )
                        valid_calls.append(
                            (caller.as_string(), descendant.lineno, method_name, cls)
                        )

    return valid_calls


def check_for_initializations(caller: nodes.NodeNG, scope: nodes.NodeNG):
    inits: list[str] = []

    for assign in scope.nodes_of_class(nodes.Assign):
        if assign.targets[0].as_string() == caller.as_string() and isinstance(
            assign.value, nodes.Call
        ):
            if isinstance(assign.value.func, nodes.Name):
                inits.append(assign.value.func.name)

    return inits


def check_for_annotations(caller: nodes.NodeNG, scope: nodes.NodeNG):
    if not isinstance(scope, nodes.FunctionDef):
        return None

    hint = None
    logger.debug(f"annotations: {scope.args}")

    args = scope.args.args
    anns = scope.args.annotations
    if args and anns:
        for arg, ann in zip(args, anns):
            if arg.name == caller.as_string() and ann:
                hint = ann
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
        self.transformer: CallTransformer = None  # type: ignore

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,
        smell: MIMSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        self.target_line = smell.occurences[0].line
        self.target_file = target_file

        print("smell:", smell)

        if not smell.obj:
            raise TypeError("No method object found")

        self.mim_method_class, self.mim_method = smell.obj.split(".")
        self.valid_classes.add(self.mim_method_class)

        source_code = target_file.read_text()
        tree = MetadataWrapper(cst.parse_module(source_code))

        # Find all subclasses of the target class
        self._find_subclasses(source_dir)

        modified_tree = tree.visit(self)
        target_file.write_text(modified_tree.code)

        self.transformer = CallTransformer(self.mim_method_class)

        self.traverse_and_process(source_dir)
        if not overwrite:
            output_file.write_text(target_file.read_text())

    def _find_subclasses(self, directory: Path):
        """Find all subclasses of the target class within the file."""

        def get_subclasses(tree: nodes.Module):
            subclasses: set[str] = set()
            for klass in tree.nodes_of_class(nodes.ClassDef):
                if any(base == self.mim_method_class for base in klass.basenames):
                    if not any(method.name == self.mim_method for method in klass.mymethods()):
                        subclasses.add(klass.name)
            return subclasses

        logger.debug("find all subclasses")
        self.traverse(directory)
        for file in self.py_files:
            tree = astroid.parse(file.read_text())
            self.valid_classes = self.valid_classes.union(get_subclasses(tree))
        logger.debug(f"valid classes: {self.valid_classes}")

    def _process_file(self, file: Path):
        processed = False

        source_code = file.read_text("utf-8")

        astroid_tree = astroid.parse(source_code)
        valid_calls = find_valid_method_calls(astroid_tree, self.mim_method, self.valid_classes)
        self.transformer.set_calls(valid_calls)

        tree = MetadataWrapper(cst.parse_module(source_code))
        modified_tree = tree.visit(self.transformer)

        if self.transformer.transformed:
            file.write_text(modified_tree.code)
            if not file.samefile(self.target_file):
                processed = True
            self.transformer.transformed = False

        return processed

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
