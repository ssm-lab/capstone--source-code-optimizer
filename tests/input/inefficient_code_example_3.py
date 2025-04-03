import numpy as np
import time


def heavy_computation():
    # Start a large matrix multiplication task to consume CPU
    print("Starting heavy computation...")
    size = 1000
    matrix_a = np.random.rand(size, size)
    matrix_b = np.random.rand(size, size)

    start_time = time.time()
    result = np.dot(matrix_a, matrix_b)
    end_time = time.time()

    print(f"Heavy computation finished in {end_time - start_time:.2f} seconds")


# Run the heavy computation in a loop for a longer duration
for _ in range(5):
    heavy_computation()
    time.sleep(1)  # Add a small delay to observe periodic CPU load
