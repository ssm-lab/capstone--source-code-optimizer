import logging
import re

from pathlib import Path
import astroid
from astroid import nodes

from .base_refactorer import BaseRefactorer
from ..data_types.smell import SCLSmell


class UseListAccumulationRefactorer(BaseRefactorer):
    """
    Refactorer that targets string concatenations inside loops
    """

    def __init__(self):
        super().__init__()
        self.target_lines: list[int] = []
        self.assign_var = ""
        self.last_assign_node: nodes.Assign | nodes.AugAssign = None  # type: ignore
        self.concat_nodes: list[nodes.Assign | nodes.AugAssign] = []
        self.reassignments: list[nodes.Assign] = []
        self.outer_loop_line: int = 0
        self.outer_loop: nodes.For | nodes.While = None  # type: ignore

    def reset(self):
        self.__init__()

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: SCLSmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactor string concatenations in loops to use list accumulation and join

        :param target_file: absolute path to source code
        :param smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_lines = [occ.line for occ in smell.occurences]

        if not smell.additionalInfo:
            raise RuntimeError("Missing additional info for 'string-concat-loop' smell")

        self.assign_var = smell.additionalInfo.concatTarget
        self.outer_loop_line = smell.additionalInfo.innerLoopLine

        logging.info(
            f"Applying 'Use List Accumulation' refactor on '{target_file.name}' at line {self.target_lines[0]} for identified code smell."
        )
        logging.debug(f"target_lines: {self.target_lines}")
        print(f"target_lines: {self.target_lines}")
        logging.debug(f"assign_var: {self.assign_var}")
        logging.debug(f"outer line: {self.outer_loop_line}")
        print(f"outer line: {self.outer_loop_line}")

        # Parse the code into an AST
        source_code = target_file.read_text()
        tree = astroid.parse(source_code)
        for node in tree.get_children():
            self.visit(node)

        if not self.outer_loop or len(self.concat_nodes) != len(self.target_lines):
            logging.error("Missing inner loop or concat nodes.")
            raise Exception("Missing inner loop or concat nodes.")

        self.find_reassignments()
        self.find_scope()

        temp_concat_nodes = [("concat", node) for node in self.concat_nodes]
        temp_reassignments = [("reassign", node) for node in self.reassignments]

        combined_nodes = temp_concat_nodes + temp_reassignments

        combined_nodes = sorted(
            combined_nodes,
            key=lambda x: x[1].lineno,  # type: ignore
            reverse=True,
        )

        modified_code = self.add_node_to_body(source_code, combined_nodes)

        temp_file_path = output_file

        temp_file_path.write_text(modified_code)
        if overwrite:
            target_file.write_text(modified_code)
        else:
            output_file.write_text(modified_code)

        self.modified_files.append(target_file)
        logging.info(f"Refactoring completed and saved to: {temp_file_path}")

    def visit(self, node: nodes.NodeNG):
        if isinstance(node, nodes.Assign) and node.lineno in self.target_lines:
            self.concat_nodes.append(node)
        elif isinstance(node, nodes.AugAssign) and node.lineno in self.target_lines:
            self.concat_nodes.append(node)
        elif isinstance(node, (nodes.For, nodes.While)) and node.lineno == self.outer_loop_line:
            self.outer_loop = node
            for child in node.get_children():
                self.visit(child)
        else:
            for child in node.get_children():
                self.visit(child)

    def find_reassignments(self):
        for node in self.outer_loop.nodes_of_class(nodes.Assign):
            for target in node.targets:
                if target.as_string() == self.assign_var and node.lineno not in self.target_lines:
                    self.reassignments.append(node)

        logging.debug(f"reassignments: {self.reassignments}")

    def find_last_assignment(self, scope_node: nodes.NodeNG):
        """Find the last assignment of the target variable within a given scope node."""
        last_assignment_node = None

        logging.debug("Finding last assignment node")
        # Traverse the scope node and find assignments within the valid range
        for node in scope_node.nodes_of_class((nodes.AugAssign, nodes.Assign)):
            logging.debug(f"node: {node.as_string()}")

            if isinstance(node, nodes.Assign):
                for target in node.targets:
                    if (
                        target.as_string() == self.assign_var
                        and node.lineno < self.outer_loop.lineno  # type: ignore
                    ):
                        if last_assignment_node is None:
                            last_assignment_node = node
                        elif node.lineno > last_assignment_node.lineno:  # type: ignore
                            last_assignment_node = node
            else:
                if (
                    node.target.as_string() == self.assign_var
                    and node.lineno < self.outer_loop.lineno  # type: ignore
                ):
                    if last_assignment_node is None:
                        last_assignment_node = node
                    elif node.lineno > last_assignment_node.lineno:  # type: ignore
                        last_assignment_node = node

        self.last_assign_node = last_assignment_node  # type: ignore
        logging.debug(f"last assign node: {self.last_assign_node}")

    def find_scope(self):
        """Locate the second innermost loop if nested, else find first non-loop function/method/module ancestor."""
        logging.debug("Finding scope")

        for node in self.outer_loop.node_ancestors():
            if isinstance(node, (nodes.For, nodes.While)):
                logging.debug(f"checking loop scope: {node.as_string()}")
                self.find_last_assignment(node)
                if not self.last_assign_node:
                    self.outer_loop = node
                else:
                    self.scope_node = node
                    break
            elif isinstance(node, (nodes.Module, nodes.FunctionDef, nodes.AsyncFunctionDef)):
                logging.debug(f"checking big dog scope: {node.as_string()}")
                self.find_last_assignment(node)
                self.scope_node = node
                break

        logging.debug("Finished scopping")

    def last_assign_is_referenced(self, search_area: str):
        logging.debug(f"search area: {search_area}")
        return (
            search_area.find(self.assign_var) != -1
            or isinstance(self.last_assign_node, nodes.AugAssign)
            or self.assign_var in self.last_assign_node.value.as_string()
        )

    def generate_temp_list_name(self, node: nodes.NodeNG):
        def _get_node_representation(node: nodes.NodeNG):
            """Helper function to get a string representation of a node."""
            if isinstance(node, astroid.Const):
                return str(node.value)
            if isinstance(node, astroid.Name):
                return node.name
            if isinstance(node, astroid.Attribute):
                return node.attrname
            if isinstance(node, astroid.Slice):
                lower = _get_node_representation(node.lower) if node.lower else ""
                upper = _get_node_representation(node.upper) if node.upper else ""
                step = _get_node_representation(node.step) if node.step else ""
                step_part = f"_step_{step}" if step else ""
                return f"{lower}_{upper}{step_part}"
            return "unknown"

        if isinstance(node, astroid.Subscript):
            # Extracting slice and value for a Subscript node
            slice_repr = _get_node_representation(node.slice)
            value_repr = _get_node_representation(node.value)
            custom_component = f"{value_repr}_at_{slice_repr}"
        elif isinstance(node, astroid.AssignAttr):
            # Extracting attribute name for an AssignAttr node
            attribute_name = node.attrname
            custom_component = attribute_name
        else:
            raise TypeError("Node must be either Subscript or AssignAttr.")

        return f"temp_{custom_component}"

    def add_node_to_body(self, code_file: str, nodes_to_change: list[tuple]):  # type: ignore
        """
        Add a new AST node
        """
        logging.debug("Adding new nodes")

        code_file_lines = code_file.splitlines()
        logging.debug(f"\n{code_file_lines}")

        list_name = self.assign_var

        if isinstance(self.concat_nodes[0], nodes.Assign) and not isinstance(
            self.concat_nodes[0].targets[0], nodes.AssignName
        ):
            list_name = self.generate_temp_list_name(self.concat_nodes[0].targets[0])
        elif isinstance(self.concat_nodes[0], nodes.AugAssign) and not isinstance(
            self.concat_nodes[0].target, nodes.AssignName
        ):
            list_name = self.generate_temp_list_name(self.concat_nodes[0].target)

        # -------------  ADD JOIN STATEMENT TO SOURCE ----------------

        join_line = f"{self.assign_var} = ''.join({list_name})"
        indent_lno: int = self.outer_loop.lineno - 1  # type: ignore
        join_lno: int = self.outer_loop.end_lineno  # type: ignore

        source_line = code_file_lines[indent_lno]
        outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

        code_file_lines.insert(join_lno, outer_scope_whitespace + join_line)

        def get_new_concat_line(concat_node: nodes.AugAssign | nodes.Assign):
            concat_line = ""
            if isinstance(concat_node, nodes.AugAssign):
                concat_line = f"{list_name}.append({concat_node.value.as_string()})"
            else:
                parts = re.split(
                    rf"\s*[+]*\s*\b{re.escape(self.assign_var)}\b\s*[+]*\s*",
                    concat_node.value.as_string(),
                )

                logging.debug(f"Parts: {parts}")

                if len(parts[0]) == 0:
                    concat_line = f"{list_name}.append({parts[1]})"
                elif len(parts[1]) == 0:
                    concat_line = f"{list_name}.insert(0, {parts[0]})"
                else:
                    concat_line = [
                        f"{list_name}.insert(0, {parts[0]})",
                        f"{list_name}.append({parts[1]})",
                    ]
            return concat_line

        def get_new_reassign_line(reassign_node: nodes.Assign):
            if reassign_node.value.as_string() in ["''", "str()"]:
                return f"{list_name}.clear()"
            else:
                return f"{list_name} = [{reassign_node.value.as_string()}]"

        # -------------  REFACTOR CONCATS and REASSIGNS  ----------------------------

        for node in nodes_to_change:
            if node[0] == "concat":
                new_concat = get_new_concat_line(node[1])
                concat_lno = node[1].lineno - 1

                if isinstance(new_concat, list):
                    source_line = code_file_lines[concat_lno]
                    concat_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

                    code_file_lines.pop(concat_lno)
                    code_file_lines.insert(concat_lno, concat_whitespace + new_concat[1])
                    code_file_lines.insert(concat_lno, concat_whitespace + new_concat[0])
                else:
                    source_line = code_file_lines[concat_lno]
                    concat_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

                    code_file_lines.pop(concat_lno)
                    code_file_lines.insert(concat_lno, concat_whitespace + new_concat)
            else:
                new_reassign = get_new_reassign_line(node[1])
                reassign_lno = node[1].lineno - 1

                source_line = code_file_lines[reassign_lno]
                reassign_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

                code_file_lines.pop(reassign_lno)
                code_file_lines.insert(reassign_lno, reassign_whitespace + new_reassign)

        # -------------  INITIALIZE TARGET VAR AS A LIST  -------------
        if not self.last_assign_node or self.last_assign_is_referenced(
            "".join(code_file_lines[self.last_assign_node.lineno : self.outer_loop.lineno - 1])  # type: ignore
        ):
            logging.debug("Making list separate")
            list_lno: int = self.outer_loop.lineno - 1  # type: ignore

            source_line = code_file_lines[list_lno]
            outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            list_line = f"{list_name} = [{self.assign_var}]"

            code_file_lines.insert(list_lno, outer_scope_whitespace + list_line)
        elif (
            isinstance(self.concat_nodes[0], nodes.Assign)
            and not isinstance(self.concat_nodes[0].targets[0], nodes.AssignName)
        ) or (
            isinstance(self.concat_nodes[0], nodes.AugAssign)
            and not isinstance(self.concat_nodes[0].target, nodes.AssignName)
        ):
            list_lno: int = self.outer_loop.lineno - 1  # type: ignore

            source_line = code_file_lines[list_lno]
            outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            list_line = f"{list_name} = [{self.assign_var}]"

            code_file_lines.insert(list_lno, outer_scope_whitespace + list_line)

        elif self.last_assign_node.value.as_string() in ["''", "str()"]:
            logging.debug("Overwriting assign with list")
            list_lno: int = self.last_assign_node.lineno - 1  # type: ignore

            source_line = code_file_lines[list_lno]
            outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            list_line = f"{list_name} = []"

            code_file_lines.pop(list_lno)
            code_file_lines.insert(list_lno, outer_scope_whitespace + list_line)

        else:
            logging.debug(f"last assign value: {self.last_assign_node.value.as_string()}")
            list_lno: int = self.last_assign_node.lineno - 1  # type: ignore

            source_line = code_file_lines[list_lno]
            outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            list_line = f"{list_name} = [{self.last_assign_node.value.as_string()}]"

            code_file_lines.pop(list_lno)
            code_file_lines.insert(list_lno, outer_scope_whitespace + list_line)

        logging.debug("New Nodes added")

        return "\n".join(code_file_lines)
