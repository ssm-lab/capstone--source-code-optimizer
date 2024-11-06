import resource

from measurement_utils import (start_process, calculate_ram_power,
                               start_pm_process, stop_pm_process, get_cpu_power_from_pm_logs)
import time


class CustomEnergyMeasure:
    """
    Handles custom CPU and RAM energy measurements for executing a Python script.
    Currently only works for Apple Silicon Chips with sudo access(password prompt in terminal)
    Next step includes device detection for calculating on multiple platforms
    """

    def __init__(self, script_path: str):
        self.script_path = script_path
        self.results = {"cpu": 0.0, "ram": 0.0}
        self.code_process_time = 0

    def measure_cpu_power(self):
        # start powermetrics as a child process
        powermetrics_process = start_pm_process()
        # allow time to enter password for sudo rights in mac
        time.sleep(5)
        try:
            start_time = time.time()
            # execute the provided code as another child process and wait to finish
            code_process = start_process(["python3", self.script_path])
            code_process_pid = code_process.pid
            code_process.wait()
            end_time = time.time()
            self.code_process_time = end_time - start_time
            # Parse powermetrics log to extract CPU power data for this PID
        finally:
            stop_pm_process(powermetrics_process)
        self.results["cpu"] = get_cpu_power_from_pm_logs("custom_energy_output.txt", code_process_pid)

    def measure_ram_power(self):
        # execute provided code as a child process, this time without simultaneous powermetrics process
        # code needs to rerun to use resource.getrusage() for a single child
        # might look into another library that does not require this
        code_process = start_process(["python3", self.script_path])
        code_process.wait()

        # get peak memory usage in bytes for this process
        peak_memory_b = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss

        # calculate RAM power based on peak memory(3W/8GB ratio)
        self.results["ram"] = calculate_ram_power(peak_memory_b)

    def calculate_energy_from_power(self):
        # Return total energy consumed
        total_power = self.results["cpu"] + self.results["ram"] # in watts
        return total_power * self.code_process_time


if __name__ == "__main__":
    custom_measure = CustomEnergyMeasure("/capstone--source-code-optimizer/test/high_energy_code_example.py")
    custom_measure.measure_cpu_power()
    custom_measure.measure_ram_power()
    #can be saved as a report later
    print(custom_measure.calculate_energy_from_power())
