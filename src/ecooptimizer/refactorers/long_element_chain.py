import logging
from pathlib import Path
import re
from enum import Enum

from testing.run_tests import run_tests
from .base_refactorer import BaseRefactorer
from data_wrappers.smell import Smell


class RefactoringStrategy(Enum):
    INTERMEDIATE_VARS = "intermediate_vars"
    DESTRUCTURING = "destructuring"
    METHOD_EXTRACTION = "method_extraction"
    CACHE_RESULT = "cache_result"


class LongElementChainRefactorer(BaseRefactorer):
    """
    Enhanced refactorer that implements multiple strategies for optimizing element chains:
    1. Intermediate Variables: Break chain into separate assignments
    2. Destructuring: Use Python's destructuring assignment
    3. Method Extraction: Create a dedicated method for frequently used chains
    4. Result Caching: Cache results for repeated access patterns
    """

    def __init__(self):
        super().__init__()
        self._cache: dict[str, str] = {}
        self._seen_patterns: dict[str, int] = {}

    def _get_leading_context(self, lines: list[str], line_number: int) -> tuple[str, int]:
        """Get indentation and context from surrounding lines."""
        target_line = lines[line_number - 1]
        leading_whitespace = re.match(r"^\s*", target_line).group()

        # Analyze surrounding lines for pattern frequency
        context_range = 10  # Look 10 lines before and after
        pattern_count = 0

        start = max(0, line_number - context_range)
        end = min(len(lines), line_number + context_range)

        for i in range(start, end):
            if i == line_number - 1:
                continue
            if target_line.strip() in lines[i]:
                pattern_count += 1

        return leading_whitespace, pattern_count

    def _apply_intermediate_vars(
        self, base_var: str, access_ops: list[str], leading_whitespace: str, original_line: str
    ) -> list[str]:
        """Strategy 1: Break chain into intermediate variables."""
        refactored_lines = []
        current_var = base_var

        # Extract the original operation (e.g., print, assign, etc.)
        chain_expr = f"{base_var}{''.join(access_ops)}"
        operation_prefix = original_line[: original_line.index(chain_expr)].rstrip()
        operation_suffix = original_line[
            original_line.index(chain_expr) + len(chain_expr) :
        ].rstrip()

        # Add intermediate assignments
        for i, op in enumerate(access_ops[:-1]):
            next_var = f"intermediate_{i}"
            refactored_lines.append(f"{leading_whitespace}{next_var} = {current_var}{op}")
            current_var = next_var

        # Add final line with same operation and indentation as original
        final_access = f"{current_var}{access_ops[-1]}"
        final_line = f"{operation_prefix}{final_access}{operation_suffix}"
        refactored_lines.append(final_line)

        return refactored_lines

    def _apply_destructuring(
        self, base_var: str, access_ops: list[str], leading_whitespace: str, original_line: str
    ) -> list[str]:
        """Strategy 2: Use Python destructuring assignment."""
        # Extract the original operation
        chain_expr = f"{base_var}{''.join(access_ops)}"
        operation_prefix = original_line[: original_line.index(chain_expr)].rstrip()
        operation_suffix = original_line[
            original_line.index(chain_expr) + len(chain_expr) :
        ].rstrip()

        keys = [op.strip("[]").strip("'\"") for op in access_ops]

        if all(key.isdigit() for key in keys):  # List destructuring
            unpacking_vars = [f"_{i}" for i in range(len(keys) - 1)]
            target_var = "result"
            unpacking = f"{', '.join(unpacking_vars)}, {target_var}"
            return [
                f"{leading_whitespace}{unpacking} = {base_var}",
                f"{operation_prefix}{target_var}{operation_suffix}",
            ]
        else:  # Dictionary destructuring
            target_key = keys[-1]
            return [
                f"{leading_whitespace}result = {base_var}.get('{target_key}', None)",
                f"{operation_prefix}result{operation_suffix}",
            ]

    def _apply_method_extraction(
        self,
        base_var: str,
        access_ops: list[str],
        leading_whitespace: str,
        original_line: str,
        pattern_count: int,
    ) -> list[str]:
        """Strategy 3: Extract repeated patterns into methods."""
        if pattern_count < 2:
            return [original_line]

        method_name = (
            f"get_{base_var}_{'_'.join(op.strip('[]').strip('\"\'') for op in access_ops)}"
        )

        # Extract the original operation
        chain_expr = f"{base_var}{''.join(access_ops)}"
        operation_prefix = original_line[: original_line.index(chain_expr)].rstrip()
        operation_suffix = original_line[
            original_line.index(chain_expr) + len(chain_expr) :
        ].rstrip()

        # Generate method definition
        method_def = [
            f"\n{leading_whitespace}def {method_name}(data):",
            f"{leading_whitespace}    try:",
            f"{leading_whitespace}        return data{(''.join(access_ops))}",
            f"{leading_whitespace}    except (KeyError, IndexError):",
            f"{leading_whitespace}        return None",
        ]

        # Replace original line with method call, maintaining original operation
        new_line = f"{operation_prefix}{method_name}({base_var}){operation_suffix}"

        return [*method_def, f"\n{leading_whitespace}{new_line}"]

    def _apply_caching(
        self, base_var: str, access_ops: list[str], leading_whitespace: str, original_line: str
    ) -> list[str]:
        """Strategy 4: Cache results for repeated access."""
        # Extract the original operation
        chain_expr = f"{base_var}{''.join(access_ops)}"
        operation_prefix = original_line[: original_line.index(chain_expr)].rstrip()
        operation_suffix = original_line[
            original_line.index(chain_expr) + len(chain_expr) :
        ].rstrip()

        cache_key = f"{base_var}{''.join(access_ops)}"
        # cache_var = f"_cached_{base_var}_{len(access_ops)}"

        return [
            f"{leading_whitespace}if '{cache_key}' not in self._cache:",
            f"{leading_whitespace}    self._cache['{cache_key}'] = {cache_key}",
            f"{operation_prefix}self._cache['{cache_key}']{operation_suffix}",
        ]

    def _determine_best_strategy(
        self, pattern_count: int, access_ops: list[str]
    ) -> RefactoringStrategy:
        """Determine the best refactoring strategy based on context."""
        if pattern_count > 2:
            return RefactoringStrategy.METHOD_EXTRACTION
        elif len(access_ops) > 3:
            return RefactoringStrategy.INTERMEDIATE_VARS
        elif all(op.strip("[]").strip("'\"").isdigit() for op in access_ops):
            return RefactoringStrategy.DESTRUCTURING
        else:
            return RefactoringStrategy.CACHE_RESULT

    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Refactor long element chains using the most appropriate strategy based on context.
        """
        line_number = pylint_smell["line"]
        temp_filename = self.temp_dir / Path(f"{file_path.stem}_LECR_line_{line_number}.py")

        logging.info(f"Analyzing element chain on '{file_path.name}' at line {line_number}")

        try:
            # Read and analyze the file
            with file_path.open() as f:
                lines = f.readlines()

            target_line = lines[line_number - 1].rstrip()
            leading_whitespace, pattern_count = self._get_leading_context(lines, line_number)

            # Parse the element chain
            chain_pattern = r"(\w+)(\[[^\]]+\])+"
            match = re.search(chain_pattern, target_line)

            if not match or len(re.findall(r"\[", target_line)) <= 2:
                logging.info("No valid long element chain found. Skipping refactor.")
                return

            base_var = match.group(1)
            access_ops = re.findall(r"\[[^\]]+\]", match.group(0))

            # Choose and apply the best strategy
            strategy = self._determine_best_strategy(pattern_count, access_ops)
            logging.info(f"Applying {strategy.value} strategy")

            if strategy == RefactoringStrategy.INTERMEDIATE_VARS:
                refactored_lines = self._apply_intermediate_vars(
                    base_var, access_ops, leading_whitespace, target_line
                )
            elif strategy == RefactoringStrategy.DESTRUCTURING:
                refactored_lines = self._apply_destructuring(
                    base_var, access_ops, leading_whitespace, target_line
                )
            elif strategy == RefactoringStrategy.METHOD_EXTRACTION:
                refactored_lines = self._apply_method_extraction(
                    base_var, access_ops, leading_whitespace, target_line, pattern_count
                )
            else:  # CACHE_RESULT
                refactored_lines = self._apply_caching(
                    base_var, access_ops, leading_whitespace, target_line
                )

            # Replace the original line with refactored code
            lines[line_number - 1 : line_number] = [line + "\n" for line in refactored_lines]

            # Write to temporary file
            with temp_filename.open("w") as temp_file:
                temp_file.writelines(lines)

            # Measure new emissions
            final_emission = self.measure_energy(temp_filename)

            if not final_emission:
                logging.info(
                    f"Could not measure emissions for '{temp_filename.name}'. Discarding refactor."
                )
                return

            # Verify improvement and test passing
            if self.check_energy_improvement(initial_emissions, final_emission):
                if run_tests() == 0:
                    logging.info(
                        f"Successfully refactored using {strategy.value} strategy. "
                        f"Energy improvement confirmed and tests passing."
                    )
                    return
                logging.info("Tests failed! Discarding refactored changes.")
            else:
                logging.info("No emission improvement. Discarding refactored changes.")

        except Exception as e:
            logging.error(f"Error during refactoring: {e!s}")
            return
