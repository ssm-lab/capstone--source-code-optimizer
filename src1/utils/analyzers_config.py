# Any configurations that are done by the analyzers

from enum import Enum

# Enum class for standard Pylint code smells
class PylintSmell(Enum):
    LINE_TOO_LONG = "C0301"  # Pylint code smell for lines that exceed the max length
    LONG_MESSAGE_CHAIN = "R0914"  # Pylint code smell for long message chains
    LARGE_CLASS = "R0902"  # Pylint code smell for classes with too many attributes
    LONG_PARAMETER_LIST = "R0913"  # Pylint code smell for functions with too many parameters
    LONG_METHOD = "R0915"  # Pylint code smell for methods that are too long
    COMPLEX_LIST_COMPREHENSION = "C0200"  # Pylint code smell for complex list comprehensions
    INVALID_NAMING_CONVENTIONS = "C0103"  # Pylint code smell for naming conventions violations
    USE_A_GENERATOR = "R1729"  # Pylint code smell for unnecessary list comprehensions inside `any()` or `all()`


# Enum class for custom code smells not detected by Pylint
class CustomPylintSmell(Enum):
    LONG_TERN_EXPR = "CUST-1"  # Custom code smell for long ternary expressions

# Combined enum for all smells
AllPylintSmells = Enum('AllSmells', {**{s.name: s.value for s in PylintSmell}, **{s.name: s.value for s in CustomPylintSmell}})

# Additional Pylint configuration options for analyzing code
EXTRA_PYLINT_OPTIONS = [
    "--max-line-length=80",  # Sets maximum allowed line length
    "--max-nested-blocks=3",  # Limits maximum nesting of blocks
    "--max-branches=3",  # Limits maximum branches in a function
    "--max-parents=3"  # Limits maximum inheritance levels for a class
]
