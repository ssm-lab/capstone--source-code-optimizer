import resource
import subprocess
import time
import re


def start_process(command):
    return subprocess.Popen(command)

def calculate_ram_power(memory_b):
    memory_gb = memory_b / (1024 ** 3)
    return memory_gb * 3 / 8  # 3W/8GB ratio


def start_pm_process(log_path="custom_energy_output.txt"):
    powermetrics_process = subprocess.Popen(
        ["sudo", "powermetrics", "--samplers", "tasks,cpu_power", "--show-process-gpu", "-i", "5000"],
        stdout=open(log_path, "w"),
        stderr=subprocess.PIPE
    )
    return powermetrics_process


def stop_pm_process(powermetrics_process):
    powermetrics_process.terminate()

def get_cpu_power_from_pm_logs(log_path, pid):
    cpu_share, total_cpu_power = None, None # in ms/s and mW respectively
    with open(log_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if str(pid) in line:
                cpu_share = float(line.split()[2])
            elif "CPU Power:" in line:
                total_cpu_power = float(line.split()[2])
            if cpu_share and total_cpu_power:
                break
    if cpu_share and total_cpu_power:
        cpu_power = (cpu_share / 1000) * (total_cpu_power / 1000)
        return cpu_power
    return None
