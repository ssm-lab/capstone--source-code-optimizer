import pytest
import textwrap

from ecooptimizer.refactorers.concrete.long_parameter_list import LongParameterListRefactorer
from ecooptimizer.data_types import LPLSmell, Occurence
from ecooptimizer.utils.smell_enums import PylintSmell


@pytest.fixture
def refactorer():
    return LongParameterListRefactorer()


def create_smell(occurences: list[int]):
    """Factory function to create a smell object"""

    def _create():
        return LPLSmell(
            path="fake.py",
            module="some_module",
            obj=None,
            type="refactor",
            symbol="too-many-arguments",
            message="Too many arguments (8/6)",
            messageId=PylintSmell.LONG_PARAMETER_LIST.value,
            confidence="UNDEFINED",
            occurences=[
                Occurence(line=occ, endLine=999, column=999, endColumn=999) for occ in occurences
            ],
        )

    return _create


def test_lpl_constructor_1(refactorer, source_files):
    """Test for constructor with 8 params all used, mix of keyword and positions params"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class UserDataProcessor:
        def __init__(self, user_id, username, email, preferences, timezone_config, language, notification_settings, is_active):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.timezone_config = timezone_config
            self.language = language
            self.notification_settings = notification_settings
            self.is_active = is_active
    user4 = UserDataProcessor(2, "johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", language="en", notification_settings=False, is_active=True)
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams___init___2:
        def __init__(self, user_id, username, email, preferences, language, is_active):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
            self.is_active = is_active
    class ConfigParams___init___2:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    class UserDataProcessor:
        def __init__(self, data_params, config_params):
            self.user_id = data_params.user_id
            self.username = data_params.username
            self.email = data_params.email
            self.preferences = data_params.preferences
            self.timezone_config = config_params.timezone_config
            self.language = data_params.language
            self.notification_settings = config_params.notification_settings
            self.is_active = data_params.is_active
    user4 = UserDataProcessor(DataParams___init___2(2, "johndoe", "johndoe@example.com", {"theme": "dark"}, language = "en", is_active = True), ConfigParams___init___2("UTC", notification_settings = False))
    """)
    test_file.write_text(code)
    smell = create_smell([2])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_constructor_2(refactorer, source_files):
    """Test for constructor with 8 params 1 unused, mix of keyword and positions params"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class UserDataProcessor:
        # 8 parameters (1 unused)
        def __init__(self, user_id, username, email, preferences, timezone_config, region, notification_settings=True, theme="light"):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.timezone_config = timezone_config
            self.region = region
            self.notification_settings = notification_settings
            # theme is unused
    user5 = UserDataProcessor(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "UTC", region="en", notification_settings=False)
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams___init___3:
        def __init__(self, user_id, username, email, preferences, region):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.region = region
    class ConfigParams___init___3:
        def __init__(self, timezone_config, notification_settings = True):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    class UserDataProcessor:
        # 8 parameters (1 unused)
        def __init__(self, data_params, config_params):
            self.user_id = data_params.user_id
            self.username = data_params.username
            self.email = data_params.email
            self.preferences = data_params.preferences
            self.timezone_config = config_params.timezone_config
            self.region = data_params.region
            self.notification_settings = config_params.notification_settings
            # theme is unused
    user5 = UserDataProcessor(DataParams___init___3(2, "janedoe", "janedoe@example.com", {"theme": "light"}, region = "en"), ConfigParams___init___3("UTC", notification_settings = False))
    """)
    test_file.write_text(code)
    smell = create_smell([3])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_instance(refactorer, source_files):
    """Test for instance method 8 params 0 unused"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class UserDataProcessor6:
        # 8 parameters (4 unused)
        def __init__(self, user_id, username, email, preferences, timezone_config, backup_config=None, display_theme=None, active_status=None):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            # timezone_config, backup_config, display_theme, active_status are unused
        # 8 parameters (no unused)
        def bulk_update(self, username, email, preferences, timezone_config, region, notification_settings, theme="light", is_active=None):
            self.username = username
            self.email = email
            self.preferences = preferences
            self.settings["timezone"] = timezone_config
            self.settings["region"] = region
            self.settings["notifications"] = notification_settings
            self.settings["theme"] = theme
            self.settings["is_active"] = is_active
    user6 = UserDataProcessor6(3, "janedoe", "janedoe@example.com", {"theme": "blue"})
    user6.bulk_update("johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", "en", True, "dark", is_active=True)
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_bulk_update_10:
        def __init__(self, username, email, preferences, region, theme = "light", is_active = None):
            self.username = username
            self.email = email
            self.preferences = preferences
            self.region = region
            self.theme = theme
            self.is_active = is_active
    class ConfigParams_bulk_update_10:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    class UserDataProcessor6:
        # 8 parameters (4 unused)
        def __init__(self, user_id, username, email, preferences, timezone_config, backup_config=None, display_theme=None, active_status=None):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            # timezone_config, backup_config, display_theme, active_status are unused
        # 8 parameters (no unused)
        def bulk_update(self, data_params, config_params):
            self.username = data_params.username
            self.email = data_params.email
            self.preferences = data_params.preferences
            self.settings["timezone"] = config_params.timezone_config
            self.settings["region"] = data_params.region
            self.settings["notifications"] = config_params.notification_settings
            self.settings["theme"] = data_params.theme
            self.settings["is_active"] = data_params.is_active
    user6 = UserDataProcessor6(3, "janedoe", "janedoe@example.com", {"theme": "blue"})
    user6.bulk_update(DataParams_bulk_update_10("johndoe", "johndoe@example.com", {"theme": "dark"}, "en", "dark", is_active = True), ConfigParams_bulk_update_10("UTC", True))
    """)
    test_file.write_text(code)
    smell = create_smell([10])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_static(refactorer, source_files):
    """Test for static method for 8 params 1 unused, default values"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class UserDataProcessor6:
        # 8 parameters (4 unused)
        def __init__(self, user_id, username, email, preferences, timezone_config, backup_config=None, display_theme=None, active_status=None):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            # timezone_config, backup_config, display_theme, active_status are unused
        # 8 parameters (1 unused)
        @staticmethod
        def generate_report_partial(username, email, preferences, timezone_config, region, notification_settings, theme, active_status=None):
            report = {}
            report.username= username
            report.email = email
            report.preferences = preferences
            report.timezone = timezone_config
            report.region = region
            report.notifications = notification_settings
            report.active_status = active_status
            #theme is unused
            return report
    UserDataProcessor6.generate_report_partial("janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", False, theme="green", active_status="online")
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_generate_report_partial_11:
        def __init__(self, username, email, preferences, region, active_status = None):
            self.username = username
            self.email = email
            self.preferences = preferences
            self.region = region
            self.active_status = active_status
    class ConfigParams_generate_report_partial_11:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    class UserDataProcessor6:
        # 8 parameters (4 unused)
        def __init__(self, user_id, username, email, preferences, timezone_config, backup_config=None, display_theme=None, active_status=None):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            # timezone_config, backup_config, display_theme, active_status are unused
        # 8 parameters (1 unused)
        @staticmethod
        def generate_report_partial(data_params, config_params):
            report = {}
            report.username= data_params.username
            report.email = data_params.email
            report.preferences = data_params.preferences
            report.timezone = config_params.timezone_config
            report.region = data_params.region
            report.notifications = config_params.notification_settings
            report.active_status = data_params.active_status
            #theme is unused
            return report
    UserDataProcessor6.generate_report_partial(DataParams_generate_report_partial_11("janedoe", "janedoe@example.com", {"theme": "light"}, "en", active_status = "online"), ConfigParams_generate_report_partial_11("PST", False))
    """)
    test_file.write_text(code)
    smell = create_smell([11])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_standalone(refactorer, source_files):
    """Test for standalone function 8 params 1 unused keyword arguments and default values"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    # 8 parameters (1 unused)
    def create_partial_report(user_id, username, email, preferences, timezone_config, language, notification_settings, active_status=None):
        report = {}
        report.user_id= user_id
        report.username = username
        report.email = email
        report.preferences = preferences
        report.timezone = timezone_config
        report.language = language
        report.notifications = notification_settings
        # active_status is unused
        return report
    create_partial_report(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", notification_settings=False)
    """)

    expected_modified_code = textwrap.dedent("""\
    # 8 parameters (1 unused)
    class DataParams_create_partial_report_2:
        def __init__(self, user_id, username, email, preferences, language):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
    class ConfigParams_create_partial_report_2:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    def create_partial_report(data_params, config_params):
        report = {}
        report.user_id= data_params.user_id
        report.username = data_params.username
        report.email = data_params.email
        report.preferences = data_params.preferences
        report.timezone = config_params.timezone_config
        report.language = data_params.language
        report.notifications = config_params.notification_settings
        # active_status is unused
        return report
    create_partial_report(DataParams_create_partial_report_2(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "en"), ConfigParams_create_partial_report_2("PST", notification_settings = False))
    """)
    test_file.write_text(code)
    smell = create_smell([2])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_most_unused_params(refactorer, source_files):
    """Test for function with 8 params that has 5 parameters unused, refactoring should only remove unused parameters"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    def create_partial_report(user_id, username, email, preferences, timezone_config, language, notification_settings, active_status=None):
        report = {}
        report.user_id = user_id
        report.username = username

    create_partial_report(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", notification_settings=False)
    """)

    expected_modified_code = textwrap.dedent("""\
    def create_partial_report(user_id, username):
        report = {}
        report.user_id = user_id
        report.username = username

    create_partial_report(2, "janedoe")
    """)
    test_file.write_text(code)
    smell = create_smell([1])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()


def test_lpl_method_operations(refactorer, source_files):
    """Test for function with 8 params that performs operations on parameters"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    def process_user_data(username, email, age, address, phone, preferences, settings, notifications):
        \"\"\"Process user data and return a formatted result.\"\"\"
        # Process the data
        full_name = username.strip()
        contact_email = email.lower()
        user_age = age + 1
        formatted_address = address.replace(',', '')
        clean_phone = phone.replace('-', '')
        user_prefs = preferences.copy()
        user_settings = settings.copy()
        notif_list = notifications.copy()
        return {
            'name': full_name,
            'email': contact_email,
            'age': user_age,
            'address': formatted_address,
            'phone': clean_phone,
            'preferences': user_prefs,
            'settings': user_settings,
            'notifications': notif_list
        }
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_process_user_data_1:
        def __init__(self, username, email, age, address, phone, preferences, notifications):
            self.username = username
            self.email = email
            self.age = age
            self.address = address
            self.phone = phone
            self.preferences = preferences
            self.notifications = notifications
    class ConfigParams_process_user_data_1:
        def __init__(self, settings):
            self.settings = settings
    def process_user_data(data_params, config_params):
        \"\"\"Process user data and return a formatted result.\"\"\"
        # Process the data
        full_name = data_params.username.strip()
        contact_email = data_params.email.lower()
        user_age = data_params.age + 1
        formatted_address = data_params.address.replace(',', '')
        clean_phone = data_params.phone.replace('-', '')
        user_prefs = data_params.preferences.copy()
        user_settings = config_params.settings.copy()
        notif_list = data_params.notifications.copy()
        return {
            'name': full_name,
            'email': contact_email,
            'age': user_age,
            'address': formatted_address,
            'phone': clean_phone,
            'preferences': user_prefs,
            'settings': user_settings,
            'notifications': notif_list
        }
    """)
    test_file.write_text(code)
    smell = create_smell([1])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_parameter_assignments(refactorer, source_files):
    """Test for handling parameter assignments and transformations in various contexts"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class DataProcessor:
        def process_data(self, input_data, output_format, config_path, temp_path, cache_path, log_path, backup_path, format_options):
            # Simple parameter assignment
            backup_path = "/new/backup/path"

            # Parameter used in computation
            cache_path = temp_path + "/cache"

            # Parameter assigned to attribute
            self.config = config_path

            # Parameter used in method call
            output_format = output_format.strip()

            # Parameter used in dictionary
            paths = {
                "input": input_data,
                "output": output_format,
                "config": config_path,
                "temp": temp_path,
                "cache": cache_path,
                "log": log_path,
                "backup": backup_path
            }

            # Parameter used in list
            all_paths = [
                input_data,
                output_format,
                config_path,
                temp_path,
                cache_path,
                log_path,
                backup_path
            ]

            # Use format options
            formatted = format_options.get("style", "default")

            return paths, all_paths, formatted

    processor = DataProcessor()
    result = processor.process_data(
        "/input",
        "json",
        "/config",
        "/temp",
        "/cache",
        "/logs",
        "/backup",
        {"style": "pretty"}
    )
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_process_data_2:
        def __init__(self, input_data, output_format):
            self.input_data = input_data
            self.output_format = output_format
    class ConfigParams_process_data_2:
        def __init__(self, config_path, temp_path, cache_path, log_path, backup_path, format_options):
            self.config_path = config_path
            self.temp_path = temp_path
            self.cache_path = cache_path
            self.log_path = log_path
            self.backup_path = backup_path
            self.format_options = format_options
    class DataProcessor:
        def process_data(self, data_params, config_params):
            # Simple parameter assignment
            config_params.backup_path = "/new/backup/path"

            # Parameter used in computation
            config_params.cache_path = config_params.temp_path + "/cache"

            # Parameter assigned to attribute
            self.config = config_params.config_path

            # Parameter used in method call
            data_params.output_format = data_params.output_format.strip()

            # Parameter used in dictionary
            paths = {
                "input": data_params.input_data,
                "output": data_params.output_format,
                "config": config_params.config_path,
                "temp": config_params.temp_path,
                "cache": config_params.cache_path,
                "log": config_params.log_path,
                "backup": config_params.backup_path
            }

            # Parameter used in list
            all_paths = [
                data_params.input_data,
                data_params.output_format,
                config_params.config_path,
                config_params.temp_path,
                config_params.cache_path,
                config_params.log_path,
                config_params.backup_path
            ]

            # Use format options
            formatted = config_params.format_options.get("style", "default")

            return paths, all_paths, formatted

    processor = DataProcessor()
    result = processor.process_data(
        DataParams_process_data_2("/input", "json"), ConfigParams_process_data_2("/config", "/temp", "/cache", "/logs", "/backup", {"style": "pretty"}))
    """)
    test_file.write_text(code)
    smell = create_smell([2])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_with_args_kwargs(refactorer, source_files):
    """Test for function with *args and **kwargs"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    def process_data(user_id, username, email, preferences, timezone_config, language, notification_settings, *args, **kwargs):
        report = {}
        # Use all regular parameters
        report.user_id = user_id
        report.username = username
        report.email = email
        report.preferences = preferences
        report.timezone = timezone_config
        report.language = language
        report.notifications = notification_settings

        # Use *args
        for arg in args:
            report.setdefault("extra_data", []).append(arg)

        # Use **kwargs
        for key, value in kwargs.items():
            report[key] = value

        return report

    # Test call with various argument types
    result = process_data(
        2,
        "janedoe",
        "janedoe@example.com",
        {"theme": "light"},
        "PST",
        "en",
        False,
        "extra1",
        "extra2",
        custom_field="custom_value",
        another_field=123
    )
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_process_data_1:
        def __init__(self, user_id, username, email, preferences, language):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
    class ConfigParams_process_data_1:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    def process_data(data_params, config_params, *args, **kwargs):
        report = {}
        # Use all regular parameters
        report.user_id = data_params.user_id
        report.username = data_params.username
        report.email = data_params.email
        report.preferences = data_params.preferences
        report.timezone = config_params.timezone_config
        report.language = data_params.language
        report.notifications = config_params.notification_settings

        # Use *args
        for arg in args:
            report.setdefault("extra_data", []).append(arg)

        # Use **kwargs
        for key, value in kwargs.items():
            report[key] = value

        return report

    # Test call with various argument types
    result = process_data(
        DataParams_process_data_1(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "en"), ConfigParams_process_data_1("PST", False), "extra1", "extra2", custom_field = "custom_value", another_field = 123)""")
    test_file.write_text(code)
    smell = create_smell([1])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_with_kwargs_only(refactorer, source_files):
    """Test for function with **kwargs"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    def process_data_2(user_id, username, email, preferences, timezone_config, language, notification_settings, **kwargs):
        report = {}
        # Use all regular parameters
        report.user_id = user_id
        report.username = username
        report.email = email
        report.preferences.update(preferences)
        report.timezone = timezone_config
        report.language = language
        report.notifications = notification_settings

        # Use **kwargs
        for key, value in kwargs.items():
            report[key] = value  # kwargs used

        # Additional processing using the parameters
        if notification_settings:
            report.timezone = f"{timezone_config}_notified"

        if "theme" in preferences:
            report.language = f"{language}_{preferences['theme']}"

        return report

    # Test call with various argument types
    result = process_data_2(
        2,
        "janedoe",
        "janedoe@example.com",
        {"theme": "light"},
        "PST",
        "en",
        False,
        custom_field="custom_value",
        another_field=123
    )
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_process_data_2_1:
        def __init__(self, user_id, username, email, preferences, language):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
    class ConfigParams_process_data_2_1:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    def process_data_2(data_params, config_params, **kwargs):
        report = {}
        # Use all regular parameters
        report.user_id = data_params.user_id
        report.username = data_params.username
        report.email = data_params.email
        report.preferences.update(data_params.preferences)
        report.timezone = config_params.timezone_config
        report.language = data_params.language
        report.notifications = config_params.notification_settings

        # Use **kwargs
        for key, value in kwargs.items():
            report[key] = value  # kwargs used

        # Additional processing using the parameters
        if config_params.notification_settings:
            report.timezone = f"{config_params.timezone_config}_notified"

        if "theme" in data_params.preferences:
            report.language = f"{data_params.language}_{data_params.preferences['theme']}"

        return report

    # Test call with various argument types
    result = process_data_2(
        DataParams_process_data_2_1(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "en"), ConfigParams_process_data_2_1("PST", False), custom_field = "custom_value", another_field = 123)""")
    test_file.write_text(code)
    smell = create_smell([1])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_complex_attribute_access(refactorer, source_files):
    """Test for complex attribute access and nested parameter usage"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "fake.py"

    code = textwrap.dedent("""\
    class DataProcessor:
        def process_complex_data(self, user_data, setup_data, cache_data, log_data, temp_data, backup_data, format_data, extra_data):
            # Complex attribute access and assignments
            self.settings = {
                "user": user_data,
                "config": setup_data.settings,
                "cache": cache_data.path,
                "logs": log_data.directory,
                "temp": temp_data.location,
                "backup": backup_data.storage,
                "format": format_data.options,
                "extra": extra_data.metadata
            }

            # Nested attribute access
            if setup_data.settings["enabled"]:
                user_data.preferences["theme"] = format_data.options["theme"]

            # Complex assignments
            backup_data.storage["path"] = temp_data.location + "/backup"
            cache_data.path = temp_data.location + "/cache"

            # Method calls on parameters
            cleaned_user = user_data.name.strip().lower()
            formatted_config = setup_data.format()

            # Dictionary comprehension using parameters
            result = {
                key: value.strip()
                for key, value in user_data.metadata.items()
                if key in setup_data.allowed_keys
            }

            return result

    processor = DataProcessor()
    result = processor.process_complex_data(
        user_data={"name": "  John  ", "metadata": {"id": "123 ", "role": " admin "}},
        setup_data={"settings": {"enabled": True}, "allowed_keys": ["id"]},
        cache_data={"path": "/tmp/cache"},
        log_data={"directory": "/var/log"},
        temp_data={"location": "/tmp"},
        backup_data={"storage": {}},
        format_data={"options": {"theme": "dark"}},
        extra_data={"metadata": {}}
    )
    """)

    expected_modified_code = textwrap.dedent("""\
    class DataParams_process_complex_data_2:
        def __init__(self, user_data, setup_data, cache_data, log_data, temp_data, backup_data, format_data, extra_data):
            self.user_data = user_data
            self.setup_data = setup_data
            self.cache_data = cache_data
            self.log_data = log_data
            self.temp_data = temp_data
            self.backup_data = backup_data
            self.format_data = format_data
            self.extra_data = extra_data
    class DataProcessor:
        def process_complex_data(self, data_params):
            # Complex attribute access and assignments
            self.settings = {
                "user": data_params.user_data,
                "config": data_params.setup_data.settings,
                "cache": data_params.cache_data.path,
                "logs": data_params.log_data.directory,
                "temp": data_params.temp_data.location,
                "backup": data_params.backup_data.storage,
                "format": data_params.format_data.options,
                "extra": data_params.extra_data.metadata
            }

            # Nested attribute access
            if data_params.setup_data.settings["enabled"]:
                data_params.user_data.preferences["theme"] = data_params.format_data.options["theme"]

            # Complex assignments
            data_params.backup_data.storage["path"] = data_params.temp_data.location + "/backup"
            data_params.cache_data.path = data_params.temp_data.location + "/cache"

            # Method calls on parameters
            cleaned_user = data_params.user_data.name.strip().lower()
            formatted_config = data_params.setup_data.format()

            # Dictionary comprehension using parameters
            result = {
                key: value.strip()
                for key, value in data_params.user_data.metadata.items()
                if key in data_params.setup_data.allowed_keys
            }

            return result

    processor = DataProcessor()
    result = processor.process_complex_data(
        DataParams_process_complex_data_2(user_data = {"name": "  John  ", "metadata": {"id": "123 ", "role": " admin "}}, setup_data = {"settings": {"enabled": True}, "allowed_keys": ["id"]}, cache_data = {"path": "/tmp/cache"}, log_data = {"directory": "/var/log"}, temp_data = {"location": "/tmp"}, backup_data = {"storage": {}}, format_data = {"options": {"theme": "dark"}}, extra_data = {"metadata": {}}))
    """)
    test_file.write_text(code)
    smell = create_smell([2])()
    refactorer.refactor(test_file, test_dir, smell, test_file)

    modified_code = test_file.read_text()
    assert modified_code.strip() == expected_modified_code.strip()

    # cleanup after test
    test_file.unlink()
    test_dir.rmdir()


def test_lpl_multi_file_refactor(refactorer, source_files):
    """Test refactoring a function that is called from another file"""

    test_dir = source_files / "temp_test_lpl"
    test_dir.mkdir(exist_ok=True)

    # Create the main file with function definition
    main_file = test_dir / "main.py"
    main_code = textwrap.dedent("""\
    def process_user_data(user_id, username, email, preferences, timezone_config, language, notification_settings, theme):
        result = {
            'id': user_id,
            'name': username,
            'email': email,
            'prefs': preferences,
            'tz': timezone_config,
            'lang': language,
            'notif': notification_settings,
            'theme': theme
        }
        return result
    """)
    main_file.write_text(main_code)

    # Create another file that uses this function
    user_file = test_dir / "user_processor.py"
    user_code = textwrap.dedent("""\
    from main import process_user_data

    def handle_user():
        # Call with positional args
        result1 = process_user_data(
            1,
            "john",
            "john@example.com",
            {"theme": "light"},
            "PST",
            "en",
            False,
            "dark"
        )

        # Call with keyword args
        result2 = process_user_data(
            user_id=2,
            username="jane",
            email="jane@example.com",
            preferences={"theme": "dark"},
            timezone_config="UTC",
            language="fr",
            notification_settings=True,
            theme="light"
        )

        return result1, result2
    """)
    user_file.write_text(user_code)

    # Expected output for main.py
    expected_main_code = textwrap.dedent("""\
    class DataParams_process_user_data_1:
        def __init__(self, user_id, username, email, preferences, language, theme):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
            self.theme = theme
    class ConfigParams_process_user_data_1:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings
    def process_user_data(data_params, config_params):
        result = {
            'id': data_params.user_id,
            'name': data_params.username,
            'email': data_params.email,
            'prefs': data_params.preferences,
            'tz': config_params.timezone_config,
            'lang': data_params.language,
            'notif': config_params.notification_settings,
            'theme': data_params.theme
        }
        return result
    """)

    # Expected output for user_processor.py
    expected_user_code = textwrap.dedent("""\
    from main import process_user_data
    class DataParams_process_user_data_1:
        def __init__(self, user_id, username, email, preferences, language, theme):
            self.user_id = user_id
            self.username = username
            self.email = email
            self.preferences = preferences
            self.language = language
            self.theme = theme
    class ConfigParams_process_user_data_1:
        def __init__(self, timezone_config, notification_settings):
            self.timezone_config = timezone_config
            self.notification_settings = notification_settings

    def handle_user():
        # Call with positional args
        result1 = process_user_data(
            DataParams_process_user_data_1(1, "john", "john@example.com", {"theme": "light"}, "en", "dark"), ConfigParams_process_user_data_1("PST", False))

        # Call with keyword args
        result2 = process_user_data(
            DataParams_process_user_data_1(user_id = 2, username = "jane", email = "jane@example.com", preferences = {"theme": "dark"}, language = "fr", theme = "light"), ConfigParams_process_user_data_1(timezone_config = "UTC", notification_settings = True))

        return result1, result2
    """)

    # Apply the refactoring
    smell = create_smell([1])()
    refactorer.refactor(main_file, test_dir, smell, main_file)

    # Verify both files were updated correctly
    modified_main_code = main_file.read_text()
    modified_user_code = user_file.read_text()

    assert modified_main_code.strip() == expected_main_code.strip()
    assert modified_user_code.strip() == expected_user_code.strip()

    # cleanup after test
    main_file.unlink()
    user_file.unlink()
    test_dir.rmdir()
