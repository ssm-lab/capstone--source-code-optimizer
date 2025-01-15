from .smell_config import SmellConfig

# Fetch the list of Pylint smell IDs
pylint_smell_ids = SmellConfig.list_pylint_smell_ids()

if pylint_smell_ids:
    EXTRA_PYLINT_OPTIONS = [
        "--enable-all-extensions",
        "--max-line-length=80",  # Sets maximum allowed line length
        "--max-nested-blocks=3",  # Limits maximum nesting of blocks
        "--max-branches=3",  # Limits maximum branches in a function
        "--max-parents=3",  # Limits maximum inheritance levels for a class
        "--max-args=6",  # Limits max parameters for each function signature
        "--disable=all",  # Disable all Pylint checks
        f"--enable={','.join(pylint_smell_ids)}",  # Enable specific smells
    ]

# Fetch the list of AST smell methods
ast_smell_methods = SmellConfig.list_ast_smell_methods()

if ast_smell_methods:
    EXTRA_AST_OPTIONS = ast_smell_methods
