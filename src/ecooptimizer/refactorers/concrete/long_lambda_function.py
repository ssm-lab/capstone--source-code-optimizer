from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

import libcst as cst
from libcst import metadata as mcst

from ecooptimizer.refactorers.base_refactorer import BaseRefactorer
from ecooptimizer.data_types.smell import LLESmell

# Set up logging
logger = logging.getLogger("refactor")


@dataclass
class LambdaConversionContext:
    """Holds all contextual information about a lambda being converted."""

    lambda_node: cst.Lambda
    parent_node: cst.CSTNode
    position: mcst.CodePosition
    scope: mcst.Scope
    args_str: str = None
    body_str: str = None
    is_assigned: bool = False
    assigned_name: str = None
    assigned_to_attribute: bool = False
    function_name: str = None


class LongLambdaFunctionRefactorer(BaseRefactorer[LLESmell]):
    """
    Refactorer that targets long lambda functions by converting them into normal functions.
    Uses libCST for reliable parsing and transformation.
    """

    def __init__(self):
        super().__init__()
        self._function_name_counter = 0

    def _generate_function_name(self, context: LambdaConversionContext):
        """Generate a unique function name for converted lambdas."""
        if context.assigned_name:
            logger.debug(f"Using assignment name {context.assigned_name} as function name")
            return context.assigned_name

        self._function_name_counter += 1
        name = f"converted_lambda_{self._function_name_counter}"
        logger.debug(f"Generated new function name: {name}")
        return name

    def _find_lambda_context(self, wrapper: cst.MetadataWrapper, line_number: int):
        """
        Find the lambda node at the specified line number and gather context information.
        Returns a LambdaConversionContext if found, None otherwise.
        """
        logger.info(f"Searching for lambda at line {line_number}")

        class LambdaFinder(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (
                mcst.PositionProvider,
                mcst.ParentNodeProvider,
                mcst.ScopeProvider,
            )

            def __init__(self):
                self.found_context: Optional[LambdaConversionContext] = None

            def visit_Lambda(self, node: cst.Lambda):
                pos = self.get_metadata(mcst.PositionProvider, node).start
                if pos.line == line_number:
                    parent = self.get_metadata(mcst.ParentNodeProvider, node, None)
                    scope = self.get_metadata(mcst.ScopeProvider, node, None)

                    if parent is None or scope is None:
                        logger.error("Parent or scope metadata not found for lambda")
                        return

                    logger.debug(f"Found lambda at line {pos.line}")
                    self.found_context = LambdaConversionContext(
                        lambda_node=node, parent_node=parent, position=pos, scope=scope
                    )

        finder = LambdaFinder()
        wrapper.visit(finder)
        return finder.found_context

    def _analyze_lambda_context(self, context: LambdaConversionContext):
        """Analyze the lambda context and populate the context object with relevant information."""
        logger.debug("Analyzing lambda context")

        # Extract arguments and body
        args = []
        for param in context.lambda_node.params.params:
            if param.star == "":
                args.append(param.name.value)
            elif param.star == "*":
                args.append(f"*{param.name.value}")
            elif param.star == "**":
                args.append(f"**{param.name.value}")
        context.args_str = ", ".join(args)
        context.body_str = cst.Module([]).code_for_node(context.lambda_node.body)

        # Check if lambda is assigned to a variable
        if isinstance(context.parent_node, (cst.Assign, cst.AnnAssign)):
            context.is_assigned = True
            if (
                isinstance(context.parent_node, cst.AnnAssign)
                or len(context.parent_node.targets) == 1
            ):
                if isinstance(context.parent_node, cst.Assign):
                    pnode = context.parent_node.targets[0]
                else:
                    pnode = context.parent_node
                target = pnode.target
                if isinstance(target, cst.Name):
                    context.assigned_name = target.value
                    logger.debug(f"Lambda is assigned to variable: {context.assigned_name}")
                elif isinstance(target, cst.Attribute):
                    context.assigned_to_attribute = True
                    logger.debug("Lambda is assigned to attribute")

        if context.is_assigned and context.assigned_name:
            context.function_name = context.assigned_name
            logger.info("Lambda is assigned, using assigned name as function name")
        else:
            # Generate a unique function name
            logger.debug("Lambda is not assigned, generating new function name")
            context.function_name = self._generate_function_name(context)
        logger.info(f"Lambda will be converted to function: {context.function_name}")

    def _create_new_function(self, context: LambdaConversionContext):
        """Create a new function definition from the lambda."""
        logger.debug(f"Creating new function {context.function_name}")

        # Create parameters
        params = [
            cst.Param(name=cst.Name(arg.strip()))
            for arg in context.args_str.split(",")
            if arg.strip()
        ]

        # Create function body with return statement
        return_stmt = cst.Return(value=context.lambda_node.body)
        body = cst.IndentedBlock(body=[cst.SimpleStatementLine(body=[return_stmt])])

        return cst.FunctionDef(
            name=cst.Name(context.function_name), params=cst.Parameters(params=params), body=body
        )

    def _create_transformer(self, context: LambdaConversionContext) -> cst.CSTTransformer:
        """Transformer that inserts functions right before their enclosing statements."""
        logger.debug("Creating statement-focused lambda transformer")

        class LambdaTransformer(cst.CSTTransformer):
            METADATA_DEPENDENCIES = (
                mcst.PositionProvider,
                mcst.ParentNodeProvider,
                mcst.ScopeProvider,
            )

            def __init__(self, refactorer: LongLambdaFunctionRefactorer):
                self.refactorer = refactorer
                self._function_added = False
                self._enclosing_statement = None
                self._in_surrounding_block = False
                self._found_innermost_block = False
                self._found_assign = False
                self._assign_removed = False
                self._target_header = False

            def _node_in_range(self, lambda_pos: mcst.CodeRange, block_pos: mcst.CodeRange) -> bool:
                in_range = block_pos.start.line <= lambda_pos.start.line <= block_pos.end.line
                if in_range:
                    logger.info(f"Lambda is within statement range: {block_pos}")
                return in_range

            def leave_SimpleStatementLine(
                self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
            ):
                """Handle simple statements like assignments or expressions."""
                stmt_pos = self.get_metadata(mcst.PositionProvider, original_node)
                lambda_pos = self.get_metadata(mcst.PositionProvider, context.lambda_node)
                if self._node_in_range(lambda_pos, stmt_pos):  # type: ignore
                    logger.debug(
                        f"Found enclosing statement for lambda at line {stmt_pos.start.line}"
                    )
                    self._enclosing_statement = updated_node
                return updated_node

            def _contains_lambda(self, node: cst.CSTNode) -> bool:
                if isinstance(node, cst.Lambda):
                    if context.lambda_node == node:
                        logger.debug(f"Target lambda found in node:\n{node}")
                        return True
                    return False
                for child in node.children:
                    if self._contains_lambda(child):
                        return True
                return False

            def leave_BaseCompoundStatement(
                self,
                original_node: cst.BaseCompoundStatement,
                updated_node: cst.BaseCompoundStatement,
            ):
                """Check if lambda is in the header (before colon)"""
                # logger.debug(f"Visiting BaseCompoundStatement: {type(node).__name__}")
                header_fields = []

                # Get all header fields depending on statement type
                if isinstance(original_node, (cst.If, cst.While)):
                    header_fields = [original_node.test]
                elif isinstance(original_node, cst.For):
                    header_fields = [original_node.iter]
                elif isinstance(original_node, cst.With):
                    header_fields = [item.item for item in original_node.items]

                if header_fields:
                    # logger.debug(f"Checking header fields for lambda in {type(original_node).__name__}")
                    # Check if our lambda appears in any header field
                    for field in header_fields:
                        if self._contains_lambda(field):
                            self._enclosing_statement = updated_node
                            self._target_header = True
                            logger.debug(
                                f"Lambda found in header of {type(original_node).__name__}"
                            )
                            return True
                return updated_node

            def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):
                if (
                    context.is_assigned
                    and not context.assigned_to_attribute
                    and not self._assign_removed
                    and isinstance(original_node.value, cst.Lambda)
                    and original_node.value == context.lambda_node
                ):
                    logger.debug("Found assignment of target lambda")
                    self._assign_removed = True
                    self._found_assign = True
                    # return cst.RemoveFromParent()

                return updated_node

            def leave_AnnAssign(self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign):
                if (
                    context.is_assigned
                    and not context.assigned_to_attribute
                    and not self._assign_removed
                    and isinstance(original_node.value, cst.Lambda)
                    and original_node.value == context.lambda_node
                ):
                    logger.debug("Found assignment of target lambda")
                    self._assign_removed = True
                    self._found_assign = True
                    # return cst.RemoveFromParent()

                return updated_node

            def leave_Lambda(self, original_node: cst.Lambda, updated_node: cst.Lambda):
                if not context.is_assigned or context.assigned_to_attribute:
                    # If not assigned, replace lambda with function call
                    pos = self.get_metadata(mcst.PositionProvider, original_node).start

                    logger.debug(
                        f"Lambda is not assigned or assigned to attribute, replacing with function call at line {pos.line}"
                    )

                    logger.debug(f"Target lambda position: {context.position.line}")

                    if pos.line == context.position.line:
                        logger.debug(
                            f"Replacing lambda at line {pos.line} with function call to {context.function_name}"
                        )
                        return cst.Name(context.function_name)
                return updated_node

            def visit_IndentedBlock(self, node: cst.IndentedBlock) -> bool:
                """Identify the innermost block containing our lambda"""
                if not self._found_innermost_block:
                    # Check if our lambda is referenced in this scope
                    lambda_pos = self.get_metadata(mcst.PositionProvider, context.lambda_node)
                    block_pos = self.get_metadata(mcst.PositionProvider, node)
                    block_contains_lambda = self._node_in_range(lambda_pos, block_pos)  # type: ignore

                    if block_contains_lambda:
                        logger.debug(f"Block at line {block_pos.start.line} contains lambda")
                        self._in_surrounding_block = True
                return True

            def leave_IndentedBlock(
                self, original_node: cst.IndentedBlock, updated_node: cst.IndentedBlock
            ) -> cst.IndentedBlock:
                if not self._in_surrounding_block:
                    return updated_node

                lambda_pos = self.get_metadata(mcst.PositionProvider, context.lambda_node)
                block_pos = self.get_metadata(mcst.PositionProvider, original_node)
                block_contains_lambda = self._node_in_range(lambda_pos, block_pos)  # type: ignore

                if not block_contains_lambda:
                    return updated_node

                self._found_innermost_block = True
                self._in_surrounding_block = False
                logger.debug("Found surrounding block for lambda, preparing to insert function")
                logger.debug("Adding new function before enclosing statement")

                new_function = self.refactorer._create_new_function(context)
                new_body = []

                for stmt in updated_node.body:
                    if stmt == self._enclosing_statement:
                        new_body.append(new_function)

                        if self._found_assign:
                            continue
                    new_body.append(stmt)

                if new_body != original_node.body:  # We found and inserted before our statement
                    self._function_added = True
                    logger.debug(
                        f"Inserted function before {type(self._enclosing_statement).__name__}"
                    )
                    return updated_node.with_changes(body=new_body)

                logger.error(
                    "Failed to insert function: no enclosing statement found or no changes made"
                )

                return updated_node

            def leave_Module(self, original_node: cst.Module, updated_node: cst.Module):
                if not self._function_added and self._enclosing_statement:
                    logger.warning("Function not yet added, attempting to insert at module level")
                    new_function = self.refactorer._create_new_function(context)
                    new_body = []

                    for stmt in original_node.body:
                        if stmt == self._enclosing_statement:
                            logger.debug(
                                f"Inserting new function at module level before statement at line {self.get_metadata(mcst.PositionProvider, stmt).start.line}"
                            )
                            new_body.append(new_function)
                        new_body.append(stmt)

                    if new_body != original_node.body:
                        self._function_added = True
                        logger.debug("Function inserted at module level")
                        return updated_node.with_changes(body=new_body)

                    logger.error("No function added at module level, returning original module")

                return updated_node

        return LambdaTransformer(self)

    def refactor(
        self,
        target_file: Path,
        source_dir: Path,  # noqa: ARG002
        smell: LLESmell,
        output_file: Path,
        overwrite: bool = True,
    ):
        """
        Refactor long lambda functions by converting them into normal functions.

        Args:
            target_file: Path to the file to refactor
            source_dir: Root directory of the source code (unused)
            smell: The smell detection result containing lambda location
            output_file: Path to write the refactored code if not overwriting
            overwrite: Whether to overwrite the original file

        Returns:
            None
        """
        logger.info(f"Starting refactoring of {target_file}")

        try:
            # Read and parse the original file
            content = target_file.read_text(encoding="utf-8")
            module = cst.parse_module(content)
            # logger.debug(f"Parsed module from {target_file}:\n{module}")

            wrapper = cst.MetadataWrapper(module)

            # Find the lambda at the specified line
            line_number = smell.occurences[0].line
            context = self._find_lambda_context(wrapper, line_number)

            if not context:
                logger.warning(f"No lambda found at line {line_number} in {target_file}")
                return

            # Analyze the lambda context
            self._analyze_lambda_context(context)

            # Create and apply the transformation
            transformer = self._create_transformer(context)
            modified_module = wrapper.visit(transformer)

            # Write the modified content
            new_content = modified_module.code

            root_idx = target_file.parts.index(source_dir.name)
            rel_path = Path(*target_file.parts[root_idx:])
            print("rel_path:", rel_path)
            self.store_original(target_file, rel_path, smell.id)

            if overwrite:
                logger.info(f"Overwriting original file: {target_file}")
                target_file.write_text(new_content, encoding="utf-8")
            else:
                logger.info(f"Writing to output file: {output_file}")
                output_file.write_text(new_content, encoding="utf-8")

            self.modified_files.append(target_file)
            logger.info(f"Successfully refactored lambda at line {line_number}")

        except Exception as e:
            logger.error(f"Error refactoring {target_file}: {e!s}")
            raise
