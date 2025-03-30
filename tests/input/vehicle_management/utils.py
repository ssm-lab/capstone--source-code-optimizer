from datetime import datetime
from typing import Any


class Utility:
    """
    General-purpose utility functions for the vehicle management system.
    """

    @staticmethod
    def format_timestamp(ts: datetime = None) -> str:
        """Returns a formatted timestamp."""
        if ts is None:
            ts = datetime.now()
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def capitalize_words(text: str) -> str:
        """Capitalize the first letter of each word in a string."""
        return " ".join(word.capitalize() for word in text.strip().split())

    @staticmethod
    def validate_positive_number(value: Any) -> bool:
        """Checks if a value is a positive int or float."""
        return isinstance(value, (int, float)) and value > 0

    @staticmethod
    def safe_divide(numerator: float, denominator: float) -> float:
        """Performs division and avoids ZeroDivisionError."""
        return numerator / denominator if denominator != 0 else 0.0
