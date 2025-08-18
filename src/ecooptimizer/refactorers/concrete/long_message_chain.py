import logging
from pathlib import Path
import libcst as cst
from libcst.metadata import PositionProvider, ParentNodeProvider
from ecooptimizer.refactorers.base_refactorer import BaseRefactorer
from ecooptimizer.data_types.smell import LMCSmell

logger = logging.getLogger("refactor")


class LongMessageChainRefactorer(BaseRefactorer[LMCSmell]):
    """Refactorer that safely breaks long method chains using libCST."""

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Initialized LongMessageChainRefactorer")

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: LMCSmell,
        output_file: Path,
        overwrite: bool = True,
    ) -> None:
        logger.info(f"Refactoring {target_file} (line {smell.occurences[0].line})")

        try:
            logger.debug(f"Reading file: {target_file}")
            content = target_file.read_text()
            logger.debug("Parsing module with libcst")
            wrapper = cst.MetadataWrapper(cst.parse_module(content))

            transformer = ChainTransformer(line_number=smell.occurences[0].line)
            logger.debug("Visiting CST with ChainTransformer")
            modified_module = wrapper.visit(transformer)

            if not transformer.found_chain:
                logger.warning(f"No chain found at line {smell.occurences[0].line}")
                return

            output_path = target_file if overwrite else output_file
            logger.debug(f"Writing refactored code to: {output_path}")
            output_path.write_text(modified_module.code, encoding="utf-8")
            self.modified_files.append(output_path)
            logger.info(f"Successfully refactored {target_file}")

        except Exception as e:
            logger.error(f"Failed to refactor {target_file}: {e!s}")
            raise


class ChainTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

    def __init__(self, line_number: int):
        self.target_line = line_number
        self.found_chain = False
        self.intermediate_statements: list[cst.SimpleStatementLine] = []
        self.root_chain = None
        self.target_parent = None  # The statement/compound where we insert above
        self.inserted = False
        self.module_body_insert = False  # Flag for top-level insertion
        self.existing_names = set()
        logger.debug(f"ChainTransformer initialized for line {line_number}")

    def visit_Name(self, node: cst.Name) -> None:
        """Track all existing variable names to avoid collisions."""
        # logger.debug(f"Tracking variable name: {node.value}")
        self.existing_names.add(node.value)

    def visit_Call(self, node: cst.Call) -> bool:
        """Find the first call in the chain that matches the smell location."""
        # logger.debug(f"Visiting Call node at line {self.target_line}")
        if not self.found_chain or self.inserted:
            pos = self.get_metadata(PositionProvider, node)
            logger.debug(f"Call node position: {pos.start.line}-{pos.end.line}")
            if pos.start.line <= self.target_line <= pos.end.line:
                # logger.info(f"Found target chain at line {self.target_line}:\n{node}")
                self.found_chain = True
                self.root_chain = node
                return True
        return self.found_chain

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        """Replace the original long chain with the last call, using intermediates."""
        if not self.found_chain or self.inserted or not original_node.deep_equals(self.root_chain):
            return updated_node

        pos = self.get_metadata(PositionProvider, original_node)
        logger.debug(f"Leave_Call node position: {pos.start.line}-{pos.end.line}")
        if not (pos.start.line <= self.target_line <= pos.end.line):
            logger.debug("Node not at target line, returning updated node")
            return updated_node

        # Break into base + steps
        logger.debug(f"Decomposing message chain:\n{original_node}")
        base, steps = self._decompose_chain(original_node)
        logger.debug(f"Decomposed chain: base={base}, steps={steps}")

        current_value = base
        for i, method in enumerate(steps[:-1]):
            intermediate_name = self._generate_unique_name(f"intermediate_{i}")
            logger.debug(
                f"Creating intermediate statement: {intermediate_name} for method {method}"
            )
            self.intermediate_statements.append(
                self._create_intermediate_statement(intermediate_name, current_value, method)
            )
            current_value = cst.Name(intermediate_name)

        # Build final call using last intermediate
        logger.debug("Building final call using last intermediate")
        return cst.Call(func=cst.Attribute(value=current_value, attr=steps[-1]))

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        """Capture insertion point for normal statements."""
        if self.found_chain and self.target_parent is None:
            pos = self.get_metadata(PositionProvider, original_node)
            logger.debug(f"SimpleStatementLine position: {pos.start.line}-{pos.end.line}")
            if pos.start.line <= self.target_line <= pos.end.line:
                logger.debug("Setting target_parent for insertion")
                self.target_parent = original_node
        return updated_node

    def leave_BaseCompoundStatement(
        self, original_node: cst.BaseCompoundStatement, updated_node: cst.BaseCompoundStatement
    ) -> cst.BaseCompoundStatement:
        """Capture insertion point when chain is in a header line."""
        if self.found_chain and self.target_parent is None:
            pos = self.get_metadata(PositionProvider, original_node)
            logger.debug(f"BaseCompoundStatement position: {pos.start.line}-{pos.end.line}")
            if pos.start.line <= self.target_line <= pos.end.line:
                logger.debug("Setting target_parent for compound statement insertion")
                self.target_parent = original_node
        return updated_node

    def leave_IndentedBlock(
        self, original_node: cst.IndentedBlock, updated_node: cst.IndentedBlock
    ) -> cst.IndentedBlock:
        """Insert intermediates above the target statement if in a block."""
        if not self.found_chain or not self.target_parent or not self.intermediate_statements:
            logger.debug("No insertion needed in IndentedBlock")
            return updated_node

        if self.inserted:
            logger.debug("Already inserted intermediates in IndentedBlock")
            return updated_node

        # Find the matching statement inside this block
        for idx, stmt in enumerate(original_node.body):
            if stmt.deep_equals(self.target_parent):
                logger.info(
                    f"Inserting {len(self.intermediate_statements)} intermediate statements before target in IndentedBlock"
                )
                new_body = (
                    list(updated_node.body[:idx])
                    + self.intermediate_statements
                    + list(updated_node.body[idx:])
                )
                self.insertion_done = True
                self.inserted = True
                return updated_node.with_changes(body=new_body)

        logger.debug("Target parent not found in IndentedBlock body")
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Top-level fallback insertion."""
        if self.found_chain and not self.target_parent and self.intermediate_statements:
            logger.info(
                f"Inserting {len(self.intermediate_statements)} intermediate statements at module top level"
            )
            body = list(updated_node.body)
            if body:
                body = self.intermediate_statements + body
                return updated_node.with_changes(body=body)
        return updated_node

    # ---------------------
    # Helpers
    # ---------------------
    def _decompose_chain(self, node: cst.Call):
        """Return base object and list of method names from a call chain."""
        logger.debug("Decomposing call chain")
        steps = []
        current = node
        # logger.debug(f"Whole chain: {node}")
        while isinstance(current, cst.Call):
            if isinstance(current.func, cst.Attribute):
                steps.append(current.func.attr)
                current = current.func.value
            else:
                break
        logger.debug(f"Chain decomposition result: base={current}, steps={steps[::-1]}")
        return current, steps[::-1]

    def _create_intermediate_statement(
        self, name: str, value: cst.BaseExpression, method: cst.Name
    ):
        """Create: intermediate_X = value.method()"""
        logger.debug(f"Creating intermediate assignment: {name} = {value}.{method.value}()")
        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name(name))],
                    value=cst.Call(func=cst.Attribute(value=value, attr=method)),
                )
            ]
        )

    def _generate_unique_name(self, base: str) -> str:
        """Ensure intermediate variable name doesn't collide."""
        logger.debug(f"Generating unique name for base: {base}")
        name = base
        counter = 0
        while name in self.existing_names:
            counter += 1
            name = f"{base}_{counter}"
        logger.debug(f"Unique name generated: {name}")
        self.existing_names.add(name)
        return name
