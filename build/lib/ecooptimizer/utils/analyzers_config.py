# Any configurations that are done by the analyzers
from enum import EnumMeta, StrEnum


class ExtendedEnum(StrEnum):
    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]

    def __str__(self):
        return str(self.value)


# Enum class for standard Pylint code smells
class PylintSmell(ExtendedEnum):
    LARGE_CLASS = "R0902"  # Pylint code smell for classes with too many attributes
    LONG_PARAMETER_LIST = "R0913"  # Pylint code smell for functions with too many parameters
    LONG_METHOD = "R0915"  # Pylint code smell for methods that are too long
    COMPLEX_LIST_COMPREHENSION = "C0200"  # Pylint code smell for complex list comprehensions
    INVALID_NAMING_CONVENTIONS = "C0103"  # Pylint code smell for naming conventions violations
    NO_SELF_USE = "R6301"  # Pylint code smell for class methods that don't use any self calls
    UNUSED_IMPORT = "W0611"  # Pylint code smell for unused imports
    UNUSED_VARIABLE = "W0612"  # Pylint code smell for unused variable
    UNUSED_CLASS_ATTRIBUTE = "W0615"  # Pylint code smell for unused class attribute
    USE_A_GENERATOR = (
        "R1729"  # Pylint code smell for unnecessary list comprehensions inside `any()` or `all()`
    )


# Enum class for custom code smells not detected by Pylint
class CustomSmell(ExtendedEnum):
    LONG_TERN_EXPR = "LTE001"  # Custom code smell for long ternary expressions
    LONG_MESSAGE_CHAIN = "LMC001"  # CUSTOM CODE
    UNUSED_VAR_OR_ATTRIBUTE = "UVA001"  # CUSTOM CODE


class IntermediateSmells(ExtendedEnum):
    LINE_TOO_LONG = "C0301"  # pylint smell


class CombinedSmellsMeta(EnumMeta):
    def __new__(metacls, clsname, bases, clsdict):  # noqa: ANN001
        # Add all members from base enums
        for enum in (PylintSmell, CustomSmell):
            for member in enum:
                clsdict[member.name] = member.value
        return super().__new__(metacls, clsname, bases, clsdict)


# Define AllSmells, combining all enum members
class AllSmells(ExtendedEnum, metaclass=CombinedSmellsMeta):
    pass


# Additional Pylint configuration options for analyzing code
EXTRA_PYLINT_OPTIONS = [
    "--enable-all-extensions",
    "--max-line-length=80",  # Sets maximum allowed line length
    "--max-nested-blocks=3",  # Limits maximum nesting of blocks
    "--max-branches=3",  # Limits maximum branches in a function
    "--max-parents=3",  # Limits maximum inheritance levels for a class
    "--max-args=6",  # Limits max parameters for each function signature
]
