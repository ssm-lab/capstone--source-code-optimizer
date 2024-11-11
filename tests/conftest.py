import os
import pytest

from ecooptimizer.utils.logger import Logger

@pytest.fixture(scope="session")
def output_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("output")

@pytest.fixture
def logger(output_dir):
    file = os.path.join(output_dir, "log.txt")
    return Logger(file)