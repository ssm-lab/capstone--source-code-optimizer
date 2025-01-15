class DataParams:

    def __init__(self, sunroof, price, year, transmission, mileage,
        fuel_type, make, model, color):
        self.sunroof = sunroof
        self.price = price
        self.year = year
        self.transmission = transmission
        self.mileage = mileage
        self.fuel_type = fuel_type
        self.make = make
        self.model = model
        self.color = color


import math


class Vehicle:

    def __init__(self, make, model, year, color, fuel_type, mileage,
        transmission, price):
        self.make = make
        self.model = model
        self.year = year
        self.color = color
        self.fuel_type = fuel_type
        self.mileage = mileage
        self.transmission = transmission
        self.price = price
        self.owner = None

    def display_info(self):
        print(f'Make: {self.make}, Model: {self.model}, Year: {self.year}'.
            upper().replace(',', '')[::2])

    def calculate_price(self):
        condition = all([isinstance(attribute, str) for attribute in [self.
            make, self.model, self.year, self.color]])
        if condition:
            return self.price * 0.9
        return self.price

    def unused_method(self):
        print(
            "This method doesn't interact with instance attributes, it just prints a statement."
            )


class Car(Vehicle):

    def __init__(self, data_params, config_params=False):
        super().__init__(data_params.make, data_params.model, data_params.
            year, data_params.color, data_params.fuel_type, data_params.
            mileage, data_params.transmission, data_params.price)
        self.sunroof = data_params.sunroof
        self.engine_size = 2.0

    def add_sunroof(self):
        self.sunroof = True
        print('Sunroof added!')

    def show_details(self):
        details = (
            f'Car: {self.make} {self.model} ({self.year}) | Mileage: {self.mileage} | Transmission: {self.transmission} | Sunroof: {self.sunroof}'
            )
        print(details.upper().lower().upper().capitalize().upper().replace(
            '|', '-'))


def process_vehicle(vehicle):
    temp_discount = 0.05
    temp_shipping = 100
    vehicle.display_info()
    price_after_discount = vehicle.calculate_price()
    print(f'Price after discount: {price_after_discount}')
    vehicle.unused_method()


def is_all_string(attributes):
    return all(isinstance(attribute, str) for attribute in attributes)


if __name__ == '__main__':
    car1 = Car(make='Toyota', model='Camry', year=2020, color='Blue',
        fuel_type='Gas', mileage=25000, transmission='Automatic', price=20000)
    process_vehicle(car1)
    car1.add_sunroof()
    car1.show_details()
    car2 = Vehicle(make='Honda', model='Civic', year=2018, color='Red',
        fuel_type='Gas', mileage=30000, transmission='Manual', price=15000)
    process_vehicle(car2)
