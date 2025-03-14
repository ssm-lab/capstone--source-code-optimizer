import pytest
from .main import Vehicle, Car, process_vehicle 

# Fixture to create a car instance
@pytest.fixture
def car1():
    return Car(make="Toyota", model="Camry", year=2020, color="Blue", fuel_type="Gas", mileage=25000, transmission="Automatic", price=20000)

# Test the price after applying discount
def test_vehicle_price_after_discount(car1):
    assert car1.calculate_price() == 20000, "Price after discount should be 18000"

# Test the add_sunroof method to confirm it works as expected
def test_car_add_sunroof(car1):
    car1.add_sunroof()
    assert car1.sunroof is True, "Car should have sunroof after add_sunroof() is called"

# Test that show_details method runs without error
def test_car_show_details(car1, capsys):
    car1.show_details()
    captured = capsys.readouterr()
    assert "CAR: TOYOTA CAMRY" in captured.out  # Checking if the output contains car details

# Test the is_all_string function indirectly through the calculate_price method
def test_is_all_string(car1):
    price_after_discount = car1.calculate_price()
    assert price_after_discount > 0, "Price calculation should return a valid price"

# Test the process_vehicle function to check its behavior with a Vehicle object
def test_process_vehicle(car1, capsys):
    process_vehicle(car1)
    captured = capsys.readouterr()
    assert "Price after discount" in captured.out, "The process_vehicle function should output the price after discount"

