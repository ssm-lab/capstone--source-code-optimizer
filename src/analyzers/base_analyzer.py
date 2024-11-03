from abc import ABC, abstractmethod
import os


class BaseAnalyzer(ABC):
    def __init__(self, code_path: str):
        self.code_path = os.path.abspath(code_path)

    @abstractmethod
    def analyze(self):
        pass
