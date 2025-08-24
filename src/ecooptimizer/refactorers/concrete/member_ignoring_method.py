import re
import astroid
from astroid import nodes, util
import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper

from pathlib import Path
from dataclasses import dataclass
import logging

from ecooptimizer.refactorers.multi_file_refactorer import MultiFileRefactorer
from ecooptimizer.data_types.smell import MIMSmell

logger = logging.getLogger("refactor")


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


def import_resolves_to_class(
    importing_module: str, import_stmt: str, full_class_path: str, target_cls: str
) -> bool:
    """
    Determine if an import statement resolves to a specific class.

    Args:
        importing_module: full dot-separated path of the module doing the import
        import_stmt: the import statement string (e.g., "import x.y as z" or "from ..x.y import A, B")
        full_class_path: full dot-separated path to the intended class (e.g., "mypkg.subpkg.module.MyClass")

    Returns:
        True if the import resolves to the target class, False otherwise.
    """

    logger.debug(
        f"import_resolves_to_class: importing_module={importing_module}, import_stmt={import_stmt}, full_class_path={full_class_path}"
    )

    importing_parts = importing_module.split(".")

    logger.debug(
        f"target_module_path={full_class_path}, target_cls={target_cls}, importing_parts={importing_parts}"
    )

    import_stmt = import_stmt.strip()

    # Handle "import x.y [as z], ..." style
    m_import = re.match(r"import\s+(.+)$", import_stmt)
    if m_import:
        modules = [m.strip() for m in m_import.group(1).split(",")]
        logger.debug(f"import style: modules={modules}")
        for mod in modules:
            # Remove optional alias
            mod_name = mod.split(" as ")[0].strip()
            resolved_name = mod_name.split(".")[-1]
            logger.debug(f"Checking mod_name={mod_name}, resolved_name={resolved_name}")
            if mod_name == full_class_path and resolved_name == target_cls:
                logger.debug("Matched import style")
                return True
        return False

    # Handle "from x.y import A, B as C, ..." style
    m_from = re.match(r"from\s+([.\w]+)\s+import\s+(.+)$", import_stmt)
    if m_from:
        module_part, imported_part = m_from.groups()
        logger.debug(f"from-import style: module_part={module_part}, imported_part={imported_part}")

        # Resolve relative imports
        if module_part.startswith("."):
            leading_dots = len(module_part) - len(module_part.lstrip("."))
            relative_module = module_part.lstrip(".")
            logger.debug(
                f"Relative import: leading_dots={leading_dots}, relative_module={relative_module}"
            )
            if leading_dots > len(importing_parts) - 1:
                logger.debug("Relative import goes beyond top-level")
                return False  # relative import goes beyond top-level
            resolved_module_parts = importing_parts[:-leading_dots]
            if relative_module:
                resolved_module_parts += relative_module.split(".")
            resolved_module_path = ".".join(resolved_module_parts)
        else:
            resolved_module_path = module_part

        logger.debug(f"Resolved module path: {resolved_module_path}")

        # Check all imported names
        imported_names = [i.split(" as ")[0].strip() for i in imported_part.split(",")]
        logger.debug(f"Imported names: {imported_names}")
        for name in imported_names:
            logger.debug(f"Checking name={name} against target_cls={target_cls}")
            if resolved_module_path == full_class_path and name == target_cls:
                logger.debug("Matched from-import style")
                return True
        return False

    # Not a recognized import statement
    logger.debug("Not a recognized import statement")
    return False


def find_valid_method_calls(
    module_path: str,
    tree: nodes.Module,
    mim_method: str,
    valid_classes: dict[str, str],
) -> list[MethodCall]:
    """
    Finds method calls where the instance is of a valid class **and** the module
    imports that class.
    """
    valid_calls: list[MethodCall] = []

    logger.debug(
        f"Scanning module {module_path} for calls to {mim_method} in valid classes: {valid_classes}"
    )

    for node in tree.body:
        for descendant in node.nodes_of_class(nodes.Call):
            if not isinstance(descendant.func, nodes.Attribute):
                continue

            caller_node = descendant.func.expr
            method_name = descendant.func.attrname

            if method_name != mim_method:
                continue

            logger.debug(
                f"Found call to {method_name} at line {descendant.lineno}: {descendant.as_string()}"
            )

            # --- Step 1: infer the caller's class ---
            inferred_types: list[str] = []
            try:
                inferrences = caller_node.infer()
                for inferred in inferrences:
                    if isinstance(inferred, util.UninferableBase):
                        logger.debug(
                            f"Uninferable type for {caller_node.as_string()} at line {descendant.lineno}"
                        )
                        hint = check_for_annotations(caller_node, descendant.scope())
                        inits = check_for_initializations(caller_node, descendant.scope())
                        if hint:
                            logger.debug(f"Type hint found: {hint.as_string()}")
                            inferred_types.append(hint.as_string())
                        elif inits:
                            logger.debug(f"Initializations found: {inits}")
                            inferred_types.extend(inits)
                    else:
                        logger.debug(f"Inferred type: {inferred.repr_name()}")
                        inferred_types.append(inferred.repr_name())
            except astroid.InferenceError:
                logger.debug(
                    f"InferenceError for {caller_node.as_string()} at line {descendant.lineno}"
                )
                continue

            # --- Step 2: filter to valid classes ---
            class_module, cls_name = ("", "")
            for cls in inferred_types:
                class_module = valid_classes.get(cls, "")
                if class_module:
                    cls_name = cls

            if not class_module:
                logger.debug(f"No valid class found for inferred types: {inferred_types}")
                continue

            logger.debug(f"Valid class found: {cls_name} (module: {class_module})")

            # --- Step 3: check module-level imports for this specific class ---
            scope_node = descendant.scope()
            scope_from = getattr(scope_node, "fromlineno", 1) or 1
            scope_to = getattr(scope_node, "tolineno", 10**9) or 10**9

            def _iter_scope_imports(scope: nodes.NodeNG):
                # only direct children of this scope
                for stmt in getattr(scope, "body", []) or []:
                    if isinstance(stmt, nodes.Import | nodes.ImportFrom):
                        yield stmt

            logger.debug(f"Comparing class mod: {class_module} vs mod path: {module_path}")
            if class_module != module_path:
                imports = []

                # climb scopes until module scope to check for local imports
                imported = False
                scope = scope_node
                while scope:
                    logger.debug(f"Checking scope: {scope.__repr__()}")
                    for imp in _iter_scope_imports(scope):
                        if isinstance(imp, nodes.Import):
                            for name, asname in imp.names:
                                logger.debug(f"Checking Import: {imp.as_string()} for {cls_name}")
                                if (asname or name.split(".")[-1]) == cls_name:
                                    imported = True
                                    imports.append(imp.as_string())
                        else:
                            mod = imp.modname or ""
                            for name, asname in imp.names:
                                logger.debug(
                                    f"Checking ImportFrom: {imp.as_string()} for {cls_name}"
                                )
                                if (asname or name) == cls_name:
                                    imported = True
                                    imports.append(imp.as_string())
                    if isinstance(scope, nodes.Module):
                        break
                    scope = scope.parent

                if not imported:
                    logger.debug(f"No import found for class {cls_name} in module {module_path}")
                    continue

                logger.debug(f"Imports found for {cls_name}: {imports}")

                for imp in imports:
                    if import_resolves_to_class(module_path, imp, class_module, cls_name):
                        logger.debug(f"Import resolves to class: {imp}")
                        valid_calls.append(
                            MethodCall(
                                caller_node.as_string(),
                                descendant.lineno,
                                method_name,
                                cls_name,
                                scope_from,
                                scope_to,
                            )
                        )
                        break
                    else:
                        logger.debug(f"Import does not resolve to class: {imp}")

            else:
                valid_calls.append(
                    MethodCall(
                        caller_node.as_string(),
                        descendant.lineno,
                        method_name,
                        cls_name,
                        scope_from,
                        scope_to,
                    )
                )

    logger.debug(f"Total valid calls found: {len(valid_calls)}")
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
        self.rel_path: Path | None = None
        self.target_line = None
        self.cls_module = ""
        self.mim_method_class = ""
        self.mim_method = ""
        self.valid_classes: dict[str, str] = dict()
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
        self.source_dir = source_dir
        self.cls_module = smell.module

        if not smell.obj:
            raise TypeError("No method object found")

        self.mim_method_class, self.mim_method = smell.obj.split(".")
        self.valid_classes[self.mim_method_class] = smell.module

        source_code = target_file.read_text()
        tree = MetadataWrapper(cst.parse_module(source_code))

        # Find all subclasses of the target class
        self._find_subclasses(source_dir)

        modified_tree = tree.visit(self)

        root_idx = target_file.parts.index(source_dir.name)
        rel_path = Path(*target_file.parts[root_idx:])
        print("rel_path:", rel_path)
        self.store_original(target_file, rel_path, smell.id)

        target_file.write_text(modified_tree.code)
        self.modified_files.append(target_file)

        self.transformer = CallTransformer(self.mim_method_class)

        self.traverse_and_process(source_dir, smell.id)
        if not overwrite:
            output_file.write_text(target_file.read_text())

    def _make_relative_module_str(self, module_path: Path):
        logger.debug(f"Formating module path: {module_path}")
        mod_parts = module_path.parts
        try:
            idx_pckg = mod_parts.index(self.cls_module.split(".")[0])
        except ValueError:
            logger.error("Module not found in path")
            return
        return ".".join(mod_parts[idx_pckg:]).rstrip(".py")

    def _find_subclasses(self, directory: Path):
        """Find all subclasses of the target class within the file."""

        def get_subclasses(path: str, tree: nodes.Module):
            subclasses: dict[str, str] = dict()
            for klass in tree.nodes_of_class(nodes.ClassDef):
                if any(base == self.mim_method_class for base in klass.basenames):
                    if not any(method.name == self.mim_method for method in klass.mymethods()):
                        subclasses[klass.name] = path
            return subclasses

        logger.debug("find all subclasses")
        self.traverse(directory)
        for file in self.py_files:
            logger.debug(f"Parsing {file}")
            tree = astroid.parse(file.read_text())
            module_str = self._make_relative_module_str(file)
            if module_str:
                self.valid_classes.update(get_subclasses(module_str, tree))
        logger.debug(f"valid classes: {self.valid_classes}")

    def _process_file(self, file: Path, smell_id: str):
        processed = False

        source_code = file.read_text("utf-8")

        astroid_tree = astroid.parse(source_code)
        module_str = self._make_relative_module_str(file) or ".".join(file.parts).rstrip(".py")
        valid_calls = find_valid_method_calls(
            module_str,
            astroid_tree,
            self.mim_method,
            self.valid_classes,
        )
        self.transformer.set_calls(valid_calls)

        tree = MetadataWrapper(cst.parse_module(source_code))
        modified_tree = tree.visit(self.transformer)

        if self.transformer.transformed:
            root_idx = self.target_file.parts.index(self.source_dir.name)
            rel_path = Path(*self.target_file.parts[root_idx:])
            print("rel_path:", rel_path)
            self.store_original(self.target_file, rel_path, smell_id)

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
