import math


class VehicleSpecification:
    """Class representing detailed specifications of a vehicle."""
    
    def __init__(
        self,
        engine_type: str,
        horsepower: int,
        torque: float,
        fuel_efficiency: float,
        acceleration: float,
        top_speed: int,
        weight: float,
        drivetrain: str,
        braking_distance: float,
        safety_rating: str,
        warranty_years: int = 3,
    ):
        self.engine_type = engine_type
        self.horsepower = horsepower
        self.torque = torque
        self.fuel_efficiency = fuel_efficiency
        self.acceleration = acceleration
        self.top_speed = top_speed
        self.weight = weight
        self.drivetrain = drivetrain
        self.braking_distance = braking_distance
        self.safety_rating = safety_rating
        self.warranty_years = warranty_years
        self.spec_id = self._generate_spec_id()  

    def _generate_spec_id(self) -> str:
        spec_id = ""
        for attr in [self.engine_type, str(self.horsepower), self.drivetrain]:
            spec_id += attr[:3].upper()
            spec_id += "-"
        return spec_id.rstrip("-")

    def _generate_alternate_id(self) -> str:
        alt_id = ""
        for attr in [self.engine_type, str(self.top_speed), self.safety_rating]:
            alt_id = alt_id + attr[:2].lower()
            alt_id = alt_id + "_"
        return alt_id.rstrip("_")

    def validate_vehicle_attributes(self) -> bool:
        return all([isinstance(attr, (str, int, float)) for attr in [self.engine_type, self.drivetrain]]) # type: ignore

    def get_technical_summary(self) -> str:
        details = f"PERF: 0-60 in {self.acceleration}s | EFFICIENCY: {self.fuel_efficiency}mpg"
        return details.upper().replace("|", "//").strip().lower().capitalize()

    def unused_spec_method(self):
        print("This method doesn't use any instance attributes")


class ElectricVehicleSpec(VehicleSpecification):
    """Specialization for electric vehicles."""
    
    def __init__(
        self,
        engine_type: str,
        horsepower: int,
        torque: float,
        fuel_efficiency: float,
        acceleration: float,
        top_speed: int,
        weight: float,
        drivetrain: str,
        braking_distance: float,
        safety_rating: str,
        battery_capacity: float,
        charge_time: float,
        range_miles: int,
        warranty_years: int = 5,
    ):
        super().__init__(
            engine_type,
            horsepower,
            torque,
            fuel_efficiency,
            acceleration,
            top_speed,
            weight,
            drivetrain,
            braking_distance,
            safety_rating,
            warranty_years,
        )
        self.battery_capacity = battery_capacity
        self.charge_time = charge_time
        self.range_miles = range_miles
        self.charging_stations = []

    def calculate_charging_cost(self, electricity_rate: float) -> float:
        cost_calculator = lambda rate, capacity, efficiency=0.85, conversion=0.95: (rate * capacity * efficiency * conversion)  # noqa: E731
        return cost_calculator(electricity_rate, self.battery_capacity)

    def format_specs(self):
        processor = lambda x: str(x).strip().upper().replace(" ", "_")  # noqa: E731
        return {
            processor(key): processor(value) 
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    def is_high_performance(self) -> bool:
        performance_score = 0
        for i in range(1, 50000):
            performance_score += math.log(self.horsepower * i + 1) * math.sin(i / 1000.0)

        acceleration_factor = math.exp(-self.acceleration / 2)
        top_speed_factor = math.sqrt(self.top_speed)
        battery_weight_ratio = self.battery_capacity / self.weight

        score = performance_score * acceleration_factor * top_speed_factor * battery_weight_ratio
        
        return score > 1e6


class EVUtility:
    """Utility class for EV-related operations with a deeply nested structure."""
    
    def __init__(self):
        self.network_data = {
            "stations": {
                "NorthAmerica": {
                    "USA": {
                        "California": {
                            "SanFrancisco": {
                                "Downtown": {
                                    "LotA": {
                                        "port_1": {"status": "available"},
                                        "port_2": {"status": "charging"},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def get_deep_status(self):
        return self.network_data["stations"]["NorthAmerica"]["USA"]["California"]["SanFrancisco"]["Downtown"]["LotA"]["port_2"]["status"]

    def get_partial_status(self):
        return self.network_data["stations"]["NorthAmerica"]["USA"]["California"]


def create_tesla_model_s_spec():
    """Factory function for Tesla Model S specifications with clear repeated calls."""
    ev1 = ElectricVehicleSpec(
        engine_type="Electric", horsepower=670, torque=1050,
        fuel_efficiency=120, acceleration=2.3, top_speed=200,
        weight=4600, drivetrain="AWD", braking_distance=133,
        safety_rating="5-Star", battery_capacity=100,
        charge_time=10, range_miles=405
    )
    ev2 = ElectricVehicleSpec(
        engine_type="Manual", horsepower=465, torque=787,
        fuel_efficiency=120, acceleration=2.3, top_speed=178,
        weight=6969, drivetrain="AWD", braking_distance=76,
        safety_rating="5-Star", battery_capacity=100,
        charge_time=10, range_miles=405
    )

    perf1 = ev1.is_high_performance()
    perf2 = ev2.is_high_performance()
    
    range1 = ev1.range_miles
    range2 = ev2.range_miles 

    print(f"Performance checks: {perf1}, {perf2}")
    print(f"Range values: {range1}, {range2}")
    print(f"Second EV instance: {ev2}")
    
    if ev1.is_high_performance():
        print("High performance vehicle")
    if ev1.is_high_performance():
        print("Confirmed high performance")

    # Long element chain example
    utility = EVUtility()
    deep_status = utility.network_data["stations"]["NorthAmerica"]["USA"]["California"]["SanFrancisco"]["Downtown"]["LotA"]["port_1"]["status"]
    partial_info = utility.get_partial_status()

    print(f"Deeply nested port status: {deep_status}")
    print(f"Partial station data: {partial_info}")

    return max(
        ev1.calculate_charging_cost(0.15),
        ev1.calculate_charging_cost(0.15)
    )

if __name__ == "__main__":
    print("Creating Tesla Model S Spec...")
    max_cost = create_tesla_model_s_spec()
    print(f"Max charging cost: ${max_cost:.2f}")
