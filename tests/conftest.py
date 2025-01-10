import pytest


# ===== FIXTURES ======================
@pytest.fixture(scope="session")
def output_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("output")


@pytest.fixture(scope="session")
def source_files(tmp_path_factory):
    return tmp_path_factory.mktemp("input")
