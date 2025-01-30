import logging
from pathlib import Path
import re
from astroid import nodes, util, parse

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

        logging.debug(f"visiting node {type(node)}")
        logging.debug(f"loops: {in_loop_counter}")

        if isinstance(node, (nodes.For, nodes.While)):
            logging.debug("in loop")
            in_loop_counter += 1
            current_loops.append(node)
            logging.debug(f"node body {node.body}")
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
            logging.debug("in Assign")
            logging.debug(node.as_string())
            logging.debug(f"loops: {in_loop_counter}")

            if len(node.targets) == 1 > 1:
                return

            target = node.targets[0]
            value = node.value

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
                logging.debug("Checking conditions")
                if (
                    target.as_string() not in current_smells
                    and is_string_type(node)
                    and is_concatenating_with_self(value, target)
                    and is_not_referenced(node)
                ):
                    logging.debug(f"Found a smell {node}")
                    current_smells[target.as_string()] = (
                        len(smells),
                        in_loop_counter - 1,
                    )
                    create_smell(node)
                elif target.as_string() in current_smells and is_concatenating_with_self(
                    value, target
                ):
                    smell_id = current_smells[target.as_string()][0]
                    logging.debug(f"Related to smell at line {smells[smell_id].occurences[0].line}")
                    smells[smell_id].occurences.append(create_smell_occ(node))
        else:
            for child in node.get_children():
                visit(child)

    def is_not_referenced(node: nodes.Assign):
        nonlocal current_loops

        logging.debug("Checking if referenced")
        loop_source_str = current_loops[-1].as_string()
        loop_source_str = loop_source_str.replace(node.as_string(), "", 1)
        lines = loop_source_str.splitlines()
        logging.debug(lines)
        for line in lines:
            if (
                line.find(node.targets[0].as_string()) != -1
                and re.search(rf"\b{re.escape(node.targets[0].as_string())}\b\s*=", line) is None
            ):
                logging.debug(node.targets[0].as_string())
                logging.debug("matched")
                return False
        return True

    def is_string_type(node: nodes.Assign):
        logging.debug("checking if string")

        inferred_types = node.targets[0].infer()

        for inferred in inferred_types:
            logging.debug(f"inferred type '{type(inferred.repr_name())}'")

            if inferred.repr_name() == "str":
                return True
            elif isinstance(inferred.repr_name(), util.UninferableBase) and has_str_format(
                node.value
            ):
                return True
            elif isinstance(inferred.repr_name(), util.UninferableBase) and has_str_interpolation(
                node.value
            ):
                return True
            elif isinstance(inferred.repr_name(), util.UninferableBase) and has_str_vars(
                node.value
            ):
                return True

        return False

    def is_concatenating_with_self(binop_node: nodes.BinOp, target: nodes.NodeNG):
        """Check if the BinOp node includes the target variable being added."""
        logging.debug("checking that is valid concat")

        def is_same_variable(var1: nodes.NodeNG, var2: nodes.NodeNG):
            logging.debug(f"node 1: {var1}, node 2: {var2}")
            if isinstance(var1, nodes.Name) and isinstance(var2, nodes.AssignName):
                return var1.name == var2.name
            if isinstance(var1, nodes.Attribute) and isinstance(var2, nodes.AssignAttr):
                return var1.as_string() == var2.as_string()
            if isinstance(var1, nodes.Subscript) and isinstance(var2, nodes.Subscript):
                logging.debug(f"subscript value: {var1.value.as_string()}, slice {var1.slice}")
                if isinstance(var1.slice, nodes.Const) and isinstance(var2.slice, nodes.Const):
                    return var1.as_string() == var2.as_string()
            if isinstance(var1, nodes.BinOp) and var1.op == "+":
                return is_same_variable(var1.left, target) or is_same_variable(var1.right, target)
            return False

        left, right = binop_node.left, binop_node.right
        return is_same_variable(left, target) or is_same_variable(right, target)

    def has_str_format(node: nodes.NodeNG):
        logging.debug("Checking for str format")
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("{.*}", str_repr)
            logging.debug(match)
            if match:
                return True

        return False

    def has_str_interpolation(node: nodes.NodeNG):
        logging.debug("Checking for str interpolation")
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("%[a-z]", str_repr)
            logging.debug(match)
            if match:
                return True

        return False

    def has_str_vars(node: nodes.NodeNG):
        logging.debug("Checking if has string variables")
        binops = find_all_binops(node)
        for binop in binops:
            inferred_types = binop.left.infer()

            for inferred in inferred_types:
                logging.debug(f"inferred type '{type(inferred.repr_name())}'")

                if inferred.repr_name() == "str":
                    return True

        return False

    def find_all_binops(node: nodes.NodeNG):
        binops: list[nodes.BinOp] = []
        for child in node.get_children():
            if isinstance(child, nodes.BinOp):
                binops.append(child)
                # Recursively search within the current BinOp
                binops.extend(find_all_binops(child))
            else:
                # Continue searching in non-BinOp children
                binops.extend(find_all_binops(child))
        return binops

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

        logging.debug("\n".join(str_code))
        return "\n".join(str_code)

    # Change all AugAssigns to Assigns
    tree = parse(transform_augassign_to_assign(file_path.read_text()))

    # Start traversal
    for child in tree.get_children():
        visit(child)

    return smells
