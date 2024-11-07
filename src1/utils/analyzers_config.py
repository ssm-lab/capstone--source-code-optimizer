# Any configurations that are done by the analyzers

from enum import Enum

class PylintSmell(Enum):
    LINE_TOO_LONG = "C0301" # pylint smell
    LONG_MESSAGE_CHAIN = "R0914" # pylint smell
    LARGE_CLASS = "R0902" # pylint smell
    LONG_PARAMETER_LIST = "R0913" # pylint smell
    LONG_METHOD = "R0915" # pylint smell
    COMPLEX_LIST_COMPREHENSION = "C0200" # pylint smell
    INVALID_NAMING_CONVENTIONS = "C0103" # pylint smell

class CustomSmell(Enum):
    LONG_TERN_EXPR = "CUST-1" # custom smell

AllSmells = Enum('AllSmells', {**{s.name: s.value for s in PylintSmell}, **{s.name: s.value for s in CustomSmell}})

# Extra pylint options
EXTRA_PYLINT_OPTIONS = [
    "--max-line-length=80", 
    "--max-nested-blocks=3", 
    "--max-branches=3", 
    "--max-parents=3"
]
