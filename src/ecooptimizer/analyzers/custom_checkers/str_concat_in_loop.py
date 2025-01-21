from pathlib import Path
import re
import astroid
from astroid import nodes
import logging

import astroid.util

from ...utils.analyzers_config import CustomSmell
from ...data_wrappers.occurence import BasicOccurence
from ...data_wrappers.smell import SCLSmell


class StringConcatInLoopChecker:
    def __init__(self, filename: Path):
        super().__init__()
        self.filename = filename
        self.smells: list[SCLSmell] = []
        self.in_loop_counter = 0
        # self.current_semlls = { var_name : ( index of smell, index of loop )}
        self.current_smells: dict[str, tuple[int, int]] = {}
        self.current_loops: list[nodes.NodeNG] = []
        self.referenced = False

        logging.debug("Starting string concat checker")

        self.check_string_concatenation()

    def check_string_concatenation(self):
        logging.debug("Parsing astroid node")
        node = astroid.parse(self._transform_augassign_to_assign(self.filename.read_text()))
        logging.debug("Start iterating through nodes")
        for child in node.get_children():
            self._visit(child)

    def _create_smell(self, node: nodes.Assign):
        if node.lineno and node.col_offset:
            self.smells.append(
                {
                    "path": str(self.filename),
                    "module": self.filename.name,
                    "obj": None,
                    "type": "performance",
                    "symbol": "",
                    "message": "String concatenation inside loop detected",
                    "messageId": CustomSmell.STR_CONCAT_IN_LOOP,
                    "confidence": "UNDEFINED",
                    "occurences": [self._create_smell_occ(node)],
                    "additionalInfo": {
                        "outerLoopLine": self.current_smells[node.targets[0].as_string()][1],
                    },
                }
            )

    def _create_smell_occ(self, node: nodes.Assign | nodes.AugAssign) -> BasicOccurence:
        return {
            "line": node.fromlineno,
            "endLine": node.tolineno,
            "column": node.col_offset,  # type: ignore
            "endColumn": node.end_col_offset,
        }

    def _visit(self, node: nodes.NodeNG):
        logging.debug(f"visiting node {type(node)}")
        logging.debug(f"loops: {self.in_loop_counter}")

        if isinstance(node, (nodes.For, nodes.While)):
            logging.debug("in loop")
            self.in_loop_counter += 1
            self.current_loops.append(node)
            logging.debug(f"node body {node.body}")
            for stmt in node.body:
                self._visit(stmt)

            self.in_loop_counter -= 1

            self.current_smells = {
                key: val
                for key, val in self.current_smells.items()
                if val[1] != self.in_loop_counter
            }
            self.current_loops.pop()

        elif self.in_loop_counter > 0 and isinstance(node, nodes.Assign):
            target = None
            value = None
            logging.debug("in Assign")
            logging.debug(node.as_string())
            logging.debug(f"loops: {self.in_loop_counter}")

            if len(node.targets) == 1 > 1:
                return

            target = node.targets[0]
            value = node.value

            if target and isinstance(value, nodes.BinOp) and value.op == "+":
                logging.debug("Checking conditions")
                if (
                    target.as_string() not in self.current_smells
                    and self._is_string_type(node)
                    and self._is_concatenating_with_self(value, target)
                    and self._is_not_referenced(node)
                ):
                    logging.debug(f"Found a smell {node}")
                    self.current_smells[target.as_string()] = (
                        len(self.smells),
                        self.in_loop_counter - 1,
                    )
                    self._create_smell(node)
                elif target.as_string() in self.current_smells and self._is_concatenating_with_self(
                    value, target
                ):
                    smell_id = self.current_smells[target.as_string()][0]
                    logging.debug(
                        f"Related to smell at line {self.smells[smell_id]['occurences'][0]['line']}"
                    )
                    self.smells[smell_id]["occurences"].append(self._create_smell_occ(node))
        else:
            for child in node.get_children():
                self._visit(child)

    def _is_not_referenced(self, node: nodes.Assign):
        logging.debug("Checking if referenced")
        loop_source_str = self.current_loops[-1].as_string()
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
            elif isinstance(
                inferred.repr_name(), astroid.util.UninferableBase
            ) and self._has_str_vars(node.value):
                return True

        return False

    def _is_concatenating_with_self(self, binop_node: nodes.BinOp, target: nodes.NodeNG):
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

    def _has_str_vars(self, node: nodes.NodeNG):
        logging.debug("Checking if has string variables")
        binops = self._find_all_binops(node)
        for binop in binops:
            inferred_types = binop.left.infer()

            for inferred in inferred_types:
                logging.debug(f"inferred type '{type(inferred.repr_name())}'")

                if inferred.repr_name() == "str":
                    return True

        return False

    def _find_all_binops(self, node: nodes.NodeNG):
        binops: list[nodes.BinOp] = []
        for child in node.get_children():
            if isinstance(child, astroid.BinOp):
                binops.append(child)
                # Recursively search within the current BinOp
                binops.extend(self._find_all_binops(child))
            else:
                # Continue searching in non-BinOp children
                binops.extend(self._find_all_binops(child))
        return binops

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
