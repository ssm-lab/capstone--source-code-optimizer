import logging
import re

from pathlib import Path
import astroid
from astroid import nodes

from .base_refactorer import BaseRefactorer
from ..data_wrappers.smell import Smell
from ..testing.run_tests import run_tests


class UseListAccumulationRefactorer(BaseRefactorer):
    """
    Refactorer that targets string concatenations inside loops
    """

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.target_line = 0
        self.target_node: nodes.NodeNG | None = None
        self.assign_var = ""
        self.last_assign_node: nodes.Assign | nodes.AugAssign | None = None
        self.concat_node: nodes.Assign | nodes.AugAssign | None = None
        self.scope_node: nodes.NodeNG | None = None
        self.outer_loop: nodes.For | nodes.While | None = None

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Refactor string concatenations in loops to use list accumulation and join

        :param file_path: absolute path to source code
        :param pylint_smell: pylint code for smell
        :param initial_emission: inital carbon emission prior to refactoring
        """
        self.target_line = pylint_smell["line"]
        logging.info(
            f"Applying 'Use List Accumulation' refactor on '{file_path.name}' at line {self.target_line} for identified code smell."
        )

        # Parse the code into an AST
        source_code = file_path.read_text()
        tree = astroid.parse(source_code)
        for node in tree.get_children():
            self.visit(node)
        self.find_scope()
        modified_code = self.add_node_to_body(source_code)

        temp_file_path = self.temp_dir / Path(f"{file_path.stem}_SCLR_line_{self.target_line}.py")

        with temp_file_path.open("w") as temp_file:
            temp_file.write(modified_code)

        # Measure emissions of the modified code
        final_emission = self.measure_energy(temp_file_path)

        if not final_emission:
            # os.remove(temp_file_path)
            logging.info(
                f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring.\n"
            )
            return

        # Check for improvement in emissions
        if self.check_energy_improvement(initial_emissions, final_emission):
            # If improved, replace the original file with the modified content

            if run_tests() == 0:
                logging.info("All test pass! Functionality maintained.")
                # shutil.move(temp_file_path, file_path)
                logging.info(
                    f"Refactored 'String Concatenation in Loop' to 'List Accumulation and Join' on line {self.target_line} and saved.\n"
                )
                return

            logging.info("Tests Fail! Discarded refactored changes\n")

        else:
            logging.info(
                "No emission improvement after refactoring. Discarded refactored changes.\n"
            )

        # Remove the temporary file if no energy improvement or failing tests
        temp_file_path.unlink()

    def visit(self, node: nodes.NodeNG):
        if isinstance(node, nodes.Assign) and node.lineno == self.target_line:
            self.concat_node = node
            self.target_node = node.targets[0]
            self.assign_var = node.targets[0].as_string()
        elif isinstance(node, nodes.AugAssign) and node.lineno == self.target_line:
            self.concat_node = node
            self.target_node = node.target
            self.assign_var = node.target.as_string()
        else:
            for child in node.get_children():
                self.visit(child)

    def find_last_assignment(self, scope: nodes.NodeNG):
        """Find the last assignment of the target variable within a given scope node."""
        last_assignment_node = None

        logging.debug("Finding last assignment node")
        # Traverse the scope node and find assignments within the valid range
        for node in scope.nodes_of_class((nodes.AugAssign, nodes.Assign)):
            logging.debug(f"node: {node.as_string()}")

            if isinstance(node, nodes.Assign):
                for target in node.targets:
                    if (
                        target.as_string() == self.assign_var
                        and node.lineno < self.outer_loop.lineno  # type: ignore
                    ):
                        if last_assignment_node is None:
                            last_assignment_node = node
                        elif (
                            last_assignment_node is not None
                            and node.lineno > last_assignment_node.lineno  # type: ignore
                        ):
                            last_assignment_node = node
            else:
                if (
                    node.target.as_string() == self.assign_var
                    and node.lineno < self.outer_loop.lineno  # type: ignore
                ):
                    if last_assignment_node is None:
                        logging.debug(node)
                        last_assignment_node = node
                    elif (
                        last_assignment_node is not None
                        and node.lineno > last_assignment_node.lineno  # type: ignore
                    ):
                        logging.debug(node)
                        last_assignment_node = node

        self.last_assign_node = last_assignment_node
        logging.debug(f"last assign node: {self.last_assign_node}")
        logging.debug("Finished")

    def find_scope(self):
        """Locate the second innermost loop if nested, else find first non-loop function/method/module ancestor."""
        passed_inner_loop = False

        logging.debug("Finding scope")
        logging.debug(f"concat node: {self.concat_node}")

        if not self.concat_node:
            logging.error("Concat node is null")
            raise TypeError("Concat node is null")

        for node in self.concat_node.node_ancestors():
            if isinstance(node, (nodes.For, nodes.While)) and not passed_inner_loop:
                logging.debug(f"Passed inner loop: {node.as_string()}")
                passed_inner_loop = True
                self.outer_loop = node
            elif isinstance(node, (nodes.For, nodes.While)) and passed_inner_loop:
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

    def add_node_to_body(self, code_file: str):
        """
        Add a new AST node
        """
        logging.debug("Adding new nodes")
        if self.target_node is None:
            raise TypeError("Target node is None.")

        new_list_name = f"temp_concat_list_{self.target_line}"

        list_line = f"{new_list_name} = [{self.assign_var}]"
        join_line = f"{self.assign_var} = ''.join({new_list_name})"
        concat_line = ""

        if isinstance(self.concat_node, nodes.AugAssign):
            concat_line = f"{new_list_name}.append({self.concat_node.value.as_string()})"
        elif isinstance(self.concat_node, nodes.Assign):
            parts = re.split(
                rf"\s*[+]*\s*\b{re.escape(self.assign_var)}\b\s*[+]*\s*",
                self.concat_node.value.as_string(),
            )
            if len(parts[0]) == 0:
                concat_line = f"{new_list_name}.append({parts[1]})"
            elif len(parts[1]) == 0:
                concat_line = f"{new_list_name}.insert(0, {parts[0]})"
            else:
                concat_line = [
                    f"{new_list_name}.insert(0, {parts[0]})",
                    f"{new_list_name}.append({parts[1]})",
                ]

        code_file_lines = code_file.splitlines()
        logging.debug(f"\n{code_file_lines}")
        list_lno: int = self.outer_loop.lineno - 1  # type: ignore
        concat_lno: int = self.concat_node.lineno - 1  # type: ignore
        join_lno: int = self.outer_loop.end_lineno  # type: ignore

        source_line = code_file_lines[list_lno]
        outer_scope_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

        code_file_lines.insert(list_lno, outer_scope_whitespace + list_line)
        concat_lno += 1
        join_lno += 1

        if isinstance(concat_line, list):
            source_line = code_file_lines[concat_lno]
            concat_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            code_file_lines.pop(concat_lno)
            code_file_lines.insert(concat_lno, concat_whitespace + concat_line[1])
            code_file_lines.insert(concat_lno, concat_whitespace + concat_line[0])
            join_lno += 1
        else:
            source_line = code_file_lines[concat_lno]
            concat_whitespace = source_line[: len(source_line) - len(source_line.lstrip())]

            code_file_lines.pop(concat_lno)
            code_file_lines.insert(concat_lno, concat_whitespace + concat_line)

        source_line = code_file_lines[join_lno]

        code_file_lines.insert(join_lno, outer_scope_whitespace + join_line)

        logging.debug("New Nodes added")

        return "\n".join(code_file_lines)
