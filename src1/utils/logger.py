# utils/logger.py

import os
from datetime import datetime

class Logger:
    def __init__(self, log_path):
        """
        Initializes the Logger with a path to the log file.
        
        :param log_path: Path to the log file where messages will be stored.
        """
        self.log_path = log_path

        # Ensure the log file directory exists and clear any previous content
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        open(self.log_path, 'w').close()  # Open in write mode to clear the file

    def log(self, message):
        """
        Appends a message with a timestamp to the log file.
        
        :param message: The message to log.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        # Append the message to the log file
        with open(self.log_path, 'a') as log_file:
            log_file.write(full_message)
        print(full_message.strip())  # Optional: also print the message
