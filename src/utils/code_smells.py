from enum import Enum

class ExtendedEnum(Enum):

    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]

class CodeSmells(ExtendedEnum):
    # Add codes here
    LINE_TOO_LONG = "C0301"
    LONG_MESSAGE_CHAIN = "R0914"
    LONG_LAMBDA_FUNC = "R0914"
    LONG_TERN_EXPR = "CUST-1"
    # "R0902": LargeClassRefactorer,  # Too many instance attributes
    # "R0913": "Long Parameter List",  # Too many arguments
    # "R0915": "Long Method",  # Too many statements
    # "C0200": "Complex List Comprehension",  # Loop can be simplified
    # "C0103": "Invalid Naming Convention",  # Non-standard names

    def __str__(self):
        return str(self.value)
