from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]

    def __eq__(self, value: object) -> bool:
        return str(self.value) == value


# Enum class for standard Pylint code smells
class PylintSmell(ExtendedEnum):
    LONG_PARAMETER_LIST = "R0913"  # Pylint code smell for functions with too many parameters
    NO_SELF_USE = "R6301"  # Pylint code smell for class methods that don't use any self calls
    USE_A_GENERATOR = (
        "R1729"  # Pylint code smell for unnecessary list comprehensions inside `any()` or `all()`
    )


# Enum class for custom code smells not detected by Pylint
class CustomSmell(ExtendedEnum):
    LONG_MESSAGE_CHAIN = "LMC001"  # Ast code smell for long message chains
    UNUSED_VAR_OR_ATTRIBUTE = "UVA001"  # Ast code smell for unused variable or attribute
    LONG_ELEMENT_CHAIN = "LEC001"  # Ast code smell for long element chains
    LONG_LAMBDA_EXPR = "LLE001"  # Ast code smell for long lambda expressions
    STR_CONCAT_IN_LOOP = "SCL001"  # Astroid code smell for string concatenation inside loops
    CACHE_REPEATED_CALLS = "CRC001"  # Ast code smell for repeated calls
