from src.utils import Utility

def process_data(data):
    """
    Process some data and call the long_element_chain method from Utility.
    """
    util = Utility()
    my_call = util.long_chain["level1"]["level2"]["level3"]["level4"]["level5"]["level6"]["level7"]
    lastVal = util.get_last_value()
    fourthLevel = util.get_4th_level_value()   
    print(f"My call here: {my_call}")
    print(f"Extracted Value1: {lastVal}")
    print(f"Extracted Value2: {fourthLevel}")
    return data.upper()


