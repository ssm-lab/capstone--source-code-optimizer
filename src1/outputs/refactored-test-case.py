
class DataProcessor:

    def __init__(self, data):
        self.data = data
        self.processed_data = []

    def process_all_data(self):
        results = []
        for item in self.data:
            try:
                result = self.complex_calculation(item, True, False,
                    'multiply', 10, 20, None, 'end')
                results.append(result)
            except Exception as e:
                print('An error occurred:', e)
        if isinstance(self.data[0], str):
            print(self.data[0].upper().strip().replace(' ', '_').lower())
        self.processed_data = list(filter(lambda x: x is not None and x != 
            0 and len(str(x)) > 1, results))
        return self.processed_data

    @staticmethod
    def complex_calculation(item, flag1, flag2, operation, threshold,
        max_value, option, final_stage):
        if operation == 'multiply':
            result = item * threshold
        elif operation == 'add':
            result = item + max_value
        else:
            result = item
        return result

    @staticmethod
    def multi_param_calculation(item1, item2, item3, flag1, flag2, flag3, operation, threshold, 
                                max_value, option, final_stage, min_value):
        value = 0
        if operation == 'multiply':
            value = item1 * item2 * item3
        elif operation == 'add':
            value = item1 + item2 + item3
        elif flag1 == 'true':
            value = item1
        elif flag2 == 'true':
            value = item2
        elif flag3 == 'true':
            value = item3
        elif max_value < threshold:
            value = max_value
        else:
            value = min_value
        return value


class AdvancedProcessor(DataProcessor):

    @staticmethod
    def check_data(item):
        return (True if item > 10 else False if item < -10 else None if 
            item == 0 else item)

    def complex_comprehension(self):
        self.processed_data = [(x ** 2 if x % 2 == 0 else x ** 3) for x in
            range(1, 100) if x % 5 == 0 and x != 50 and x > 3]

    def long_chain(self):
        try:
            deep_value = self.data[0][1]['details']['info']['more_info'][2][
                'target']
            return deep_value
        except (KeyError, IndexError, TypeError):
            return None

    @staticmethod
    def long_scope_chaining():
        for a in range(10):
            for b in range(10):
                for c in range(10):
                    for d in range(10):
                        for e in range(10):
                            if a + b + c + d + e > 25:
                                return 'Done'


if __name__ == '__main__':
    sample_data = [1, 2, 3, 4, 5]
    processor = DataProcessor(sample_data)
    processed = processor.process_all_data()
    print('Processed Data:', processed)
