from src.utils import Utility

def process_data(data):
    """
    Process some data and call the long_element_chain method from Utility.
    """
    util = Utility()
    result = util.long_element_chain()
    value1 = result["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["level7"]
    value2 = util.get_value(result)
    print(f"Extracted Value1: {value1}")
    print(f"Extracted Value2: {value2}")
    return data.upper()


