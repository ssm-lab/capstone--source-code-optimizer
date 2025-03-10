# python benchmark.py /path/to/source_file.py

#!/usr/bin/env python3
"""
Benchmarking script for ecooptimizer.
This script benchmarks:
    1) Detection/analyzer runtime (via AnalyzerController.run_analysis)
    2) Refactoring runtime (via RefactorerController.run_refactorer)
    3) Energy measurement time (via CodeCarbonEnergyMeter.measure_energy)

For each detected smell (grouped by smell type), refactoring is run multiple times to compute average times.
Usage: python benchmark.py <source_file_path>
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))


import time
import statistics
import json
import logging
import sys
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

# Import controllers and energy measurement module
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.refactorers.refactorer_controller import RefactorerController
from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter


# Set up logging configuration
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("benchmark")

# Create a logger
logger = logging.getLogger("benchmark")

# Set the global logging level
logger.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # You can adjust the level for the console if needed

# Create a file handler
file_handler = logging.FileHandler("benchmark_log.txt", mode="w")
file_handler.setLevel(logging.INFO)  # You can adjust the level for the file if needed

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def benchmark_detection(source_path: str, iterations: int = 10):
    """
    Benchmarks the detection phase.
    Runs analyzer_controller.run_analysis multiple times on the given source file,
    records the runtime for each iteration, and returns the average detection time.
    Also returns the smells data from the final iteration.
    """
    analyzer_controller = AnalyzerController()
    detection_times = []
    smells_data = None
    for i in range(iterations):
        start = time.perf_counter()
        # Run the analysis; this call detects all smells in the source file.
        smells_data = analyzer_controller.run_analysis(Path(source_path))
        end = time.perf_counter()
        elapsed = end - start
        detection_times.append(elapsed)
        logger.info(f"Detection iteration {i+1}/{iterations} took {elapsed:.6f} seconds")
    avg_detection = statistics.mean(detection_times)
    logger.info(f"Average detection time over {iterations} iterations: {avg_detection:.6f} seconds")
    return smells_data, avg_detection


def benchmark_refactoring(smells_data, source_path: str, iterations: int = 10):
    """
    Benchmarks the refactoring phase for each smell type.
    For each smell in smells_data, runs refactoring (using refactorer_controller.run_refactorer)
    repeatedly on a temporary copy of the source file. Also measures energy measurement time
    (via energy_meter.measure_energy) after refactoring.
    Returns two dictionaries:
        - refactoring_stats: average refactoring time per smell type
        - energy_stats: average energy measurement time per smell type
    """
    refactorer_controller = RefactorerController()
    energy_meter = CodeCarbonEnergyMeter()
    refactoring_stats = {}  # smell_type -> average refactoring time
    energy_stats = {}  # smell_type -> average energy measurement time

    # Group smells by type. (Assuming each smell has a 'messageId' attribute.)
    grouped_smells = {}
    for smell in smells_data:
        smell_type = getattr(smell, "messageId", "unknown")
        if smell_type not in grouped_smells:
            grouped_smells[smell_type] = []
        grouped_smells[smell_type].append(smell)

    # For each smell type, benchmark refactoring and energy measurement times.
    for smell_type, smell_list in grouped_smells.items():
        ref_times = []
        eng_times = []
        logger.info(f"Benchmarking refactoring for smell type: {smell_type}")
        for smell in smell_list:
            for i in range(iterations):
                with TemporaryDirectory() as temp_dir:
                    # Create a temporary copy of the source file for refactoring.
                    temp_source = Path(temp_dir) / Path(source_path).name
                    shutil.copy(Path(source_path), temp_source)

                    # Start timer for refactoring.
                    start_ref = time.perf_counter()
                    try:
                        _ = refactorer_controller.run_refactorer(
                            temp_source, Path(temp_dir), smell, overwrite=False
                        )
                    except NotImplementedError as e:
                        logger.warning(f"Refactoring not implemented for smell: {e}")
                        continue
                    end_ref = time.perf_counter()
                    ref_time = end_ref - start_ref
                    ref_times.append(ref_time)
                    logger.info(
                        f"Refactoring iteration {i+1}/{iterations} for smell type '{smell_type}' took {ref_time:.6f} seconds"
                    )

                    # Measure energy measurement time immediately after refactoring.
                    start_eng = time.perf_counter()
                    energy_meter.measure_energy(temp_source)
                    end_eng = time.perf_counter()
                    eng_time = end_eng - start_eng
                    eng_times.append(eng_time)
                    logger.info(
                        f"Energy measurement iteration {i+1}/{iterations} for smell type '{smell_type}' took {eng_time:.6f} seconds"
                    )

        # Compute average times for this smell type.
        avg_ref_time = statistics.mean(ref_times) if ref_times else None
        avg_eng_time = statistics.mean(eng_times) if eng_times else None
        refactoring_stats[smell_type] = avg_ref_time
        energy_stats[smell_type] = avg_eng_time
        logger.info(f"Smell Type: {smell_type} - Average Refactoring Time: {avg_ref_time:.6f} sec")
        logger.info(
            f"Smell Type: {smell_type} - Average Energy Measurement Time: {avg_eng_time:.6f} sec"
        )
    return refactoring_stats, energy_stats


def main():
    """
    Main benchmarking entry point.
    Accepts the source file path as a command-line argument.
    Runs detection and refactoring benchmarks, then logs and saves overall stats.
    """
    # if len(sys.argv) < 2:
    #     print("Usage: python benchmark.py <source_file_path>")
    #     sys.exit(1)

    source_file_path = "/Users/mya/Code/Capstone/capstone--source-code-optimizer/tests/benchmarking/test_code/250_sample.py"  # sys.argv[1]
    logger.info(f"Starting benchmark on source file: {source_file_path}")

    # Benchmark the detection phase.
    smells_data, avg_detection = benchmark_detection(source_file_path, iterations=3)

    # Benchmark the refactoring phase per smell type.
    ref_stats, eng_stats = benchmark_refactoring(smells_data, source_file_path, iterations=3)

    # Compile overall benchmark results.
    overall_stats = {
        "detection_average_time": avg_detection,
        "refactoring_times": ref_stats,
        "energy_measurement_times": eng_stats,
    }
    logger.info("Overall Benchmark Results:")
    logger.info(json.dumps(overall_stats, indent=4))

    # Save benchmark results to a JSON file.
    with open("benchmark_results.json", "w") as outfile:
        json.dump(overall_stats, outfile, indent=4)
    logger.info("Benchmark results saved to benchmark_results.json")


if __name__ == "__main__":
    main()
