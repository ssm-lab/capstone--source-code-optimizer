import unittest
from ..src.ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer


class TestPylintAnalyzer(unittest.TestCase):
    def test_analyze_method(self):
        analyzer = PylintAnalyzer("input/ineffcient_code_example_2.py")
        analyzer.analyze()
        analyzer.configure_smells()

        data = analyzer.smells_data

        print(data)
        # self.assertIsInstance(report, list)  # Check if the output is a list
        # # Add more assertions based on expected output


if __name__ == "__main__":
    unittest.main()
