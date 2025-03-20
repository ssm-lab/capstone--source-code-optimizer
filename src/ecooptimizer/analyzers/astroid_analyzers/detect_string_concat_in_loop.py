from pathlib import Path
import re
from typing import Any
from astroid import nodes, util, parse, AttributeInferenceError

from ...config import CONFIG
from ...data_types.custom_fields import Occurence, SCLInfo
from ...data_types.smell import SCLSmell
from ...utils.smell_enums import CustomSmell

logger = CONFIG["detectLogger"]


def detect_string_concat_in_loop(file_path: Path, tree: nodes.Module):
    """
    Detects string concatenation inside loops within a Python AST tree.

    Parameters:
        file_path (Path): The file path to analyze.
        tree (nodes.Module): The parsed AST tree of the Python code.

    Returns:
        list[dict]: A list of dictionaries containing details about detected string concatenation smells.
    """
    smells: list[SCLSmell] = []
    in_loop_counter = 0
    current_loops: list[nodes.NodeNG] = []
    current_smells: dict[str, tuple[int, int]] = {}

    logger.debug(f"Starting analysis of file: {file_path}")
    logger.debug(
        f"Initial state - smells: {smells}, in_loop_counter: {in_loop_counter}, current_loops: {current_loops}, current_smells: {current_smells}"
    )

    def create_smell(node: nodes.Assign):
        nonlocal current_loops, current_smells

        logger.debug(f"Creating smell for node: {node.as_string()}")
        if node.lineno and node.col_offset:
            smell = SCLSmell(
                path=str(file_path),
                module=file_path.name,
                obj=None,
                type="performance",
                symbol="string-concat-loop",
                message="String concatenation inside loop detected",
                messageId=CustomSmell.STR_CONCAT_IN_LOOP.value,
                confidence="UNDEFINED",
                occurences=[create_smell_occ(node)],
                additionalInfo=SCLInfo(
                    innerLoopLine=current_loops[
                        current_smells[node.targets[0].as_string()][1]
                    ].lineno,  # type: ignore
                    concatTarget=node.targets[0].as_string(),
                ),
            )
            smells.append(smell)
            logger.debug(f"Added smell: {smell}")

    def create_smell_occ(node: nodes.Assign | nodes.AugAssign) -> Occurence:
        logger.debug(f"Creating occurrence for node: {node.as_string()}")
        return Occurence(
            line=node.lineno,  # type: ignore
            endLine=node.end_lineno,
            column=node.col_offset,  # type: ignore
            endColumn=node.end_col_offset,
        )

    def visit(node: nodes.NodeNG):
        nonlocal smells, in_loop_counter, current_loops, current_smells

        logger.debug(f"Visiting node: {node.as_string()}")
        if isinstance(node, (nodes.For, nodes.While)):
            in_loop_counter += 1
            current_loops.append(node)
            logger.debug(
                f"Entered loop. in_loop_counter: {in_loop_counter}, current_loops: {current_loops}"
            )

            for stmt in node.body:
                visit(stmt)

            in_loop_counter -= 1
            logger.debug(f"Exited loop. in_loop_counter: {in_loop_counter}")

            current_smells = {
                key: val for key, val in current_smells.items() if val[1] != in_loop_counter
            }
            current_loops.pop()
            logger.debug(
                f"Updated current_smells: {current_smells}, current_loops: {current_loops}"
            )

        elif in_loop_counter > 0 and isinstance(node, nodes.Assign):
            target = None
            value = None

            if len(node.targets) != 1:
                logger.debug(f"Skipping node due to multiple targets: {node.as_string()}")
                return

            target = node.targets[0]
            value = node.value
            logger.debug(
                f"Processing assignment node. target: {target.as_string()}, value: {value.as_string()}"
            )

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
                logger.debug(
                    f"Found binary operation with '+' in loop. target: {target.as_string()}, value: {value.as_string()}"
                )
                if (
                    target.as_string() not in current_smells
                    and is_string_type(node)
                    and is_concatenating_with_self(value, target)
                    and is_not_referenced(node)
                ):
                    current_smells[target.as_string()] = (
                        len(smells),
                        in_loop_counter - 1,
                    )
                    logger.debug(f"Adding new smell to current_smells: {current_smells}")
                    create_smell(node)
                elif target.as_string() in current_smells and is_concatenating_with_self(
                    value, target
                ):
                    smell_id = current_smells[target.as_string()][0]
                    logger.debug(f"Updating existing smell with id: {smell_id}")
                    smells[smell_id].occurences.append(create_smell_occ(node))
        else:
            for child in node.get_children():
                visit(child)

    def is_not_referenced(node: nodes.Assign):
        nonlocal current_loops

        logger.debug(f"Checking if node is referenced: {node.as_string()}")
        loop_source_str = current_loops[-1].as_string()
        loop_source_str = loop_source_str.replace(node.as_string(), "", 1)
        lines = loop_source_str.splitlines()
        for line in lines:
            if (
                line.find(node.targets[0].as_string()) != -1
                and re.search(rf"\b{re.escape(node.targets[0].as_string())}\b\s*=", line) is None
            ):
                logger.debug(f"Node is referenced in line: {line}")
                return False
        logger.debug("Node is not referenced in loop")
        return True

    def is_concatenating_with_self(binop_node: nodes.BinOp, target: nodes.NodeNG):
        """Check if the BinOp node includes the target variable being added."""
        logger.debug(
            f"Checking if binop_node is concatenating with self: {binop_node.as_string()}, target: {target.as_string()}"
        )

        def is_same_variable(var1: nodes.NodeNG, var2: nodes.NodeNG):
            if isinstance(var1, nodes.Name) and isinstance(var2, nodes.AssignName):
                return var1.name == var2.name
            if isinstance(var1, nodes.Attribute) and isinstance(var2, nodes.AssignAttr):
                return var1.as_string() == var2.as_string()
            if isinstance(var1, nodes.Subscript) and isinstance(var2, nodes.Subscript):
                if isinstance(var1.slice, nodes.Const) and isinstance(var2.slice, nodes.Const):
                    return var1.as_string() == var2.as_string()
            if isinstance(var1, nodes.BinOp) and var1.op == "+":
                return is_same_variable(var1.left, target) or is_same_variable(var1.right, target)
            return False

        left, right = binop_node.left, binop_node.right
        logger.debug(f"Left: {left.as_string()}, Right: {right.as_string()}")
        return is_same_variable(left, target) or is_same_variable(right, target)

    def is_string_type(node: nodes.Assign, visited: set[str] | None = None) -> bool:
        """Check if assignment target is inferred to be string type."""
        if visited is None:
            visited = set()

        target = node.targets[0]
        target_name = target.as_string()

        if target_name in visited:
            logger.debug(f"Cycle detected for {target_name}")
            return False
        visited.add(target_name)

        logger.debug(f"Checking string type for {target_name}")

        # Check explicit type hints first
        if has_type_hints_str(node, target, visited):
            return True

        # Check string literals
        if isinstance(node.value, nodes.Const) and isinstance(node.value.value, str):
            logger.debug(f"String literal found: {node.as_string()}")
            return True

        # Check string operations
        if has_str_operation(node.value):
            logger.debug(f"String operation pattern found: {node.as_string()}")
            return True

        # Check inferred type
        try:
            inferred_types = list(node.value.infer())
        except util.InferenceError:
            inferred_types = [util.Uninferable]

        if not any(isinstance(t, util.UninferableBase) for t in inferred_types):
            return is_inferred_string(node, inferred_types)

        def get_top_level_rhs_vars(value: nodes.NodeNG) -> list[nodes.NodeNG]:
            """Get top-level variables from RHS expression."""
            if isinstance(value, nodes.BinOp):
                return get_top_level_rhs_vars(value.left) + get_top_level_rhs_vars(value.right)
            else:
                return [value]

        # Recursive check for RHS variables
        rhs_vars = get_top_level_rhs_vars(node.value)
        for rhs_node in rhs_vars:
            if isinstance(rhs_node, nodes.Const):
                if rhs_node.pytype() == "str":
                    logger.debug(f"String literal found in RHS: {rhs_node.as_string()}")
                    return True
                else:
                    return False
            if isinstance(rhs_node, nodes.Call):
                if rhs_node.func.as_string() == "str":
                    logger.debug(f"str() call found in RHS: {rhs_node.as_string()}")
                    return True
                else:
                    return False
            try:
                inferred_types = list(rhs_node.infer())
            except util.InferenceError:
                inferred_types = [util.Uninferable]

            if not any(isinstance(t, util.UninferableBase) for t in inferred_types):
                return is_inferred_string(rhs_node, inferred_types)
            var_name = rhs_node.as_string()
            if var_name == target_name:
                continue

            logger.debug(f"Checking RHS variable: {var_name}")
            if has_type_hints_str(node, rhs_node, visited):  # Pass new visited set
                return True

        return False

    def is_inferred_string(node: nodes.NodeNG, inferred_types: list[Any]) -> bool:
        if all(t.repr_name() == "str" for t in inferred_types):
            logger.debug(f"Definitively inferred as string: {node.as_string()}")
            return True
        else:
            logger.debug(f"Definitively non-string: {node.as_string()}")
            return False

    def has_type_hints_str(context: nodes.NodeNG, target: nodes.NodeNG, visited: set[str]) -> bool:
        """Check for string type hints with simplified subscript handling and scope-aware checks."""

        def check_annotation(annotation: nodes.NodeNG) -> bool:
            """Check if annotation is strictly a string type."""
            annotation_str = annotation.as_string()

            if re.search(r"(^|[^|\w])str($|[^|\w])", annotation_str):
                # Ensure it's not part of a union or optional
                if not re.search(r"\b(str\s*[|]\s*\w|\w\s*[|]\s*str)\b", annotation_str):
                    return True
            return False

        def is_allowed_target(node: nodes.NodeNG) -> bool:
            """Check if target matches allowed patterns:
            - self.var
            - self.var[subscript]
            - var[subscript]
            - simple_var
            """
            # Case 1: Simple Name (var)
            if isinstance(node, (nodes.AssignName, nodes.Name)):
                return True

            # Case 2: Direct self attribute (self.var)
            if isinstance(node, (nodes.AssignAttr, nodes.Attribute)):
                return (
                    node.attrname.count(".") == 0  # No nested attributes
                    and node.expr.as_string() == "self"  # Direct self attribute
                )

            # Case 3: Simple subscript (var[sub] or self.var[sub])
            if isinstance(node, nodes.Subscript):
                # Check base is allowed
                base = node.value
                return (
                    is_allowed_target(base)  # Base must be allowed target
                    and not has_nested_subscript(base)  # No nested subscripts
                )

            return False

        def has_nested_subscript(node: nodes.NodeNG) -> bool:
            """Check for nested subscript/attribute structures"""
            if isinstance(node, nodes.Subscript):
                return not is_allowed_target(node.value)
            if isinstance(node, nodes.Attribute):
                return node.expr.as_string() != "self"
            return False

        target_name = target.as_string()

        # First: Filter complex targets according to rules
        if not is_allowed_target(target):
            logger.debug(f"Skipping complex target: {target_name}")
            return False

        # Handle simple subscript case (single level)
        base_name = target.value.as_string() if isinstance(target, nodes.Subscript) else target_name
        parent = context.scope()

        # 1. Check function parameters
        if isinstance(parent, nodes.FunctionDef) and parent.args.args:
            for arg, ann in zip(parent.args.args, parent.args.annotations or []):
                if arg.name == base_name and ann and check_annotation(ann):
                    return True

        # 2. Check class attributes for self.* targets
        if target_name.startswith("self."):
            class_def = next(
                (n for n in context.node_ancestors() if isinstance(n, nodes.ClassDef)), None
            )
            if class_def:
                attr_name = target_name.split("self.", 1)[1].split("[")[0]
                try:
                    for attr in class_def.instance_attr(attr_name):
                        if isinstance(attr, nodes.AnnAssign) and check_annotation(attr.annotation):
                            return True
                        else:
                            try:
                                inferred_types = list(attr.infer())
                            except util.InferenceError:
                                inferred_types = [util.Uninferable]

                            if not any(isinstance(t, util.UninferableBase) for t in inferred_types):
                                return is_inferred_string(attr, inferred_types)
                            return has_type_hints_str(attr, target, visited)
                except AttributeInferenceError:
                    pass

        def get_ordered_scope_nodes(
            scope: nodes.NodeNG, target: nodes.NodeNG
        ) -> list[nodes.NodeNG]:
            """Get all nodes in scope in execution order, flattening nested blocks."""
            nodes_list = []
            for child in scope.body:
                # Recursively flatten block nodes (loops, ifs, etc)
                if child.lineno >= target.lineno:  # type: ignore
                    break
                if isinstance(child, (nodes.For, nodes.While, nodes.If)):
                    nodes_list.extend(get_ordered_scope_nodes(child, target))
                else:
                    nodes_list.append(child)
            return nodes_list

        try:
            current_lineno = target.lineno
            scope_nodes = get_ordered_scope_nodes(parent, target)

            for child in scope_nodes:
                if child.lineno >= current_lineno:  # type: ignore
                    break

                # Check AnnAssigns
                if isinstance(child, nodes.AnnAssign):
                    if (
                        isinstance(child.target, nodes.AssignName)
                        and child.target.name == target_name
                        and check_annotation(child.annotation)
                    ):
                        return True

            for child in scope_nodes:
                if child.lineno >= current_lineno:  # type: ignore
                    break

                # Check Assigns
                if isinstance(child, nodes.Assign):
                    if any(
                        isinstance(t, nodes.AssignName) and t.name == target_name
                        for t in child.targets
                    ):
                        if is_string_type(child, visited):
                            return True
        except (ValueError, AttributeError):
            pass

        return False

    def has_str_operation(node: nodes.NodeNG) -> bool:
        """Check for string-specific operations."""
        if isinstance(node, nodes.JoinedStr):
            logger.debug(f"Found f-string: {node.as_string()}")
            return True

        if isinstance(node, nodes.Call) and isinstance(node.func, nodes.Attribute):
            if node.func.attrname == "format":
                logger.debug(f"Found .format() call: {node.as_string()}")
                return True

        if isinstance(node, nodes.BinOp) and node.op == "%":
            logger.debug(f"Found % formatting: {node.as_string()}")
            return True

        return False

    def transform_augassign_to_assign(code_file: str):
        """
        Changes all AugAssign occurences to Assign in a code file.

        :param code_file: The source code file as a string
        :return: The same string source code with all AugAssign stmts changed to Assign
        """
        logger.debug("Transforming AugAssign to Assign in code file")
        str_code = code_file.splitlines()

        for i in range(len(str_code)):
            eq_col = str_code[i].find(" +=")

            if eq_col == -1:
                continue

            target_var = str_code[i][0:eq_col].strip()

            # Replace '+=' with '=' to form an Assign string
            str_code[i] = str_code[i].replace("+=", f"= {target_var} +", 1)
            logger.debug(f"Transformed line {i}: {str_code[i]}")

        return "\n".join(str_code)

    # Change all AugAssigns to Assigns
    logger.debug(f"Transforming AugAssign to Assign in file: {file_path}")
    tree = parse(transform_augassign_to_assign(file_path.read_text()))

    # Entry Point
    logger.debug("Starting AST traversal")
    for child in tree.get_children():
        visit(child)

    logger.debug(f"Analysis complete. Detected smells: {smells}")
    return smells
