################################################ Constructors ###############################################################
class UserDataProcessor1:
    # 1. 0 parameters
    def __init__(self):
        self.config = {}
        self.data = []

class UserDataProcessor2:
    # 2. 4 parameters (no unused)
    def __init__(self, user_id, username, email, app_config):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.app_config = app_config

class UserDataProcessor3:
    # 3. 4 parameters (1 unused)
    def __init__(self, user_id, username, email, theme="light"):
        self.user_id = user_id
        self.username = username
        self.email = email
        # theme is unused

class UserDataProcessor4:
    # 4. 8 parameters (no unused)
    def __init__(self, user_id, username, email, preferences, timezone, language, notification_settings, is_active):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.preferences = preferences
        self.timezone = timezone
        self.language = language
        self.notification_settings = notification_settings
        self.is_active = is_active

class UserDataProcessor5:
    # 5. 8 parameters (1 unused)
    def __init__(self, user_id, username, email, preferences, timezone, region, notification_settings, theme="light"):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.preferences = preferences
        self.timezone = timezone
        self.region = region
        self.notification_settings = notification_settings
        # theme is unused

class UserDataProcessor6:
    # 6. 8 parameters (4 unused)
    def __init__(self, user_id, username, email, preferences, timezone, backup_config=None, display_theme=None, active_status=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.preferences = preferences
        # timezone, backup_config, display_theme, active_status are unused

    ################################################ Instance Methods ###############################################################
    # 1. 0 parameters
    def clear_data(self):
        self.data = []

    # 2. 4 parameters (no unused)
    def update_settings(self, display_mode, alert_settings, language_preference, timezone):
        self.settings["display_mode"] = display_mode
        self.settings["alert_settings"] = alert_settings
        self.settings["language_preference"] = language_preference
        self.settings["timezone"] = timezone

    # 3. 4 parameters (1 unused)
    def update_profile(self, username, email, timezone, bio=None):
        self.username = username
        self.email = email
        self.settings["timezone"] = timezone
        # bio is unused

    # 4. 8 parameters (no unused)
    def bulk_update(self, username, email, preferences, timezone, region, notifications, theme="light", is_active=None):
        self.username = username
        self.email = email
        self.preferences = preferences
        self.settings["timezone"] = timezone
        self.settings["region"] = region
        self.settings["notifications"] = notifications
        self.settings["theme"] = theme
        self.settings["is_active"] = is_active

    # 5. 8 parameters (1 unused)
    def bulk_update_partial(self, username, email, preferences, timezone, region, notifications, theme, active_status=None):
        self.username = username
        self.email = email
        self.preferences = preferences
        self.settings["timezone"] = timezone
        self.settings["region"] = region
        self.settings["notifications"] = notifications
        self.settings["theme"] = theme
        # active_status is unused

    # 6. 7 parameters (3 unused)
    def partial_update(self, username, email, preferences, timezone, backup_config=None, display_theme=None, active_status=None):
        self.username = username
        self.email = email
        self.preferences = preferences
        self.settings["timezone"] = timezone
        # backup_config, display_theme, active_status are unused

################################################ Static Methods ###############################################################

    # 1. 0 parameters
    @staticmethod
    def reset_global_settings():
        return {"theme": "default", "language": "en", "notifications": True}

    # 2. 4 parameters (no unused)
    @staticmethod
    def validate_user_input(username, email, password, age):
        return all([username, email, password, age >= 18])

    # 3. 4 parameters (2 unused)
    @staticmethod
    def hash_password(password, salt, encryption="SHA256", retries=1000):
        # encryption and retries are unused
        return f"hashed({password} + {salt})"

    # 4. 8 parameters (no unused)
    @staticmethod
    def generate_report(username, email, preferences, timezone, region, notifications, theme, is_active):
        return {
            "username": username,
            "email": email,
            "preferences": preferences,
            "timezone": timezone,
            "region": region,
            "notifications": notifications,
            "theme": theme,
            "is_active": is_active,
        }

    # 5. 8 parameters (1 unused)
    @staticmethod
    def generate_report_partial(username, email, preferences, timezone, region, notifications, theme, active_status=None):
        return {
            "username": username,
            "email": email,
            "preferences": preferences,
            "timezone": timezone,
            "region": region,
            "notifications": notifications,
            "active status": active_status,
        }
        # theme is unused

    # 6. 8 parameters (3 unused)
    @staticmethod
    def minimal_report(username, email, preferences, timezone, backup, region="Global", display_mode=None, status=None):
        return {
            "username": username,
            "email": email,
            "preferences": preferences,
            "timezone": timezone,
            "region": region
        }
        # backup, display_mode, status are unused


################################################ Standalone Functions ###############################################################

# 1. 0 parameters
def reset_system():
    return "System reset completed"

# 2. 4 parameters (no unused)
def calculate_discount(price, discount_rate, minimum_purchase, maximum_discount):
    if price >= minimum_purchase:
        return min(price * discount_rate, maximum_discount)
    return 0

# 3. 4 parameters (1 unused)
def apply_coupon(coupon_code, expiry_date, discount_rate, minimum_order=None):
    return f"Coupon {coupon_code} applied with {discount_rate}% off until {expiry_date}"
    # minimum_order is unused

# 4. 8 parameters (no unused)
def create_user_report(user_id, username, email, preferences, timezone, language, notifications, is_active):
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "preferences": preferences,
        "timezone": timezone,
        "language": language,
        "notifications": notifications,
        "is_active": is_active,
    }

# 5. 8 parameters (1 unused)
def create_partial_report(user_id, username, email, preferences, timezone, language, notifications, active_status=None):
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "preferences": preferences,
        "timezone": timezone,
        "language": language,
        "notifications": notifications,
    }
    # active_status is unused

# 6. 8 parameters (3 unused)
def create_minimal_report(user_id, username, email, preferences, timezone, backup_config=None, alert_settings=None, active_status=None):
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "preferences": preferences,
        "timezone": timezone,
    }
    # backup_config, alert_settings, active_status are unused

################################################ Calls ###############################################################

# Constructor calls
user1 = UserDataProcessor1()
user2 = UserDataProcessor2(1, "johndoe", "johndoe@example.com", app_config={"theme": "dark"})
user3 = UserDataProcessor3(1, "janedoe", email="janedoe@example.com")
user4 = UserDataProcessor4(2, "johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", language="en", notification_settings=False, is_active=True)
user5 = UserDataProcessor5(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "UTC", region="en", notification_settings=False)
user6 = UserDataProcessor6(3, "janedoe", "janedoe@example.com", {"theme": "blue"}, timezone="PST")

# Instance method calls
user6.clear_data()
user6.update_settings("dark_mode", True, "en", timezone="UTC")
user6.update_profile(username="janedoe", email="janedoe@example.com", timezone="PST")
user6.bulk_update("johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", "en", True, "dark", is_active=True)
user6.bulk_update_partial("janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", False, "light", active_status="offline")
user6.partial_update("janedoe", "janedoe@example.com", preferences={"theme": "blue"}, timezone="PST")

# Static method calls
UserDataProcessor6.reset_global_settings()
UserDataProcessor6.validate_user_input("johndoe", "johndoe@example.com", password="password123", age=25)
UserDataProcessor6.hash_password("password123", "salt123", retries=200)
UserDataProcessor6.generate_report("johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", "en", True, "dark", True)
UserDataProcessor6.generate_report_partial("janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", False, theme="green", active_status="online")
UserDataProcessor6.minimal_report("janedoe", "janedoe@example.com", {"theme": "blue"}, "PST", False, "Canada")

# Standalone function calls
reset_system()
calculate_discount(price=100, discount_rate=0.1, minimum_purchase=50, maximum_discount=20)
apply_coupon("SAVE10", "2025-12-31", 10, minimum_order=2)
create_user_report(1, "johndoe", "johndoe@example.com", {"theme": "dark"}, "UTC", "en", True, True)
create_partial_report(2, "janedoe", "janedoe@example.com", {"theme": "light"}, "PST", "en", notifications=False)
create_minimal_report(3, "janedoe", "janedoe@example.com", {"theme": "blue"}, timezone="PST")

