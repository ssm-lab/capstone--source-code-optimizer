# utils/output_config.py
import json
import os
import shutil
from utils.logger import Logger  # Import Logger if used elsewhere

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../outputs/"))

def save_file(filename: str, data, mode: str, message="", logger=None):
    """
    Saves any data to a file in the output folder.

    :param filename: Name of the file to save data to.
    :param data: Data to be saved.
    :param mode: file IO mode (w,w+,a,a+,etc).
    :param logger: Optional logger instance to log messages.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)

    # Ensure the output directory exists; if not, create it
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Write data to the specified file
    with open(file_path, mode) as file:
        file.write(data)

    message = message if len(message) > 0 else f"Output saved to {file_path.removeprefix(os.path.dirname(__file__))}"
    if logger:
        logger.log(message)
    else:
        print(message)

def save_json_files(filename, data, logger=None):
    """
    Saves JSON data to a file in the output folder.

    :param filename: Name of the file to save data to.
    :param data: Data to be saved.
    :param logger: Optional logger instance to log messages.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)

    # Ensure the output directory exists; if not, create it
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Write JSON data to the specified file
    with open(file_path, 'w+') as file:
        json.dump(data, file, sort_keys=True, indent=4)

    message = f"Output saved to {file_path.removeprefix(os.path.dirname(__file__))}"
    if logger:
        logger.log(message)
    else:
        print(message)


def copy_file_to_output(source_file_path, new_file_name, logger=None):
    """
    Copies the specified file to the output directory with a specified new name.

    :param source_file_path: The path of the file to be copied.
    :param new_file_name: The desired name for the copied file in the output directory.
    :param logger: Optional logger instance to log messages.

    :return: Path of the copied file in the output directory.
    """
    # Ensure the output directory exists; if not, create it
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Define the destination path with the new file name
    destination_path = os.path.join(OUTPUT_DIR, new_file_name)

    # Copy the file to the destination path with the specified name
    shutil.copy(source_file_path, destination_path)

    message = f"File copied to {destination_path.removeprefix(os.path.dirname(__file__))}"
    if logger:
        logger.log(message)
    else:
        print(message)

    return destination_path
