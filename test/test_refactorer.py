import unittest
from src.refactorer.long_method_refactorer import LongMethodRefactorer
from src.refactorer.large_class_refactorer import LargeClassRefactorer
from src.refactorer.complex_list_comprehension_refactorer import ComplexListComprehensionRefactorer

class TestRefactorers(unittest.TestCase):
    """
    Unit tests for various refactorers.
    """

    def test_refactor_long_method(self):
        """
        Test the refactor method of the LongMethodRefactorer.
        """
        original_code = """
        def long_method():
            # A long method with too many lines of code
            a = 1
            b = 2
            c = a + b
            # More complex logic...
            return c
        """
        expected_refactored_code = """
        def long_method():
            result = calculate_result()
            return result

        def calculate_result():
            a = 1
            b = 2
            return a + b
        """
        refactorer = LongMethodRefactorer(original_code)
        result = refactorer.refactor()
        self.assertEqual(result.strip(), expected_refactored_code.strip())

    def test_refactor_large_class(self):
        """
        Test the refactor method of the LargeClassRefactorer.
        """
        original_code = """
        class LargeClass:
            def method1(self):
                # Method 1
                pass

            def method2(self):
                # Method 2
                pass

            def method3(self):
                # Method 3
                pass
            
            # ... many more methods ...
        """
        expected_refactored_code = """
        class LargeClass:
            def method1(self):
                # Method 1
                pass

        class AnotherClass:
            def method2(self):
                # Method 2
                pass

            def method3(self):
                # Method 3
                pass
        """
        refactorer = LargeClassRefactorer(original_code)
        result = refactorer.refactor()
        self.assertEqual(result.strip(), expected_refactored_code.strip())

    def test_refactor_complex_list_comprehension(self):
        """
        Test the refactor method of the ComplexListComprehensionRefactorer.
        """
        original_code = """
        def complex_list():
            return [x**2 for x in range(10) if x % 2 == 0 and x > 3]
        """
        expected_refactored_code = """
        def complex_list():
            result = []
            for x in range(10):
                if x % 2 == 0 and x > 3:
                    result.append(x**2)
            return result
        """
        refactorer = ComplexListComprehensionRefactorer(original_code)
        result = refactorer.refactor()
        self.assertEqual(result.strip(), expected_refactored_code.strip())

# Run all tests in the module
if __name__ == "__main__":
    unittest.main()
