class Utility:
    def long_element_chain(self):
        """
        A method that accepts a parameter but doesn’t use it.
        This demonstrates the member ignoring code smell.
        """

        long_chain = {
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
        
        print("This method has a long element chain.")

        return long_chain
    
    def get_value(self, result):
        return result["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["level7"]
