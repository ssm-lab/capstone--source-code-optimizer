from pathlib import Path
import re
import astroid
from astroid import nodes
import logging

import astroid.util

from ...utils.analyzers_config import CustomSmell
from ...data_wrappers.smell import Smell


class StringConcatInLoopChecker:
    def __init__(self, filename: Path):
        super().__init__()
        self.filename = filename
        self.smells: list[Smell] = []
        self.in_loop_counter = 0

        logging.debug("Starting string concat checker")

        self.check_string_concatenation()

    def check_string_concatenation(self):
        logging.debug("Parsing astroid node")
        node = astroid.parse(self._transform_augassign_to_assign(self.filename.read_text()))
        logging.debug("Start iterating through nodes")
        for child in node.get_children():
            self._visit(child)

    def _create_smell(self, node: nodes.Assign | nodes.AugAssign):
        if node.lineno and node.col_offset:
            self.smells.append(
                {
                    "absolutePath": str(self.filename),
                    "column": node.col_offset,
                    "confidence": "UNDEFINED",
                    "endColumn": None,
                    "endLine": None,
                    "line": node.lineno,
                    "message": "String concatenation inside loop detected",
                    "messageId": CustomSmell.STR_CONCAT_IN_LOOP.value,
                    "module": self.filename.name,
                    "obj": "",
                    "path": str(self.filename),
                    "symbol": "string-concat-in-loop",
                    "type": "convention",
                }
            )

    def _visit(self, node: nodes.NodeNG):
        logging.debug(f"visiting node {type(node)}")

        if isinstance(node, (nodes.For, nodes.While)):
            logging.debug("in loop")
            self.in_loop_counter += 1
            print(f"node body {node.body}")
            for stmt in node.body:
                self._visit(stmt)

            self.in_loop_counter -= 1

        elif self.in_loop_counter > 0 and isinstance(node, nodes.Assign):
            target = None
            value = None
            logging.debug("in Assign")

            if len(node.targets) == 1:
                target = node.targets[0]
                value = node.value

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
                if self._is_string_type(node) and self._is_concatenating_with_self(value, target):
                    logging.debug(f"Found a smell {node}")
                    self._create_smell(node)

        else:
            for child in node.get_children():
                self._visit(child)

    def _is_string_type(self, node: nodes.Assign):
        logging.debug("checking if string")

        inferred_types = node.targets[0].infer()

        for inferred in inferred_types:
            logging.debug(f"inferred type '{type(inferred.repr_name())}'")

            if inferred.repr_name() == "str":
                return True
            elif isinstance(
                inferred.repr_name(), astroid.util.UninferableBase
            ) and self._has_str_format(node.value):
                return True
            elif isinstance(
                inferred.repr_name(), astroid.util.UninferableBase
            ) and self._has_str_interpolation(node.value):
                return True

        return False

    def _is_concatenating_with_self(self, binop_node: nodes.BinOp, target: nodes.NodeNG):
        """Check if the BinOp node includes the target variable being added."""
        logging.debug("checking that is valid concat")

        def is_same_variable(var1: nodes.NodeNG, var2: nodes.NodeNG):
            print(f"node 1: {var1}, node 2: {var2}")
            if isinstance(var1, nodes.Name) and isinstance(var2, nodes.AssignName):
                return var1.name == var2.name
            if isinstance(var1, nodes.Attribute) and isinstance(var2, nodes.AssignAttr):
                return (
                    var1.attrname == var2.attrname
                    and var1.expr.as_string() == var2.expr.as_string()
                )
            if isinstance(var1, nodes.Subscript) and isinstance(var2, nodes.Subscript):
                print(f"subscript value: {var1.value.as_string()}, slice {var1.slice}")
                if isinstance(var1.slice, nodes.Const) and isinstance(var2.slice, nodes.Const):
                    return (
                        var1.value.as_string() == var2.value.as_string()
                        and var1.slice.value == var2.slice.value
                    )
            if isinstance(var1, nodes.BinOp) and var1.op == "+":
                return is_same_variable(var1.left, target) or is_same_variable(var1.right, target)
            return False

        left, right = binop_node.left, binop_node.right
        return is_same_variable(left, target) or is_same_variable(right, target)

    def _has_str_format(self, node: nodes.NodeNG):
        logging.debug("Checking for str format")
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("{.*}", str_repr)
            logging.debug(match)
            if match:
                return True

        return False

    def _has_str_interpolation(self, node: nodes.NodeNG):
        logging.debug("Checking for str interpolation")
        if isinstance(node, nodes.BinOp) and node.op == "+":
            str_repr = node.as_string()
            match = re.search("%[a-z]", str_repr)
            logging.debug(match)
            if match:
                return True

        return False

    def _transform_augassign_to_assign(self, code_file: str):
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
