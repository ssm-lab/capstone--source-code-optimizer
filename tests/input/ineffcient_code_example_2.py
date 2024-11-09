# LC: Large Class with too many responsibilities
class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed_data = []

    # LM: Long Method - this method does way too much
    def process_all_data(self):
        results = []
        for item in self.data:
            try:
                # LPL: Long Parameter List
                result = self.complex_calculation(
                    item, True, False, "multiply", 10, 20, None, "end"
                )
                results.append(result)
            except Exception as e:  # UEH: Unqualified Exception Handling
                print("An error occurred:", e)

        # LMC: Long Message Chain
        if isinstance(self.data[0], str):
            print(self.data[0].upper().strip().replace(" ", "_").lower())

        # LLF: Long Lambda Function
        self.processed_data = list(
            filter(lambda x: x is not None and x != 0 and len(str(x)) > 1, results)
        )

        return self.processed_data

    # Moved the complex_calculation method here
    def complex_calculation(
        self, item, flag1, flag2, operation, threshold, max_value, option, final_stage
    ):
        if operation == "multiply":
            result = item * threshold
        elif operation == "add":
            result = item + max_value
        else:
            result = item
        return result


class AdvancedProcessor(DataProcessor):
    # LTCE: Long Ternary Conditional Expression
    def check_data(self, item):
        return True if item > 10 else False if item < -10 else None if item == 0 else item

    # Complex List Comprehension
    def complex_comprehension(self):
        # CLC: Complex List Comprehension
        self.processed_data = [
            x**2 if x % 2 == 0 else x**3
            for x in range(1, 100)
            if x % 5 == 0 and x != 50 and x > 3
        ]

    # Long Element Chain
    def long_chain(self):
        try:
            deep_value = self.data[0][1]["details"]["info"]["more_info"][2]["target"]
            return deep_value
        except (KeyError, IndexError, TypeError):
            return None

    # Long Scope Chaining (LSC)
    def long_scope_chaining(self):
        for a in range(10):
            for b in range(10):
                for c in range(10):
                    for d in range(10):
                        for e in range(10):
                            if a + b + c + d + e > 25:
                                return "Done"


# Main method to execute the code
if __name__ == "__main__":
    sample_data = [1, 2, 3, 4, 5]
    processor = DataProcessor(sample_data)
    processed = processor.process_all_data()
    print("Processed Data:", processed)
