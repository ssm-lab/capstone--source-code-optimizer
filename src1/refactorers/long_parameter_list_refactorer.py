from .base_refactorer import BaseRefactorer


class LongParameterListRefactorer(BaseRefactorer):
    """
    Refactorer that targets methods that take too many arguments
    """

    def __init__(self, logger):
        super().__init__(logger)

    def refactor(self, file_path, pylint_smell, initial_emission):
        # Logic to identify methods that take too many arguments goes here
        pass
