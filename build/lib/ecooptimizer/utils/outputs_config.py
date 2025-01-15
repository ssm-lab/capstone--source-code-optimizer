# utils/output_config.py
import json
import logging
import shutil

from pathlib import Path


class OutputConfig:
    def __init__(self, out_folder: Path) -> None:
        self.out_folder = out_folder

        self.out_folder.mkdir(exist_ok=True)

    def save_file(self, filename: Path, data: str, mode: str, message: str = ""):
        """
        Saves any data to a file in the output folder.

        :param filename: Name of the file to save data to.
        :param data: Data to be saved.
        :param mode: file IO mode (w,w+,a,a+,etc).
        """
        file_path = self.out_folder / filename

        # Write data to the specified file
        with file_path.open(mode) as file:
            file.write(data)

        message = message if len(message) > 0 else f"Output saved to {file_path!s}"
        logging.info(message)

    def save_json_files(self, filename: Path, data: dict | list):
        """
        Saves JSON data to a file in the output folder.

        :param filename: Name of the file to save data to.
        :param data: Data to be saved.
        """
        file_path = self.out_folder / filename

        # Write JSON data to the specified file
        file_path.write_text(json.dumps(data, sort_keys=True, indent=4))

        logging.info(f"Output saved to {file_path!s}")

    def copy_file_to_output(self, source_file_path: Path, new_file_name: str):
        """
        Copies the specified file to the output directory with a specified new name.

        :param source_file_path: The path of the file to be copied.
        :param new_file_name: The desired name for the copied file in the output directory.
        """
        # Define the destination path with the new file name
        destination_path = self.out_folder / new_file_name

        # Copy the file to the destination path with the specified name
        shutil.copy(source_file_path, destination_path)

        logging.info(f"File copied to {destination_path!s}")
