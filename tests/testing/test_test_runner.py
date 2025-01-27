from pathlib import Path
import textwrap
import pytest

from ecooptimizer.testing.test_runner import TestRunner


@pytest.fixture(scope="module")
def mock_test_dir(source_files):
    SAMPLE_DIR = source_files / "mock_project"
    SAMPLE_DIR.mkdir(exist_ok=True)

    TEST_DIR = SAMPLE_DIR / "tests"
    TEST_DIR.mkdir(exist_ok=True)

    return TEST_DIR


@pytest.fixture
def mock_pass_test(mock_test_dir) -> Path:
    TEST_FILE_PASS = mock_test_dir / "test_pass.py"
    TEST_FILE_PASS.touch()

    pass_content = textwrap.dedent(
        """\
    def test_placeholder():
        pass
    """
    )

    TEST_FILE_PASS.write_text(pass_content)

    return TEST_FILE_PASS


@pytest.fixture
def mock_fail_test(mock_test_dir) -> Path:
    TEST_FILE_FAIL = mock_test_dir / "test_fail.py"
    TEST_FILE_FAIL.touch()

    fail_content = textwrap.dedent(
        """\
    import pytest


    def test_placeholder():
        pytest.fail("The is suppose to fail.")
    """
    )

    TEST_FILE_FAIL.write_text(fail_content)

    return TEST_FILE_FAIL


def test_runner_pass(mock_test_dir, mock_pass_test):
    test_runner = TestRunner(
        f"pytest {mock_pass_test.name!s}",
        mock_test_dir,
    )

    assert test_runner.retained_functionality()


def test_runner_fail(mock_test_dir, mock_fail_test):
    test_runner = TestRunner(
        f"pytest {mock_fail_test.name!s}",
        mock_test_dir,
    )

    assert not test_runner.retained_functionality()
