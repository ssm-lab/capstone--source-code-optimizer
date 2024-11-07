# Any configurations that are done by the analyzers
from enum import Enum
from itertools import chain

class ExtendedEnum(Enum):

    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]
    
    def __str__(self):
        return str(self.value)

# =============================================
# IMPORTANT
# =============================================
# Make sure any new smells are added to the factory in this same directory
class PylintSmell(ExtendedEnum):
    LONG_MESSAGE_CHAIN = "R0914" # pylint smell
    LARGE_CLASS = "R0902" # pylint smell
    LONG_PARAMETER_LIST = "R0913" # pylint smell
    LONG_METHOD = "R0915" # pylint smell
    COMPLEX_LIST_COMPREHENSION = "C0200" # pylint smell
    INVALID_NAMING_CONVENTIONS = "C0103" # pylint smell

class CustomSmell(ExtendedEnum):
    LONG_TERN_EXPR = "CUST-1" # custom smell

# Smells that lead to wanted smells
class IntermediateSmells(ExtendedEnum):
    LINE_TOO_LONG = "C0301" # pylint smell

# Enum containing a combination of all relevant smells
class AllSmells(ExtendedEnum):
    _ignore_ = 'member cls'
    cls = vars()
    for member in chain(list(PylintSmell), list(CustomSmell)):
        cls[member.name] = member.value

# List of all codes
SMELL_CODES = [s.value for s in AllSmells]

# Extra pylint options
EXTRA_PYLINT_OPTIONS = [
    "--max-line-length=80", 
    "--max-nested-blocks=3", 
    "--max-branches=3", 
    "--max-parents=3"
]
