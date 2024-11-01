from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    def __init__(self, code_path: str):
        self.code_path = code_path

    @abstractmethod
    def analyze(self):
        pass
