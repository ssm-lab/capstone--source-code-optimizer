from pathlib import Path
import re
from astroid import nodes, util, parse, AttributeInferenceError

from ...data_types.custom_fields import Occurence, SCLInfo
from ...data_types.smell import SCLSmell
from ...utils.smell_enums import CustomSmell


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
    # current_semlls = { var_name : ( index of smell, index of loop )}
    current_smells: dict[str, tuple[int, int]] = {}

    def create_smell(node: nodes.Assign):
        nonlocal current_loops, current_smells

        if node.lineno and node.col_offset:
            smells.append(
                SCLSmell(
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
            )

    def create_smell_occ(node: nodes.Assign | nodes.AugAssign) -> Occurence:
        return Occurence(
            line=node.lineno,  # type: ignore
            endLine=node.end_lineno,
            column=node.col_offset,  # type: ignore
            endColumn=node.end_col_offset,
        )

    def visit(node: nodes.NodeNG):
        nonlocal smells, in_loop_counter, current_loops, current_smells

        if isinstance(node, (nodes.For, nodes.While)):
            in_loop_counter += 1
            current_loops.append(node)
            for stmt in node.body:
                visit(stmt)

            in_loop_counter -= 1

            current_smells = {
                key: val for key, val in current_smells.items() if val[1] != in_loop_counter
            }
            current_loops.pop()

        elif in_loop_counter > 0 and isinstance(node, nodes.Assign):
            target = None
            value = None

            if len(node.targets) == 1 > 1:
                return

            target = node.targets[0]
            value = node.value

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
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
                    create_smell(node)
                elif target.as_string() in current_smells and is_concatenating_with_self(
                    value, target
                ):
                    smell_id = current_smells[target.as_string()][0]
                    smells[smell_id].occurences.append(create_smell_occ(node))
        else:
            for child in node.get_children():
                visit(child)

    def is_not_referenced(node: nodes.Assign):
        nonlocal current_loops

        loop_source_str = current_loops[-1].as_string()
        loop_source_str = loop_source_str.replace(node.as_string(), "", 1)
        lines = loop_source_str.splitlines()
        for line in lines:
            if (
                line.find(node.targets[0].as_string()) != -1
                and re.search(rf"\b{re.escape(node.targets[0].as_string())}\b\s*=", line) is None
            ):
                return False
        return True

    def is_concatenating_with_self(binop_node: nodes.BinOp, target: nodes.NodeNG):
        """Check if the BinOp node includes the target variable being added."""

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
        return is_same_variable(left, target) or is_same_variable(right, target)

    def is_string_type(node: nodes.Assign) -> bool:
        target = node.targets[0]

        # Check type hints first
        if has_type_hints_str(node, target):
            return True

        # Infer types
        for inferred in target.infer():
            if inferred.repr_name() == "str":
                return True
            if isinstance(inferred, util.UninferableBase):
                print(f"here: {node}")
                if has_str_format(node.value) or has_str_interpolation(node.value):
                    return True
                for var in node.value.nodes_of_class(
                    (nodes.Name, nodes.Attribute, nodes.Subscript)
                ):
                    if var.as_string() == target.as_string():
                        for inferred_target in var.infer():
                            if inferred_target.repr_name() == "str":
                                return True

                    print(f"Checking type hints for {var}")
                    if has_type_hints_str(node, var):
                        return True

        return False

    def has_type_hints_str(context: nodes.NodeNG, target: nodes.NodeNG) -> bool:
        """Checks if a variable has an explicit type hint for `str`"""
        parent = context.scope()

        # Function argument type hints
        if isinstance(parent, nodes.FunctionDef) and parent.args.args:
            for arg, ann in zip(parent.args.args, parent.args.annotations):
                print(f"arg: {arg}, target: {target}, ann: {ann}")
                if arg.name == target.as_string() and ann and ann.as_string() == "str":
                    return True

            # Class attributes (annotations in class scope or __init__)
            if "self." in target.as_string():
                class_def = parent.frame()
                if not isinstance(class_def, nodes.ClassDef):
                    class_def = next(
                        (
                            ancestor
                            for ancestor in context.node_ancestors()
                            if isinstance(ancestor, nodes.ClassDef)
                        ),
                        None,
                    )

                if class_def:
                    attr_name = target.as_string().replace("self.", "")
                    try:
                        for attr in class_def.instance_attr(attr_name):
                            if (
                                isinstance(attr, nodes.AnnAssign)
                                and attr.annotation.as_string() == "str"
                            ):
                                return True
                            if any(inf.repr_name() == "str" for inf in attr.infer()):
                                return True
                    except AttributeInferenceError:
                        pass

        # Global/scope variable annotations before assignment
        for child in parent.nodes_of_class((nodes.AnnAssign, nodes.Assign)):
            if child == context:
                break
            if (
                isinstance(child, nodes.AnnAssign)
                and child.target.as_string() == target.as_string()
            ):
                return child.annotation.as_string() == "str"
            print("checking var types")
            if isinstance(child, nodes.Assign) and is_string_type(child):
                return True

        return False

    def has_str_format(node: nodes.NodeNG):
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("{.*}", str_repr)
            if match:
                return True

        return False

    def has_str_interpolation(node: nodes.NodeNG):
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("%[a-z]", str_repr)
            if match:
                return True
        return False

    def transform_augassign_to_assign(code_file: str):
        """
        Changes all AugAssign occurences to Assign in a code file.

        :param code_file: The source code file as a string
        :return: The same string source code with all AugAssign stmts changed to Assign
        """
        str_code = code_file.splitlines()

        for i in range(len(str_code)):
            eq_col = str_code[i].find(" +=")

            if eq_col == -1:
                continue

            target_var = str_code[i][0:eq_col].strip()

            # Replace '+=' with '=' to form an Assign string
            str_code[i] = str_code[i].replace("+=", f"= {target_var} +", 1)

        return "\n".join(str_code)

    # Change all AugAssigns to Assigns
    tree = parse(transform_augassign_to_assign(file_path.read_text()))

    # Start traversal
    for child in tree.get_children():
        visit(child)

    return smells
