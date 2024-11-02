import time
from typing import Callable
import pyJoules.energy as joules


class EnergyMeter:
    """
    A class to measure the energy consumption of specific code blocks using PyJoules.
    """

    def __init__(self):
        """
        Initializes the EnergyMeter class.
        """
        # Optional: Any initialization for the energy measurement can go here
        pass

    def measure_energy(self, func: Callable, *args, **kwargs):
        """
        Measures the energy consumed by the specified function during its execution.

        Parameters:
        - func (Callable): The function to measure.
        - *args: Arguments to pass to the function.
        - **kwargs: Keyword arguments to pass to the function.

        Returns:
        - tuple: A tuple containing the return value of the function and the energy consumed (in Joules).
        """
        start_energy = joules.getEnergy()  # Start measuring energy
        start_time = time.time()  # Record start time

        result = func(*args, **kwargs)  # Call the specified function

        end_time = time.time()  # Record end time
        end_energy = joules.getEnergy()  # Stop measuring energy

        energy_consumed = end_energy - start_energy  # Calculate energy consumed

        # Log the timing (optional)
        print(f"Execution Time: {end_time - start_time:.6f} seconds")
        print(f"Energy Consumed: {energy_consumed:.6f} Joules")

        return (
            result,
            energy_consumed,
        )  # Return the result of the function and the energy consumed

    def measure_block(self, code_block: str):
        """
        Measures energy consumption for a block of code represented as a string.

        Parameters:
        - code_block (str): A string containing the code to execute.

        Returns:
        - float: The energy consumed (in Joules).
        """
        local_vars = {}
        exec(code_block, {}, local_vars)  # Execute the code block
        energy_consumed = joules.getEnergy()  # Measure energy after execution
        print(f"Energy Consumed for the block: {energy_consumed:.6f} Joules")
        return energy_consumed

    def measure_file_energy(self, file_path: str):
        """
        Measures the energy consumption of the code in the specified Python file.

        Parameters:
        - file_path (str): The path to the Python file.

        Returns:
        - float: The energy consumed (in Joules).
        """
        try:
            with open(file_path, "r") as file:
                code = file.read()  # Read the content of the file

            # Execute the code block and measure energy consumption
            return self.measure_block(code)

        except Exception as e:
            print(f"An error occurred while measuring energy for the file: {e}")
            return None  # Return None in case of an error
