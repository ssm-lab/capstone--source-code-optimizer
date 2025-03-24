import pytest
import textwrap
from pathlib import Path

from ecooptimizer.refactorers.concrete.long_element_chain import LongElementChainRefactorer
from ecooptimizer.data_types import LECSmell, Occurence
from ecooptimizer.utils.smell_enums import CustomSmell


@pytest.fixture
def refactorer():
    return LongElementChainRefactorer()


def create_smell(occurences: list[int]):
    """Factory function to create a smell object"""

    def _create():
        return LECSmell(
            confidence="UNDEFINED",
            message="Dictionary chain too long (6/4)",
            obj="lec_function",
            symbol="long-element-chain",
            type="convention",
            messageId=CustomSmell.LONG_ELEMENT_CHAIN.value,
            path="fake.py",
            module="some_module",
            occurences=[
                Occurence(
                    line=occ,
                    endLine=occ,
                    column=0,
                    endColumn=999,
                )
                for occ in occurences
            ],
            additionalInfo=None,
        )

    return _create


def test_lec_basic_case(source_files, refactorer):
    """
    Tests that the long element chain refactorer:
    - Identifies nested dictionary access
    - Flattens the access pattern
    - Updates the dictionary definition
    """

    # --- File 1: Defines and uses the nested dictionary ---
    test_dir = Path(source_files, "temp_basic_lec")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "dict_def.py"
    file1.write_text(
        textwrap.dedent("""\
        config = {
            "server": {
                "host": "localhost",
                "port": 8080,
                "settings": {
                    "timeout": 30,
                    "retry": 3
                }
            },
            "database": {
                "type": "postgresql",
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            }
        }

        # Line where the smell is detected
        timeout = config["server"]["settings"]["timeout"]
        """)
    )

    smell = create_smell(occurences=[20])()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    # The dictionary should be flattened and accesses should be updated
    expected_file1 = textwrap.dedent("""config = {"server_host": "localhost","server_port": 8080,"server_settings_timeout": 30,"server_settings_retry": 3,"database_type": "postgresql","database_credentials_username": "admin","database_credentials_password": "secret"}

# Line where the smell is detected
timeout = config['server_settings_timeout']
        """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()


def test_lec_multiple_files(source_files, refactorer):
    """
    Tests that the refactorer updates dictionary accesses across multiple files.
    """

    # --- File 1: Defines the nested dictionary ---
    test_dir = Path(source_files, "temp_multi_lec")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "dict_def.py"
    file1.write_text(
        textwrap.dedent("""\
        class Utility:
            def __init__(self):
                    self.long_chain = {
                        "level1": {
                            "level2": {
                                "level3": {
                                    "level4": {
                                        "level5": {
                                            "level6": {
                                                "level7": "deeply nested value"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

            def get_last_value(self):
                return self.long_chain["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["level7"]

            def get_4th_level_value(self):
                return self.long_chain["level1"]["level2"]["level3"]["level4"]
        """)
    )

    # --- File 2: Uses the nested dictionary ---
    file2 = test_dir / "dict_user.py"
    file2.write_text(
        textwrap.dedent("""\
        from src.utils import Utility

        def process_data(data):
            util = Utility()
            my_call = util.long_chain["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["level7"]
            lastVal = util.get_last_value()
            fourthLevel = util.get_4th_level_value()
            return data.upper()
        """)
    )

    smell = create_smell(occurences=[20])()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
        class Utility:
            def __init__(self):
                    self.long_chain = {"level1_level2_level3_level4": {"level5": {"level6": {"level7": "deeply nested value"}}}}

            def get_last_value(self):
                return self.long_chain['level1_level2_level3_level4']['level5']['level6']['level7']

            def get_4th_level_value(self):
                return self.long_chain['level1_level2_level3_level4']
        """)

    # --- Expected Result for File 2 ---
    expected_file2 = textwrap.dedent("""\
        from src.utils import Utility

        def process_data(data):
            util = Utility()
            my_call = util.long_chain['level1_level2_level3_level4']['level5']['level6']['level7']
            lastVal = util.get_last_value()
            fourthLevel = util.get_4th_level_value()
            return data.upper()
        """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
    assert file2.read_text().strip() == expected_file2.strip()


def test_lec_attribute_access(source_files, refactorer):
    """
    Tests refactoring of dictionary accessed via class attribute.
    """

    # --- File 1: Defines and uses the nested dictionary as class attribute ---
    test_dir = Path(source_files, "temp_attr_lec")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "class_dict.py"
    file1.write_text(
        textwrap.dedent("""\
        class ConfigManager:
            def __init__(self):
                self.config = {
                    "server": {
                        "host": "localhost",
                        "port": 8080,
                        "settings": {
                            "timeout": 30,
                            "retry": 3
                        }
                    }
                }

            def get_timeout(self):
                return self.config["server"]["settings"]["timeout"]

        manager = ConfigManager()
        timeout = manager.config["server"]["settings"]["timeout"]
        """)
    )

    smell = create_smell(occurences=[15])()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result for File 1 ---
    expected_file1 = textwrap.dedent("""\
        class ConfigManager:
    def __init__(self):
        self.config = {"server_host": "localhost","server_port": 8080,"server_settings_timeout": 30,"server_settings_retry": 3}

    def get_timeout(self):
        return self.config['server_settings_timeout']

manager = ConfigManager()
timeout = manager.config['server_settings_timeout']
        """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()


def test_lec_shallow_access_ignored(source_files, refactorer):
    """
    Tests that refactoring is skipped when dictionary access is too shallow.
    """

    # --- File with shallow dictionary access ---
    test_dir = Path(source_files, "temp_shallow_lec")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "shallow_dict.py"
    original_content = textwrap.dedent("""\
        config = {
            "server": {
                "host": "localhost",
                "port": 8080
            },
            "database": {
                "type": "postgresql"
            }
        }

        # Only one level deep
        host = config["server"]
        """)

    file1.write_text(original_content)

    smell = create_smell(occurences=[11])()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # Refactoring should be skipped because access is too shallow
    assert file1.read_text().strip() == original_content.strip()


# def test_lec_multiple_occurrences(source_files, refactorer):
#     """
#     Tests refactoring when there are multiple dictionary access patterns in the same file.
#     """

#     # --- File with multiple dictionary accesses ---
#     test_dir = Path(source_files, "temp_multi_occur_lec")
#     test_dir.mkdir(exist_ok=True)

#     file1 = test_dir / "multi_access.py"
#     file1.write_text(
#         textwrap.dedent("""\
#         settings = {
#             "app": {
#                 "name": "EcoOptimizer",
#                 "version": "1.0",
#                 "config": {
#                     "debug": True,
#                     "logging": {
#                         "level": "INFO",
#                         "format": "standard"
#                     }
#                 }
#             }
#         }

#         # Multiple deep accesses
#         print(settings["app"]["config"]["debug"])
#         print(settings["app"]["config"]["logging"]["level"])
#         print(settings["app"]["config"]["logging"]["format"])
#         """)
#     )

#     smell = create_smell(occurences=[15])()

#     refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

#     # --- Expected Result ---
#     expected_file1 = textwrap.dedent("""\
#         settings = {"app_name": "EcoOptimizer", "app_version": "1.0", "app_config_debug": true, "app_config_logging_level": "INFO", "app_config_logging_format": "standard"}

#         # Multiple deep accesses
#         debug_mode = settings["app_config_debug"]
#         log_level = settings["app_config_logging_level"]
#         app_name = settings["app_name"]
#         """)

#     print("this is the file: " + file1.read_text().strip())
#     print("this is the expected: " + expected_file1.strip())
#     print(file1.read_text().strip() == expected_file1.strip())
#     # Check if the refactoring worked
#     assert file1.read_text().strip() == expected_file1.strip()


def test_lec_mixed_access_depths(source_files, refactorer):
    """
    Tests refactoring when there are different depths of dictionary access.
    """
    # --- File with different depths of dictionary access ---
    test_dir = Path(source_files, "temp_mixed_depth_lec")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "mixed_depth.py"
    file1.write_text(
        textwrap.dedent("""\
        data = {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "preferences": {
                        "theme": "dark",
                        "notifications": True
                    }
                },
                "role": "admin"
            }
        }

        # Different access depths
        name = data["user"]["profile"]["name"]
        theme = data["user"]["profile"]["preferences"]["theme"]
        role = data["user"]["role"]
        """)
    )

    smell = create_smell(occurences=[16])()

    refactorer.refactor(file1, test_dir, smell, Path("fake.py"))

    # --- Expected Result ---
    # Note: The min nesting level determines what gets flattened
    expected_file1 = textwrap.dedent("""\
        data = {"user_profile": {"name": "John Doe","email": "john@example.com","preferences": {"theme": "dark","notifications": true}},"user_role": "admin"}

        # Different access depths
        name = data['user_profile']['name']
        theme = data['user_profile']['preferences']['theme']
        role = data['user_role']
        """)

    # Check if the refactoring worked
    assert file1.read_text().strip() == expected_file1.strip()
