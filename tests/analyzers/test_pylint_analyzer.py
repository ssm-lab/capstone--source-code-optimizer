import ast
from pathlib import Path
import textwrap
import pytest
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
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
def LMC_code(source_files: Path):
    lmc_code = textwrap.dedent(
        """\
    def transform_str(string):
        return string.lstrip().rstrip().lower().capitalize().split().remove("var")
    """
    )
    file = source_files / Path("lmc_code.py")
    with file.open("w") as f:
        f.write(lmc_code)

    return file


@pytest.fixture
def MIM_code(source_files: Path):
    mim_code = textwrap.dedent(
        """\
    class SomeClass():
        def __init__(self, string):
            self.string = string

        def print_str(self):
            print(self.string)

        def say_hello(self, name):
            print(f"Hello {name}!")
    """
    )
    file = source_files / Path("mim_code.py")
    with file.open("w") as f:
        f.write(mim_code)

    return file


def test_long_message_chain(LMC_code: Path):
    smells = get_smells(LMC_code)

    assert len(smells) == 1
    assert smells[0].get("symbol") == "long-message-chain"
    assert smells[0].get("messageId") == "LMC001"
    assert smells[0].get("line") == 2
    assert smells[0].get("module") == LMC_code.name


def test_member_ignoring_method(MIM_code: Path):
    smells = get_smells(MIM_code)

    assert len(smells) == 1
    assert smells[0].get("symbol") == "no-self-use"
    assert smells[0].get("messageId") == "R6301"
    assert smells[0].get("line") == 8
    assert smells[0].get("module") == MIM_code.stem


@pytest.fixture
def long_lambda_code(source_files: Path):
    mim_code = textwrap.dedent(
        """\
    class OrderProcessor:
    def __init__(self, orders):
        self.orders = orders

    def process_orders(self):
        # Long lambda functions for sorting, filtering, and mapping orders
        sorted_orders = sorted(
            self.orders,
            # LONG LAMBDA FUNCTION
            key=lambda x: x.get("priority", 0)
            + (10 if x.get("vip", False) else 0)
            + (5 if x.get("urgent", False) else 0),
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
    file = source_files / Path("mim_code.py")
    with file.open("w") as f:
        f.write(mim_code)

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
    expected_lines = {8, 14, 20}  # Update based on actual line numbers of long lambdas
    detected_lines = {smell["line"] for smell in long_lambda_smells}
    assert detected_lines == expected_lines
