# Any configurations that are done by the analyzers
from enum import EnumMeta, Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]

    # def __str__(self):
    #     return str(self.value)

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
    LONG_MESSAGE_CHAIN = "LMC001"  # CUSTOM CODE
    UNUSED_VAR_OR_ATTRIBUTE = "UVA001"  # CUSTOM CODE
    LONG_ELEMENT_CHAIN = "LEC001"  # Custom code smell for long element chains (e.g dict["level1"]["level2"]["level3"]... )
    LONG_LAMBDA_EXPR = "LLE001"  # CUSTOM CODE
    STR_CONCAT_IN_LOOP = "SCL001"
    CACHE_REPEATED_CALLS = "CRC001"


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
