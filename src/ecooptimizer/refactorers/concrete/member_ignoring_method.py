import astroid
from astroid import nodes, util
import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper

from pathlib import Path
from dataclasses import dataclass

from ecooptimizer.log_config import CONFIG

from ecooptimizer.refactorers.multi_file_refactorer import MultiFileRefactorer
from ecooptimizer.data_types.smell import MIMSmell

logger = CONFIG["refactorLogger"]


@dataclass
class MethodCall:
    """Represents a detected method call to be refactored."""

    caller: str
    lineno: int
    method_name: str
    cls_name: str
    scope_from: int
    scope_to: int

    def __eq__(self, other):  # noqa: ANN001
        if not isinstance(other, MethodCall):
            return NotImplemented
        return (
            self.caller == other.caller
            and self.lineno == other.lineno
            and self.method_name == other.method_name
            and self.cls_name == other.cls_name
            and self.scope_from == other.scope_from
            and self.scope_to == other.scope_to
        )

    def __hash__(self):
        return hash(
            (
                self.caller,
                self.lineno,
                self.method_name,
                self.cls_name,
                self.scope_from,
                self.scope_to,
            )
        )


@dataclass
class CallSite:
    """Represents a call site affected by the refactor."""

    var: str
    scope_from: int
    scope_to: int
    obj_class: str

    def __eq__(self, other):  # noqa: ANN001
        if not isinstance(other, CallSite):
            return NotImplemented
        return (
            self.var == other.var
            and self.scope_from == other.scope_from
            and self.scope_to == other.scope_to
            and self.obj_class == other.obj_class
        )

    def __hash__(self):
        return hash((self.var, self.scope_from, self.scope_to, self.obj_class))


class CallTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, class_name: str):
        self.method_calls: list[MethodCall] = None  # type: ignore
        self.class_name = class_name
        self.transformed = False
        self.affected_vars: set[str] = set()
        self.affected_call_sites: set[CallSite] = set()

    def set_calls(self, valid_calls: list[MethodCall]):
        self.method_calls = valid_calls

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Transform instance calls to static calls if they match."""
        if isinstance(original_node.func, cst.Attribute):
            caller = original_node.func.value
            method = original_node.func.attr.value
            position = self.get_metadata(PositionProvider, original_node, None)

            if not position:
                raise TypeError("What do you mean you can't find the position?")

            for mcall in self.method_calls:
                logger.debug(f"cst caller: {mcall.caller} at line {position.start.line}")
                if (
                    method == mcall.method_name
                    and position.start.line == mcall.lineno
                    and caller.deep_equals(cst.parse_expression(mcall.caller))
                ):
                    logger.debug("transforming")
                    if isinstance(caller, cst.Name):
                        self.affected_vars.add(caller.value)
                        self.affected_call_sites.add(
                            CallSite(caller.value, mcall.scope_from, mcall.scope_to, mcall.cls_name)
                        )

                    new_func = cst.Attribute(
                        value=cst.Name(mcall.cls_name),
                        attr=original_node.func.attr,
                    )
                    self.transformed = True
                    return updated_node.with_changes(func=new_func)

        return updated_node


def find_valid_method_calls(
    tree: nodes.Module, mim_method: str, valid_classes: set[str]
) -> list[MethodCall]:
    """
    Finds method calls where the instance is of a valid class.

    Returns:
        A list of (caller_name, line_number, method_name, class_name, scope_from, scope_to).
    """
    valid_calls: list[MethodCall] = []

    logger.debug("Finding valid method calls")

    for node in tree.body:
        for descendant in node.nodes_of_class(nodes.Call):
            if isinstance(descendant.func, nodes.Attribute):
                logger.debug(f"caller: {descendant.func.expr.as_string()}")
                caller = descendant.func.expr
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

                scope_node = descendant.scope()
                scope_from = getattr(scope_node, "fromlineno", 1) or 1
                scope_to = getattr(scope_node, "tolineno", 10**9) or 10**9

                # Check if any inferred type matches a valid class
                for cls in inferred_types:
                    if cls in valid_classes:
                        logger.debug(
                            f"Found valid call: {caller.as_string()} at line {descendant.lineno}"
                        )
                        valid_calls.append(
                            MethodCall(
                                caller.as_string(),
                                descendant.lineno,  # type: ignore
                                method_name,
                                cls,
                                scope_from,
                                scope_to,
                            )  # CHANGED
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

    def __init__(self, patterns_to_exclude: set[str] | None = None):
        super().__init__(patterns_to_exclude)
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
            logger.debug(f"Parsing {file}")
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

            self._remove_useless_inits(
                file,
                self.transformer.affected_call_sites,  # (var, scope_from, scope_to, call_line, cls)
            )

            if not file.samefile(self.target_file):
                processed = True

            self.transformer.transformed = False
            self.transformer.affected_vars.clear()
            self.transformer.affected_call_sites.clear()

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

    def _remove_useless_inits(
        self,
        file: Path,
        call_sites: set[CallSite],
    ):
        if not call_sites:
            return

        code_after = file.read_text("utf-8")
        tree = astroid.parse(code_after)

        # Decide which assignment lines to remove
        inits_to_remove: set[int] = set()

        for cs in call_sites:
            # 1) Check for any references to `var` in the same scope (excluding AssignName).
            #    We treat any nodes.Name with the same name within [scope_from, scope_to] as a reference.
            any_refs = False
            for name_node in tree.nodes_of_class(nodes.Name):
                if (
                    name_node.name == cs.var
                    and (getattr(name_node, "lineno", 0) or 0) >= cs.scope_from
                    and (getattr(name_node, "lineno", 0) or 0) <= cs.scope_to
                ):
                    any_refs = True
                    break

            if any_refs:
                continue  # some use of var remains in this scope → keep init

            # Collect simple assignments like `var = ClassName()` and annotated `var: T = ClassName()`
            for assign in tree.nodes_of_class((nodes.Assign, nodes.AnnAssign)):
                if not (cs.scope_from <= (assign.fromlineno or 0) <= cs.scope_to):
                    continue

                if isinstance(assign, nodes.Assign):
                    tgt = assign.targets[0]
                else:
                    tgt = assign.target

                if not isinstance(tgt, nodes.AssignName):
                    continue

                if tgt.name != cs.var:
                    continue

                if isinstance(assign.value, nodes.Call) and isinstance(
                    assign.value.func, nodes.Name
                ):
                    if assign.value.func.name == cs.obj_class:
                        inits_to_remove.add(assign.fromlineno)

        if not inits_to_remove:
            return

        class InitRemover(cst.CSTTransformer):
            METADATA_DEPENDENCIES = (PositionProvider,)

            def __init__(self, lines_to_remove: set[int]):
                self.lines_to_remove = lines_to_remove

            def leave_SimpleStatementLine(
                self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
            ):
                pos = self.get_metadata(PositionProvider, original_node, None)
                if not pos:
                    return updated_node
                start_line = pos.start.line
                if start_line not in self.lines_to_remove:
                    return updated_node

                # Be conservative: ensure it's an Assign or AnnAssign to a Name target matching the recorded line.
                if len(original_node.body) != 1:
                    return updated_node
                body0 = original_node.body[0]
                if isinstance(body0, cst.Assign):
                    if len(body0.targets) == 1 and isinstance(body0.targets[0].target, cst.Name):
                        return cst.RemoveFromParent()
                elif isinstance(body0, cst.AnnAssign):
                    if isinstance(body0.target, cst.Name):
                        return cst.RemoveFromParent()
                return updated_node

        wrapper = MetadataWrapper(cst.parse_module(code_after))
        new_mod = wrapper.visit(InitRemover(inits_to_remove))
        file.write_text(new_mod.code)
