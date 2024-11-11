import unittest
from datetime import datetime

from ineffcient_code_example_2 import (
    AdvancedProcessor,
    DataProcessor,
)  # Just to show the unused import issue


# Assuming the classes DataProcessor and AdvancedProcessor are already defined
# and imported


class TestDataProcessor(unittest.TestCase):

    def test_process_all_data(self):
        # Test valid data processing
        data = [1, 2, 3, 4, 5]
        processor = DataProcessor(data)
        processed_data = processor.process_all_data()
        # Expecting values [10, 20, 30, 40, 50] (because all are greater than 1 character in length)
        self.assertEqual(processed_data, [10, 20, 30, 40, 50])

    def test_process_all_data_empty(self):
        # Test with empty data list
        processor = DataProcessor([])
        processed_data = processor.process_all_data()
        self.assertEqual(processed_data, [])

    def test_complex_calculation_multiply(self):
        # Test multiplication operation
        result = DataProcessor.complex_calculation(
            5, True, False, "multiply", 10, 20, None, "end"
        )
        self.assertEqual(result, 50)  # 5 * 10

    def test_complex_calculation_add(self):
        # Test addition operation
        result = DataProcessor.complex_calculation(
            5, True, False, "add", 10, 20, None, "end"
        )
        self.assertEqual(result, 25)  # 5 + 20

    def test_complex_calculation_default(self):
        # Test default operation
        result = DataProcessor.complex_calculation(
            5, True, False, "unknown", 10, 20, None, "end"
        )
        self.assertEqual(result, 5)  # Default value is item itself


class TestAdvancedProcessor(unittest.TestCase):

    def test_complex_comprehension(self):
        # Test complex list comprehension
        processor = AdvancedProcessor([1, 2, 3, 4, 5])
        processor.complex_comprehension()
        expected_result = [
            125,
            100,
            3375,
            400,
            15625,
            900,
            42875,
            1600,
            91125,
            166375,
            3600,
            274625,
            4900,
            421875,
            6400,
            614125,
            8100,
            857375,
        ]
        self.assertEqual(processor.processed_data, expected_result)

    def test_long_chain_valid(self):
        # Test valid deep chain access
        data = [
            [
                None,
                {
                    "details": {
                        "info": {"more_info": [{}, {}, {"target": "Valid Value"}]}
                    }
                },
            ]
        ]
        processor = AdvancedProcessor(data)
        result = processor.long_chain()
        self.assertEqual(result, "Valid Value")

    def test_long_chain_invalid(self):
        # Test invalid deep chain access, should return None
        data = [{"details": {"info": {"more_info": [{}]}}}]
        processor = AdvancedProcessor(data)
        result = processor.long_chain()
        self.assertIsNone(result)

    def test_long_scope_chaining(self):
        # Test long scope chaining, expecting 'Done' when the sum exceeds 25
        processor = AdvancedProcessor([1, 2, 3, 4, 5])
        result = processor.long_scope_chaining()
        self.assertEqual(result, "Done")


if __name__ == "__main__":
    unittest.main()
