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
