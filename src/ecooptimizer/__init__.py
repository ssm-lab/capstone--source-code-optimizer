from pathlib import Path
from .utils.outputs_config import OutputConfig

DIRNAME = Path(__file__).parent

# Define paths
BASE_DIR = Path.home() / ".ecooptimizer"
OUTPUT_DIR = (BASE_DIR / Path("outputs")).resolve()

# Initialize output manager
OUTPUT_MANAGER = OutputConfig(OUTPUT_DIR, clean_existing=True)

# Entire project directory path
SAMPLE_PROJ_DIR = (DIRNAME / Path("../../tests/input/project_repeated_calls")).resolve()
SOURCE = SAMPLE_PROJ_DIR / "main.py"
TEST_FILE = SAMPLE_PROJ_DIR / "test_main.py"
