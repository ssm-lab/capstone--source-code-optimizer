import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.refactorers.long_lambda_function import LongLambdaFunctionRefactorer
from ecooptimizer.utils.analyzers_config import CustomSmell


def get_smells(code: Path):
    analyzer = PylintAnalyzer(code, ast.parse(code.read_text()))
    analyzer.analyze()
    analyzer.configure_smells()

    return analyzer.smells_data


@pytest.fixture(scope="module")
def source_files(tmp_path_factory):
    return tmp_path_factory.mktemp("input")


@pytest.fixture
def long_lambda_code(source_files: Path):
    long_lambda_code = textwrap.dedent(
        """\
    class OrderProcessor:
        def __init__(self, orders):
            self.orders = orders

        def process_orders(self):
            # Long lambda functions for sorting, filtering, and mapping orders
            sorted_orders = sorted(
                self.orders,
                # LONG LAMBDA FUNCTION
                key=lambda x: x.get("priority", 0) + (10 if x.get("vip", False) else 0) + (5 if x.get("urgent", False) else 0),
            )

            filtered_orders = list(
                filter(
                    # LONG LAMBDA FUNCTION
                    lambda x: x.get("status", "").lower() in ["pending", "confirmed"]
                    and len(x.get("notes", "")) > 50
                    and x.get("department", "").lower() == "sales",
                    sorted_orders,
                )
            )

            processed_orders = list(
                map(
                    # LONG LAMBDA FUNCTION
                    lambda x: {
                        "id": x["id"],
                        "priority": (
                            x["priority"] * 2 if x.get("rush", False) else x["priority"]
                        ),
                        "status": "processed",
                        "remarks": f"Order from {x.get('client', 'unknown')} processed with priority {x['priority']}.",
                    },
                    filtered_orders,
                )
            )

            return processed_orders


    if __name__ == "__main__":
        orders = [
            {
                "id": 1,
                "priority": 5,
                "vip": True,
                "status": "pending",
                "notes": "Important order.",
                "department": "sales",
            },
            {
                "id": 2,
                "priority": 2,
                "vip": False,
                "status": "confirmed",
                "notes": "Rush delivery requested.",
                "department": "support",
            },
            {
                "id": 3,
                "priority": 1,
                "vip": False,
                "status": "shipped",
                "notes": "Standard order.",
                "department": "sales",
            },
        ]
        processor = OrderProcessor(orders)
        print(processor.process_orders())
    """
    )
    file = source_files / Path("long_lambda_code.py")
    with file.open("w") as f:
        f.write(long_lambda_code)

    return file


def test_long_lambda_detection(long_lambda_code: Path):
    smells = get_smells(long_lambda_code)

    # Filter for long lambda smells
    long_lambda_smells = [
        smell for smell in smells if smell["messageId"] == CustomSmell.LONG_LAMBDA_EXPR.value
    ]

    # Assert the expected number of long lambda functions
    assert len(long_lambda_smells) == 3

    # Verify that the detected smells correspond to the correct lines in the sample code
    expected_lines = {10, 16, 26}  # Update based on actual line numbers of long lambdas
    detected_lines = {smell["line"] for smell in long_lambda_smells}
    assert detected_lines == expected_lines


def test_long_lambda_refactoring(long_lambda_code: Path):
    smells = get_smells(long_lambda_code)

    # Filter for long lambda smells
    long_lambda_smells = [
        smell for smell in smells if smell["messageId"] == CustomSmell.LONG_LAMBDA_EXPR.value
    ]

    # Instantiate the refactorer
    refactorer = LongLambdaFunctionRefactorer()

    # Measure initial emissions (mocked or replace with actual implementation)
    initial_emissions = 100.0  # Mock value, replace with actual measurement

    # Apply refactoring to each smell
    for smell in long_lambda_smells:
        refactorer.refactor(long_lambda_code, smell, initial_emissions)

    for smell in long_lambda_smells:
        # Verify the refactored file exists and contains expected changes
        refactored_file = refactorer.temp_dir / Path(
            f"{long_lambda_code.stem}_LLFR_line_{smell['line']}.py"
        )
        assert refactored_file.exists()

        with refactored_file.open() as f:
            refactored_content = f.read()

        # Check that lambda functions have been replaced by normal functions
        assert "def converted_lambda_" in refactored_content

    # CHECK FILES MANUALLY AFTER PASS
