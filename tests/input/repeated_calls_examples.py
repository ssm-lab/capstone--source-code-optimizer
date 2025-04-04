# Example Python file with repeated calls smells

class Demo:
    def __init__(self, value):
        self.value = value

    def compute(self):
        return self.value * 2

# Simple repeated function calls
def simple_repeated_calls():
    value = Demo(10).compute()
    result = value + Demo(10).compute()  # Repeated call
    return result

# Repeated method calls on an object
def repeated_method_calls():
    demo = Demo(5)
    first = demo.compute()
    second = demo.compute()  # Repeated call on the same object
    return first + second

# Repeated attribute access with method calls
def repeated_attribute_calls():
    demo = Demo(3)
    first = demo.compute()
    demo.value = 10  # Modify attribute
    second = demo.compute()  # Repeated but valid since the attribute was modified
    return first + second

# Repeated nested calls
def repeated_nested_calls():
    data = [Demo(i) for i in range(3)]
    total = sum(demo.compute() for demo in data)
    repeated = sum(demo.compute() for demo in data)  # Repeated nested call
    return total + repeated

# Repeated calls in a loop
def repeated_calls_in_loop():
    results = []
    for i in range(5):
        results.append(Demo(i).compute())  # Repeated call for each loop iteration
    return results

# Repeated calls with modifications in between
def repeated_calls_with_modification():
    demo = Demo(2)
    first = demo.compute()
    demo.value = 4  # Modify object
    second = demo.compute()  # Repeated but valid due to modification
    return first + second

# Repeated calls with mixed contexts
def repeated_calls_mixed_context():
    demo1 = Demo(1)
    demo2 = Demo(2)
    result1 = demo1.compute()
    result2 = demo2.compute()
    result3 = demo1.compute()  # Repeated for demo1
    return result1 + result2 + result3

# Repeated calls with multiple arguments
def repeated_calls_with_args():
    result = max(Demo(1).compute(), Demo(1).compute())  # Repeated identical calls
    return result

# Repeated calls using a lambda
def repeated_lambda_calls():
    compute_demo = lambda x: Demo(x).compute()
    first = compute_demo(3)
    second = compute_demo(3)  # Repeated lambda call
    return first + second

# Repeated calls with external dependencies
def repeated_calls_with_external_dependency(data):
    result = len(data.get('key'))  # Repeated external call
    repeated = len(data.get('key'))
    return result + repeated

# Repeated calls with slightly different arguments
def repeated_calls_slightly_different():
    demo = Demo(10)
    first = demo.compute()
    second = Demo(20).compute()  # Different object, not a true repeated call
    return first + second
