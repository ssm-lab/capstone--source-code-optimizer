"""Enums for code smell classification and identification."""

from enum import Enum


class ExtendedEnum(Enum):
    """Base enum class with additional utility methods."""

    @classmethod
    def list(cls) -> list[str]:
        """Returns all enum values as a list.

        Returns:
            List of all enum values as strings
        """
        return [c.value for c in cls]

    def __eq__(self, value: object) -> bool:
        """Compares enum value with string representation.

        Args:
            value: Value to compare against

        Returns:
            True if values match, False otherwise
        """
        return str(self.value) == value


class PylintSmell(ExtendedEnum):
    """Standard code smells detected by Pylint."""

    LONG_PARAMETER_LIST = "R0913"  # Too many function parameters
    NO_SELF_USE = "R6301"  # Class methods not using self
    USE_A_GENERATOR = "R1729"  # Unnecessary list comprehensions in any()/all()


class CustomSmell(ExtendedEnum):
    """Custom code smells not detected by standard Pylint."""

    LONG_MESSAGE_CHAIN = "LMC001"  # Excessive method chaining
    LONG_ELEMENT_CHAIN = "LEC001"  # Excessive dictionary/object chaining
    LONG_LAMBDA_EXPR = "LLE001"  # Overly complex lambda expressions
    STR_CONCAT_IN_LOOP = "SCL001"  # Inefficient string concatenation in loops
    CACHE_REPEATED_CALLS = "CRC001"  # Repeated expensive function calls
