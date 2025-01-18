import logging
from pathlib import Path
import shlex
import subprocess


class TestRunner:
    def __init__(self, run_command: str, project_path: Path):
        self.project_path = project_path
        self.run_command = run_command

    def retained_functionality(self):
        try:
            # Run the command as a subprocess
            result = subprocess.run(
                shlex.split(self.run_command),
                cwd=self.project_path,
                shell=True,
                check=True,
            )

            if result.returncode == 0:
                logging.info("Tests passed!\n")
            else:
                logging.info("Tests failed!\n")

            return result.returncode == 0  # True if tests passed, False otherwise

        except subprocess.CalledProcessError as e:
            logging.error(f"Error running tests: {e}")
            return False
