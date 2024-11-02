import time
from typing import Callable
from pyJoules.device import DeviceFactory
from pyJoules.device.rapl_device import RaplPackageDomain, RaplDramDomain
from pyJoules.device.nvidia_device import NvidiaGPUDomain
from pyJoules.energy_meter import EnergyMeter

## Required for installation
# pip install pyJoules
# pip install nvidia-ml-py3


class EnergyMeterWrapper:
    """
    A class to measure the energy consumption of specific code blocks using PyJoules.
    """

    def __init__(self):
        """
        Initializes the EnergyMeterWrapper class.
        """
        # Create and configure the monitored devices
        domains = [RaplPackageDomain(0), RaplDramDomain(0), NvidiaGPUDomain(0)]
        devices = DeviceFactory.create_devices(domains)
        self.meter = EnergyMeter(devices)

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
        self.meter.start(tag="function_execution")  # Start measuring energy

        start_time = time.time()  # Record start time

        result = func(*args, **kwargs)  # Call the specified function

        end_time = time.time()  # Record end time
        self.meter.stop()  # Stop measuring energy

        # Retrieve the energy trace
        trace = self.meter.get_trace()
        total_energy = sum(
            sample.energy for sample in trace
        )  # Calculate total energy consumed

        # Log the timing (optional)
        print(f"Execution Time: {end_time - start_time:.6f} seconds")
        print(f"Energy Consumed: {total_energy:.6f} Joules")

        return (
            result,
            total_energy,
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
        self.meter.start(tag="block_execution")  # Start measuring energy
        exec(code_block, {}, local_vars)  # Execute the code block
        self.meter.stop()  # Stop measuring energy

        # Retrieve the energy trace
        trace = self.meter.get_trace()
        total_energy = sum(
            sample.energy for sample in trace
        )  # Calculate total energy consumed
        print(f"Energy Consumed for the block: {total_energy:.6f} Joules")
        return total_energy

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


# Example usage
if __name__ == "__main__":
    meter = EnergyMeterWrapper()
    energy_used = meter.measure_file_energy("../test/inefficent_code_example.py")
    if energy_used is not None:
        print(f"Total Energy Consumed: {energy_used:.6f} Joules")
