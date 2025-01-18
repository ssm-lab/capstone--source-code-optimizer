import ast
from pathlib import Path
import textwrap
import pytest

from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
# from ecooptimizer.refactorers.repeated_calls import CacheRepeatedCallsRefactorer


@pytest.fixture
def crc_code(source_files: Path):
    crc_code = textwrap.dedent(
        """\
        class Demo:
            def __init__(self, value):
                self.value = value

            def compute(self):
                return self.value * 2

        def repeated_calls():
            demo = Demo(10)
            result1 = demo.compute()
            result2 = demo.compute()  # Repeated call
            return result1 + result2
        """
    )
    file = source_files / Path("crc_code.py")
    with file.open("w") as f:
        f.write(crc_code)

    return file


@pytest.fixture(autouse=True)
def get_smells(crc_code):
    analyzer = PylintAnalyzer(crc_code, ast.parse(crc_code.read_text()))
    analyzer.analyze()
    analyzer.configure_smells()

    return analyzer.smells_data


def test_cached_repeated_calls_detection(get_smells, crc_code: Path):
    smells = get_smells

    # Filter for cached repeated calls smells
    crc_smells = [smell for smell in smells if smell["messageId"] == "CRC001"]

    assert len(crc_smells) == 1
    assert crc_smells[0].get("symbol") == "cached-repeated-calls"
    assert crc_smells[0].get("messageId") == "CRC001"
    assert crc_smells[0]["occurrences"][0]["line"] == 11
    assert crc_smells[0]["occurrences"][1]["line"] == 12
    assert crc_smells[0]["module"] == crc_code.stem


# def test_cached_repeated_calls_refactoring(get_smells, crc_code: Path, output_dir: Path):
#     smells = get_smells

#     # Filter for cached repeated calls smells
#     crc_smells = [smell for smell in smells if smell["messageId"] == "CRC001"]

#     # Instantiate the refactorer
#     refactorer = CacheRepeatedCallsRefactorer(output_dir)

#     # for smell in crc_smells:
#     #     refactorer.refactor(crc_code, smell)
#     #     # Apply refactoring to the detected smell
#     #     refactored_file = refactorer.temp_dir / Path(
#     #             f"{crc_code.stem}_crc_line_{crc_smells[0]['occurrences'][0]['line']}.py"
#     #         )

#     #     assert refactored_file.exists()

#     #     # Check that the refactored file compiles
#     #     py_compile.compile(str(refactored_file), doraise=True)

#     #     refactored_lines = refactored_file.read_text().splitlines()

#     #     # Verify the cached variable and replaced calls
#     #     assert any("cached_demo_compute = demo.compute()" in line for line in refactored_lines)
#     #     assert "result1 = cached_demo_compute" in refactored_lines
#     #     assert "result2 = cached_demo_compute" in refactored_lines
