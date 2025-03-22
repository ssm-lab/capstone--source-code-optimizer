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
    print("***************************************")
    print(modified_code.strip())
    print("***************************************")
    print(expected_modified_code.strip())
    print("***************************************")
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
    print("***************************************")
    print(modified_code.strip())
    print("***************************************")
    print(expected_modified_code.strip())
    print("***************************************")
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
