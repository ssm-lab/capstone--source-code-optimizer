from car_models import VehicleSpecification


def manage_fleet():
    """
    Example function to demonstrate multiple code smells in a vehicle management context.
    """
    vehicle = VehicleSpecification(
        engine_type="Hybrid",
        horsepower=300,
        torque=400.5,
        fuel_efficiency=45.2,
        acceleration=6.2,
        top_speed=150,
        weight=3200.0,
        drivetrain="FWD",
        braking_distance=120.5,
        safety_rating="4-Star"
    )

    diagnostics = lambda a, b, c, d, e: ((a + b) * (c - d) / (e + 1) + (a * d) - (c ** 2) + (e * b - a / c) + a + b + c + d + e)  # noqa: E731
    print("Running diagnostics:", diagnostics(1, 2, 3, 4, 5))

    vehicle.unused_spec_method()

    status = ""
    for i in range(5):
        status += "Status-" + str(i) + "; "
    print("Status Log:", status)

    report = {"summary": ""}
    for i in range(3):
        report["summary"] += f"Trip-{i}, "
    print("Trip Summary:", report["summary"])

    return vehicle.get_technical_summary()


if __name__ == "__main__":
    summary = manage_fleet()
    print("Vehicle Summary:", summary)
