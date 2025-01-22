import math  # Unused import

# Code Smell: Long Parameter List
class Vehicle:
    def __init__(self, make, model, year, color, fuel_type, mileage, transmission, price):
        # Code Smell: Long Parameter List in __init__
        self.make = make
        self.model = model
        self.year = year
        self.color = color
        self.fuel_type = fuel_type
        self.mileage = mileage
        self.transmission = transmission
        self.price = price
        self.owner = None  # Unused class attribute, used in constructor

    def display_info(self):
        # Code Smell: Long Message Chain
        print(f"Make: {self.make}, Model: {self.model}, Year: {self.year}".upper().replace(",", "")[::2])

    def calculate_price(self):
        # Code Smell: List Comprehension in an All Statement
        condition = all([isinstance(attribute, str) for attribute in [self.make, self.model, self.year, self.color]])
        if condition:
            return self.price * 0.9  # Apply a 10% discount if all attributes are strings (totally arbitrary condition)
        
        return self.price

    def unused_method(self):
        # Code Smell: Member Ignoring Method
        print("This method doesn't interact with instance attributes, it just prints a statement.")

class Car(Vehicle):
    def __init__(self, make, model, year, color, fuel_type, mileage, transmission, price, sunroof=False):
        super().__init__(make, model, year, color, fuel_type, mileage, transmission, price)
        self.sunroof = sunroof
        self.engine_size = 2.0  # Unused variable in class

    def add_sunroof(self):
        # Code Smell: Long Parameter List
        self.sunroof = True
        print("Sunroof added!")

    def show_details(self):
        # Code Smell: Long Message Chain
        details = f"Car: {self.make} {self.model} ({self.year}) | Mileage: {self.mileage} | Transmission: {self.transmission} | Sunroof: {self.sunroof}"
        print(details.upper().lower().upper().capitalize().upper().replace("|", "-"))

def process_vehicle(vehicle):
    # Code Smell: Unused Variables
    temp_discount = 0.05
    temp_shipping = 100

    vehicle.display_info()
    price_after_discount = vehicle.calculate_price()
    print(f"Price after discount: {price_after_discount}")
    
    vehicle.unused_method()  # Calls a method that doesn't actually use the class attributes

def is_all_string(attributes):
    # Code Smell: List Comprehension in an All Statement
    return all(isinstance(attribute, str) for attribute in attributes)

def access_nested_dict():
    nested_dict1 = {
        "level1": {
            "level2": {
                "level3": {
                    "key": "value"
                }
            }
        }
    }

    nested_dict2 = {
        "level1": {
            "level2": {
                "level3": {
                    "key": "value",
                    "key2": "value2"
                },
                "level3a": {
                    "key": "value"
                }
            }
        }
    }
    print(nested_dict1["level1"]["level2"]["level3"]["key"])
    print(nested_dict2["level1"]["level2"]["level3"]["key2"])
    print(nested_dict2["level1"]["level2"]["level3"]["key"])
    print(nested_dict2["level1"]["level2"]["level3a"]["key"])
    print(nested_dict1["level1"]["level2"]["level3"]["key"])

# Main loop: Arbitrary use of the classes and demonstrating code smells
if __name__ == "__main__":
    car1 = Car(make="Toyota", model="Camry", year=2020, color="Blue", fuel_type="Gas", mileage=25000, transmission="Automatic", price=20000)
    process_vehicle(car1)
    car1.add_sunroof()
    car1.show_details()

    # Testing with another vehicle object
    car2 = Vehicle(make="Honda", model="Civic", year=2018, color="Red", fuel_type="Gas", mileage=30000, transmission="Manual", price=15000)
    process_vehicle(car2)

    car1.unused_method()
